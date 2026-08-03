🚀 Master Handover Plan & Execution Specification (v5)
Project: Sovereignty / Master Hand (Tier 1 Edge Router Migration)
Target Host: ultra64 (HP T730, AMD RX-427BB, XFS Filesystem, Fedora Server Minimal)
Orchestration Host: gamecube (Proxmox/Debian execution environment)
Document Purpose: Complete specification and context package to be provided directly to an AI coding agent (e.g., Aider, Roo Code) for declarative Ansible and YAML generation.
I. Project Scope & Target Environment
The goal of this project is to transform ultra64 into a bare-metal, single-binary, zero-trust edge router. All core networking, DNS, reverse proxying, VPN mesh, and security services must run natively on the host OS without containerization overhead, managed strictly via Ansible.
Identity services (Authelia and LLDAP) reside on Tier 2 infrastructure (gamecube). The edge router's reverse proxy (ultra64) acts as an access gateway, forwarding authorization queries to Authelia on gamecube via forward_auth.
II. The Seven Architectural Charters (Non-Negotiable)
1. The YAML Source-of-Truth (SoT) Charter
YAML files in data/ define all facts. Ansible tasks and Jinja templates must remain purely stateless translation mechanisms. Never hardcode facts, subnets, or intermediate variables inside Ansible roles.
2. The Bare-Metal Systemd Sandboxing Charter
No Docker, Podman, or LXC containers are permitted on ultra64. Every service must be deployed as a compiled Go/Rust binary managed by a hardened systemd service unit utilizing strict kernel-level sandboxing.
3. The Passive SSH & Isolation Charter
gamecube is the orchestration client; ultra64 is the managed node.
 * Ansible must never modify system files (like ~/.ssh/config) directly on gamecube.
 * Passive SSH artifacts must be generated locally inside ansible/generated/.
4. The Zero-Guesswork Charter (>95% Certainty Rule)
The coding agent is strictly forbidden from assuming or inventing missing system variables, network interfaces, IP ranges, or file paths.
 * If a variable cannot be deduced from the repository's YAML schema with greater than 95% certainty, the agent MUST NOT guess standard Linux defaults.
 * The agent MUST insert the marker string FIXME_AI: <Description missing of variable> directly into the code and explicitly request clarification from the user.
5. The Atomic, Idempotent, & Global Data Charter
 * Global YAML API: The data/ directory is a universal, platform-agnostic source of truth for the entire homelab, built for any present or future service to consume. YAML keys must avoid Ansible-specific jargon (e.g., use ip_address, not ansible_host).
 * Atomic Modularity: Ansible roles must be broken down into small, composable task files (e.g., install.yml, config.yml, service.yml included within main.yml) rather than monolithic scripts.
 * Strict Idempotency: Every Ansible task must be strictly idempotent.
6. The Anti-Hardcoding Mandate
Hardcoded paths, service names, instance counts, ports, and IP addresses are strictly banned in Ansible tasks and Jinja templates unless absolutely unavoidable (e.g., a universal Linux standard like /etc/resolv.conf). If a value can theoretically change, it must be parameterized as a variable.
7. The Compiler Contract
The Python script compile.py is the strict bridge between the agnostic data/ schema and Ansible.
 * It must be written using only standard Python libraries (e.g., PyYAML, os, sys). No complex virtual environments or third-party bloat.
 * Its sole job is to parse data/, map agnostic keys to Ansible variables, and write ansible/generated/inventory.yaml, ssh_config, and known_hosts.
III. Pre-Flight Cleanup Checklist (ultra64)
Before executing Ansible deployments against ultra64, perform these steps manually to avoid DNS lockouts and port collisions:
# 1. Temporarily override DNS to ensure internet access during binary downloads
sudo rm -f /etc/resolv.conf
echo "nameserver 1.1.1.1" | sudo tee /etc/resolv.conf

# 2. Stop, disable, and purge legacy DNS packages (frees Port 53)
sudo systemctl stop unbound dnscrypt-proxy
sudo systemctl disable unbound dnscrypt-proxy
sudo dnf remove -y unbound dnscrypt-proxy

# 3. Clean up obsolete repository roles (in your git working directory)
rm -rf ansible/roles/{unbound,dnscrypt-proxy,adguard,netbird,authelia,lldap,step-ca}

IV. Repository File Tree Schema (Atomic Structure)
infrastructure/
├── Makefile                      # Targets: diff, check, apply, compile
├── compile.py                    # Compiles data/ into ansible/generated/ artifacts
│
├── data/                         # UNIVERSAL SOURCE OF TRUTH (Agnostic schemas)
│   ├── environment.yaml          # Global variables (timezone, domains, org name)
│   ├── users.yaml                # Agnostic user identities and public SSH keys
│   ├── nodes/
│   │   └── ultra64.yaml          # Hardware specs, assigned roles, public host keys
│   └── services/
│       ├── dns.yaml              # Local records, blocklists, upstream resolvers
│       ├── ingress.yaml          # Universal routing logic, bypass rules, backends
│       └── identity.yaml         # OIDC and Authelia client mapping definitions
│
├── ansible/                      # STATELESS EXECUTION ENGINE
│   ├── site.yml                  # Main playbook; dictates strict execution order
│   ├── group_vars/all/vault.yml  # Vaulted secrets (API keys, private keys)
│   ├── generated/                # (Ignored by Git) Output of compile.py
│   │
│   └── roles/                    # Atomic, Systemd-sandboxed executors
│       ├── caddy/
│       │   ├── tasks/
│       │   │   ├── main.yml      # Includes the sub-tasks
│       │   │   ├── install.yml   # Binary download and SELinux contexts
│       │   │   ├── config.yml    # Renders Caddyfile with validation checks
│       │   │   └── service.yml   # Deploys systemd unit and manages state
│       │   └── templates/
│       │       ├── caddy.service.j2
│       │       └── Caddyfile.j2
│       └── blocky/               # (Follows same atomic task structure)

V. Phased Implementation Roadmap
Phase 1: Core System & Network Bedrock
 * Time Synchronization: Configure chrony to prevent time drift.
 * DNS Resolution Prep: Disable and stop systemd-resolved.
 * SSH Hardening: Template /etc/ssh/sshd_config. Inject keys into ~/.ssh/authorized_keys.
 * Dynamic DNS: Deploy ddns-go as a sandboxed systemd service.
Phase 2: Ingress Gateway (Caddy)
 * Service Deployment: Deploy Caddy binary with SELinux contexts (bin_t) and httpd_can_network_connect=true.
 * Authentication Flow: Caddy forwards authorization checks to Authelia on gamecube via forward_auth.
 * Pre-Flight Verification: Execute validate: {{ bin_dir }}/caddy validate --config %s.
Phase 3: Core Network Services & Mesh
 * Blocky DNS: Deploy blocky using DoT upstreams and local domain mappings.
 * Headscale Control Plane: Deploy Headscale with Restart=always and RestartSec=10s.
Phase 4: Security & Disaster Recovery
 * CrowdSec & nftables: Deploy CrowdSec bouncer to an isolated nftables table (table inet crowdsec).
 * XFS State Backups: Deploy restic as a systemd timer (running as root or CAP_DAC_READ_SEARCH).
VI. Hardening, Systemd, & SELinux Standards
Standard Systemd Sandbox Unit Template
[Unit]
Description={{ service_name }} Service
After=network.target network-online.target
Requires=network-online.target

[Service]
Type=exec
User={{ service_name }}
Group={{ service_name }}
ExecStart={{ bin_dir }}/{{ service_name }} --config {{ config_dir }}/config.yaml

# XFS System Sandboxing
ProtectSystem=strict
PrivateTmp=yes
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
NoNewPrivileges=yes

StateDirectory={{ service_name }}
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
LimitNOFILE={{ systemd_limit_nofile }}
LimitNPROC={{ systemd_limit_nproc }}

[Install]
WantedBy=multi-user.target

Mandatory SELinux Handling in Ansible
- name: Set SELinux file context for binary
  community.general.sefcontext:
    target: '{{ bin_dir }}/{{ binary_name }}'
    setype: bin_t
    state: present

- name: Restore SELinux context
  ansible.builtin.command: restorecon -v {{ bin_dir }}/{{ binary_name }}
  register: restorecon_out
  changed_when: restorecon_out.stdout != ""

VII. Ansible Best Practices & Anti-Patterns (For Coding Agents)
 * Native Modules Over Shell: The use of ansible.builtin.shell or ansible.builtin.command is banned unless a native module truly does not exist. If used, it MUST include creates:, removes:, or changed_when: to guarantee idempotency.
 * Explicit File Permissions: Every task creating a file or directory MUST explicitly define owner, group, and mode (e.g., mode: '0644', mode: '0755').
 * Handler Flushing: If a service must be online before a subsequent role executes, use - name: Flush handlers with meta: flush_handlers mid-playbook.
 * Variable Flattening: Do not use complex set_fact chains. Pass raw data from the YAML schema directly into Jinja templates.
 * Idempotent Binary Downloads: When using get_url or unarchive, always use the checksum parameter or track the installed version to prevent redownloading.
VIII. AI Agent Execution Protocol
The AI coding agent must follow this exact loop for every change:
 * Run the Compiler (MANDATORY FIRST STEP): If you alter any YAML in data/, you must recompile the inventory before Ansible can see the changes.
   python3 compile.py

 * Linting & Syntax Validation:
   ansible-playbook -i ansible/generated/inventory.yaml ansible/site.yml --syntax-check

 * Dry-Run Inspections (Diff Check): Verify state changes without applying them.
   ansible-playbook -i ansible/generated/inventory.yaml ansible/site.yml --check --diff

 * Post-Deployment Verification:
   ssh -F ansible/generated/ssh_config ultra64 "systemctl status <service_name> --no-pager"
ssh -F ansible/generated/ssh_config ultra64 "journalctl -u <service_name> -n 30 --no-pager"


