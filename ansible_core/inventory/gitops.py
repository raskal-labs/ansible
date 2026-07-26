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
    network_data = load_yaml(os.path.join(data_dir, 'network.yaml'))
    services_data = load_yaml(os.path.join(data_dir, 'services.yaml'))

    # Extract router config
    net_infra = network_data.get('networking_infrastructure', {})
    router_cfg = net_infra.get('ultra-64', {})

    # Default values if not specified
    timezone = env_data.get('timezone', 'UTC')
    domain_local = env_data.get('domain_local', 'lan')

    host_vars = {
        "ansible_host": router_cfg.get('ansible_host', '127.0.0.1'),
        "timezone": timezone,
        "domain_local": domain_local,
        "iface_wan_permanent_mac": router_cfg.get('iface_wan_permanent_mac', '00:00:00:00:00:00'),
        "iface_wan_spoof_mac": router_cfg.get('iface_wan_spoof_mac', '00:00:00:00:00:00'),
        "iface_wan": router_cfg.get('iface_wan', 'eth0'),
        "iface_lan": router_cfg.get('iface_lan', 'eth1'),
        "iface_lan_ip": router_cfg.get('iface_lan_ip', '192.168.1.1/24'),
        "dhcp_subnet": router_cfg.get('dhcp_subnet', '192.168.1.0/24'),
        "dhcp_range_start": router_cfg.get('dhcp_range_start', '192.168.1.100'),
        "dhcp_range_end": router_cfg.get('dhcp_range_end', '192.168.1.200'),
        "static_leases": router_cfg.get('static_leases', []),
        "packages": services_data.get('services', {}).get('packages', ['kea', 'unbound', 'dnscrypt-proxy', 'nftables'])
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
