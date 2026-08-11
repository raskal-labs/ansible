/add data/services/headscale.yaml ansible/roles/headscale/templates/headscale.yaml.j2 ansible/roles/headscale/tasks/main.yml HANDOFF.md batch-2.4.md

Please execute the final Phase 2 tasks exactly as specified in the batch-2.4.md document. Do not invent any other changes.

CRITICAL INSTRUCTION: Before making any changes, analyze the current contents of each file. If a requested modification is already present (e.g., the schema is already updated, or the task already exists), skip that specific modification.

1. In `data/services/headscale.yaml`:
   - Check if `database:` -> `sqlite:` -> `path:` already exists. If not, replace `db_path: /var/lib/headscale/db.sqlite` with this nested structure.

2. In `ansible/roles/headscale/templates/headscale.yaml.j2`:
   - Check if `prefixes:` -> `v4:` exists. If not, update `ip_prefixes:` to this format.
   - Check if `policy:` -> `path:` exists. If not, update `acls_policy_path:` to this format.
   - Check if the root key `dns:` exists. If `dns_config:` is still there, rename it to `dns:` (keep its existing nested children as they are).
   - Check the database path variable. If it is not `{{ infra_services.headscale.server.database.sqlite.path }}`, update it to that exact string.
   - Check `listen_addr`. If it is still `0.0.0.0:8080`, change it to `127.0.0.1:8085`.

3. In `ansible/roles/headscale/tasks/main.yml`:
   - Search for a task deploying `headscale-acls.yaml.j2`. 
   - If it does NOT exist, add a new `ansible.builtin.template` task to deploy `headscale-acls.yaml.j2` to `dest: /etc/headscale/acls.yaml`.
   - Set owner: `headscale`, group: `headscale`, mode: `'0640'`.
   - Place this new task IMMEDIATELY AFTER the "Deploy Headscale configuration" task.

4. Overwrite `HANDOFF.md` entirely with the following literal text (unless it already matches exactly):

# HANDOFF.md

## Goal
Remediate critical deployment flaws (Phase 2 complete, entering Phase 3).

## Current State
Phase 2 batches executed:
- Packages decoupled from global aggregation.
- step-ca lifecycle and directory dependencies fixed.
- Caddyfile ACME issuer block syntax corrected.
- CrowdSec bouncer fixed (nftables mode, correct blacklist set).
- DNS: Blocky pinned to v0.24, Unbound chroot explicitly disabled.
- Headscale: Schema migrated to 0.23+ (nested database, prefixes, policy, dns).
- Headscale: listen_addr moved to 127.0.0.1:8085 to resolve CrowdSec LAPI collision.
- Headscale: ACLs actively deployed via template task.

## Decisions Made
- Architectural choices and routing logic locked in during Phase 2.

## Open Questions & Blockers
- Phase 3: Move step-ca off 0.0.0.0, implement journalctl acquisition for CrowdSec, deploy Caddy JSON access logs, secure world-readable bouncer secrets, auth-gate WAN vhosts, mask secrets from diffs, and deploy SSH keys.
- Phase 4: Purge phantom hosts, clean up dead vlan-32 data, and fix ca.json hardcoding.

## Resume Directive
Phase 2 is complete. Begin Phase 3 execution based on the master refactor plan.

---
Once complete, run `make compile` and `make dry-run` to verify the changes. Do not commit until both pass.
