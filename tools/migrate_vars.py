import os
import re

# Word boundaries (\b) ensure we don't accidentally replace 'iface_wan_old' when looking for 'iface_wan'
replacements = {
    r'\biface_wan\b': 'hardware.interfaces.wan.name',
    r'\biface_lan\b': 'hardware.interfaces.lan.name',
    r'\biface_lan_ip\b': 'network.lan.ip',
    r'\bdhcp_subnet\b': 'services.dhcp.subnet',
    r'\bdhcp_range_start\b': 'services.dhcp.range_start',
    r'\bdhcp_range_end\b': 'services.dhcp.range_end',
    r'\bdhcp_dns_server\b': 'services.dhcp.dns_server',
    r'\bdomain_local\b': 'network.lan.domain',
    r'\bstatic_leases\b': 'services.dhcp.static_leases'
}

for root, dirs, files in os.walk('ansible/roles'):
    for file in files:
        if file.endswith('.j2') or file.endswith('.yml'):
            path = os.path.join(root, file)
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements.items():
                new_content = re.sub(old, new, new_content)
            
            if new_content != content:
                # Safer: Overwrite only if changes were made
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Migrated variables in: {path}')

print("Migration complete.")
