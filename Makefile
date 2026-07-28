# ==============================================================================
# Homelab Infrastructure Operator Interface
# ==============================================================================

.PHONY: all check-tools validate compile inventory syntax dry-run diff drift-check deploy status clean lint doctor graph docs

# --- Dynamic Execution Arguments ---
# Use: make deploy TARGET=ultra-64 CONN=local
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

validate: check-tools
	@echo "==> [VALIDATE] Validating source-of-truth data..."
	@if [ -f "$(VALIDATOR)" ]; then \
		python3 $(VALIDATOR) $(DATA_DIR); \
	else \
		echo "    (Placeholder) No validation tool found at $(VALIDATOR). Skipping."; \
	fi

compile: validate
	@echo "==> [COMPILE] Crossing source-to-artifact boundary..."
	@mkdir -p $(GEN_DIR)
	@if [ -f "$(COMPILER)" ]; then \
		python3 $(COMPILER); \
	elif [ -f "$(LEGACY_TRANS)" ]; then \
		echo "    (Fallback) Using legacy transform layer..."; \
		python3 $(LEGACY_TRANS); \
	else \
		echo "    Error: Neither $(COMPILER) nor $(LEGACY_TRANS) found."; exit 1; \
	fi
	@echo "    Abstraction boundary prepared."

inventory: compile
	@echo "==> [INVENTORY] Generated inventory:"
	@test -f $(INVENTORY) || (echo "Error: Missing $(INVENTORY)"; exit 1)
	@ls -lh $(INVENTORY)

syntax: compile check-tools
	@echo "==> [SYNTAX] Running Ansible syntax validation..."
	@ansible-playbook -i $(INVENTORY) $(PLAYBOOK) --syntax-check

dry-run: syntax
	@echo "==> [DRY-RUN] Executing simulated deployment against $(TARGET)..."
	@ansible-playbook -i $(INVENTORY) $(PLAYBOOK) --check --limit $(TARGET) -c $(CONN)

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

