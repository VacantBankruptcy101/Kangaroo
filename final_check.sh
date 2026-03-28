#!/bin/bash

echo "======================================================================"
echo "  KANGAROO PYTHON - FINAL VERIFICATION"
echo "======================================================================"
echo ""

echo "1. Checking all core Python files exist..."
files="kangaroo.py ec_operations.py kangaroo_engine.py work_file.py config_parser.py network_server.py network_client.py utils.py"
for f in $files; do
    if [ -f "$f" ]; then
        echo "   âœ“ $f"
    else
        echo "   âœ— $f MISSING"
        exit 1
    fi
done
echo ""

echo "2. Checking documentation..."
docs="README_KANGAROO.md QUICKSTART.md CONVERSION_SUMMARY.md"
for f in $docs; do
    if [ -f "$f" ]; then
        echo "   âœ“ $f"
    else
        echo "   âœ— $f MISSING"
        exit 1
    fi
done
echo ""

echo "3. Checking example configs..."
if [ -f "example_config_small.txt" ] && [ -f "example_config_puzzle40.txt" ]; then
    echo "   âœ“ Example configs present"
else
    echo "   âœ— Example configs missing"
    exit 1
fi
echo ""

echo "4. Checking Python syntax..."
python3 -m py_compile kangaroo.py ec_operations.py kangaroo_engine.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   âœ“ Python syntax valid"
else
    echo "   âœ— Python syntax errors"
    exit 1
fi
echo ""

echo "5. Checking dependencies..."
python3 -c "import numpy; import ecdsa" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   âœ“ Dependencies installed"
else
    echo "   âœ— Dependencies missing"
    exit 1
fi
echo ""

echo "6. Checking CLI works..."
python3 kangaroo.py --version > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   âœ“ CLI functional"
else
    echo "   âœ— CLI not working"
    exit 1
fi
echo ""

echo "======================================================================"
echo "  âœ“ ALL CHECKS PASSED - KANGAROO PYTHON IS READY!"
echo "======================================================================"
echo ""
echo "Quick start:"
echo "  1. Run tests:    python3 test_kangaroo.py"
echo "  2. Try example:  python3 kangaroo.py -t 2 example_config_small.txt"
echo "  3. Read docs:    cat README_KANGAROO.md"
echo ""
