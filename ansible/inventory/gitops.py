#!/usr/bin/env python3
import ipaddress
import json
import os
import sys

import yaml


def load_yaml(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required configuration file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        if data is None:
            raise ValueError(f"File is empty: {path}")
        return data


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.abspath(os.path.join(script_dir, '../../data'))

    env_data = load_yaml(os.path.join(data_dir, 'environment.yaml'))
    compute_data = load_yaml(os.path.join(data_dir, 'compute.yaml'))
    network_data = load_yaml(os.path.join(data_dir, 'network.yaml'))
    services_data = load_yaml(os.path.join(data_dir, 'services.yaml'))

    # Environment & IPAM processing
    env = env_data.get('environment', {})
    timezone = env.get('localization', {}).get('timezone')
    if not timezone:
        raise ValueError("Missing localization.timezone in environment.yaml")

    domain_local = env.get('domains', {}).get('local')
    if not domain_local:
        raise ValueError("Missing domains.local in environment.yaml")

    subnets = env.get('ipam', {}).get('subnets', [])
    lan_main = next((s for s in subnets if s.get('name') == 'LAN_MAIN'), None)
    if not lan_main:
        raise ValueError("Missing LAN_MAIN subnet configuration in environment.yaml")

    cidr = lan_main.get('cidr')
    gateway_ip_str = lan_main.get('gateway')
    dhcp_pool = lan_main.get('dhcp_pool', {})
    dhcp_start_str = dhcp_pool.get('start')
    dhcp_end_str = dhcp_pool.get('stop')
    dns_servers = dhcp_pool.get('dns_servers', [])

    if not all([cidr, gateway_ip_str, dhcp_start_str, dhcp_end_str, dns_servers]):
        raise ValueError("Incomplete IPAM details for LAN_MAIN in environment.yaml")

    net = ipaddress.ip_network(cidr, strict=True)
    gateway_ip = ipaddress.ip_address(gateway_ip_str)
    dhcp_start = ipaddress.ip_address(dhcp_start_str)
    dhcp_end = ipaddress.ip_address(dhcp_end_str)

    if gateway_ip not in net:
        raise ValueError(f"Gateway IP {gateway_ip_str} is not in subnet {cidr}")
    if dhcp_start not in net:
        raise ValueError(f"DHCP pool start {dhcp_start_str} is not in subnet {cidr}")
    if dhcp_end not in net:
        raise ValueError(f"DHCP pool stop {dhcp_end_str} is not in subnet {cidr}")
    if dhcp_start > dhcp_end:
        raise ValueError(
            f"DHCP pool start {dhcp_start_str} is greater than "
            f"pool stop {dhcp_end_str}"
        )

    iface_lan_ip = f"{gateway_ip_str}/{net.prefixlen}"

    # Compute node processing
    nodes = compute_data.get('computing_nodes', [])
    router_cfg = next((n for n in nodes if n.get('hostname') == 'ultra-64'), None)
    if not router_cfg:
        raise ValueError("Host 'ultra-64' not found in compute.yaml")

    ansible_host = router_cfg.get('ip_address')
    if not ansible_host or ipaddress.ip_address(ansible_host) not in net:
        raise ValueError(f"Invalid host IP for ultra-64: {ansible_host}")

    profile_name = router_cfg.get('assigned_profile', 'edge_router')
    profile = services_data.get('service_profiles', {}).get(profile_name, {})
    packages = profile.get('packages') or router_cfg.get('software_stack')
    if not packages:
        raise ValueError(f"No packages defined for profile '{profile_name}'")

    interfaces = router_cfg.get('connectivity', {}).get('os_interfaces', {})
    wan_iface = interfaces.get('wan', {})
    lan_iface = interfaces.get('lan', {})

    iface_wan = wan_iface.get('kernel_name')
    iface_lan = lan_iface.get('kernel_name')
    iface_wan_hardware_mac = wan_iface.get('hardware_mac')
    iface_wan_functional_mac = wan_iface.get('functional_mac')

    if not iface_wan or not iface_lan:
        raise ValueError("WAN or LAN interface kernel_name missing in compute.yaml")

    if (
        not iface_wan_hardware_mac
        or "AA:BB:CC" in iface_wan_hardware_mac.upper()
    ):
        raise ValueError(
            "Missing or placeholder hardware MAC address for WAN interface"
        )

    if (
        not iface_wan_functional_mac
        or "AA:BB:CC" in iface_wan_functional_mac.upper()
    ):
        raise ValueError(
            "Missing or placeholder functional MAC address for WAN interface"
        )

    # Network devices and static leases validation
    net_devices = network_data.get('networking_infrastructure', [])
    cafe_device = next(
        (d for d in net_devices if d.get('hostname') == 'cafe'),
        None
    )
    if not cafe_device:
        raise ValueError("Device 'cafe' not found in network.yaml")

    cafe_wan_mac = cafe_device.get('wan_mac_address')
    if not cafe_wan_mac or "AA:BB:CC" in cafe_wan_mac.upper():
        raise ValueError(
            "Missing or placeholder WAN MAC address on cafe device"
        )

    if cafe_wan_mac.upper() != iface_wan_functional_mac.upper():
        raise ValueError(
            "WAN functional_mac for ultra-64 does not match "
            "cafe.wan_mac_address"
        )

    seen_ips = {gateway_ip_str}
    seen_macs = {
        iface_wan_hardware_mac.upper(),
        iface_wan_functional_mac.upper()
    }
    seen_hostnames = {'ultra-64'}

    static_leases = []
    for dev in net_devices:
        ip = dev.get('ip_address')
        mac = dev.get('hardware_mac')
        hostname = dev.get('hostname')
        if ip and mac and hostname:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj not in net:
                raise ValueError(
                    f"Static lease IP {ip} for host {hostname} "
                    f"is outside subnet {cidr}"
                )
            if dhcp_start <= ip_obj <= dhcp_end:
                raise ValueError(
                    f"Static lease IP {ip} for host {hostname} "
                    "overlaps dynamic pool range"
                )
            if ip in seen_ips:
                raise ValueError(f"Duplicate IP address in static leases: {ip}")
            if mac.upper() in seen_macs:
                raise ValueError(
                    f"Duplicate MAC address in static leases: {mac}"
                )
            if hostname in seen_hostnames:
                raise ValueError(
                    f"Duplicate hostname in static leases: {hostname}"
                )

            seen_ips.add(ip)
            seen_macs.add(mac.upper())
            seen_hostnames.add(hostname)

            static_leases.append({
                "hostname": hostname,
                "mac": mac,
                "ip": ip
            })

    host_vars = {
        "ansible_host": ansible_host,
        "timezone": timezone,
        "domain_local": domain_local,
        "iface_wan_permanent_mac": iface_wan_hardware_mac,
        "iface_wan_spoof_mac": iface_wan_functional_mac,
        "iface_wan": iface_wan,
        "iface_lan": iface_lan,
        "iface_lan_ip": iface_lan_ip,
        "dhcp_subnet": cidr,
        "dhcp_range_start": dhcp_start_str,
        "dhcp_range_end": dhcp_end_str,
        "dhcp_dns_server": dns_servers[0],
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

    if len(sys.argv) == 3 and sys.argv[1] == '--host':
        target_host = sys.argv[2]
        if target_host == "ultra-64":
            print(json.dumps(host_vars, indent=2))
        else:
            print(json.dumps({}, indent=2))
    elif len(sys.argv) == 2 and sys.argv[1] == '--list':
        print(json.dumps(inventory, indent=2))
    else:
        print(json.dumps(inventory, indent=2))


if __name__ == '__main__':
    main()
