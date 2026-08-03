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
    # Load identities
    identities = load_yaml('data/identities.yaml')
    
    # Load existing inventory template or create base structure
    inventory_path = 'ansible/generated/inventory.yaml'
    if os.path.exists(inventory_path):
        inventory = load_yaml(inventory_path)
    else:
        # Create minimal structure if file doesn't exist
        inventory = {'all': {'hosts': {}}}
    
    # Inject global_identities into the 'all' group
    if 'vars' not in inventory['all']:
        inventory['all']['vars'] = {}
    
    inventory['all']['vars']['global_identities'] = identities.get('system_accounts', [])
    
    # Write updated inventory
    with open(inventory_path, 'w') as f:
        yaml.dump(inventory, f, default_flow_style=False, sort_keys=False)


def generate_known_hosts():
    """Generate ansible/generated/known_hosts from node data."""
    known_hosts_entries = []
    
    # Process all node files
    for node_file in glob.glob('data/nodes/*.yaml'):
        node_data = load_yaml(node_file)
        
        # Extract hostname and IP
        hostname = node_data.get('identity', {}).get('hostname')
        ip = node_data.get('ip')
        
        if hostname and ip:
            # FIXME_AI: Need host_keys data in node files to generate proper known_hosts entries
            # For now, create placeholder entries
            known_hosts_entries.append(f"# {hostname} ({ip}) - FIXME_AI: Add host_keys to node data")
    
    # Write known_hosts file
    known_hosts_path = 'ansible/generated/known_hosts'
    with open(known_hosts_path, 'w') as f:
        f.write("# Generated known_hosts file\n")
        f.write("# FIXME_AI: Populate with actual host keys from node data\n")
        for entry in known_hosts_entries:
            f.write(f"{entry}\n")


def generate_ssh_config():
    """Generate ansible/generated/ssh_config for orchestration client."""
    # Load ultra64 node data
    ultra64_data = load_yaml('data/nodes/ultra64.yaml')
    
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
    ssh_config_path = 'ansible/generated/ssh_config'
    with open(ssh_config_path, 'w') as f:
        f.write(ssh_config_content)


def main():
    """Main compiler function."""
    # Ensure generated directory exists
    ensure_directory('ansible/generated')
    
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
