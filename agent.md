SYSTEM INSTRUCTIONS: INFRASTRUCTURE CMS & YAML SOURCE-OF-TRUTH
1. CORE PHILOSOPHY
YAML is the Source of Truth (SoT): It models real-world infrastructure (concepts), not the implementation (tools).
Ansible/Jinja are Renderers: They adapt to the YAML. Do not shape YAML to make Ansible's job easier.
Treat as a CMS: You are building an Infrastructure CMS. Ansible is just one consumer of this data.
2. STRICT DATA RULES
Zero Implementation Leakage: Name keys by concept (wan_mac), never by tool (networkmanager_mac). YAML must remain hypervisor and OS-agnostic.
Derive Everything: Never store calculable data. Store network: 64 and host: 10. Do NOT store the IP, gateway, CIDR, or broadcast. Let generators/Jinja calculate them.
Single Source / No Duplication: Every fact has exactly one owner.
Network owns: subnets, vlans, dhcp policy, zones.
Node owns: hostname, hardware, mac, host ID.
Service owns: ports, domains.
Composition over Inheritance: Link objects via flat references. Avoid deep nested YAML trees.
Passive Metadata: Flavor metadata (e.g., Nintendo themes, codenames) is for naming/docs only. It does not dictate routing or network behavior.
3. NAMESPACES & PIPELINES
Strict DNS Separation:
Identity: hostname.rsk.al
Internal Alias: app.rsk.al
External/Public: app.raskal.io
Approved Pipeline: YAML \rightarrow Inventory Generator \rightarrow Ansible \rightarrow Jinja \rightarrow Service Config.
Forbidden: Do not invent intermediate schemas, parallel inventories, or hidden compiler rules.
4. AIDER QA CHECKLIST (Before writing code, ask:)
Does this introduce duplication?
Can this value be mathematically derived instead of stored?
Is tool-specific logic leaking into the YAML data model?
