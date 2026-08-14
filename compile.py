#!/usr/bin/env python3
"""
Ansible Infrastructure Compiler
Generates inventory, known_hosts, and ssh_config from data files.
Consolidates all node data, services, and packages without stripping any keys.
"""

import os
import sys
import yaml
import glob

THIRD_PARTY_PACKAGES = {'headscale', 'step-ca', 'step-cli', 'crowdsec', 'crowdsec-firewall-bouncer-nftables'}


def load_yaml(filepath):
    """Load YAML file and return parsed content."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)


def ensure_directory(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def aggregate_packages(environment_data, node_data, services_data):
    """
    Aggregate and deduplicate packages for a single host.

    Scope (audit fix 2026-08-14): package aggregation was previously global
    — every host received every service's packages regardless of whether
    that host actually ran the service. This is now computed per host:
      - environment.yaml packages always apply (baseline for all hosts).
      - the node's own declared packages always apply.
      - service packages only apply to hosts that actually run services.
        Currently, service placement is expressed only via the
        `profile: router` flag (the same flag ansible/site.yml and
        ansible/dry-run.yml already use to gate whether router roles are
        applied to a host), so that is used here as the equivalent gate
        for which hosts should receive service packages.
    """
    packages = set()
    packages_absent = set()

    if 'packages' in environment_data:
        packages.update(environment_data['packages'])
    if 'packages_absent' in environment_data:
        packages_absent.update(environment_data['packages_absent'])

    if 'packages' in node_data:
        packages.update(node_data['packages'])
    if 'packages_absent' in node_data:
        packages_absent.update(node_data['packages_absent'])

    if node_data.get('profile') == 'router':
        for service_data in services_data.values():
            if 'packages' in service_data:
                packages.update(service_data['packages'])
            if 'packages_absent' in service_data:
                packages_absent.update(service_data['packages_absent'])

    # Exclude third‑party packages that do not exist in Fedora's default repos
    packages = packages - THIRD_PARTY_PACKAGES

    return sorted(list(packages)), sorted(list(packages_absent))


def load_services_data():
    """Load all service configuration files."""
    services_data = {}
    services_dir = os.path.join("data", "services")

    if os.path.exists(services_dir):
        for service_file in glob.glob(os.path.join(services_dir, "*.yaml")):
            service_name = os.path.splitext(os.path.basename(service_file))[0]
            services_data[service_name] = load_yaml(service_file)

    return services_data


def load_networks_data():
    """Load all network configuration files."""
    networks_data = {}
    networks_dir = os.path.join("data", "networks")

    if os.path.exists(networks_dir):
        for network_file in glob.glob(os.path.join(networks_dir, "*.yaml")):
            network_name = os.path.splitext(os.path.basename(network_file))[0]
            networks_data[network_name] = load_yaml(network_file)

    return networks_data


def derive_network_calculations(networks_data):
    """
    Derive calculated network values from conceptual data.
    Skips files that do not have a `network:` integer key (e.g. dhcp.yaml policy index).
    """
    derived_networks = {}

    for network_name, network_data in networks_data.items():
        if 'network' not in network_data:
            continue
        network_id = network_data['network']
        gateway_host = network_data.get('gateway_host', 1)
        prefix_len = network_data.get('prefix_len', 24)

        derived_networks[network_name] = {
            'id': network_data.get('id', network_name),
            'network': network_id,
            'prefix_len': prefix_len,
            'cidr': f"10.{network_id}.0.0/{prefix_len}",
            'gateway': f"10.{network_id}.0.{gateway_host}",
            'subnet_mask': "255.255.255.0",
            'broadcast': f"10.{network_id}.0.255",
            'network_address': f"10.{network_id}.0.0"
        }

    return derived_networks


def derive_ip_from_network_host(network, host):
    """Calculate IP address from network and host IDs."""
    return f"10.{network}.0.{host}"


def derive_cidr_from_network_host(network, host, prefix_len=32):
    """Calculate CIDR from network and host IDs."""
    return f"10.{network}.0.{host}/{prefix_len}"


def _get_node_ip(node_data):
    """Derive a clean IP address from node data, or return None."""
    network = node_data.get('network')
    host = node_data.get('host')
    if network is not None and host is not None:
        return derive_ip_from_network_host(network, host)
    return None


def process_vpn_service(vpn_data):
    """
    Derive vpn.cidr from prefix + prefix_len.
    Removes the need to store cidr in vpn.yaml.
    """
    processed = dict(vpn_data)
    prefix = processed.get('prefix')
    prefix_len = processed.get('prefix_len', 24)
    if prefix:
        processed['cidr'] = f"{prefix}.0/{prefix_len}"
    return processed


def process_headscale_service(headscale_data):
    """
    Derive mesh_gateway_ip from mesh_gateway_network + mesh_gateway_host.
    Removes the need to store mesh_gateway_ip in headscale.yaml.
    """
    processed = dict(headscale_data)
    gw_network = processed.get('mesh_gateway_network')
    gw_host = processed.get('mesh_gateway_host')
    if gw_network is not None and gw_host is not None:
        processed['mesh_gateway_ip'] = derive_ip_from_network_host(gw_network, gw_host)
    return processed


def process_dns_service(dns_data):
    """
    Derive IPs for custom_dns entries from network + host integers.
    Injects .ip into each list entry for template consumption.
    """
    processed = dict(dns_data)
    raw_custom_dns = processed.get('custom_dns', [])

    if isinstance(raw_custom_dns, list):
        derived = []
        for entry in raw_custom_dns:
            e = dict(entry)
            if 'network' in e and 'host' in e:
                e['ip'] = derive_ip_from_network_host(e['network'], e['host'])
            derived.append(e)
        processed['custom_dns'] = derived

    return processed


def process_caddy_service(caddy_data):
    """
    Derive backend IPs for both services and auth_profiles in caddy.yaml.
    """
    processed = dict(caddy_data)

    if 'services' in processed:
        for svc in processed['services']:
            if 'backend_network' in svc and 'backend_host' in svc:
                backend_ip = derive_ip_from_network_host(
                    svc['backend_network'],
                    svc['backend_host']
                )
                svc['backend'] = f"{backend_ip}:{svc['backend_port']}"

    if 'auth_profiles' in processed:
        for name, profile in processed['auth_profiles'].items():
            if 'backend_network' in profile and 'backend_host' in profile:
                backend_ip = derive_ip_from_network_host(
                    profile['backend_network'],
                    profile['backend_host']
                )
                profile['backend'] = f"{backend_ip}:{profile['backend_port']}"

    return processed


def process_static_leases(dhcp_config, network_id):
    """
    Derive IPs for static leases from network + host integers.
    """
    if 'static_leases' not in dhcp_config:
        return dhcp_config

    processed = dict(dhcp_config)
    for lease in processed['static_leases']:
        lease_network = lease.get('network', network_id)
        if 'host' in lease:
            lease['ip'] = derive_ip_from_network_host(lease_network, lease['host'])

    return processed


def generate_inventory():
    """Generate ansible/generated/inventory.yaml with complete data preservation."""
    data_dir = "data"
    output_dir = "ansible/generated"

    identities = load_yaml(os.path.join(data_dir, 'identities.yaml'))
    environment = load_yaml(os.path.join(data_dir, 'environment.yaml'))
    services_data = load_services_data()
    networks_data = load_networks_data()

    derived_networks = derive_network_calculations(networks_data)

    inventory = {
        'all': {
            'hosts': {},
            'vars': {}
        }
    }

    nodes_data = {}
    for node_file in glob.glob(os.path.join(data_dir, 'nodes/*.yaml')):
        node_name = os.path.splitext(os.path.basename(node_file))[0]
        nodes_data[node_name] = load_yaml(node_file)

    for node_name, node_data in nodes_data.items():
        hostname = node_data.get('identity', {}).get('hostname')
        network = node_data.get('network')
        host = node_data.get('host')

        if hostname and network is not None and host is not None:
            host_vars = dict(node_data)

            host_vars['ansible_user'] = host_vars.get('admin_user', 'root')
            host_vars['ansible_become'] = False

            ip = derive_ip_from_network_host(network, host)
            host_vars['ip'] = ip
            host_vars['ansible_host'] = ip

            if 'network' in host_vars:
                host_vars['network_cidr'] = f"10.{network}.0.0/24"
                host_vars['network_gateway'] = f"10.{network}.0.1"

            if 'host_services' in host_vars:
                # Process DHCP
                if 'dhcp' in host_vars['host_services']:
                    dhcp_config = host_vars['host_services']['dhcp']
                    dhcp_network = dhcp_config.get('network', network)
                    dhcp_config['subnet'] = f"10.{dhcp_network}.0.0/24"
                    dhcp_config['range_start'] = f"10.{dhcp_network}.0.{dhcp_config['range_start']}"
                    dhcp_config['range_end'] = f"10.{dhcp_network}.0.{dhcp_config['range_end']}"
                    if 'dns_host' in dhcp_config:
                        dhcp_config['dns_server'] = derive_ip_from_network_host(
                            dhcp_network, dhcp_config['dns_host']
                        )
                    # Inject static leases from the network definition
                    vlan_key = f"vlan-{dhcp_network}"
                    if vlan_key in networks_data:
                        vlan = networks_data[vlan_key]
                        if 'static_leases' in vlan:
                            leases = []
                            for lease in vlan['static_leases']:
                                l = dict(lease)
                                l['ip'] = derive_ip_from_network_host(dhcp_network, l['host'])
                                hostname_lease = l.get('hostname')
                                if hostname_lease:
                                    node = nodes_data.get(hostname_lease)
                                    if node and 'mac' in node:
                                        l['mac'] = node['mac']
                                leases.append(l)
                            dhcp_config['static_leases'] = leases
                    host_vars['host_services']['dhcp'] = dhcp_config

                # Process VPN peers
                if 'vpn' in host_vars['host_services']:
                    vpn_config = host_vars['host_services']['vpn']
                    if 'peers' in vpn_config:
                        for peer in vpn_config['peers']:
                            if 'extra_networks' in peer:
                                peer['extra_ips'] = []
                                for extra_net in peer['extra_networks']:
                                    if 'network' in extra_net and 'host' in extra_net:
                                        extra_ip = derive_cidr_from_network_host(
                                            extra_net['network'],
                                            extra_net['host'],
                                            prefix_len=24
                                        )
                                        peer['extra_ips'].append(extra_ip)

            # Per-host package aggregation (audit fix 2026-08-14 — see
            # aggregate_packages() docstring). This overwrites the node's
            # raw packages/packages_absent lists with the fully aggregated,
            # correctly-scoped set for this specific host.
            host_packages, host_packages_absent = aggregate_packages(
                environment, host_vars, services_data
            )
            host_vars['packages'] = host_packages
            host_vars['packages_absent'] = host_packages_absent

            inventory['all']['hosts'][hostname] = host_vars

    # Global identities
    inventory['all']['vars']['global_identities'] = identities.get('system_accounts', [])

    # Environment variables
    for key, value in environment.items():
        if key == 'ntp':
            if isinstance(value, dict) and 'servers' in value:
                inventory['all']['vars']['ntp_servers'] = value['servers']
        else:
            inventory['all']['vars'][key] = value

    # Baseline packages (all.vars level). Ansible host_vars (set per-host
    # above) take precedence over these for any host that defines its own
    # 'packages'/'packages_absent', per normal Ansible variable precedence.
    # This baseline only matters for hosts with no explicit override.
    baseline_packages = sorted(
        list(set(environment.get('packages', [])) - THIRD_PARTY_PACKAGES)
    )
    baseline_packages_absent = sorted(list(set(environment.get('packages_absent', []))))
    inventory['all']['vars']['packages'] = baseline_packages
    inventory['all']['vars']['packages_absent'] = baseline_packages_absent

    # Derived networks
    if derived_networks:
        inventory['all']['vars']['networks'] = derived_networks

    # Process and inject services
    processed_services = {}
    for service_name, service_data in services_data.items():
        if service_name == 'vpn':
            processed_services[service_name] = process_vpn_service(service_data)
        elif service_name == 'headscale':
            processed_services[service_name] = process_headscale_service(service_data)
        elif service_name == 'dns':
            processed_services[service_name] = process_dns_service(service_data)
        elif service_name == 'caddy':
            processed_services[service_name] = process_caddy_service(service_data)
        else:
            processed_services[service_name] = dict(service_data)

    if processed_services:
        inventory['all']['vars']['infra_services'] = processed_services

    inventory_path = os.path.join(output_dir, 'inventory.yaml')
    with open(inventory_path, 'w') as f:
        yaml.dump(inventory, f, default_flow_style=False, sort_keys=False)


def generate_known_hosts():
    """Generate ansible/generated/known_hosts from node data."""
    data_dir = "data"
    output_dir = "ansible/generated"

    known_hosts_entries = []

    for node_file in glob.glob(os.path.join(data_dir, 'nodes/*.yaml')):
        node_data = load_yaml(node_file)

        hostname = node_data.get('identity', {}).get('hostname')
        ip = _get_node_ip(node_data)
        host_keys = node_data.get('host_keys', {})

        if hostname and ip:
            for key_type, key_data in host_keys.items():
                if isinstance(key_data, str):
                    known_hosts_entries.append(f"{hostname},{ip} {key_type} {key_data}")
                elif isinstance(key_data, dict) and 'key' in key_data:
                    known_hosts_entries.append(f"{hostname},{ip} {key_type} {key_data['key']}")

            if not host_keys:
                known_hosts_entries.append(
                    f"# {hostname} ({ip}) - No host keys configured. "
                    f"Run: ssh-keyscan -t ed25519,rsa {ip}"
                )

    known_hosts_path = os.path.join(output_dir, 'known_hosts')
    with open(known_hosts_path, 'w') as f:
        f.write("# Generated known_hosts file\n")
        f.write("# Host keys are automatically populated from node data\n")
        for entry in known_hosts_entries:
            f.write(f"{entry}\n")


def generate_ssh_config():
    """Generate ansible/generated/ssh_config for orchestration client."""
    data_dir = "data"
    output_dir = "ansible/generated"

    ultra64_path = os.path.join(data_dir, 'nodes/ultra64.yaml')
    if os.path.exists(ultra64_path):
        ultra64_data = load_yaml(ultra64_path)
        hostname = ultra64_data.get('identity', {}).get('hostname', 'ultra64')
        ip = _get_node_ip(ultra64_data)
        if ip is None:
            ip = '0.0.0.0'
        user = ultra64_data.get('admin_user', 'root')
    else:
        hostname = 'ultra64'
        ip = '0.0.0.0'
        user = 'root'

    ssh_config_content = f"""# Generated SSH config for orchestration
Host {hostname}
    HostName {ip}
    User {user}
    IdentityFile ~/.ssh/id_ed25519
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    PasswordAuthentication no
"""

    ssh_config_path = os.path.join(output_dir, 'ssh_config')
    with open(ssh_config_path, 'w') as f:
        f.write(ssh_config_content)


def main():
    """Main compiler function."""
    output_dir = "ansible/generated"
    ensure_directory(output_dir)

    try:
        print("Generating inventory...")
        generate_inventory()

        print("Generating known_hosts...")
        generate_known_hosts()

        print("Generating ssh_config...")
        generate_ssh_config()

        print("Compilation complete!")

    except Exception as e:
        print(f"Error during compilation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
