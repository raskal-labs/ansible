#!/usr/bin/env python3
import os
import sys
import json
import yaml

def load_yaml(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def main():
    # Determine paths relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.abspath(os.path.join(script_dir, '../../data'))

    env_data = load_yaml(os.path.join(data_dir, 'environment.yaml'))
    compute_data = load_yaml(os.path.join(data_dir, 'compute.yaml'))
    services_data = load_yaml(os.path.join(data_dir, 'services.yaml'))
    # network_data contains APs/Switches - keeping it for future use if needed
    network_data = load_yaml(os.path.join(data_dir, 'network.yaml'))

    # --- 1. Extract Environment & IPAM Data ---
    env_root = env_data.get('environment', {})
    timezone = env_root.get('localization', {}).get('timezone', 'UTC')
    domain_local = env_root.get('domains', {}).get('local', 'lan')

    # Find the main LAN subnet for DHCP config
    subnets = env_root.get('ipam', {}).get('subnets', [])
    lan_subnet = next((s for s in subnets if s.get('name') == 'LAN_MAIN'), {})
    
    dhcp_subnet = lan_subnet.get('cidr', '192.168.1.0/24')
    gateway = lan_subnet.get('gateway', '192.168.1.1')
    
    # Extract the CIDR suffix (e.g. "24") to build the LAN IP string
    cidr_suffix = dhcp_subnet.split('/')[-1] if '/' in dhcp_subnet else '24'
    iface_lan_ip = f"{gateway}/{cidr_suffix}"

    dhcp_pool = lan_subnet.get('dhcp_pool', {})
    dhcp_range_start = dhcp_pool.get('start', '192.168.1.100')
    dhcp_range_end = dhcp_pool.get('stop', '192.168.1.200')

    # --- 2. Extract Compute Data (The Router Hardware) ---
    nodes = compute_data.get('computing_nodes', [])
    router_cfg = next((n for n in nodes if n.get('hostname') == 'ultra-64'), {})

    ansible_host = router_cfg.get('ip_address', '127.0.0.1')
    mac_address = router_cfg.get('mac_address', '00:00:00:00:00:00')

    interfaces = router_cfg.get('connectivity', {}).get('os_interfaces', {})
    iface_wan = interfaces.get('wan', {}).get('kernel_name', 'eth0')
    iface_lan = interfaces.get('lan', {}).get('kernel_name', 'eth1')

    # --- 3. Extract Services Data ---
    profile_name = router_cfg.get('assigned_profile', 'edge_router')
    packages = services_data.get('service_profiles', {}).get(profile_name, {}).get('packages', ['kea-dhcp4', 'unbound', 'dnscrypt-proxy', 'nftables'])

    # --- 4. Build Ansible Host Vars ---
    host_vars = {
        "ansible_host": ansible_host,
        "timezone": timezone,
        "domain_local": domain_local,
        "iface_wan_permanent_mac": mac_address,
        "iface_wan_spoof_mac": mac_address, # Sets spoof to the same as permanent by default
        "iface_wan": iface_wan,
        "iface_lan": iface_lan,
        "iface_lan_ip": iface_lan_ip,
        "dhcp_subnet": dhcp_subnet,
        "dhcp_range_start": dhcp_range_start,
        "dhcp_range_end": dhcp_range_end,
        "static_leases": [], # Future logic can parse this from network_data
        "packages": packages
    }

    inventory = {
        "_meta": {
            "hostvars": {
                "ultra-64": host_vars
            }
        },
        "all": {
            "children": ["ungrouped"]
        },
        "ungrouped": {
            "hosts": ["ultra-64"]
        }
    }

    if len(sys.argv) == 2 and sys.argv[1] == '--list':
        print(json.dumps(inventory, indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == '--host':
        print(json.dumps(host_vars, indent=2))
    else:
        print(json.dumps(inventory, indent=2))

if __name__ == '__main__':
    main()
