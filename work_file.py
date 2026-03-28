#!/usr/bin/env python3
"""
Work File Management
Handles saving, loading, and merging of work files
"""

import json
import os
from typing import Optional
from datetime import datetime


class WorkFile:
    """Manages work file operations"""
    
    VERSION = "1.0"
    
    @staticmethod
    def save(filename: str, work_state: dict, save_kangaroos: bool = False):
        """
        Save work state to file
        
        Args:
            filename: Path to save file
            work_state: Work state dictionary from KangarooEngine
            save_kangaroos: Whether to save kangaroo details (larger file)
        """
        # Add metadata
        data = {
            'version': WorkFile.VERSION,
            'timestamp': datetime.now().isoformat(),
            'save_kangaroos': save_kangaroos,
            'work_state': work_state
        }
        
        # Save to file
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Work saved to {filename}")
            print(f"  Distinguished points: {len(work_state['distinguished_points'])}")
            print(f"  Total operations: {work_state['total_operations']}")
            return True
        except Exception as e:
            print(f"Error saving work file: {e}")
            return False
    
    @staticmethod
    def load(filename: str) -> Optional[dict]:
        """
        Load work state from file
        
        Args:
            filename: Path to load file
        
        Returns:
            Work state dictionary or None if error
        """
        if not os.path.exists(filename):
            print(f"Work file not found: {filename}")
            return None
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Check version
            if data.get('version') != WorkFile.VERSION:
                print(f"Warning: Work file version mismatch (file: {data.get('version')}, current: {WorkFile.VERSION})")
            
            work_state = data['work_state']
            
            print(f"Work loaded from {filename}")
            print(f"  Saved: {data.get('timestamp', 'unknown')}")
            print(f"  Distinguished points: {len(work_state['distinguished_points'])}")
            print(f"  Total operations: {work_state['total_operations']}")
            
            return work_state
        
        except Exception as e:
            print(f"Error loading work file: {e}")
            return None
    
    @staticmethod
    def merge(files: list, output_file: str) -> bool:
        """
        Merge multiple work files into one
        
        Args:
            files: List of work file paths
            output_file: Output file path
        
        Returns:
            True if successful
        """
        if len(files) < 2:
            print("Need at least 2 files to merge")
            return False
        
        print(f"Merging {len(files)} work files...")
        
        # Load all files
        work_states = []
        for f in files:
            state = WorkFile.load(f)
            if state is None:
                print(f"Failed to load {f}, aborting merge")
                return False
            work_states.append(state)
        
        # Verify compatibility
        base_state = work_states[0]
        for state in work_states[1:]:
            if (state['range_start'] != base_state['range_start'] or 
                state['range_end'] != base_state['range_end']):
                print("Error: Cannot merge work files with different ranges")
                return False
        
        # Merge distinguished points
        merged_dps = {}
        total_ops = 0
        total_kangaroos = 0
        
        for state in work_states:
            total_ops += state.get('total_operations', 0)
            total_kangaroos += state.get('total_kangaroos', 0)
            
            for dp in state['distinguished_points']:
                x = dp['x']
                # Keep first occurrence of each DP
                if x not in merged_dps:
                    merged_dps[x] = dp
        
        # Create merged state
        merged_state = {
            'public_key_x': base_state['public_key_x'],
            'public_key_y': base_state['public_key_y'],
            'range_start': base_state['range_start'],
            'range_end': base_state['range_end'],
            'dp_bits': base_state['dp_bits'],
            'distinguished_points': list(merged_dps.values()),
            'total_operations': total_ops,
            'total_kangaroos': total_kangaroos,
            'dp_count': len(merged_dps)
        }
        
        # Save merged file
        result = WorkFile.save(output_file, merged_state)
        
        if result:
            print(f"\nMerge complete:")
            print(f"  Input files: {len(files)}")
            print(f"  Total DPs: {len(merged_dps)}")
            print(f"  Total operations: {total_ops}")
        
        return result
    
    @staticmethod
    def info(filename: str):
        """
        Display information about a work file
        
        Args:
            filename: Path to work file
        """
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            work_state = data['work_state']
            
            print(f"\nWork File Information: {filename}")
            print(f"="*60)
            print(f"Version:        {data.get('version', 'unknown')}")
            print(f"Timestamp:      {data.get('timestamp', 'unknown')}")
            print(f"Save kangaroos: {data.get('save_kangaroos', False)}")
            print(f"")
            print(f"Public Key X:   {hex(work_state['public_key_x'])}")
            print(f"Public Key Y:   {hex(work_state['public_key_y'])}")
            print(f"")
            print(f"Range Start:    {work_state['range_start']} ({hex(work_state['range_start'])})")
            print(f"Range End:      {work_state['range_end']} ({hex(work_state['range_end'])})")
            print(f"Range Size:     2^{(work_state['range_end'] - work_state['range_start']).bit_length()}")
            print(f"")
            print(f"DP Bits:        {work_state['dp_bits']}")
            print(f"DP Count:       {len(work_state['distinguished_points'])}")
            print(f"Total Ops:      {work_state.get('total_operations', 0)}")
            print(f"Total Kangaroos: {work_state.get('total_kangaroos', 0)}")
            print(f"="*60)
            
        except Exception as e:
            print(f"Error reading work file: {e}")
    
    @staticmethod
    def check(filename: str) -> bool:
        """
        Check work file integrity
        
        Args:
            filename: Path to work file
        
        Returns:
            True if file is valid
        """
        print(f"Checking work file: {filename}")
        
        state = WorkFile.load(filename)
        if state is None:
            print("âœ— File is invalid or corrupt")
            return False
        
        # Verify required fields
        required_fields = ['public_key_x', 'public_key_y', 'range_start', 'range_end', 
                          'dp_bits', 'distinguished_points']
        
        for field in required_fields:
            if field not in state:
                print(f"âœ— Missing required field: {field}")
                return False
        
        # Verify DP structure
        for i, dp in enumerate(state['distinguished_points']):
            if not all(k in dp for k in ['x', 'y', 'distance', 'is_tame']):
                print(f"âœ— Invalid DP structure at index {i}")
                return False
        
        print("âœ“ Work file is valid")
        return True
