# QUICK START GUIDE - Kangaroo Python

## Installation (30 seconds)

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 kangaroo.py --version
```

Expected output:
```
Kangaroo 1.0 (Python)
Python implementation of Pollard's Kangaroo algorithm
For solving ECDLP on secp256k1 curve
```

---

## Test It Works (1 minute)

```bash
# Run test suite
python3 test_kangaroo.py
```

Expected: All tests pass, including finding private key 12345

---

## Your First Search (2 minutes)

### Step 1: Create a config file

```bash
cat > mytest.txt << EOF
# My first kangaroo search
PublicKey: 0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798
RangeStart: 1
RangeEnd: 100000
EOF
```

### Step 2: Run the search

```bash
python3 kangaroo.py -t 2 mytest.txt
```

### Step 3: Watch it work

You'll see progress updates like:
```
Starting Kangaroo search...
Range: [1, 100000]
Range size: 17 bits
DP bits: 10
Threads: 2

Progress: 45.2% | Kangaroos: 25 | Operations: 4521 | DPs: 8 | Speed: 1.2 KKey/s | ETA: 3m
```

---

## Common Tasks

### Save/Resume Work

```bash
# Save work as you go
python3 kangaroo.py -t 4 -w work.json puzzle.txt

# Resume later
python3 kangaroo.py -t 4 -i work.json -w work.json puzzle.txt
```

### Distributed Computing

```bash
# On main machine (server)
python3 kangaroo.py -s puzzle.txt

# On worker machines (clients)
python3 kangaroo.py -c <server_ip> -t 4
```

### Merge Work Files

```bash
python3 kangaroo.py -wm work1.json work2.json merged.json
```

---

## Bitcoin Puzzle Example

Try solving Bitcoin Puzzle #40 (already solved, for demonstration):

```bash
# Use provided example
python3 kangaroo.py -t 4 example_config_puzzle40.txt
```

This will search for the private key in range [2^39, 2^40].
Known solution: 0xa2dcc9

---

## Understanding the Output

```
Progress: 25.0% | Kangaroos: 150 | Operations: 50000 | DPs: 25 | Speed: 2.5 KKey/s | ETA: 5m30s
```

- **Progress**: % of expected work done
- **Kangaroos**: Number of kangaroos created (each one walks until hitting a DP)
- **Operations**: Total jumps performed
- **DPs**: Distinguished points found (stored for collision checking)
- **Speed**: Operations per second (KKey/s = thousands per second)
- **ETA**: Estimated time remaining

---

## When You Find a Key

Output will show:
```
âœ“ Private key found: 12345
  Hex: 0x3039
```

If `-o output.txt` was specified, solution is also saved to file.

---

## Configuration File Format

```
# Comments start with #

# Public key (02/03 for compressed, 04 for uncompressed)
PublicKey: 02a1b2c3...

# Range to search (hex with 0x or decimal)
RangeStart: 0x8000000000000000
RangeEnd: 0xFFFFFFFFFFFFFFFF

# Optional: threads and DP bits
Threads: 4
DPBits: 20
```

---

## Troubleshooting

**Q: "Module not found" error**
```bash
pip install -r requirements.txt
```

**Q: How long will it take?**
Expected operations â‰ˆ 2âˆš(range_size)
- 2^40 range: ~2^21 ops (millions) - minutes/hours
- 2^50 range: ~2^26 ops (billions) - hours/days
- 2^60 range: ~2^31 ops (billions) - days/weeks

**Q: Can I use GPU?**
No, this Python version is CPU-only. Original Kangaroo.exe has GPU support.

**Q: How do I know it's working?**
You should see:
- Increasing kangaroo count
- Increasing operation count  
- DPs being found periodically
- Non-zero speed (KKey/s)

**Q: It found the wrong key**
Verify your public key is correct (compressed format recommended).

---

## Next Steps

1. âœ… Run test suite to verify: `python3 test_kangaroo.py`
2. âœ… Try small example: `python3 kangaroo.py -t 2 example_config_small.txt`
3. âœ… Read full docs: `less README_KANGAROO.md`
4. âœ… Try distributed mode with multiple machines
5. âœ… Experiment with DP bits and thread count

---

## Need Help?

- **Full documentation**: `README_KANGAROO.md`
- **All options**: `python3 kangaroo.py --help`
- **Example configs**: `example_config_*.txt`
- **Algorithm explanation**: See README section "How It Works"

---

## File Reference

```
kangaroo.py              â†’ Main program
test_kangaroo.py         â†’ Test suite
example_config_*.txt     â†’ Sample configurations
README_KANGAROO.md       â†’ Full documentation
CONVERSION_SUMMARY.md    â†’ Technical details
```

---

**Ready to go!** Start with the small example and work your way up.

Remember: This is probabilistic - the algorithm might find the key quickly or take longer than estimated. That's normal!
