#!/usr/bin/env python3
import os
import yaml

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../generated/inventory.yaml"))

def load_yaml(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        return yaml.safe_load(f) or {}

def main():
    # Load global contexts
    env_data = load_yaml(os.path.join(DATA_DIR, "environment.yaml"))
    services_data = load_yaml(os.path.join(DATA_DIR, "services.yaml"))
    
    inventory = {"all": {"hosts": {}}}
    
    # Process nodes
    nodes_dir = os.path.join(DATA_DIR, "nodes")
    if os.path.exists(nodes_dir):
        for f in os.listdir(nodes_dir):
            if not f.endswith('.yaml'): continue
            
            node = load_yaml(os.path.join(nodes_dir, f))
            hostname = node.get('identity', {}).get('hostname', 'unknown')
            
            # Start with globals, then overwrite with node specifics
            host_vars = dict(env_data)
            host_vars.update(services_data)
            host_vars.update(node)
            
            inventory["all"]["hosts"][hostname] = host_vars

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        yaml.dump(inventory, f, default_flow_style=False, sort_keys=False)
        
    print(f"Compiler finished. Artifact saved to: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
