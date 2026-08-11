# HANDOFF.md

## Goal
Remediate critical deployment flaws (Phase 2 complete, entering Phase 3).

## Current State
Phase 2 batches executed:
- Packages decoupled (compile.py excludes third-party packages).
- step-ca lifecycle fixed (directories/certs created before config).
- Caddyfile issuer block syntax corrected.
- CrowdSec bouncer fixed (nftables mode, correct blacklist set).
- Blocky pinned to version v0.24 and download task uses curl.
- Unbound chroot explicitly disabled (empty string).
- Headscale schema migrated to 0.23+ (`prefixes.v4`, `policy.path`, `dns`, `database.sqlite.path`).
- Headscale listen_addr moved to 127.0.0.1:8085 to resolve CrowdSec LAPI collision.
- Headscale ACLs deployed via template task before service start.

## Decisions Made
- compile.py aggregation now respects explicit exclusion list (headscale, step-ca, step-cli, crowdsec, crowdsec-firewall-bouncer-nftables).
- step-ca deployment order enforces idempotent certificate/key presence before config generation.
- Caddy ACME issuer uses `tls` directive inside named profile, avoiding invalid syntax.
- step-ca password path set to `/etc/step-ca/password` to match systemd ExecStart defaults.
- CrowdSec bouncer `blacklists_ipv4` binds to standard `crowdsec-blacklists` nftables set.
- Blocky downloaded with curl and explicit version pin; `check_mode: false` removed.
- Unbound `chroot` is an explicit empty string to prevent default chroot behavior.
- Headscale configuration follows current stable schema; listen port isolated to avoid LAPI collision.
- ACL template deploy ensures repeatable, auditable policy before service start.

## Open Questions & Blockers
### Phase 3 items
- Move `step-ca` off `0.0.0.0` to avoid WAN exposure.
- Migrate CrowdSec acquisition to `journalctl`.
- Implement Caddy JSON access logs and map them to `http-cve` CrowdSec collection.
- Secure world-readable bouncer secrets (0600 permissions).
- Auth-gate WAN vhosts (Proxmox and other internal services).
- Mask WireGuard and Cloudflare secrets from Ansible diff output.
- Import SSH role for proper host-key verification and authorized_keys deployment.

### Phase 4 items
- Purge phantom hosts and enforce referential integrity.
- Remove dead `vlan-32` data and vestigial Avahi/firewall dependencies.
- Remove hardcoded parameters from `ca.json.j2` and implement reproducible `step ca init`.
- Verify Caddy `:80 { respond }` block does not suppress HTTPS redirects.
- Deploy `root_ca.crt` to `ca-trust` on all hosts so internal clients can use it.

## Resume Directive
Begin Phase 3 execution. Follow the existing refactor plan and the structured role infrastructure. Start with the task: “Move step-ca off 0.0.0.0”. Apply changes incrementally and dry-run with Ansible before committing.
