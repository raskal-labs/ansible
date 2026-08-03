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
    env_data = load_yaml(os.path.join(DATA_DIR, "environment.yaml"))
    
    # Load entire service definitions, not just packages
    services_dict = {}
    services_pkgs = []
    services_absent = []
    services_dir = os.path.join(DATA_DIR, "services")
    
    if os.path.exists(services_dir):
        for f in os.listdir(services_dir):
            if f.endswith('.yaml'):
                svc = load_yaml(os.path.join(services_dir, f))
                svc_id = svc.get('id', f.replace('.yaml', ''))
                services_dict[svc_id] = svc
                services_pkgs.extend(svc.get('packages', []))
                services_absent.extend(svc.get('packages_absent', []))

    inventory = {"all": {"hosts": {}}}
    
    nodes_dir = os.path.join(DATA_DIR, "nodes")
    if os.path.exists(nodes_dir):
        for f in os.listdir(nodes_dir):
            if not f.endswith('.yaml'): continue
            
            node = load_yaml(os.path.join(nodes_dir, f))
            hostname = node.get('identity', {}).get('hostname', 'unknown')
            
            # Aggregate Packages
            raw_packages = []
            raw_packages.extend(env_data.get('packages', []))
            raw_packages.extend(services_pkgs)
            raw_packages.extend(node.get('packages', []))
            
            # Aggregate Absent Packages
            raw_absent = []
            raw_absent.extend(env_data.get('packages_absent', []))
            raw_absent.extend(services_absent)
            raw_absent.extend(node.get('packages_absent', []))
            
            # Start host_vars with env, add modular services dict, then node data
            host_vars = dict(env_data)
            host_vars['configured_services'] = services_dict
            host_vars.update(node)
            
            # Overwrite packages with deterministic deduplicated lists
            host_vars['packages'] = sorted(list(dict.fromkeys(raw_packages)))
            host_vars['packages_absent'] = sorted(list(dict.fromkeys(raw_absent)))
            
            inventory["all"]["hosts"][hostname] = host_vars

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        yaml.dump(inventory, f, default_flow_style=False, sort_keys=False)
        
    print(f"Compiler finished. Artifact saved to: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
