#!/usr/bin/env python3
"""
Kangaroo - Python Implementation of Pollard's Kangaroo Algorithm
Solves the discrete logarithm problem on secp256k1 elliptic curve

Usage:
  kangaroo.py [options] <config_file>
  kangaroo.py -s [options]          # Server mode
  kangaroo.py -c <server_ip>        # Client mode
"""

import sys
import argparse
import signal
from typing import Optional

from ec_operations import Point, public_key_to_point, point_to_public_key, point_multiply, Gx, Gy
from kangaroo_engine import KangarooEngine
from work_file import WorkFile
from config_parser import ConfigParser
from network_server import KangarooServer
from network_client import KangarooClient


VERSION = "1.0 (Python)"


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nReceived interrupt signal, shutting down...")
    sys.exit(0)


def print_version():
    """Print version information"""
    print(f"Kangaroo {VERSION}")
    print("Python implementation of Pollard's Kangaroo algorithm")
    print("For solving ECDLP on secp256k1 curve")


def print_banner():
    """Print banner"""
    print("=" * 70)
    print("  KANGAROO - Pollard's Kangaroo Algorithm for secp256k1")
    print(f"  Version: {VERSION}")
    print("=" * 70)
    print()


def run_standalone(args):
    """Run in standalone mode (single machine)"""
    print_banner()
    
    # Parse configuration
    if not args.input_file:
        print("Error: Configuration file required")
        print("Use -h for help")
        return 1
    
    config = ConfigParser.parse_file(args.input_file)
    if config is None:
        return 1
    
    # Override config with command line args
    if args.threads:
        config['threads'] = args.threads
    if args.dp_bits:
        config['dp_bits'] = args.dp_bits
    
    threads = config.get('threads', 1)
    dp_bits = config.get('dp_bits', None)
    
    # Create engine
    engine = KangarooEngine(
        public_key=config['public_key'],
        range_start=config['range_start'],
        range_end=config['range_end'],
        dp_bits=dp_bits,
        num_threads=threads
    )
    
    # Load work file if specified
    if args.load_work:
        work_state = WorkFile.load(args.load_work)
        if work_state:
            try:
                engine.load_work_state(work_state)
            except Exception as e:
                print(f"Error loading work state: {e}")
                return 1
    
    # Setup auto-save
    save_interval = args.work_interval if args.work_interval else 300  # Default 5 minutes
    last_save_time = [0]  # Use list to allow modification in nested function
    
    def auto_save():
        import time
        if args.save_work and (time.time() - last_save_time[0]) > save_interval:
            work_state = engine.get_work_state()
            WorkFile.save(args.save_work, work_state, args.save_kangaroos)
            last_save_time[0] = time.time()
    
    # Run solver
    try:
        # Setup periodic save (if enabled)
        if args.save_work:
            import threading
            def save_loop():
                import time
                while not engine.stop_flag.is_set():
                    time.sleep(save_interval)
                    auto_save()
            
            save_thread = threading.Thread(target=save_loop)
            save_thread.daemon = True
            save_thread.start()
        
        # Solve
        solution = engine.solve(
            max_time=args.max_time,
            max_operations=args.max_operations
        )
        
        # Save final work
        if args.save_work:
            auto_save()
        
        # Save solution if found
        if solution and args.output:
            with open(args.output, 'w') as f:
                f.write(f"Private Key (decimal): {solution}\n")
                f.write(f"Private Key (hex): {hex(solution)}\n")
                f.write(f"Public Key: {point_to_public_key(config['public_key'])}\n")
            print(f"\nSolution saved to {args.output}")
        
        return 0 if solution else 1
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        if args.save_work:
            auto_save()
        return 1


def run_server(args):
    """Run in server mode"""
    print_banner()
    
    # Parse configuration
    if not args.input_file:
        print("Error: Configuration file required for server mode")
        return 1
    
    config = ConfigParser.parse_file(args.input_file)
    if config is None:
        return 1
    
    # Override config
    if args.dp_bits:
        config['dp_bits'] = args.dp_bits
    
    dp_bits = config.get('dp_bits', None)
    if dp_bits is None:
        from utils import calculate_optimal_dp_bits
        dp_bits = calculate_optimal_dp_bits(config['range_end'] - config['range_start'])
    
    port = args.server_port if args.server_port else 17403
    timeout = args.network_timeout if args.network_timeout else 3000
    
    # Create server
    server = KangarooServer(
        public_key=config['public_key'],
        range_start=config['range_start'],
        range_end=config['range_end'],
        dp_bits=dp_bits,
        port=port,
        timeout=timeout
    )
    
    # Setup auto-save
    if args.save_work:
        import threading
        save_interval = args.work_interval if args.work_interval else 300
        
        def save_loop():
            import time
            while server.running:
                time.sleep(save_interval)
                work_state = server.get_work_state()
                WorkFile.save(args.save_work, work_state)
        
        save_thread = threading.Thread(target=save_loop)
        save_thread.daemon = True
        save_thread.start()
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.stop()
        
        if args.save_work:
            work_state = server.get_work_state()
            WorkFile.save(args.save_work, work_state)
    
    return 0


def run_client(args):
    """Run in client mode"""
    print_banner()
    
    threads = args.threads if args.threads else 1
    port = args.server_port if args.server_port else 17403
    timeout = args.network_timeout if args.network_timeout else 3000
    
    # Create client
    client = KangarooClient(
        server_ip=args.server_ip,
        port=port,
        timeout=timeout,
        num_threads=threads
    )
    
    # Connect to server
    if not client.connect():
        return 1
    
    # Run
    try:
        client.run()
    except KeyboardInterrupt:
        print("\n\nShutting down client...")
    
    return 0


def main():
    """Main entry point"""
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Kangaroo - Pollard\'s Kangaroo Algorithm for ECDLP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with config file
  %(prog)s input.txt
  
  # Run with multiple threads
  %(prog)s -t 4 input.txt
  
  # Run with work file save/load
  %(prog)s -w work.json -i previous_work.json input.txt
  
  # Server mode
  %(prog)s -s -sp 17403 input.txt
  
  # Client mode
  %(prog)s -c 192.168.1.100 -t 4
  
  # Merge work files
  %(prog)s -wm work1.json work2.json merged.json
  
  # Work file info
  %(prog)s -winfo work.json
        """
    )
    
    # General options
    parser.add_argument('-v', '--version', action='store_true',
                        help='Print version')
    parser.add_argument('-t', '--threads', type=int,
                        help='Number of CPU threads')
    parser.add_argument('-d', '--dp-bits', type=int,
                        help='Distinguished point bits')
    
    # Work file options
    parser.add_argument('-w', '--save-work', type=str,
                        help='Save work to file')
    parser.add_argument('-i', '--load-work', type=str,
                        help='Load work from file')
    parser.add_argument('-wi', '--work-interval', type=int,
                        help='Work save interval in seconds (default: 300)')
    parser.add_argument('-ws', '--save-kangaroos', action='store_true',
                        help='Save kangaroo details in work file')
    parser.add_argument('-wm', '--merge-work', nargs='+',
                        help='Merge work files: -wm file1 file2 ... output')
    parser.add_argument('-winfo', '--work-info', type=str,
                        help='Show work file info')
    parser.add_argument('-wcheck', '--work-check', type=str,
                        help='Check work file integrity')
    
    # Network options
    parser.add_argument('-s', '--server', action='store_true',
                        help='Run in server mode')
    parser.add_argument('-c', '--client', dest='server_ip', type=str,
                        help='Run in client mode, connect to server IP')
    parser.add_argument('-sp', '--server-port', type=int,
                        help='Server port (default: 17403)')
    parser.add_argument('-nt', '--network-timeout', type=int,
                        help='Network timeout in ms (default: 3000)')
    
    # Other options
    parser.add_argument('-o', '--output', type=str,
                        help='Output file for solution')
    parser.add_argument('-m', '--max-operations', type=int,
                        help='Maximum operations before giving up')
    parser.add_argument('--max-time', type=float,
                        help='Maximum time in seconds')
    
    # Config file
    parser.add_argument('input_file', nargs='?',
                        help='Input configuration file')
    
    args = parser.parse_args()
    
    # Handle version
    if args.version:
        print_version()
        return 0
    
    # Handle work file operations
    if args.merge_work:
        if len(args.merge_work) < 3:
            print("Error: Need at least 2 input files and 1 output file")
            return 1
        input_files = args.merge_work[:-1]
        output_file = args.merge_work[-1]
        return 0 if WorkFile.merge(input_files, output_file) else 1
    
    if args.work_info:
        WorkFile.info(args.work_info)
        return 0
    
    if args.work_check:
        return 0 if WorkFile.check(args.work_check) else 1
    
    # Determine mode
    if args.server:
        return run_server(args)
    elif args.server_ip:
        return run_client(args)
    else:
        return run_standalone(args)


if __name__ == '__main__':
    sys.exit(main())
