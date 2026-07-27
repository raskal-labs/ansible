#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "1. Validating YAML files..."
python3 -c "
import glob, yaml, sys
files = glob.glob('${REPO_ROOT}/data/*.yaml') + glob.glob('${REPO_ROOT}/ansible/*.yml')
for f in files:
    with open(f, 'r', encoding='utf-8') as fp:
        yaml.safe_load(fp)
print('All YAML files passed syntax check.')
"

echo "2. Executing GitOps dynamic inventory validation..."
python3 "${REPO_ROOT}/ansible/inventory/gitops.py" --list > /dev/null

echo "3. Validating Ansible playbook syntax..."
if command -v ansible-playbook >/dev/null 2>&1; then
    ansible-playbook --syntax-check "${REPO_ROOT}/ansible/edge-router.yml" -i "${REPO_ROOT}/ansible/inventory/gitops.py"
else
    echo "ansible-playbook command not found in environment, skipping playbook syntax validation."
fi

echo "All validations completed successfully."
