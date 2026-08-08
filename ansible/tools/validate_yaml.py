#!/usr/bin/env python3
"""
ansible/tools/validate_yaml.py — shim that delegates to tools/validate_yaml.py
This file exists for backwards compatibility only.
The authoritative validator is /tools/validate_yaml.py at the repository root.
"""
import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
canonical = os.path.join(root, "tools", "validate_yaml.py")

if not os.path.exists(canonical):
    print(f"ERROR: Canonical validator not found at {canonical}", file=sys.stderr)
    sys.exit(1)

os.chdir(root)
os.execv(sys.executable, [sys.executable, canonical] + sys.argv[1:])
