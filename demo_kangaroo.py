#!/usr/bin/env python3
"""
Quick Demo of Kangaroo Python Implementation
Shows basic usage patterns
"""

import subprocess
import sys

def run_command(cmd, description):
    """Run a command and show output"""
    print("\n" + "="*70)
    print(f"DEMO: {description}")
    print("="*70)
    print(f"Command: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    return result.returncode == 0

def main():
    print("""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘                  KANGAROO PYTHON - QUICK DEMO                        â•‘
â•‘         Pollard's Kangaroo Algorithm for Bitcoin/Crypto             â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    """)
    
    demos = [
        ("python3 kangaroo.py --version", "Show version"),
        ("python3 test_kangaroo.py", "Run test suite"),
        ("python3 kangaroo.py -winfo example_config_small.txt 2>/dev/null || echo 'Config file (not work file)'", "Check config file"),
        ("head -15 example_config_small.txt", "View example config"),
    ]
    
    for cmd, desc in demos:
        if not run_command(cmd, desc):
            print(f"Warning: Command failed")
        input("\nPress Enter to continue...")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE!")
    print("="*70)
    print("\nFor full usage, see README_KANGAROO.md")
    print("\nCommon commands:")
    print("  - Run search:        python3 kangaroo.py -t 4 config.txt")
    print("  - Server mode:       python3 kangaroo.py -s config.txt")
    print("  - Client mode:       python3 kangaroo.py -c <server_ip> -t 4")
    print("  - Merge work files:  python3 kangaroo.py -wm file1.json file2.json out.json")
    print()

if __name__ == '__main__':
    main()
