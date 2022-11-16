.DEFAULT_GOAL := help
HAS_APK := $(shell command -v apk 2>/dev/null)
HAS_APT := $(shell command -v apt 2>/dev/null)

help: ## Shows help message.
	@printf "\033[1m%s\033[36m %s\033[0m \n\n" "Development environment for" "wienerlinien";
	@awk 'BEGIN {FS = ":.*##";} /^[a-zA-Z_-]+:.*?##/ { printf " \033[36m make %-25s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST);
	@echo

init: homeassistant-install requirements

requirements:
ifdef HAS_APK
	apk add libxml2-dev libxslt-dev
endif
ifdef HAS_APT
	sudo apt update && sudo apt install libxml2-dev libxslt-dev
endif
	python3 -m pip --disable-pip-version-check install -U setuptools wheel
	python3 -m pip --disable-pip-version-check install -r requirements.txt

start: ## Start the HA with the integration
	@bash .devcontainer/integration_start;

lint: ## Run linters
	pre-commit install-hooks --config .github/pre-commit-config.yaml;
	pre-commit run --hook-stage manual --all-files --config .github/pre-commit-config.yaml;

update: ## Pull master from custom-components/wienerlinien
	git pull upstream master;

homeassistant-install: ## Install the latest dev version of Home Assistant
	python3 -m pip --disable-pip-version-check install -U setuptools wheel
	python3 -m pip --disable-pip-version-check \
		install --upgrade git+https://github.com/home-assistant/home-assistant.git@dev;

homeassistant-update: homeassistant-install ## Alias for 'homeassistant-install'