# Kangaroo - Python Implementation

Python implementation of **Pollard's Kangaroo Algorithm** for solving the discrete logarithm problem (ECDLP) on the secp256k1 elliptic curve.

This is a full-featured conversion of the original C++/CUDA Kangaroo.exe to Python, optimized with NumPy for performance.

## Features

âœ… **Core Algorithm**
- Pollard's Kangaroo (tame and wild kangaroos)
- Distinguished Point (DP) method for efficient collision detection
- Optimized with NumPy for better performance
- Multi-threaded CPU processing

âœ… **Work File Management**
- Save/load work state
- Merge multiple work files
- Work file integrity checking
- Automatic periodic saving

âœ… **Distributed Computing**
- Server mode: coordinates multiple clients
- Client mode: connects to server and contributes work
- TCP-based network protocol
- Automatic DP synchronization

âœ… **Configuration**
- Simple text-based configuration files
- Command-line argument support
- Auto-calculation of optimal DP bits

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Make kangaroo.py executable (optional)
chmod +x kangaroo.py
```

## Quick Start

### 1. Create a Configuration File

```bash
# Create sample config
cat > puzzle.txt << EOF
# Bitcoin Puzzle Configuration
PublicKey: 02a9de0a8c8a847c01d2b8ea0c3c6c48e7b2e75a6c6e4e58e4b1cf6db9e5a4c3f1
RangeStart: 0x8000000000000000
RangeEnd: 0xFFFFFFFFFFFFFFFF
EOF
```

### 2. Run Kangaroo Search

```bash
# Basic usage
python3 kangaroo.py puzzle.txt

# With multiple threads
python3 kangaroo.py -t 4 puzzle.txt

# With work file save/load
python3 kangaroo.py -t 4 -w work.json puzzle.txt

# Resume from saved work
python3 kangaroo.py -t 4 -i work.json -w work.json puzzle.txt
```

## Usage Guide

### Standalone Mode (Single Machine)

```bash
python3 kangaroo.py [options] <config_file>

Options:
  -t N          Number of CPU threads (default: 1)
  -d N          Distinguished point bits (auto-calculated if not specified)
  -w FILE       Save work to file
  -i FILE       Load work from file
  -wi N         Work save interval in seconds (default: 300)
  -ws           Save kangaroo details in work file
  -o FILE       Output solution to file
  -m N          Maximum operations before giving up
  --max-time N  Maximum time in seconds
```

**Example:**
```bash
# Run with 8 threads, save work every 5 minutes
python3 kangaroo.py -t 8 -w work.json -wi 300 puzzle.txt
```

### Server Mode (Distributed Computing)

```bash
python3 kangaroo.py -s [options] <config_file>

Options:
  -sp PORT      Server port (default: 17403)
  -nt N         Network timeout in ms (default: 3000)
  -w FILE       Save work to file
  -d N          Distinguished point bits
```

**Example:**
```bash
# Start server on port 17403
python3 kangaroo.py -s -sp 17403 -w server_work.json puzzle.txt
```

### Client Mode (Connect to Server)

```bash
python3 kangaroo.py -c <server_ip> [options]

Options:
  -t N          Number of local worker threads
  -sp PORT      Server port (default: 17403)
  -nt N         Network timeout in ms (default: 3000)
```

**Example:**
```bash
# Connect to server with 4 threads
python3 kangaroo.py -c 192.168.1.100 -t 4
```

### Work File Operations

```bash
# Show work file information
python3 kangaroo.py -winfo work.json

# Check work file integrity
python3 kangaroo.py -wcheck work.json

# Merge multiple work files
python3 kangaroo.py -wm work1.json work2.json work3.json merged.json
```

## Configuration File Format

Configuration files use a simple key-value format:

```
# Comments start with #

# Target public key (compressed 02/03 or uncompressed 04 format)
PublicKey: 02a9de0a8c8a847c01d2b8ea0c3c6c48e7b2e75a6c6e4e58e4b1cf6db9e5a4c3f1

# Search range (decimal or hex with 0x prefix)
RangeStart: 0x8000000000000000
RangeEnd: 0xFFFFFFFFFFFFFFFF

# Optional: Distinguished point bits (auto if not specified)
# DPBits: 20

# Optional: Number of threads (can be overridden by -t)
# Threads: 4
```

## How It Works

### Pollard's Kangaroo Algorithm

The algorithm uses two types of "kangaroos" that jump around on the elliptic curve:

1. **Tame Kangaroos**: Start from known points within the range [a, b]
   - Starting point: k*G where k âˆˆ [a, b]
   - We know the exact distance traveled

2. **Wild Kangaroos**: Start from the target public key W
   - Starting point: W = k*G (k is unknown)
   - We don't know the initial distance

Both kangaroos make pseudo-random jumps on the curve. When they meet at the same point (collision), we can calculate the private key:

```
private_key = range_start + tame_distance - wild_distance
```

### Distinguished Points (DP)

To efficiently detect collisions without storing every point:
- A point is "distinguished" if its x-coordinate has a certain number of leading zeros
- Only distinguished points are stored and checked for collisions
- DP bits controls the probability: higher bits = fewer DPs = less memory but more computation

### Expected Operations

The algorithm requires approximately **2âˆš(range_size)** operations on average.

Examples:
- Range 2^40: ~2^21 operations (~2 million)
- Range 2^60: ~2^31 operations (~2 billion)
- Range 2^64: ~2^33 operations (~8 billion)

## Performance Tips

1. **Use Multiple Threads**: `-t` option scales almost linearly on multi-core CPUs
2. **Optimal DP Bits**: Auto-calculation works well, but you can experiment with `-d`
3. **Distributed Mode**: Use server/client for multiple machines
4. **Save Work**: Always use `-w` for long searches to avoid losing progress
5. **Range Size**: Kangaroo is efficient for ranges up to ~2^64 (larger ranges become impractical)

## Comparison with Original Kangaroo.exe

| Feature | Original (C++/CUDA) | This (Python) |
|---------|---------------------|---------------|
| Core Algorithm | âœ… | âœ… |
| CPU Multi-threading | âœ… | âœ… |
| GPU Acceleration | âœ… CUDA | âŒ (CPU only) |
| Work Files | âœ… | âœ… |
| Server/Client | âœ… | âœ… |
| Performance | Very Fast | Moderate |
| Ease of Use | Moderate | Easy |
| Customization | Hard (C++) | Easy (Python) |

**Note**: Python version is ~10-100x slower than the C++/CUDA version due to lack of GPU support, but it's much easier to understand, modify, and extend.

## Examples

### Example 1: Small Range Test

```bash
# Create test config
cat > test.txt << EOF
PublicKey: 0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798
RangeStart: 1
RangeEnd: 100000
EOF

# Run with 4 threads
python3 kangaroo.py -t 4 test.txt
```

### Example 2: Distributed Computing

```bash
# On server machine (192.168.1.100)
python3 kangaroo.py -s -w server_work.json puzzle.txt

# On client machine 1
python3 kangaroo.py -c 192.168.1.100 -t 4

# On client machine 2
python3 kangaroo.py -c 192.168.1.100 -t 8

# Clients automatically receive configuration and send DPs to server
# When any client finds the solution, server broadcasts it to all clients
```

### Example 3: Work File Management

```bash
# Run multiple instances saving to different work files
python3 kangaroo.py -t 4 -w work1.json puzzle.txt &
python3 kangaroo.py -t 4 -w work2.json puzzle.txt &

# Later, merge the work files
python3 kangaroo.py -wm work1.json work2.json combined.json

# Check the merged file
python3 kangaroo.py -winfo combined.json

# Resume from merged work
python3 kangaroo.py -t 8 -i combined.json -w combined.json puzzle.txt
```

## Architecture

```
kangaroo.py              # Main entry point and CLI
â”œâ”€â”€ ec_operations.py     # Elliptic curve math (secp256k1)
â”œâ”€â”€ kangaroo_engine.py   # Core Kangaroo algorithm
â”œâ”€â”€ work_file.py         # Work file save/load/merge
â”œâ”€â”€ config_parser.py     # Configuration file parsing
â”œâ”€â”€ network_server.py    # Distributed server mode
â”œâ”€â”€ network_client.py    # Distributed client mode
â””â”€â”€ utils.py             # Helper functions and utilities
```

## Troubleshooting

**Q: Why is it slower than the original Kangaroo.exe?**
A: This Python version doesn't have GPU acceleration. It's designed for ease of use and modification rather than maximum performance.

**Q: How do I know if it's working?**
A: You should see progress updates showing kangaroos created, operations performed, and DPs found. Speed depends on your CPU and range size.

**Q: Can I stop and resume?**
A: Yes! Use `-w work.json` to save progress, then `-i work.json` to resume. The algorithm will continue from where it left off.

**Q: How do I choose the right DP bits?**
A: The default auto-calculation works well. Lower DP bits = more memory, faster collision detection. Higher DP bits = less memory, slower detection.

**Q: What's the maximum range size?**
A: Practically, ranges up to 2^60-2^64 are feasible with distributed computing. Larger ranges require impractical amounts of time.

## License

This is an educational implementation. Use responsibly and only on keys you own or have permission to test.

## Credits

- Original Kangaroo.exe by Jean Luc Pons
- Algorithm by John Pollard (1978)
- Python implementation optimized for clarity and functionality
