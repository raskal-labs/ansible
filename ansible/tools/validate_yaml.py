#!/usr/bin/env python3
import os
import sys
import yaml

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))

def load_yaml(filepath):
    try:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        print(f"[ERROR] YAML Syntax Error in {filepath}: {e}")
        sys.exit(1)

def main():
    errors = 0
    list_keys = ["packages", "packages_absent", "users", "templates"]

    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if not file.endswith('.yaml'): continue
            path = os.path.join(root, file)
            data = load_yaml(path)
            
            if not isinstance(data, dict):
                print(f"[ERROR] {file} root structure must be a dictionary.")
                errors += 1
                continue

            for k in list_keys:
                if k in data and not isinstance(data[k], list):
                    print(f"[ERROR] '{k}' in {file} must be a list, found {type(data[k]).__name__}")
                    errors += 1

    if errors > 0:
        print(f"==> [FAIL] Validation aborted with {errors} schema errors.")
        sys.exit(1)
    
    print("==> [VALIDATE] Data schemas passed.")

if __name__ == '__main__':
    main()
