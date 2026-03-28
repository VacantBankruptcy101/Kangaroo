#!/usr/bin/env python3
"""
Network Client for Distributed Kangaroo
Connects to server and contributes to distributed search
"""

import socket
import json
import time
import threading
from typing import Optional

from ec_operations import Point, Gx, Gy
from kangaroo_engine import KangarooEngine


class KangarooClient:
    """Client for distributed Kangaroo computation"""
    
    def __init__(self, 
                 server_ip: str,
                 port: int = 17403,
                 timeout: int = 3000,
                 num_threads: int = 1):
        """
        Initialize Kangaroo client
        
        Args:
            server_ip: Server IP address
            port: Server port
            timeout: Network timeout in milliseconds
            num_threads: Number of local worker threads
        """
        self.server_ip = server_ip
        self.port = port
        self.timeout = timeout / 1000.0  # Convert to seconds
        self.num_threads = num_threads
        
        self.socket = None
        self.engine = None
        self.running = False
        self.solution_found = False
    
    def connect(self) -> bool:
        """Connect to server and receive configuration"""
        try:
            print(f"Connecting to server {self.server_ip}:{self.port}...")
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.server_ip, self.port))
            
            print("Connected to server")
            
            # Receive configuration
            config = self._receive_message()
            
            if config is None or config.get('type') != 'config':
                print("Failed to receive configuration from server")
                return False
            
            print(f"Received configuration:")
            print(f"  Range: [{config['range_start']}, {config['range_end']}]")
            print(f"  DP bits: {config['dp_bits']}")
            
            # Create kangaroo engine
            public_key = Point(config['public_key_x'], config['public_key_y'])
            
            self.engine = KangarooEngine(
                public_key=public_key,
                range_start=config['range_start'],
                range_end=config['range_end'],
                dp_bits=config['dp_bits'],
                num_threads=self.num_threads
            )
            
            return True
        
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def run(self):
        """Run client and send DPs to server"""
        if self.engine is None:
            print("Not connected to server")
            return
        
        self.running = True
        
        print(f"Starting {self.num_threads} worker threads...")
        print("")
        
        # Start worker threads
        threads = []
        for i in range(self.num_threads):
            t = threading.Thread(target=self._worker_thread, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # Start sender thread
        sender_thread = threading.Thread(target=self._sender_loop)
        sender_thread.daemon = True
        sender_thread.start()
        
        # Monitor for solution
        last_stats_time = time.time()
        stats_interval = 10.0  # Send stats every 10 seconds
        
        try:
            while self.running and not self.solution_found:
                time.sleep(0.1)
                
                # Check for messages from server
                try:
                    self.socket.settimeout(0.1)
                    message = self._receive_message()
                    
                    if message and message.get('type') == 'solution':
                        print(f"\n\nServer found solution!")
                        print(f"Private key: {message['private_key']}")
                        print(f"Hex: {hex(message['private_key'])}")
                        self.solution_found = True
                        break
                
                except socket.timeout:
                    pass
                
                # Send statistics periodically
                if time.time() - last_stats_time > stats_interval:
                    stats_msg = {
                        'type': 'stats',
                        'operations': self.engine.stats.total_operations
                    }
                    try:
                        self._send_message(stats_msg)
                    except:
                        pass
                    
                    last_stats_time = time.time()
                    
                    # Print local stats
                    print(f"\r{self.engine.stats}", end='', flush=True)
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        
        finally:
            self.running = False
            self.engine.stop_flag.set()
            
            # Wait for threads
            for t in threads:
                t.join(timeout=1.0)
            
            if self.socket:
                self.socket.close()
    
    def _worker_thread(self, thread_id: int):
        """Worker thread that runs kangaroos"""
        while self.running and not self.solution_found:
            # Run a kangaroo
            self.engine.run_kangaroo()
    
    def _sender_loop(self):
        """Send distinguished points to server"""
        sent_dps = set()
        
        while self.running:
            time.sleep(0.5)
            
            # Get new DPs
            with self.engine.dp_lock:
                dps_to_send = []
                for x, dp in self.engine.dp_dict.items():
                    if x not in sent_dps:
                        dps_to_send.append(dp)
                        sent_dps.add(x)
            
            # Send DPs to server
            for dp in dps_to_send:
                try:
                    message = {
                        'type': 'dp',
                        'x': dp.x,
                        'y': dp.y,
                        'distance': dp.distance,
                        'is_tame': dp.is_tame
                    }
                    self._send_message(message)
                
                except Exception as e:
                    print(f"\nError sending DP to server: {e}")
                    self.running = False
                    break
    
    def _send_message(self, message: dict):
        """Send JSON message to server"""
        data = json.dumps(message).encode('utf-8')
        length = len(data)
        self.socket.sendall(length.to_bytes(4, 'big') + data)
    
    def _receive_message(self) -> Optional[dict]:
        """Receive JSON message from server"""
        try:
            # Read length
            length_bytes = self.socket.recv(4)
            if len(length_bytes) < 4:
                return None
            
            length = int.from_bytes(length_bytes, 'big')
            
            # Read data
            data = b''
            while len(data) < length:
                chunk = self.socket.recv(min(length - len(data), 4096))
                if not chunk:
                    return None
                data += chunk
            
            return json.loads(data.decode('utf-8'))
        
        except:
            return None
