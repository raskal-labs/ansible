#!/usr/bin/env python3
"""
tools/compile.py — shim that delegates to the root compile.py
This file exists for backwards compatibility only.
The authoritative compiler is /compile.py at the repository root.
"""
import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_compiler = os.path.join(root, "compile.py")

if not os.path.exists(root_compiler):
    print(f"ERROR: Root compiler not found at {root_compiler}", file=sys.stderr)
    sys.exit(1)

os.chdir(root)
os.execv(sys.executable, [sys.executable, root_compiler] + sys.argv[1:])
