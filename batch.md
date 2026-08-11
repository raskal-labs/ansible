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
