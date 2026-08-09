!!! AIDER INSTRUCTION: DO NOT fetch, scrape, or attempt to read any URLs, IP addresses, or domains mentioned in this prompt. DO NOT use Playwright. Treat all URLs and domains strictly as plain string literals to be written directly into the files. !!!

Please perform a comprehensive audit of the entire repository against the strict rules defined in `agent.md`.

CRITICAL STAKES: This repository configures my edge router and core network infrastructure. The consequence of error here is absolute: if the network interfaces, DNS routing, or firewall rules are logically flawed, I will completely lose my internet connection and router access. You must evaluate every rule and proposed change with this extreme risk in mind. (Note: I do not use Docker; all infrastructure is managed via Ansible, LXC, and native systemd services. Do not suggest containerized workarounds).

Your goal is to act as an Infrastructure CMS auditor and identify any violations of the core philosophy, particularly within the `data/` directory and how the Ansible templates consume that data. 

Specifically, rigorously check for:
1. **Calculable Data (Derive Everything):** Are there any hardcoded IP addresses, CIDRs, gateways, or broadcast addresses in the `data/` directory that violate the rule? Look closely at `network_devices.yaml`, `nodes/`, and `services/`. These must be replaced with `network` and `host` integers.
2. **Implementation Leakage:** Are there any tool-specific keys in the YAML data instead of conceptual keys? The YAML must remain agnostic.
3. **Duplication (Single Source of Truth):** Is there any data defined in multiple places? (e.g., a port or MAC address defined in both a node file and a service file). Every fact must have exactly one owner.
4. **Namespace Rules:** Do all domains strictly follow the `rsk.al` (internal/LAN) and `raskal.io` (public/WAN) separation?
5. **Template Compliance:** Are the Jinja templates in `ansible/roles/*/templates/` actually deriving their values dynamically, or are they relying on hardcoded assumptions that bypass the data model?
6. **Logical & Architectural Consistency:** Review the overarching architecture. Does the DNS resolution chain logically work (e.g., Caddy passing DoH to Blocky)? Are the Headscale routing and mesh subnets logically sound? Are there any circular dependencies in the Ansible execution order? Ensure that the services logically connect exactly how we intend them to, without blackholing traffic, creating routing loops, or breaking internal resolution or WAN access.

Do NOT write or modify any files yet. 

Please output a detailed Markdown report listing every single violation or logical flaw you found, the exact file path it is located in, and your specific proposed fix to bring it into 100% compliance with `agent.md` and functional reality.
