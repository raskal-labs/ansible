.PHONY: bootstrap

bootstrap:
	git config core.hooksPath .githooks
	pip3 install -r transforms/requirements.txt
