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


def load_yaml(filepath):
    """Load YAML file and return parsed content."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)


def ensure_directory(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def aggregate_packages(environment_data, services_data, nodes_data):
    """Aggregate and deduplicate packages from all sources."""
    packages = set()
    packages_absent = set()
    
    # Add packages from environment
    if 'packages' in environment_data:
        packages.update(environment_data['packages'])
    if 'packages_absent' in environment_data:
        packages_absent.update(environment_data['packages_absent'])
    
    # Add packages from services
    for service_data in services_data.values():
        if 'packages' in service_data:
            packages.update(service_data['packages'])
        if 'packages_absent' in service_data:
            packages_absent.update(service_data['packages_absent'])
    
    # Add packages from nodes
    for node_data in nodes_data.values():
        if 'packages' in node_data:
            packages.update(node_data['packages'])
        if 'packages_absent' in node_data:
            packages_absent.update(node_data['packages_absent'])
    
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


def generate_inventory():
    """Generate ansible/generated/inventory.yaml with complete data preservation."""
    data_dir = "data"
    output_dir = "ansible/generated"
    
    # Load all data sources
    identities = load_yaml(os.path.join(data_dir, 'identities.yaml'))
    environment = load_yaml(os.path.join(data_dir, 'environment.yaml'))
    services_data = load_services_data()
    
    # Load Headscale service data if it exists
    headscale_data = services_data.get('headscale', {})
    
    # Initialize inventory structure
    inventory = {
        'all': {
            'hosts': {},
            'vars': {}
        }
    }
    
    # Load all node data
    nodes_data = {}
    for node_file in glob.glob(os.path.join(data_dir, 'nodes/*.yaml')):
        node_name = os.path.splitext(os.path.basename(node_file))[0]
        nodes_data[node_name] = load_yaml(node_file)
    
    # Process all node files to populate hosts
    for node_name, node_data in nodes_data.items():
        # Extract hostname and IP
        hostname = node_data.get('identity', {}).get('hostname')
        ip = node_data.get('ip')
        
        if hostname and ip:
            # Inject all node data + ansible_host for routing
            host_vars = dict(node_data)
            host_vars['ansible_host'] = ip
            inventory['all']['hosts'][hostname] = host_vars
    
    # Inject global_identities into the 'all' group
    inventory['all']['vars']['global_identities'] = identities.get('system_accounts', [])
    
    # Inject Headscale routing variables if available
    if headscale_data:
        inventory['all']['vars']['headscale'] = {
            'mesh_subnet': headscale_data.get('mesh_subnet'),
            'mesh_gateway_ip': headscale_data.get('mesh_gateway_ip')
        }
    
    # Inject all top-level environment variables
    for key, value in environment.items():
        if key == 'ntp':
            # Handle NTP specially - extract servers if available
            if isinstance(value, dict) and 'servers' in value:
                inventory['all']['vars']['ntp_servers'] = value['servers']
        else:
            # Inject other top-level environment variables directly
            inventory['all']['vars'][key] = value
    
    # Aggregate and inject packages
    packages, packages_absent = aggregate_packages(environment, services_data, nodes_data)
    inventory['all']['vars']['packages'] = packages
    inventory['all']['vars']['packages_absent'] = packages_absent
    
    # Inject all services data for reference
    if services_data:
        inventory['all']['vars']['services'] = services_data
    
    # Write updated inventory
    inventory_path = os.path.join(output_dir, 'inventory.yaml')
    with open(inventory_path, 'w') as f:
        yaml.dump(inventory, f, default_flow_style=False, sort_keys=False)


def generate_known_hosts():
    """Generate ansible/generated/known_hosts from node data."""
    data_dir = "data"
    output_dir = "ansible/generated"
    
    known_hosts_entries = []
    
    # Process all node files
    for node_file in glob.glob(os.path.join(data_dir, 'nodes/*.yaml')):
        node_data = load_yaml(node_file)
        
        # Extract hostname and IP
        hostname = node_data.get('identity', {}).get('hostname')
        ip = node_data.get('ip')
        host_keys = node_data.get('host_keys', {})
        
        if hostname and ip:
            # Generate known_hosts entries for each host key type
            for key_type, key_data in host_keys.items():
                if isinstance(key_data, str):
                    # Simple string format: host_keys: { ssh-ed25519: "AAAAC3..." }
                    known_hosts_entries.append(f"{hostname},{ip} {key_type} {key_data}")
                elif isinstance(key_data, dict) and 'key' in key_data:
                    # Dict format: host_keys: { ssh-ed25519: { key: "AAAAC3...", comment: "..." } }
                    known_hosts_entries.append(f"{hostname},{ip} {key_type} {key_data['key']}")
            
            # If no host keys available, add a placeholder comment
            if not host_keys:
                known_hosts_entries.append(f"# {hostname} ({ip}) - No host keys configured")
    
    # Write known_hosts file
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
    
    # Load ultra64 node data
    ultra64_path = os.path.join(data_dir, 'nodes/ultra64.yaml')
    if os.path.exists(ultra64_path):
        ultra64_data = load_yaml(ultra64_path)
        hostname = ultra64_data.get('identity', {}).get('hostname', 'ultra64')
        ip = ultra64_data.get('ip', 'FIXME_AI: No IP found in ultra64 node data')
    else:
        hostname = 'ultra64'
        ip = 'FIXME_AI: ultra64.yaml not found'
    
    ssh_config_content = f"""# Generated SSH config for orchestration
Host {hostname}
    HostName {ip}
    User root
    IdentityFile ~/.ssh/id_ed25519
    UserKnownHostsFile ansible/generated/known_hosts
    StrictHostKeyChecking yes
    PasswordAuthentication no
"""
    
    # Write ssh_config file
    ssh_config_path = os.path.join(output_dir, 'ssh_config')
    with open(ssh_config_path, 'w') as f:
        f.write(ssh_config_content)


def main():
    """Main compiler function."""
    # Ensure generated directory exists
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
