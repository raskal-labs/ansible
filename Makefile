# =============================================================================
# Infrastructure CMS — Makefile
# =============================================================================
# Usage:
#   make compile                  Regenerate ansible/generated/inventory.yaml
#   make validate                 Validate data/ against agent.md rules
#   make dry-run                  Full dry-run (compile+validate+check+diff)
#   make deploy                   Full deploy to ultra64
#   make deploy HOST=<host>       Full deploy to a specific host
#   make deploy-role ROLE=<role>  Deploy a single role (e.g. firewall)
#   make deploy-tags TAGS=<tags>  Deploy by ansible tag (e.g. crowdsec)
#   make diff                     Show what would change (check+diff only)
#   make drift                    Detect configuration drift on HOST
#   make lint                     Run ansible-lint on site.yml
#   make known-hosts              Scan real SSH host keys from ultra64
#   make vault-edit               Open vault.yml for editing
#   make vault-rekey              Rekey the vault with a new password
#   make snapshot                 Save a snapshot of the current inventory
#   make restore                  Restore inventory from snapshot and deploy
#   make headscale-backup         Back up Headscale DB on ultra64
#   make headscale-nodes          List enrolled Headscale nodes
#   make headscale-key            Generate a new Headscale pre-auth key
#   make clean                    Remove all generated files (keeps .gitkeep)
#   make status                   Git status + last 5 commits
#   make help                     Show this help
# =============================================================================

SHELL := /bin/bash

# --- Paths ---
REPO_ROOT        := $(shell pwd)
INVENTORY        := ansible/generated/inventory.yaml
INVENTORY_BAK    := ansible/generated/inventory.bak
VAULT_PASS_FILE  := ansible/.vault_pass
VAULT_FILE       := ansible/group_vars/all/vault.yml
SITE_PLAYBOOK    := ansible/site.yml
DRY_RUN_PLAYBOOK := ansible/playbooks/dry-run.yml
COMPILE          := python3 compile.py
VALIDATE         := python3 tools/validate_yaml.py
ANSIBLE_CFG      := ansible/ansible.cfg

# --- Target host (override with: make deploy HOST=somehost) ---
HOST             := ultra64

# --- Router IP (ultra64 — also runs Headscale) ---
ROUTER_IP        := 10.64.0.1

# --- Headscale runs on ultra64 (the router) ---
HEADSCALE_HOST   := 10.64.0.1
HEADSCALE_USER   := raskal

export ANSIBLE_CONFIG := $(ANSIBLE_CFG)

ANSIBLE_FLAGS    := -i $(INVENTORY) --vault-password-file $(VAULT_PASS_FILE)

# =============================================================================
.PHONY: all compile validate dry-run deploy deploy-role deploy-tags \
        diff drift lint known-hosts vault-edit vault-rekey \
        snapshot restore headscale-backup headscale-nodes headscale-key \
        clean status help check-tools

all: help

# =============================================================================
# PREFLIGHT
# =============================================================================
check-tools:
	@command -v python3 >/dev/null 2>&1 || \
		(echo "ERROR: python3 not found"; exit 1)
	@command -v ansible-playbook >/dev/null 2>&1 || \
		(echo "ERROR: ansible-playbook not found"; exit 1)
	@test -f $(VAULT_PASS_FILE) || \
		(echo "ERROR: $(VAULT_PASS_FILE) not found — create it with your vault password"; exit 1)

# =============================================================================
# COMPILE
# =============================================================================
compile: check-tools
	@echo "==> [COMPILE] Regenerating inventory from data/..."
	@$(COMPILE)
	@echo "==> [COMPILE] Done. Output: $(INVENTORY)"

# =============================================================================
# VALIDATE
# =============================================================================
validate: check-tools
	@echo "==> [VALIDATE] Checking data/ against agent.md rules..."
	@$(VALIDATE)

# =============================================================================
# DRY RUN
# =============================================================================
dry-run: compile validate
	@echo "==> [DRY RUN] Running against $(HOST) — no changes will be made..."
	@ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook $(DRY_RUN_PLAYBOOK) \
		$(ANSIBLE_FLAGS) \
		--limit $(HOST) \
		--diff

# =============================================================================
# DIFF
# =============================================================================
diff: check-tools
	@echo "==> [DIFF] Showing pending changes on $(HOST)..."
	@ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook $(SITE_PLAYBOOK) \
		$(ANSIBLE_FLAGS) \
		--limit $(HOST) \
		--check --diff

# =============================================================================
# DRIFT
# =============================================================================
drift: compile validate
	@echo "==> [DRIFT] Scanning for configuration drift on $(HOST)..."
	@ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook $(SITE_PLAYBOOK) \
		$(ANSIBLE_FLAGS) \
		--limit $(HOST) \
		--check 2>&1 | tee /tmp/ansible-drift-$(HOST).log; \
	if grep -q 'changed=[1-9]' /tmp/ansible-drift-$(HOST).log; then \
		echo ""; \
		echo "==> [DRIFT] ALERT: Configuration drift detected on $(HOST)."; \
		echo "==> [DRIFT] Run 'make diff HOST=$(HOST)' to inspect changes."; \
		exit 1; \
	else \
		echo "==> [DRIFT] OK: No drift detected."; \
	fi

# =============================================================================
# DEPLOY
# =============================================================================
deploy: compile validate
	@echo "==> [DEPLOY] Deploying full infrastructure to $(HOST)..."
	@ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook $(SITE_PLAYBOOK) \
		$(ANSIBLE_FLAGS) \
		--limit $(HOST)

# =============================================================================
# DEPLOY ROLE
# =============================================================================
deploy-role: compile validate
ifndef ROLE
	$(error ROLE is not set. Usage: make deploy-role ROLE=firewall)
endif
	@echo "==> [DEPLOY] Deploying role '$(ROLE)' to $(HOST)..."
	@ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook $(SITE_PLAYBOOK) \
		$(ANSIBLE_FLAGS) \
		--limit $(HOST) \
		--tags $(ROLE)

# =============================================================================
# DEPLOY TAGS
# =============================================================================
deploy-tags: compile validate
ifndef TAGS
	$(error TAGS is not set. Usage: make deploy-tags TAGS=crowdsec)
endif
	@echo "==> [DEPLOY] Deploying tags '$(TAGS)' to $(HOST)..."
	@ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook $(SITE_PLAYBOOK) \
		$(ANSIBLE_FLAGS) \
		--limit $(HOST) \
		--tags $(TAGS)

# =============================================================================
# LINT
# =============================================================================
lint: check-tools
	@echo "==> [LINT] Running ansible-lint on $(SITE_PLAYBOOK)..."
	@ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-lint $(SITE_PLAYBOOK)

# =============================================================================
# KNOWN HOSTS
# =============================================================================
known-hosts:
	@echo "==> [KNOWN-HOSTS] Scanning SSH host keys from $(HOST) ($(ROUTER_IP))..."
	@echo "==> Paste the output below into data/nodes/ultra64.yaml under host_keys:"
	@echo ""
	@ssh-keyscan -t ed25519,rsa $(ROUTER_IP) 2>/dev/null | grep -v '^#' | \
		awk '{print "  " $$3 ": \"" $$2 "\""}'
	@echo ""
	@echo "==> After updating ultra64.yaml, run: make compile"

# =============================================================================
# VAULT
# =============================================================================
vault-edit:
	@echo "==> [VAULT] Opening $(VAULT_FILE) for editing..."
	@ansible-vault edit $(VAULT_FILE) --vault-password-file $(VAULT_PASS_FILE)

vault-rekey:
	@echo "==> [VAULT] Rekeying $(VAULT_FILE)..."
	@ansible-vault rekey $(VAULT_FILE) --vault-password-file $(VAULT_PASS_FILE)
	@echo "==> [VAULT] Done. Remember to update $(VAULT_PASS_FILE) with the new password."

# =============================================================================
# SNAPSHOT / RESTORE
# =============================================================================
snapshot:
	@echo "==> [SNAPSHOT] Saving inventory snapshot to $(INVENTORY_BAK)..."
	@cp $(INVENTORY) $(INVENTORY_BAK)
	@echo "==> [SNAPSHOT] Done."

restore: check-tools
	@test -f $(INVENTORY_BAK) || \
		(echo "ERROR: No snapshot found at $(INVENTORY_BAK). Run 'make snapshot' first."; exit 1)
	@echo "==> [RESTORE] Restoring inventory from snapshot..."
	@cp $(INVENTORY_BAK) $(INVENTORY)
	@echo "==> [RESTORE] Deploying from restored snapshot..."
	@ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook $(SITE_PLAYBOOK) \
		$(ANSIBLE_FLAGS) \
		--limit $(HOST)

# =============================================================================
# HEADSCALE OPERATIONS
# Headscale runs on ultra64 (the router, 10.64.0.1).
# =============================================================================
headscale-backup:
	@echo "==> [HEADSCALE] Backing up Headscale DB on ultra64 ($(HEADSCALE_HOST))..."
	@ssh root@$(HEADSCALE_HOST) \
		"mkdir -p /root/headscale-db-backups && \
		 cp /var/lib/headscale/db.sqlite \
		    /root/headscale-db-backups/db-\$$(date +%Y%m%d-%H%M%S).sqlite && \
		 ls -t /root/headscale-db-backups/db-*.sqlite | tail -n +31 | xargs rm -f 2>/dev/null; \
		 echo 'Backup complete. Current backups:'; \
		 ls -lh /root/headscale-db-backups/"
	@echo "==> [HEADSCALE] Done."

headscale-nodes:
	@echo "==> [HEADSCALE] Enrolled nodes:"
	@ssh root@$(HEADSCALE_HOST) "headscale nodes list"

headscale-key:
	@echo "==> [HEADSCALE] Generating reusable pre-auth key for user $(HEADSCALE_USER)..."
	@echo "==> Enroll a device with:"
	@echo "    tailscale up --login-server https://wfc.raskal.io --authkey <key>"
	@echo ""
	@ssh root@$(HEADSCALE_HOST) \
		"headscale preauthkeys create --user $(HEADSCALE_USER) --reusable --expiration 720h"

# =============================================================================
# CLEAN
# =============================================================================
clean:
	@echo "==> [CLEAN] Removing generated files..."
	@find ansible/generated -type f ! -name '.gitkeep' -delete
	@find generated -type f ! -name '.gitkeep' -delete 2>/dev/null || true
	@echo "==> [CLEAN] Done."

# =============================================================================
# STATUS
# =============================================================================
status:
	@echo "==> [STATUS] Git state:"
	@git status --short
	@echo ""
	@echo "==> [STATUS] Last 5 commits:"
	@git log --oneline -5
	@echo ""
	@echo "==> [STATUS] Generated artifacts:"
	@ls -lh ansible/generated/ 2>/dev/null || echo "  None."
	@echo ""
	@echo "==> [STATUS] Inventory age:"
	@test -f $(INVENTORY) && \
		echo "  $(INVENTORY) last modified: $$(date -r $(INVENTORY) '+%Y-%m-%d %H:%M:%S')" || \
		echo "  $(INVENTORY) does not exist — run: make compile"

# =============================================================================
# HELP
# =============================================================================
help:
	@echo ""
	@echo "  Infrastructure CMS — Makefile targets"
	@echo "  ======================================"
	@echo ""
	@echo "  Pipeline (enforced order: compile → validate → action):"
	@echo "    make dry-run                  Full dry-run, zero changes"
	@echo "    make deploy                   Full deploy to ultra64"
	@echo "    make deploy HOST=<host>       Full deploy to a specific host"
	@echo "    make deploy-role ROLE=<role>  Deploy one role  (e.g. firewall)"
	@echo "    make deploy-tags TAGS=<tags>  Deploy by tag    (e.g. crowdsec)"
	@echo ""
	@echo "  Inspection:"
	@echo "    make diff                     Show pending changes (no compile)"
	@echo "    make drift                    Detect config drift, exit 1 if found"
	@echo "    make lint                     Run ansible-lint"
	@echo "    make status                   Git status + inventory age"
	@echo ""
	@echo "  Data pipeline:"
	@echo "    make compile                  Regenerate inventory from data/"
	@echo "    make validate                 Validate data/ against agent.md"
	@echo ""
	@echo "  Vault:"
	@echo "    make vault-edit               Edit vault.yml"
	@echo "    make vault-rekey              Rekey vault with new password"
	@echo ""
	@echo "  Headscale (runs on ultra64 — the router):"
	@echo "    make headscale-backup         Back up Headscale DB on ultra64"
	@echo "    make headscale-nodes          List all enrolled nodes"
	@echo "    make headscale-key            Generate a new pre-auth key"
	@echo "      HEADSCALE_USER=<user>       Override user (default: raskal)"
	@echo ""
	@echo "  Utilities:"
	@echo "    make known-hosts              Scan + format SSH host keys"
	@echo "    make snapshot                 Save inventory snapshot"
	@echo "    make restore                  Restore snapshot and deploy"
	@echo "    make clean                    Remove all generated files"
	@echo ""
	@echo "  Critical pre-deploy checklist:"
	@echo "    1.  make known-hosts          Capture real SSH host keys"
	@echo "    2.  make vault-edit           Add vault_crowdsec_bouncer_api_key"
	@echo "    3.  make compile              Regenerate inventory"
	@echo "    4.  make validate             Confirm no agent.md violations"
	@echo "    5.  make dry-run              Verify all templates render"
	@echo "    6.  make deploy               Apply to router"
	@echo ""
	@echo "  Before any ultra64 OS-level maintenance:"
	@echo "    make headscale-backup         Always back up Headscale DB first"
	@echo ""
