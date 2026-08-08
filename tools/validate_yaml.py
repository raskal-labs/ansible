#!/usr/bin/env python3
"""
tools/validate_yaml.py
Validates all YAML files in data/ against agent.md rules:
  1. Schema: required list keys are lists
  2. No hardcoded internal IPs in fields that must be derived
  3. No calculable CIDRs stored directly in forbidden keys
  4. No netmask fields (derivable)
  5. No interface fields in network files (implementation leakage)
  6. CRITICAL: headscale.yaml must define derp.port
  7. Warns on cidr stored alongside prefix (redundant)
"""
import os
import sys
import re
import yaml

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))

IPV4_RE = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
CIDR_RE = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$')

FORBIDDEN_IP_KEYS = {
    'ip', 'gateway', 'broadcast', 'network_address',
    'mesh_gateway_ip', 'dns_server',
}

FORBIDDEN_CIDR_KEYS = {
    'subnet', 'network_cidr',
}

NETWORK_FILE_FORBIDDEN_KEYS = {
    'interface',
    'netmask',
}


def load_yaml(filepath):
    try:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        print(f"[ERROR] YAML Syntax Error in {filepath}: {e}")
        sys.exit(1)


def is_network_file(filepath):
    return os.path.join("data", "networks") in filepath


def check_value(key, value, filepath, errors, warnings):
    if not isinstance(value, str):
        return
    val = value.strip()

    if key in FORBIDDEN_IP_KEYS and IPV4_RE.match(val):
        errors.append(
            f"[ERROR] '{key}: {val}' in {filepath} — "
            f"hardcoded IP violates Derive Everything rule. "
            f"Use network+host integers instead."
        )
        return

    if key in FORBIDDEN_CIDR_KEYS and CIDR_RE.match(val):
        errors.append(
            f"[ERROR] '{key}: {val}' in {filepath} — "
            f"hardcoded CIDR violates Derive Everything rule."
        )
        return

    if key == 'cidr' and CIDR_RE.match(val):
        warnings.append(
            f"[WARN]  '{key}: {val}' in {filepath} — "
            f"CIDR is derivable from prefix + prefix_len. "
            f"Consider removing and deriving in compile.py."
        )
        return

    if key == 'dns' and IPV4_RE.match(val):
        if val.startswith('10.'):
            errors.append(
                f"[ERROR] 'dns: {val}' in {filepath} — "
                f"internal IP in dns list. Use host integer instead."
            )


def walk_and_check(data, filepath, errors, warnings):
    if isinstance(data, dict):
        for key, value in data.items():
            check_value(key, value, filepath, errors, warnings)

            if is_network_file(filepath) and key in NETWORK_FILE_FORBIDDEN_KEYS:
                errors.append(
                    f"[ERROR] '{key}' in {filepath} — "
                    f"implementation-specific key in network file. "
                    f"Belongs in node file under interfaces:."
                )

            if isinstance(value, str) and IPV4_RE.match(value.strip()):
                if value.strip().startswith('10.'):
                    errors.append(
                        f"[ERROR] Key '{key}' maps to hardcoded internal IP "
                        f"'{value}' in {filepath} — "
                        f"use network+host integers instead."
                    )

            walk_and_check(value, filepath, errors, warnings)

    elif isinstance(data, list):
        for item in data:
            walk_and_check(item, filepath, errors, warnings)


def check_schema(data, filepath, errors):
    list_keys = ["packages", "packages_absent", "users", "templates",
                 "blocklists", "static_leases", "peers", "authorized_clients"]

    if not isinstance(data, dict):
        errors.append(f"[ERROR] {filepath} root structure must be a dictionary.")
        return

    for k in list_keys:
        if k in data and not isinstance(data[k], list):
            errors.append(
                f"[ERROR] '{k}' in {filepath} must be a list, "
                f"found {type(data[k]).__name__}"
            )


def check_headscale_derp(data, filepath, errors):
    """
    CRITICAL: headscale.yaml must define derp.port.
    Missing this causes nftables.conf.j2 to fail to render,
    leaving the router with NO firewall rules.
    """
    if 'headscale' in filepath:
        if 'derp' not in data or 'port' not in data.get('derp', {}):
            errors.append(
                f"[CRITICAL] {filepath} is missing 'derp.port'. "
                f"The nftables.conf.j2 template references "
                f"infra_services.headscale.derp.port — without this "
                f"the firewall will FAIL TO RENDER leaving the router "
                f"with NO firewall rules."
            )


def check_vpn_redundancy(data, filepath, warnings):
    if data.get('id') == 'vpn':
        if 'prefix' in data and 'cidr' in data:
            warnings.append(
                f"[WARN]  {filepath} stores both 'prefix' and 'cidr'. "
                f"'cidr' is derivable from 'prefix' in compile.py. "
                f"Remove 'cidr' to comply with Derive Everything rule."
            )


def main():
    errors = []
    warnings = []

    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if not file.endswith('.yaml'):
                continue
            path = os.path.join(root, file)
            data = load_yaml(path)

            check_schema(data, path, errors)
            check_headscale_derp(data, path, errors)
            check_vpn_redundancy(data, path, warnings)
            walk_and_check(data, path, errors, warnings)

    for w in warnings:
        print(w)

    for e in errors:
        print(e)

    if warnings:
        print(f"\n==> {len(warnings)} warning(s).")

    if errors:
        print(f"\n==> [FAIL] Validation failed with {len(errors)} error(s).")
        sys.exit(1)

    print("==> [VALIDATE] All data schemas and agent.md rules passed.")


if __name__ == '__main__':
    main()
