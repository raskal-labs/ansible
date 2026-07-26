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

    compute_data = load_yaml(os.path.join(data_dir, 'compute.yaml'))
    network_data = load_yaml(os.path.join(data_dir, 'network.yaml'))

    # --- 1. Extract Compute Data (The Router Hardware) ---
    nodes = compute_data.get('computing_nodes', [])
    router_cfg = next((n for n in nodes if n.get('hostname') == 'ultra-64'), {})

    ansible_host = router_cfg.get('ip_address', '10.64.0.1')
    mac_address = router_cfg.get('mac_address', 'AA:BB:CC:DD:EE:FF')
    packages = router_cfg.get('software_stack', ['kea-dhcp4', 'unbound', 'dnscrypt-proxy', 'nftables'])

    interfaces = router_cfg.get('connectivity', {}).get('os_interfaces', {})
    iface_wan = interfaces.get('wan', {}).get('kernel_name', 'enp1s0')
    iface_lan = interfaces.get('lan', {}).get('kernel_name', 'enp2s0')

    # --- 2. Extract Network Data & Spoof MAC ---
    net_devices = network_data.get('networking_infrastructure', [])
    
    # Find revolution's WAN MAC to use as spoof MAC
    revolution_device = next((d for d in net_devices if d.get('hostname') == 'revolution'), {})
    iface_wan_spoof_mac = revolution_device.get('wan_mac_address', mac_address)

    # Generate static leases from all network devices with IP and MAC
    static_leases = []
    for dev in net_devices:
        ip = dev.get('ip_address')
        mac = dev.get('mac_address')
        hostname = dev.get('hostname')
        if ip and mac and hostname:
            static_leases.append({
                "hostname": hostname,
                "mac": mac,
                "ip": ip
            })

    # --- 3. Build Ansible Host Vars ---
    host_vars = {
        "ansible_host": ansible_host,
        "timezone": "UTC",
        "domain_local": "lan",
        "iface_wan_permanent_mac": mac_address,
        "iface_wan_spoof_mac": iface_wan_spoof_mac,
        "iface_wan": iface_wan,
        "iface_lan": iface_lan,
        "iface_lan_ip": "10.64.0.1/24",
        "dhcp_subnet": "10.64.0.0/24",
        "dhcp_range_start": "10.64.0.100",
        "dhcp_range_end": "10.64.0.200",
        "static_leases": static_leases,
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
