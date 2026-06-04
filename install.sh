#!/usr/bin/env bash
set -euo pipefail

echo "=== cli-anything-ledit Installer ==="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Install from https://www.python.org/downloads/"
    exit 1
fi

PY_VERSION=$(python3 --version 2>&1)
echo "Found: $PY_VERSION"

# Install
echo ""
echo "Installing cli-anything-ledit..."
pip3 install -e "." 2>/dev/null || pip install -e "."
echo "Package installed."

# Verify
echo ""
echo "Verifying installation..."
if cli-anything-ledit --json inspect 2>/dev/null; then
    echo "Installation verified."
else
    echo "WARNING: L-Edit not detected. Set LEDIT_EXE env var."
fi

echo ""
echo "=== Installation complete ==="
echo ""
echo "Quick start:"
echo '  cli-anything-ledit --json draw-square-array --rows 4 --cols 6 --size 2 --pitch 5 --layer CURRENT --out outputs/array.tco'
