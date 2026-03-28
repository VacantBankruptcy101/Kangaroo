#!/usr/bin/env python3
"""
Configuration File Parser
Parses input configuration files for Kangaroo
"""

import re
from typing import Optional, Tuple
from ec_operations import Point, public_key_to_point


class ConfigParser:
    """Parse Kangaroo configuration files"""
    
    @staticmethod
    def parse_file(filename: str) -> Optional[dict]:
        """
        Parse configuration file
        
        Expected format:
        # Comments start with #
        PublicKey: 02... or 04...
        RangeStart: <decimal or hex>
        RangeEnd: <decimal or hex>
        
        Args:
            filename: Path to config file
        
        Returns:
            Configuration dictionary or None
        """
        try:
            with open(filename, 'r') as f:
                content = f.read()
            
            config = {}
            
            # Parse public key
            pubkey_match = re.search(r'PublicKey\s*[:=]\s*([0-9a-fA-F]+)', content, re.IGNORECASE)
            if pubkey_match:
                pubkey_str = pubkey_match.group(1)
                config['public_key'] = public_key_to_point(pubkey_str)
            else:
                print("Error: PublicKey not found in config file")
                return None
            
            # Parse range start
            range_start_match = re.search(r'RangeStart\s*[:=]\s*([0-9a-fA-Fx]+)', content, re.IGNORECASE)
            if range_start_match:
                range_str = range_start_match.group(1)
                config['range_start'] = int(range_str, 0)  # Auto-detect base
            else:
                print("Error: RangeStart not found in config file")
                return None
            
            # Parse range end
            range_end_match = re.search(r'RangeEnd\s*[:=]\s*([0-9a-fA-Fx]+)', content, re.IGNORECASE)
            if range_end_match:
                range_str = range_end_match.group(1)
                config['range_end'] = int(range_str, 0)
            else:
                print("Error: RangeEnd not found in config file")
                return None
            
            # Optional: DP bits
            dp_bits_match = re.search(r'DPBits\s*[:=]\s*(\d+)', content, re.IGNORECASE)
            if dp_bits_match:
                config['dp_bits'] = int(dp_bits_match.group(1))
            
            # Optional: Threads
            threads_match = re.search(r'Threads\s*[:=]\s*(\d+)', content, re.IGNORECASE)
            if threads_match:
                config['threads'] = int(threads_match.group(1))
            
            return config
        
        except FileNotFoundError:
            print(f"Error: Config file not found: {filename}")
            return None
        except Exception as e:
            print(f"Error parsing config file: {e}")
            return None
    
    @staticmethod
    def create_sample_config(filename: str, puzzle_number: int = None):
        """
        Create a sample configuration file
        
        Args:
            filename: Output filename
            puzzle_number: Bitcoin puzzle number (optional)
        """
        if puzzle_number:
            # Create config for Bitcoin puzzle
            content = f"""# Kangaroo Configuration File
# Bitcoin Puzzle #{puzzle_number}

# Target public key (compressed format)
PublicKey: 02<replace_with_actual_pubkey>

# Search range (2^{puzzle_number-1} to 2^{puzzle_number})
RangeStart: {hex(2**(puzzle_number-1))}
RangeEnd: {hex(2**puzzle_number)}

# Optional parameters
# DPBits: 20
# Threads: 4
"""
        else:
            # Generic sample
            content = """# Kangaroo Configuration File

# Target public key (compressed 02/03 or uncompressed 04)
PublicKey: 02a6b9d7f5c1c2f3e4d5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8

# Search range (decimal or hex with 0x prefix)
RangeStart: 0x8000000000000000
RangeEnd: 0xFFFFFFFFFFFFFFFF

# Optional: Distinguished Point bits (auto-calculated if not specified)
# DPBits: 20

# Optional: Number of CPU threads (default: 1)
# Threads: 4
"""
        
        try:
            with open(filename, 'w') as f:
                f.write(content)
            print(f"Sample configuration created: {filename}")
            return True
        except Exception as e:
            print(f"Error creating sample config: {e}")
            return False
