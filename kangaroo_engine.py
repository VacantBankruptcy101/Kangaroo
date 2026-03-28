#!/usr/bin/env python3
"""
Core Kangaroo Algorithm Engine
Implements Pollard's Kangaroo algorithm for ECDLP solving
"""

import random
import hashlib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import threading
import time

from ec_operations import (
    Point, point_multiply, point_add, point_subtract,
    hash_point, N, G, Gx, Gy
)
from utils import (
    create_jump_table, get_jump_distance, is_distinguished_point,
    calculate_optimal_dp_bits, ProgressStats
)


@dataclass
class Kangaroo:
    """Represents a kangaroo in the algorithm"""
    position: Point  # Current position on the curve
    distance: int    # Distance traveled from starting point
    is_tame: bool    # True for tame, False for wild
    

@dataclass
class DistinguishedPoint:
    """Represents a distinguished point"""
    x: int           # X-coordinate of the point
    y: int           # Y-coordinate of the point
    distance: int    # Distance from start
    is_tame: bool    # Tame or wild kangaroo
    

class KangarooEngine:
    """Main engine for Kangaroo algorithm"""
    
    def __init__(self, 
                 public_key: Point,
                 range_start: int,
                 range_end: int,
                 dp_bits: int = None,
                 num_threads: int = 1):
        """
        Initialize Kangaroo engine
        
        Args:
            public_key: Target public key (W = k*G where k is unknown)
            range_start: Start of search range
            range_end: End of search range
            dp_bits: Number of bits for distinguished points (auto if None)
            num_threads: Number of CPU threads to use
        """
        self.public_key = public_key
        self.range_start = range_start
        self.range_end = range_end
        self.range_size = range_end - range_start
        
        # Calculate or use provided DP bits
        if dp_bits is None:
            self.dp_bits = calculate_optimal_dp_bits(self.range_size, num_threads)
        else:
            self.dp_bits = dp_bits
        
        self.num_threads = num_threads
        
        # Create jump table
        # Average jump should be sqrt(range_size)
        import math
        avg_jump_bits = max(1, int(math.log2(math.sqrt(self.range_size))))
        self.jump_table = create_jump_table(avg_jump_bits + 10)
        
        # Normalize jumps around average
        avg_jump = int(math.sqrt(self.range_size))
        self.jump_table = [max(1, avg_jump + (j - avg_jump // 2)) for j in self.jump_table]
        
        # Distinguished point storage
        self.dp_dict: Dict[int, DistinguishedPoint] = {}
        self.dp_lock = threading.Lock()
        
        # Statistics
        self.stats = ProgressStats(self.range_size)
        
        # Control flags
        self.stop_flag = threading.Event()
        self.solution_found = False
        self.solution = None
        
    def create_tame_kangaroo(self) -> Kangaroo:
        """Create a tame kangaroo starting from a random point in range"""
        # Start from a random point in the range: k*G where k in [range_start, range_end]
        k = random.randint(self.range_start, self.range_end)
        position = point_multiply(k, Point(Gx, Gy))
        return Kangaroo(position=position, distance=k - self.range_start, is_tame=True)
    
    def create_wild_kangaroo(self) -> Kangaroo:
        """Create a wild kangaroo starting from the public key"""
        # Start from the public key (W = k*G where k is unknown)
        return Kangaroo(position=self.public_key, distance=0, is_tame=False)
    
    def jump(self, kangaroo: Kangaroo) -> Kangaroo:
        """Make the kangaroo jump"""
        # Get jump distance based on current position
        pos_hash = hash_point(kangaroo.position)
        jump_dist = get_jump_distance(pos_hash, self.jump_table)
        
        # Calculate new position: position + jump_dist*G
        jump_point = point_multiply(jump_dist, Point(Gx, Gy))
        new_position = point_add(kangaroo.position, jump_point)
        
        # Update distance
        new_distance = kangaroo.distance + jump_dist
        
        return Kangaroo(
            position=new_position,
            distance=new_distance,
            is_tame=kangaroo.is_tame
        )
    
    def check_distinguished(self, kangaroo: Kangaroo) -> bool:
        """Check if kangaroo is at a distinguished point"""
        if kangaroo.position.is_infinity:
            return False
        return is_distinguished_point(kangaroo.position.x, self.dp_bits)
    
    def process_distinguished_point(self, kangaroo: Kangaroo) -> Optional[int]:
        """Process a distinguished point and check for collision"""
        if kangaroo.position.is_infinity:
            return None
        
        x = kangaroo.position.x
        
        with self.dp_lock:
            # Check if we've seen this DP before
            if x in self.dp_dict:
                old_dp = self.dp_dict[x]
                
                # Collision found if one is tame and one is wild
                if old_dp.is_tame != kangaroo.is_tame:
                    # Calculate the private key
                    if kangaroo.is_tame:
                        tame_dist = kangaroo.distance
                        wild_dist = old_dp.distance
                    else:
                        tame_dist = old_dp.distance
                        wild_dist = kangaroo.distance
                    
                    # k = range_start + tame_distance - wild_distance
                    private_key = (self.range_start + tame_dist - wild_dist) % N
                    
                    # Verify the solution
                    if self.verify_solution(private_key):
                        return private_key
            else:
                # Store this DP
                dp = DistinguishedPoint(
                    x=kangaroo.position.x,
                    y=kangaroo.position.y,
                    distance=kangaroo.distance,
                    is_tame=kangaroo.is_tame
                )
                self.dp_dict[x] = dp
                self.stats.update(0, 0, 1)
        
        return None
    
    def verify_solution(self, private_key: int) -> bool:
        """Verify if a private key is correct"""
        calculated_pubkey = point_multiply(private_key, Point(Gx, Gy))
        return calculated_pubkey == self.public_key
    
    def run_kangaroo(self, max_iterations: int = None) -> Optional[int]:
        """Run a single kangaroo until it finds a DP or reaches max iterations"""
        # Create kangaroo (50% chance of tame or wild)
        if random.random() < 0.5:
            kangaroo = self.create_tame_kangaroo()
        else:
            kangaroo = self.create_wild_kangaroo()
        
        iterations = 0
        max_iter = max_iterations or 1000000
        
        while iterations < max_iter and not self.stop_flag.is_set():
            # Jump
            kangaroo = self.jump(kangaroo)
            iterations += 1
            
            # Check if distinguished
            if self.check_distinguished(kangaroo):
                result = self.process_distinguished_point(kangaroo)
                if result is not None:
                    return result
                # Start new kangaroo after reaching DP
                break
        
        # Update stats
        self.stats.update(1, iterations, 0)
        return None
    
    def worker_thread(self, thread_id: int, max_kangaroos: int = None):
        """Worker thread that runs kangaroos continuously"""
        kangaroos_processed = 0
        
        while not self.stop_flag.is_set():
            if max_kangaroos and kangaroos_processed >= max_kangaroos:
                break
            
            result = self.run_kangaroo()
            kangaroos_processed += 1
            
            if result is not None:
                self.solution = result
                self.solution_found = True
                self.stop_flag.set()
                break
    
    def solve(self, max_time: float = None, max_operations: int = None) -> Optional[int]:
        """
        Solve the ECDLP using Kangaroo algorithm
        
        Args:
            max_time: Maximum time in seconds (None for unlimited)
            max_operations: Maximum operations (None for unlimited)
        
        Returns:
            Private key if found, None otherwise
        """
        print(f"Starting Kangaroo search...")
        print(f"Range: [{self.range_start}, {self.range_end}]")
        print(f"Range size: {self.range_size.bit_length()} bits")
        print(f"DP bits: {self.dp_bits}")
        print(f"Threads: {self.num_threads}")
        print(f"")
        
        # Start worker threads
        threads = []
        for i in range(self.num_threads):
            t = threading.Thread(target=self.worker_thread, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # Monitor progress
        start_time = time.time()
        last_print = start_time
        
        try:
            while not self.solution_found:
                time.sleep(0.1)
                
                # Check time limit
                if max_time and (time.time() - start_time) > max_time:
                    print("\nTime limit reached")
                    self.stop_flag.set()
                    break
                
                # Check operation limit
                if max_operations and self.stats.total_operations > max_operations:
                    print("\nOperation limit reached")
                    self.stop_flag.set()
                    break
                
                # Print progress every 2 seconds
                if time.time() - last_print > 2.0:
                    print(f"\r{self.stats}", end='', flush=True)
                    last_print = time.time()
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            self.stop_flag.set()
        
        # Wait for threads to finish
        for t in threads:
            t.join(timeout=1.0)
        
        print(f"\n\nFinal statistics:")
        print(f"  Total kangaroos: {self.stats.total_kangaroos}")
        print(f"  Total operations: {self.stats.total_operations}")
        print(f"  Distinguished points: {self.stats.dp_count}")
        print(f"  Time elapsed: {self.stats.timer.elapsed():.2f}s")
        
        if self.solution_found:
            print(f"\nâœ“ Private key found: {self.solution}")
            print(f"  Hex: {hex(self.solution)}")
            return self.solution
        else:
            print("\nâœ— Private key not found")
            return None
    
    def get_work_state(self) -> dict:
        """Get current work state for saving"""
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
        
        return {
            'public_key_x': self.public_key.x,
            'public_key_y': self.public_key.y,
            'range_start': self.range_start,
            'range_end': self.range_end,
            'dp_bits': self.dp_bits,
            'distinguished_points': dp_list,
            'total_operations': self.stats.total_operations,
            'total_kangaroos': self.stats.total_kangaroos,
            'dp_count': self.stats.dp_count
        }
    
    def load_work_state(self, state: dict):
        """Load work state from saved data"""
        # Verify compatibility
        if state['range_start'] != self.range_start or state['range_end'] != self.range_end:
            raise ValueError("Work file range doesn't match current range")
        
        # Load distinguished points
        with self.dp_lock:
            self.dp_dict.clear()
            for dp_data in state['distinguished_points']:
                dp = DistinguishedPoint(
                    x=dp_data['x'],
                    y=dp_data['y'],
                    distance=dp_data['distance'],
                    is_tame=dp_data['is_tame']
                )
                self.dp_dict[dp.x] = dp
        
        # Update stats
        self.stats.total_operations = state.get('total_operations', 0)
        self.stats.total_kangaroos = state.get('total_kangaroos', 0)
        self.stats.dp_count = state.get('dp_count', 0)
        
        print(f"Loaded work state: {len(self.dp_dict)} DPs, {self.stats.total_operations} operations")
