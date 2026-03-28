#!/usr/bin/env python3
"""
Network Server for Distributed Kangaroo
Coordinates multiple clients working on the same problem
"""

import socket
import threading
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

from ec_operations import Point, point_multiply, Gx, Gy
from kangaroo_engine import DistinguishedPoint


@dataclass
class ClientInfo:
    """Information about connected client"""
    address: tuple
    last_seen: float
    dps_received: int
    operations: int


class KangarooServer:
    """Server for distributed Kangaroo computation"""
    
    def __init__(self, 
                 public_key: Point,
                 range_start: int,
                 range_end: int,
                 dp_bits: int,
                 port: int = 17403,
                 timeout: int = 3000):
        """
        Initialize Kangaroo server
        
        Args:
            public_key: Target public key
            range_start: Start of search range
            range_end: End of search range
            dp_bits: Distinguished point bits
            port: TCP port to listen on
            timeout: Network timeout in milliseconds
        """
        self.public_key = public_key
        self.range_start = range_start
        self.range_end = range_end
        self.dp_bits = dp_bits
        self.port = port
        self.timeout = timeout / 1000.0  # Convert to seconds
        
        # Distinguished points storage
        self.dp_dict: Dict[int, DistinguishedPoint] = {}
        self.dp_lock = threading.Lock()
        
        # Client tracking
        self.clients: Dict[str, ClientInfo] = {}
        self.clients_lock = threading.Lock()
        
        # Solution
        self.solution = None
        self.solution_lock = threading.Lock()
        
        # Server control
        self.running = False
        self.server_socket = None
    
    def start(self):
        """Start the server"""
        self.running = True
        
        # Create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)  # Allow checking running flag
        
        print(f"Kangaroo server listening on port {self.port}")
        print(f"Range: [{self.range_start}, {self.range_end}]")
        print(f"DP bits: {self.dp_bits}")
        print(f"")
        
        # Start status thread
        status_thread = threading.Thread(target=self._status_loop)
        status_thread.daemon = True
        status_thread.start()
        
        # Accept connections
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"Client connected: {address}")
                
                # Handle client in new thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
        
        self.server_socket.close()
    
    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle a client connection"""
        client_socket.settimeout(self.timeout)
        client_id = f"{address[0]}:{address[1]}"
        
        # Register client
        with self.clients_lock:
            self.clients[client_id] = ClientInfo(
                address=address,
                last_seen=time.time(),
                dps_received=0,
                operations=0
            )
        
        try:
            # Send initial configuration
            config = {
                'type': 'config',
                'public_key_x': self.public_key.x,
                'public_key_y': self.public_key.y,
                'range_start': self.range_start,
                'range_end': self.range_end,
                'dp_bits': self.dp_bits
            }
            self._send_message(client_socket, config)
            
            # Receive distinguished points from client
            while self.running:
                message = self._receive_message(client_socket)
                
                if message is None:
                    break
                
                # Update client info
                with self.clients_lock:
                    if client_id in self.clients:
                        self.clients[client_id].last_seen = time.time()
                
                # Process message
                if message['type'] == 'dp':
                    self._process_dp_from_client(message, client_id)
                    
                    # Check if solution found
                    with self.solution_lock:
                        if self.solution is not None:
                            # Send solution to client
                            solution_msg = {
                                'type': 'solution',
                                'private_key': self.solution
                            }
                            self._send_message(client_socket, solution_msg)
                            break
                
                elif message['type'] == 'stats':
                    # Update client statistics
                    with self.clients_lock:
                        if client_id in self.clients:
                            self.clients[client_id].operations += message.get('operations', 0)
        
        except socket.timeout:
            print(f"Client timeout: {address}")
        except Exception as e:
            print(f"Client error {address}: {e}")
        
        finally:
            # Unregister client
            with self.clients_lock:
                if client_id in self.clients:
                    del self.clients[client_id]
            
            client_socket.close()
            print(f"Client disconnected: {address}")
    
    def _process_dp_from_client(self, message: dict, client_id: str):
        """Process distinguished point received from client"""
        try:
            dp = DistinguishedPoint(
                x=message['x'],
                y=message['y'],
                distance=message['distance'],
                is_tame=message['is_tame']
            )
            
            with self.dp_lock:
                # Check for collision
                if dp.x in self.dp_dict:
                    old_dp = self.dp_dict[dp.x]
                    
                    # Collision if different types
                    if old_dp.is_tame != dp.is_tame:
                        # Calculate private key
                        if dp.is_tame:
                            tame_dist = dp.distance
                            wild_dist = old_dp.distance
                        else:
                            tame_dist = old_dp.distance
                            wild_dist = dp.distance
                        
                        private_key = (self.range_start + tame_dist - wild_dist) % (2**256)
                        
                        # Verify solution
                        if self._verify_solution(private_key):
                            with self.solution_lock:
                                self.solution = private_key
                            print(f"\n\nâœ“ SOLUTION FOUND by client {client_id}!")
                            print(f"Private key: {private_key}")
                            print(f"Hex: {hex(private_key)}")
                else:
                    # Store new DP
                    self.dp_dict[dp.x] = dp
            
            # Update client stats
            with self.clients_lock:
                if client_id in self.clients:
                    self.clients[client_id].dps_received += 1
        
        except Exception as e:
            print(f"Error processing DP from {client_id}: {e}")
    
    def _verify_solution(self, private_key: int) -> bool:
        """Verify if private key is correct"""
        try:
            calculated = point_multiply(private_key, Point(Gx, Gy))
            return calculated == self.public_key
        except:
            return False
    
    def _send_message(self, sock: socket.socket, message: dict):
        """Send JSON message to client"""
        data = json.dumps(message).encode('utf-8')
        length = len(data)
        sock.sendall(length.to_bytes(4, 'big') + data)
    
    def _receive_message(self, sock: socket.socket) -> Optional[dict]:
        """Receive JSON message from client"""
        try:
            # Read length
            length_bytes = sock.recv(4)
            if len(length_bytes) < 4:
                return None
            
            length = int.from_bytes(length_bytes, 'big')
            
            # Read data
            data = b''
            while len(data) < length:
                chunk = sock.recv(min(length - len(data), 4096))
                if not chunk:
                    return None
                data += chunk
            
            return json.loads(data.decode('utf-8'))
        
        except:
            return None
    
    def _status_loop(self):
        """Print status periodically"""
        last_print = time.time()
        
        while self.running:
            time.sleep(1.0)
            
            if time.time() - last_print > 5.0:
                with self.clients_lock:
                    num_clients = len(self.clients)
                    total_ops = sum(c.operations for c in self.clients.values())
                
                with self.dp_lock:
                    num_dps = len(self.dp_dict)
                
                print(f"\rClients: {num_clients} | DPs: {num_dps} | Total Ops: {total_ops}", end='', flush=True)
                last_print = time.time()
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
    
    def get_work_state(self) -> dict:
        """Get current work state"""
        with self.dp_lock:
            dp_list = [
                {
                    'x': dp.x,
                    'y': dp.y,
                    'distance': dp.distance,
                    'is_tame': dp.is_tame
                }
                for dp in self.dp_dict.values()
            ]
        
        with self.clients_lock:
            total_ops = sum(c.operations for c in self.clients.values())
        
        return {
            'public_key_x': self.public_key.x,
            'public_key_y': self.public_key.y,
            'range_start': self.range_start,
            'range_end': self.range_end,
            'dp_bits': self.dp_bits,
            'distinguished_points': dp_list,
            'total_operations': total_ops,
            'dp_count': len(dp_list)
        }
