# ==============================================================================
# Homelab Infrastructure Operator Interface
# ==============================================================================

.PHONY: all check-tools validate compile inventory syntax dry-run diff drift-check deploy status clean lint doctor graph docs

# --- Dynamic Execution Arguments ---
# Use: make deploy TARGET=ultra64 CONN=local
TARGET       ?= all
CONN         ?= smart

# --- Variables & Paths ---
DATA_DIR     := data
GEN_DIR      := generated
TOOLS_DIR    := tools
ANSIBLE_DIR  := ansible

ANSIBLE_CONFIG := $(ANSIBLE_DIR)/ansible.cfg
export ANSIBLE_CONFIG

INVENTORY    := $(GEN_DIR)/inventory.yaml
PLAYBOOK     := $(ANSIBLE_DIR)/playbooks/site.yml
COMPILER     := $(TOOLS_DIR)/compile.py
LEGACY_TRANS := $(ANSIBLE_DIR)/inventory/transform.py
VALIDATOR    := $(TOOLS_DIR)/validate_yaml.py

# Default target
all: dry-run

# ==============================================================================
# Core Pipeline Targets
# ==============================================================================

check-tools:
	@command -v python3 >/dev/null || \
		(echo "Error: Missing python3"; exit 1)
	@command -v ansible-playbook >/dev/null || \
		(echo "Error: Missing ansible-playbook"; exit 1)

validate:
	@python3 ansible/tools/validate_yaml.py

compile: validate
ifndef SKIP_COMPILE
	@python3 compile.py
else
	@echo "==> [SKIP] Skipping compilation step (using existing generated/inventory.yaml)"
endif

dry-run: compile
	@ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i generated/inventory.yaml ansible/playbooks/site.yml --check

apply: compile
	@ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i generated/inventory.yaml ansible/playbooks/site.yml

snapshot:
	@cp generated/inventory.yaml generated/inventory.bak
	@echo "==> Saved snapshot to generated/inventory.bak"

restore-apply:
	@cp generated/inventory.bak generated/inventory.yaml
	@echo "==> Restored generated/inventory.bak"
	@ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i generated/inventory.yaml ansible/playbooks/site.yml

inventory: compile
	@echo "==> [INVENTORY] Generated inventory:"
	@test -f $(INVENTORY) || (echo "Error: Missing $(INVENTORY)"; exit 1)
	@ls -lh $(INVENTORY)

syntax: compile check-tools
	@echo "==> [SYNTAX] Running Ansible syntax validation..."
	@ansible-playbook -i $(INVENTORY) $(PLAYBOOK) --syntax-check

diff: syntax
	@echo "==> [DIFF] Executing simulated deployment with visual diffs against $(TARGET)..."
	@ansible-playbook -i $(INVENTORY) $(PLAYBOOK) --check --diff --limit $(TARGET) -c $(CONN)

drift-check: syntax
	@echo "==> [DRIFT] Scanning for configuration drift on $(TARGET)..."
	@ansible-playbook -i $(INVENTORY) $(PLAYBOOK) --check --limit $(TARGET) -c $(CONN) > /tmp/ansible-drift-$(TARGET).log
	@if grep -q 'changed=[1-9]' /tmp/ansible-drift-$(TARGET).log; then \
		echo "    CRITICAL: Configuration drift detected! Manual changes found."; \
		echo "    Run 'make diff TARGET=$(TARGET) CONN=$(CONN)' to view changes."; \
		exit 1; \
	else \
		echo "    OK: No drift detected. Infrastructure matches Source of Truth."; \
	fi

deploy: syntax
	@echo "==> [DEPLOY] Executing live infrastructure deployment against $(TARGET)..."
	@ansible-playbook -i $(INVENTORY) $(PLAYBOOK) --limit $(TARGET) -c $(CONN)

# ==============================================================================
# Utility & State Targets
# ==============================================================================

status:
	@echo "==> [STATUS] Git Repository State:"
	@git status -s
	@echo ""
	@echo "==> [STATUS] Generated Artifacts ($(GEN_DIR)):"
	@ls -la $(GEN_DIR) 2>/dev/null || echo "    No generated artifacts present."

clean:
	@echo "==> [CLEAN] Removing disposable build artifacts..."
	@rm -rf $(GEN_DIR)
	@echo "    Cleaned $(GEN_DIR)."

# ==============================================================================
# Future-Ready Placeholders
# ==============================================================================

lint:
	@echo "==> [LINT] (Future) Run YAML, Python, and Jinja formatting checks."

doctor:
	@echo "==> [DOCTOR] (Future) Running system health checks (tools, schemas, IPs, Ansible config)."

graph: compile
	@echo "==> [GRAPH] (Future) Generating infrastructure diagrams from source data."

docs: compile
	@echo "==> [DOCS] (Future) Auto-generating documentation from source data."

