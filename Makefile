.PHONY: bootstrap

bootstrap:
	git config core.hooksPath .githooks
	./setup_venv.sh
