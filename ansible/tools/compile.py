#!/usr/bin/env python3
"""
Ansible Infrastructure Compiler
Generates inventory, known_hosts, and ssh_config from data files.
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


def generate_inventory():
    """Generate ansible/generated/inventory.yaml with global_identities."""
    # Adjust paths to work from tools directory
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../generated"))
    
    # Load identities
    identities = load_yaml(os.path.join(data_dir, 'identities.yaml'))
    
    # Load environment data
    environment = load_yaml(os.path.join(data_dir, 'environment.yaml'))
    
    # Load Headscale service data
    headscale_data = load_yaml(os.path.join(data_dir, 'services/headscale.yaml'))
    
    # Load existing inventory template or create base structure
    inventory_path = os.path.join(output_dir, 'inventory.yaml')
    if os.path.exists(inventory_path):
        inventory = load_yaml(inventory_path)
    else:
        # Create minimal structure if file doesn't exist
        inventory = {'all': {'hosts': {}}}
    
    # Process all node files to populate hosts
    for node_file in glob.glob(os.path.join(data_dir, 'nodes/*.yaml')):
        node_data = load_yaml(node_file)
        
        # Extract hostname and IP
        hostname = node_data.get('identity', {}).get('hostname')
        ip = node_data.get('ip')
        
        if hostname and ip:
            # Add host to inventory with ansible_host for routing
            inventory['all']['hosts'][hostname] = {
                'ip': ip,
                'ansible_host': ip
            }
    
    # Inject global_identities into the 'all' group
    if 'vars' not in inventory['all']:
        inventory['all']['vars'] = {}
    
    inventory['all']['vars']['global_identities'] = identities.get('system_accounts', [])
    
    # Inject Headscale routing variables
    inventory['all']['vars']['headscale'] = {
        'mesh_subnet': headscale_data.get('mesh_subnet'),
        'mesh_gateway_ip': headscale_data.get('mesh_gateway_ip')
    }
    
    # Inject all top-level environment variables (tz, etc.)
    for key, value in environment.items():
        if key == 'ntp':
            # Handle NTP specially - extract servers if available
            if isinstance(value, dict) and 'servers' in value:
                inventory['all']['vars']['ntp_servers'] = value['servers']
        else:
            # Inject other top-level environment variables directly
            inventory['all']['vars'][key] = value
    
    # Write updated inventory
    with open(inventory_path, 'w') as f:
        yaml.dump(inventory, f, default_flow_style=False, sort_keys=False)


def generate_known_hosts():
    """Generate ansible/generated/known_hosts from node data."""
    # Adjust paths to work from tools directory
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../generated"))
    
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
    # Adjust paths to work from tools directory
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../generated"))
    
    # Load ultra64 node data
    ultra64_data = load_yaml(os.path.join(data_dir, 'nodes/ultra64.yaml'))
    
    hostname = ultra64_data.get('identity', {}).get('hostname', 'ultra64')
    ip = ultra64_data.get('ip', 'FIXME_AI: No IP found in ultra64 node data')
    
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
    # Ensure generated directory exists (relative to tools directory)
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../generated"))
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
