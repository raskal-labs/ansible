#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "1. Validating YAML files..."

python3 - <<PY
from pathlib import Path
import yaml

root = Path("${REPO_ROOT}")

files = list(root.glob("data/*.yaml")) + list(root.glob("ansible/*.yml"))

if not files:
    raise SystemExit("No YAML files found")

for file in files:
    with file.open("r", encoding="utf-8") as f:
        yaml.safe_load(f)
    print(f"OK: {file.relative_to(root)}")

print("All YAML files passed syntax check.")
PY


echo
echo "2. Executing dynamic inventory validation..."

python3 "${REPO_ROOT}/ansible/inventory/transform.py" --list > /dev/null

echo "Inventory validation passed."


echo
echo "3. Validating Ansible playbook syntax..."

if command -v ansible-playbook >/dev/null 2>&1; then
    ansible-playbook \
        --syntax-check \
        -i "${REPO_ROOT}/ansible/inventory/transform.py" \
        -e "repo_root=${REPO_ROOT}" \
        "${REPO_ROOT}/ansible/provision-ultra-64.yml"
else
    echo "ansible-playbook not found, skipping."
fi


echo
echo "All validations completed successfully."
