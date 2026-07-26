.PHONY: bootstrap

bootstrap:
	git config core.hooksPath .githooks
	python3 -m venv .venv
	.venv/bin/pip install -r transforms/requirements.txt
