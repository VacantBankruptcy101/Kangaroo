#!/usr/bin/env python3
"""
Utility functions for Kangaroo implementation
"""

import hashlib
import time
from typing import List
import numpy as np


def create_jump_table(max_jump_bits: int = 64) -> List[int]:
    """Create a table of jump distances for the kangaroo algorithm"""
    # Create powers of 2 jumps with some randomization
    jumps = []
    for i in range(max_jump_bits):
        base = 1 << i
        # Add some variation
        jump = base
        jumps.append(jump)
    return jumps


def get_jump_distance(position_hash: int, jump_table: List[int]) -> int:
    """Get jump distance based on current position"""
    # Use the position hash to select a jump from the table
    index = position_hash % len(jump_table)
    return jump_table[index]


def is_distinguished_point(x: int, dp_bits: int) -> bool:
    """Check if a point is a distinguished point (DP)"""
    # A point is distinguished if its x-coordinate has dp_bits leading zeros
    if dp_bits == 0:
        return True
    mask = (1 << dp_bits) - 1
    return (x >> (256 - dp_bits)) == 0


def calculate_expected_operations(range_size: int) -> float:
    """Calculate expected number of operations for Kangaroo algorithm"""
    # Expected operations â‰ˆ 2 * sqrt(range_size)
    import math
    return 2.0 * math.sqrt(range_size)


def format_large_number(n: int) -> str:
    """Format large number with power of 2 notation"""
    import math
    if n == 0:
        return "0"
    bits = n.bit_length()
    return f"2^{bits-1} ({n})" if bits > 20 else str(n)


def format_speed(ops_per_sec: float) -> str:
    """Format operation speed in human-readable format"""
    if ops_per_sec >= 1e9:
        return f"{ops_per_sec/1e9:.2f} GKey/s"
    elif ops_per_sec >= 1e6:
        return f"{ops_per_sec/1e6:.2f} MKey/s"
    elif ops_per_sec >= 1e3:
        return f"{ops_per_sec/1e3:.2f} KKey/s"
    else:
        return f"{ops_per_sec:.2f} Key/s"


def calculate_optimal_dp_bits(range_size: int, num_workers: int = 1) -> int:
    """Calculate optimal DP bits based on range size"""
    import math
    # More workers = more DPs needed = smaller DP bits
    # Heuristic: aim for ~1M DPs expected
    expected_ops = calculate_expected_operations(range_size)
    
    # We want about 1 DP per 10000-100000 operations
    dp_prob = 100000.0 / max(expected_ops, 1)
    
    # Convert probability to bits
    if dp_prob >= 1.0:
        return 0
    
    dp_bits = int(-math.log2(dp_prob))
    
    # Clamp to reasonable range
    return max(10, min(40, dp_bits))


class Timer:
    """Simple timer for performance measurement"""
    
    def __init__(self):
        self.start_time = time.time()
        self.lap_time = self.start_time
    
    def elapsed(self) -> float:
        """Get elapsed time since start"""
        return time.time() - self.start_time
    
    def lap(self) -> float:
        """Get elapsed time since last lap and reset lap timer"""
        now = time.time()
        elapsed = now - self.lap_time
        self.lap_time = now
        return elapsed
    
    def reset(self):
        """Reset timer"""
        self.start_time = time.time()
        self.lap_time = self.start_time


class ProgressStats:
    """Track and display progress statistics"""
    
    def __init__(self, range_size: int):
        self.range_size = range_size
        self.expected_ops = calculate_expected_operations(range_size)
        self.total_kangaroos = 0
        self.total_operations = 0
        self.dp_count = 0
        self.timer = Timer()
    
    def update(self, kangaroos: int, operations: int, dps: int):
        """Update statistics"""
        self.total_kangaroos += kangaroos
        self.total_operations += operations
        self.dp_count += dps
    
    def get_progress_percent(self) -> float:
        """Calculate progress percentage"""
        if self.expected_ops == 0:
            return 0.0
        return min(100.0, (self.total_operations / self.expected_ops) * 100.0)
    
    def get_speed(self) -> float:
        """Calculate current speed (ops/sec)"""
        elapsed = self.timer.elapsed()
        if elapsed == 0:
            return 0.0
        return self.total_operations / elapsed
    
    def get_eta(self) -> float:
        """Estimate time to completion (seconds)"""
        speed = self.get_speed()
        if speed == 0:
            return float('inf')
        remaining = max(0, self.expected_ops - self.total_operations)
        return remaining / speed
    
    def format_eta(self) -> str:
        """Format ETA in human-readable format"""
        eta = self.get_eta()
        if eta == float('inf'):
            return "Unknown"
        
        hours = int(eta // 3600)
        minutes = int((eta % 3600) // 60)
        seconds = int(eta % 60)
        
        if hours > 24:
            days = hours // 24
            hours = hours % 24
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def __str__(self) -> str:
        """Get formatted statistics string"""
        return (
            f"Progress: {self.get_progress_percent():.2f}% | "
            f"Kangaroos: {format_large_number(self.total_kangaroos)} | "
            f"Operations: {format_large_number(self.total_operations)} | "
            f"DPs: {self.dp_count} | "
            f"Speed: {format_speed(self.get_speed())} | "
            f"ETA: {self.format_eta()}"
        )
