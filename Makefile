.DEFAULT_GOAL := help

ANSIBLE_PLAYBOOK := ansible-playbook
PLAYBOOK_DIR := playbooks
VAULT_ARGS :=

# Detect best python/pip — prefer latest, fall back through versions
PYTHON := $(shell for py in python3.14 python3.13 python3.12 python3.11 python3; do \
  command -v $$py >/dev/null 2>&1 && echo $$py && break; done)
PIP := $(shell command -v pip3 >/dev/null 2>&1 && echo pip3 || echo pip)

PYTEST_PYTHON := $(shell for py in $(PYTHON) python3.14 python3.13 python3.12 python3.11 python3; do \
  command -v $$py >/dev/null 2>&1 && $$py -m pytest --version >/dev/null 2>&1 && echo $$py && break; done)

# Optional per-target overrides
CLUSTER ?=
ENV ?= mas-world-2026
SCENARIO ?=
INSTANCE_TYPE ?=

# ═══════════════════════════════════════════════════════════════════════
# Help
# ═══════════════════════════════════════════════════════════════════════

.PHONY: help
help: ## Show this help
	@echo ""
	@echo "  MAS World 2026 — Workshop Automation"
	@echo "  ═════════════════════════════════════"
	@echo ""
	@echo "  Setup:"
	@grep -E '^[a-zA-Z_-]+:.*?## \[setup\]' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## \\[setup\\] "}; {printf "    \033[36m%-28s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Phase 1 — Infrastructure:"
	@grep -E '^[a-zA-Z_-]+:.*?## \[infra\]' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## \\[infra\\] "}; {printf "    \033[36m%-28s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Phase 2 — Application (MAS World):"
	@grep -E '^[a-zA-Z_-]+:.*?## \[mas\]' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## \\[mas\\] "}; {printf "    \033[36m%-28s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Deployment Scenarios:"
	@grep -E '^[a-zA-Z_-]+:.*?## \[deploy\]' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## \\[deploy\\] "}; {printf "    \033[36m%-28s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  End-to-End:"
	@grep -E '^[a-zA-Z_-]+:.*?## \[e2e\]' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## \\[e2e\\] "}; {printf "    \033[36m%-28s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Quality:"
	@grep -E '^[a-zA-Z_-]+:.*?## \[quality\]' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## \\[quality\\] "}; {printf "    \033[36m%-28s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ═══════════════════════════════════════════════════════════════════════
# Setup
# ═══════════════════════════════════════════════════════════════════════

.PHONY: setup
setup: ## [setup] Install all dependencies (Python, Galaxy collections, pre-commit)
	$(PIP) install -e ".[dev]" || $(PYTHON) -m pip install -e ".[dev]"
	ansible-galaxy install -r requirements.yml --force
	@if git rev-parse --git-dir >/dev/null 2>&1; then pre-commit install; else echo "Skipping pre-commit install (not a git repository)"; fi

# ═══════════════════════════════════════════════════════════════════════
# Phase 1 — Infrastructure
# ═══════════════════════════════════════════════════════════════════════

.PHONY: preflight validate setup-infra verify-infra provision status deploy-infra destroy destroy-auto destroy-infra destroy-infra-auto

preflight: ## [infra] Run preflight checks (CLI tools, credentials, AWS, ROSA)
	@PROJECT_ROOT=$(CURDIR) bash scripts/preflight.sh $(MODE)

validate: ## [infra] Run Ansible preflight playbook
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/preflight.yml $(VAULT_ARGS)

setup-infra: ## [infra] Create AWS VPCs, subnets, NAT gateways, enroll ROSA accounts
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/setup-infra.yml $(VAULT_ARGS)

verify-infra: ## [infra] Verify AWS infrastructure exists for all accounts
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/setup-infra.yml $(VAULT_ARGS) -e infra_action=verify --skip-tags all --tags verify

provision: ## [infra] Provision all ROSA HCP clusters
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/provision.yml $(VAULT_ARGS)

status: ## [infra] Check status of all clusters
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/status.yml $(VAULT_ARGS)

deploy-infra: ## [infra] Full Phase 1: preflight -> infra -> clusters
	@echo ""
	@echo "  ╔══════════════════════════════════════════════════════════╗"
	@echo "  ║  Phase 1 — Infrastructure Deployment                   ║"
	@echo "  ╚══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "=== Step 1/3: Preflight Checks ==="
	@PROJECT_ROOT=$(CURDIR) bash scripts/preflight.sh all
	@echo ""
	@echo "=== Step 2/3: AWS Infrastructure ==="
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/setup-infra.yml $(VAULT_ARGS)
	@echo ""
	@echo "=== Step 3/3: ROSA HCP Cluster Provisioning ==="
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/provision.yml $(VAULT_ARGS)
	@echo ""
	@echo "  Phase 1 complete — infrastructure deployed."

destroy: ## [infra] Destroy all ROSA HCP clusters (interactive confirmation)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/destroy.yml $(VAULT_ARGS)

destroy-auto: ## [infra] Destroy all clusters without confirmation prompt
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/destroy.yml $(VAULT_ARGS) -e auto_confirm=true

destroy-infra: ## [infra] Destroy AWS infrastructure (interactive confirmation)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/destroy-infra.yml $(VAULT_ARGS)

destroy-infra-auto: ## [infra] Destroy AWS infrastructure without confirmation
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/destroy-infra.yml $(VAULT_ARGS) -e auto_confirm=true

# ═══════════════════════════════════════════════════════════════════════
# Phase 2 — Application (MAS World)
# ═══════════════════════════════════════════════════════════════════════

.PHONY: mas-prepare-cluster mas-prepare-fleet mas-validate-cluster mas-validate-fleet mas-repair-cluster mas-create-students mas-rotate-credentials mas-reset-exercises mas-decommission

mas-prepare-cluster: ## [mas] Prepare a single cluster (CLUSTER=seat-01)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/prepare-cluster.yml $(VAULT_ARGS) -e cluster_id=$(CLUSTER)

mas-prepare-fleet: ## [mas] Prepare entire fleet (all clusters)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/prepare-fleet.yml $(VAULT_ARGS)

mas-validate-cluster: ## [mas] Validate a single cluster (CLUSTER=seat-01)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/validate-cluster.yml $(VAULT_ARGS) -e cluster_id=$(CLUSTER)

mas-validate-fleet: ## [mas] Validate entire fleet readiness
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/validate-fleet.yml $(VAULT_ARGS)

mas-repair-cluster: ## [mas] Repair a failed cluster (CLUSTER=seat-01)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/repair-cluster.yml $(VAULT_ARGS) -e cluster_id=$(CLUSTER)

mas-create-students: ## [mas] Create student accounts on all clusters
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/prepare-fleet.yml $(VAULT_ARGS) --tags students

mas-rotate-credentials: ## [mas] Rotate student passwords
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/rotate-credentials.yml $(VAULT_ARGS)

mas-reset-exercises: ## [mas] Reset lab exercises to clean state
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/reset-exercises.yml $(VAULT_ARGS)

mas-decommission: ## [mas] Decommission workshop (remove MAS, cleanup)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/decommission-workshop.yml $(VAULT_ARGS)

.PHONY: deploy-mas

deploy-mas: ## [mas] Full Phase 2: prepare fleet -> validate fleet
	@echo ""
	@echo "  ╔══════════════════════════════════════════════════════════╗"
	@echo "  ║  Phase 2 — Application Deployment (MAS World)          ║"
	@echo "  ╚══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "=== Step 1/2: Fleet Preparation (MAS + Components) ==="
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/prepare-fleet.yml $(VAULT_ARGS)
	@echo ""
	@echo "=== Step 2/2: Fleet Validation ==="
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/validate-fleet.yml $(VAULT_ARGS)
	@echo ""
	@echo "  Phase 2 complete — application deployed."

# ═══════════════════════════════════════════════════════════════════════
# Deployment Scenarios
# ═══════════════════════════════════════════════════════════════════════

.PHONY: wizard deploy deploy-greenfield deploy-aws-ready deploy-cluster-ready validate-greenfield validate-aws-ready validate-cluster-ready

wizard: ## [deploy] Interactive deployment wizard (guided scenario selection + validation)
	@bash scripts/deploy-wizard.sh

deploy: ## [deploy] Deploy by scenario (SCENARIO=greenfield|aws-ready|cluster-ready)
	@if [ -z "$(SCENARIO)" ]; then \
		echo ""; \
		echo "  Usage: make deploy SCENARIO=<scenario>"; \
		echo ""; \
		echo "  Available scenarios:"; \
		echo "    greenfield     Fresh AWS accounts — build everything"; \
		echo "    aws-ready      AWS infra exists — provision ROSA + app"; \
		echo "    cluster-ready  Clusters running — add autoscaler + app"; \
		echo ""; \
		echo "  Examples:"; \
		echo "    make deploy SCENARIO=greenfield"; \
		echo "    make deploy SCENARIO=aws-ready"; \
		echo "    make deploy-cluster-ready INSTANCE_TYPE=m5.2xlarge"; \
		echo ""; \
		exit 1; \
	fi
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/deploy.yml $(VAULT_ARGS) \
		-e deployment_scenario=$(SCENARIO) \
		$(if $(INSTANCE_TYPE),-e workshop_machinepool_instance_type=$(INSTANCE_TYPE))

deploy-greenfield: ## [deploy] Scenario 1: Fresh AWS accounts — full build
	@$(MAKE) deploy SCENARIO=greenfield

deploy-aws-ready: ## [deploy] Scenario 2: AWS infra exists — ROSA + app
	@$(MAKE) deploy SCENARIO=aws-ready

deploy-cluster-ready: ## [deploy] Scenario 3: Clusters exist — autoscaler + app (INSTANCE_TYPE required)
	@if [ -z "$(INSTANCE_TYPE)" ]; then \
		echo ""; \
		echo "  Error: INSTANCE_TYPE is required for cluster-ready scenario"; \
		echo "  Usage: make deploy-cluster-ready INSTANCE_TYPE=m5.2xlarge"; \
		echo ""; \
		exit 1; \
	fi
	@$(MAKE) deploy SCENARIO=cluster-ready INSTANCE_TYPE=$(INSTANCE_TYPE)

validate-greenfield: ## [deploy] Validate greenfield inputs only (no deployment)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/deploy.yml $(VAULT_ARGS) \
		-e deployment_scenario=greenfield --tags preflight

validate-aws-ready: ## [deploy] Validate aws-ready inputs only (no deployment)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/deploy.yml $(VAULT_ARGS) \
		-e deployment_scenario=aws-ready --tags preflight

validate-cluster-ready: ## [deploy] Validate cluster-ready inputs only (INSTANCE_TYPE required)
	@if [ -z "$(INSTANCE_TYPE)" ]; then \
		echo ""; \
		echo "  Error: INSTANCE_TYPE is required for cluster-ready validation"; \
		echo "  Usage: make validate-cluster-ready INSTANCE_TYPE=m5.2xlarge"; \
		echo ""; \
		exit 1; \
	fi
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/deploy.yml $(VAULT_ARGS) \
		-e deployment_scenario=cluster-ready \
		-e workshop_machinepool_instance_type=$(INSTANCE_TYPE) --tags preflight

# ═══════════════════════════════════════════════════════════════════════
# End-to-End
# ═══════════════════════════════════════════════════════════════════════

.PHONY: workshop teardown

workshop: ## [e2e] Full build-out: Phase 1 (infra) + Phase 2 (application)
	@echo ""
	@echo "  ╔══════════════════════════════════════════════════════════╗"
	@echo "  ║  MAS World 2026 — Full Workshop Build-Out              ║"
	@echo "  ╚══════════════════════════════════════════════════════════╝"
	@echo ""
	@$(MAKE) deploy-infra
	@echo ""
	@$(MAKE) deploy-mas
	@echo ""
	@echo "  Workshop build-out complete."

teardown: ## [e2e] Full teardown: decommission -> destroy clusters -> destroy infra
	@echo ""
	@echo "  ╔══════════════════════════════════════════════════════════╗"
	@echo "  ║  MAS World 2026 — Full Workshop Teardown               ║"
	@echo "  ╚══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "=== Step 1/3: Decommission Workshop ==="
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/decommission-workshop.yml $(VAULT_ARGS)
	@echo ""
	@echo "=== Step 2/3: Destroy ROSA HCP Clusters ==="
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/destroy.yml $(VAULT_ARGS) -e auto_confirm=true
	@echo ""
	@echo "=== Step 3/3: Destroy AWS Infrastructure ==="
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/destroy-infra.yml $(VAULT_ARGS) -e auto_confirm=true
	@echo ""
	@echo "  Workshop teardown complete."

# ═══════════════════════════════════════════════════════════════════════
# Quality
# ═══════════════════════════════════════════════════════════════════════

.PHONY: lint test test-cov lab-test lab-test-fleet lab-test-ansible encrypt-secrets decrypt-secrets clean

lint: ## [quality] Run yamllint and ansible-lint
	yamllint -c .yamllint.yml .
	ansible-lint playbooks/ roles/

test: lint ## [quality] Run all tests (lint + syntax + unit tests)
	bash tests/test_syntax.sh
	$(PYTEST_PYTHON) -m pytest tests/ -v

test-cov: ## [quality] Run tests with coverage report
	$(PYTEST_PYTHON) -m pytest tests/ -v --cov=plugins --cov=cli --cov-report=term-missing

lab-test: ## [quality] Lab readiness test for one cluster (CLUSTER=lab-seat-01)
	@if [ -z "$(CLUSTER)" ]; then \
		echo ""; \
		echo "  Usage: make lab-test CLUSTER=<cluster_id>"; \
		echo "  Example: make lab-test CLUSTER=lab-seat-01"; \
		echo ""; \
		exit 1; \
	fi
	@PROJECT_ROOT=$(CURDIR) bash scripts/lab-readiness-test.sh $(CLUSTER)

lab-test-fleet: ## [quality] Lab readiness test for all enabled clusters
	@PROJECT_ROOT=$(CURDIR) bash scripts/lab-readiness-test.sh --fleet

lab-test-ansible: ## [quality] Lab readiness test via Ansible (CLUSTER=lab-seat-01)
	@if [ -z "$(CLUSTER)" ]; then \
		echo ""; \
		echo "  Usage: make lab-test-ansible CLUSTER=<cluster_id>"; \
		echo "  Example: make lab-test-ansible CLUSTER=lab-seat-01"; \
		echo ""; \
		exit 1; \
	fi
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/lab-readiness.yml $(VAULT_ARGS) -e cluster_id=$(CLUSTER)

fix-permissions: ## [quality] Set restrictive permissions on secret files
	@echo "Setting 0600 permissions on secrets/ files..."
	@chmod 0600 secrets/*.yml secrets/*.yaml secrets/*.json secrets/*.dat 2>/dev/null || true
	@echo "Done. All secret files are now owner-read/write only."

encrypt-secrets: ## [quality] Encrypt secrets with ansible-vault
	ansible-vault encrypt secrets/cluster-credentials.yml secrets/rosa-token.yml secrets/masworld-secrets.yml

decrypt-secrets: ## [quality] Decrypt secrets for editing
	ansible-vault decrypt secrets/cluster-credentials.yml secrets/rosa-token.yml secrets/masworld-secrets.yml

clean: ## [quality] Remove temporary artifacts
	rm -rf .ansible_async/
	rm -rf .cache/ansible_facts/
	rm -rf *.retry
	rm -f cluster-report.txt
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
