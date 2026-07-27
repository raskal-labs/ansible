.PHONY: help run dry-run syntax inventory

HOST ?= ultra-64
ACTION ?= provision

help:
	@echo "Raskal Labs Infrastructure Architecture"
	@echo "---------------------------------------"
	@echo "make run [ACTION=name] [HOST=name]  - Execute playbook (default: provision-ultra-64)"
	@echo "make dry-run [ACTION=..] [HOST=..]  - Simulate run and show config diffs"
	@echo "make syntax [ACTION=..] [HOST=..]   - Validate playbook syntax"
	@echo "make inventory                      - Print the compiled JSON inventory"

run:
	@echo "==> Executing $(ACTION) on $(HOST)..."
	ansible-playbook -i $(CURDIR)/ansible/inventory/transform.py -e "repo_root=$(CURDIR)" -c local $(CURDIR)/ansible/$(ACTION)-$(HOST).yml

dry-run:
	@echo "==> Dry-run for $(ACTION) on $(HOST)..."
	ansible-playbook -i $(CURDIR)/ansible/inventory/transform.py -e "repo_root=$(CURDIR)" -c local $(CURDIR)/ansible/$(ACTION)-$(HOST).yml --check --diff

syntax:
	@echo "==> Checking syntax for $(ACTION)-$(HOST).yml..."
	ansible-playbook -i $(CURDIR)/ansible/inventory/transform.py -e "repo_root=$(CURDIR)" $(CURDIR)/ansible/$(ACTION)-$(HOST).yml --syntax-check

inventory:
	@echo "==> Transforming YAML data to Ansible JSON inventory..."
	$(CURDIR)/ansible/inventory/transform.py --list
