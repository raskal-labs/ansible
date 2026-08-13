# INFRASTRUCTURE REFACTOR MASTER QUEUE

## Status Overview
* [x] Phase 1: Lockout Vectors & Safety Nets (COMPLETED)
* [x] Phase 2: Execution Blockers (COMPLETED)
* [x] Phase 3: Secrets & Detection (COMPLETED)
* [x] Phase 4: Data Model Cleanup (COMPLETED)

---

## PHASE 4: Data Model Cleanup (COMPLETED)
* [ ] **A4/A5/A6/B14 & N26:** Purge `.202` dead-ends, `vlan-32` data, and vestigial Avahi/firewall dependencies across all data models and roles.
* [ ] **DHCP-1:** Map user-provided MAC addresses to `data/nodes/` and define static DHCP leases in `data/network/`.
* [ ] **N5:** Fix `root_ca.crt` permissions and deploy to `ca-trust` so internal clients can use it.
* [ ] **A3:** Force roles to dynamically consume `templates:` block from data model.
* [x] **N22:** Remove hardcoded parameters from `ca.json.j2` and implement `step ca init` for proper CA reproducibility.
* [x] **N9:** Verify or fix Caddy `:80` block so it doesn't suppress automated HTTPS redirects.
