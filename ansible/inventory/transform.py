#!/usr/bin/env python3
import ipaddress
import json
import os
import sys
import yaml

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
    env = load_yaml(os.path.join(base, 'environment.yaml'))
    compute = load_yaml(os.path.join(base, 'compute.yaml'))
    network = load_yaml(os.path.join(base, 'network.yaml'))
    services = load_yaml(os.path.join(base, 'services.yaml'))

    lan = env.get('subnets', {}).get('lan', {})
    net = ipaddress.ip_network(lan.get('cidr'), strict=True)
    
    router = next((n for n in compute.get('nodes', []) if n.get('host') == 'ultra-64'), {})
    wan = router.get('net', {}).get('wan', {})
    lan_iface = router.get('net', {}).get('lan', {})
    
    profile = router.get('profile', 'router')
    pkgs = services.get('profiles', {}).get(profile, {}).get('pkgs', [])

    leases = [
        {"hostname": d.get('host'), "mac": d.get('mac'), "ip": d.get('ip')}
        for d in network.get('devices', []) if d.get('ip') and d.get('mac')
    ]

    host_vars = {
        "ansible_host": router.get('ip'),
        "timezone": env.get('tz'),
        "domain_local": env.get('domains', {}).get('local'),
        "iface_wan_permanent_mac": wan.get('mac'),
        "iface_wan_spoof_mac": wan.get('spoof'),
        "iface_wan": wan.get('dev'),
        "iface_lan": lan_iface.get('dev'),
        "iface_lan_ip": f"{lan.get('gw')}/{net.prefixlen}",
        "dhcp_subnet": lan.get('cidr'),
        "dhcp_range_start": lan.get('dhcp', {}).get('start'),
        "dhcp_range_end": lan.get('dhcp', {}).get('end'),
        "dhcp_dns_server": lan.get('dhcp', {}).get('dns', [lan.get('gw')])[0],
        "static_leases": leases,
        "packages": pkgs
    }

    inventory = {
        "_meta": {"hostvars": {"ultra-64": host_vars}},
        "all": {"children": ["ungrouped"]},
        "ungrouped": {"hosts": ["ultra-64"]}
    }

    if len(sys.argv) == 3 and sys.argv[1] == '--host':
        print(json.dumps(host_vars if sys.argv[2] == "ultra-64" else {}, indent=2))
    else:
        print(json.dumps(inventory, indent=2))

if __name__ == '__main__':
    main()
