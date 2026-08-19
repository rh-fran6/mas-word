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
SEAT_START ?=
SEAT_END ?=

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
	ansible-galaxy collection install -r requirements.yml -p collections/ --force
	$(MAKE) patch-collection
	@if git rev-parse --git-dir >/dev/null 2>&1; then pre-commit install; else echo "Skipping pre-commit install (not a git repository)"; fi

# Post-install patches for IBM collection compatibility with ansible-core 2.21
# and strategy:free parallel execution. Re-applied automatically on every make setup.
# Patches:
#   1. regex_search() returns string in until/assert — append 'is not none'
#   2. pause module breaks strategy:free — replace with wait_for timeout
IBM_COLLECTION := collections/ansible_collections/ibm/mas_devops
.PHONY: patch-collection
patch-collection: ## [setup] Apply ansible-core 2.21 + strategy:free patches to IBM collection
	@if [ -d "$(IBM_COLLECTION)" ]; then \
		echo "Patching IBM collection for ansible-core 2.21 + strategy:free compatibility..."; \
		$(PYTHON) scripts/patch-collection.py "$(IBM_COLLECTION)"; \
	else \
		echo "WARNING: IBM collection not found at $(IBM_COLLECTION). Run 'make setup' to install."; \
	fi

.PHONY: fetch-charts
fetch-charts: ## [setup] Download Showroom Helm chart for local deployment
	@mkdir -p charts
	helm pull showroom-single-pod \
	  --repo https://rhpds.github.io/showroom-deployer \
	  --version v2.1.8 \
	  --destination charts/
	@echo "Chart downloaded to charts/"

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

mas-prepare-fleet: ## [mas] Prepare entire fleet (all clusters, or SEAT_START/SEAT_END range)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/prepare-fleet.yml $(VAULT_ARGS) \
		$(if $(SEAT_START),-e seat_start=$(SEAT_START)) \
		$(if $(SEAT_END),-e seat_end=$(SEAT_END))

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
		echo "    make deploy-cluster-ready                          # defaults to m6a.4xlarge"; \
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

deploy-cluster-ready: ## [deploy] Scenario 3: Clusters exist — machinepool + app (INSTANCE_TYPE, SEAT_START, SEAT_END optional)
	@_IT="$(INSTANCE_TYPE)"; \
	if [ -z "$$_IT" ]; then \
		echo ""; \
		echo "  Workshop machinepool instance type not specified."; \
		echo ""; \
		echo "  Options:"; \
		echo "    m6a.4xlarge   16 vCPU / 64 GB — recommended for MAS + Manage + Db2 (default)"; \
		echo "    m5.2xlarge     8 vCPU / 32 GB — lighter workloads, demos, cost-sensitive"; \
		echo "    <custom>      Any valid EC2 instance type (e.g. m6i.8xlarge, r6a.2xlarge)"; \
		echo ""; \
		echo "  Usage:"; \
		echo "    make deploy-cluster-ready                                          # all clusters"; \
		echo "    make deploy-cluster-ready INSTANCE_TYPE=m5.2xlarge"; \
		echo "    make deploy-cluster-ready SEAT_START=29 SEAT_END=50               # seats 29-50 only"; \
		echo "    make deploy-cluster-ready SEAT_START=29                            # seats 29+"; \
		echo ""; \
		echo "  Proceeding with default: m6a.4xlarge"; \
		echo ""; \
		_IT="m6a.4xlarge"; \
	fi; \
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/deploy-cluster-ready.yml $(VAULT_ARGS) \
		-e workshop_machinepool_instance_type=$$_IT \
		$(if $(SEAT_START),-e seat_start=$(SEAT_START)) \
		$(if $(SEAT_END),-e seat_end=$(SEAT_END)) \
		$(if $(FORCE_SHOWROOM),-e masworld_force_showroom_refresh=true)

validate-greenfield: ## [deploy] Validate greenfield inputs only (no deployment)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/deploy.yml $(VAULT_ARGS) \
		-e deployment_scenario=greenfield --tags preflight

validate-aws-ready: ## [deploy] Validate aws-ready inputs only (no deployment)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/deploy.yml $(VAULT_ARGS) \
		-e deployment_scenario=aws-ready --tags preflight

validate-cluster-ready: ## [deploy] Validate cluster-ready inputs only (INSTANCE_TYPE optional, default m6a.4xlarge)
	@_IT="$(INSTANCE_TYPE)"; \
	if [ -z "$$_IT" ]; then _IT="m6a.4xlarge"; fi; \
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/deploy.yml $(VAULT_ARGS) \
		-e deployment_scenario=cluster-ready \
		-e workshop_machinepool_instance_type=$$_IT --tags preflight

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
# Maintenance
# ═══════════════════════════════════════════════════════════════════════

.PHONY: cleanup-community-keycloak lab-reset lab-reset-fleet restart-showroom redeploy-showroom update-rbac prepare-operator-roles

restart-showroom: ## [maintenance] Restart Showroom pods across fleet to pick up content changes
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/restart-showroom.yml $(VAULT_ARGS)

redeploy-showroom: ## [maintenance] Redeploy Showroom (Helm upgrade) across fleet — fixes user_data attributes
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/redeploy-showroom.yml $(VAULT_ARGS)

update-rbac: ## [maintenance] Update RBAC policies (ClusterRoles + bindings) across all clusters
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/update-rbac.yml $(VAULT_ARGS)

prepare-operator-roles: ## [maintenance] Create IAM roles for STS operator installation and store ARNs for Showroom
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/prepare-operator-roles.yml $(VAULT_ARGS)

cleanup-community-keycloak: ## [maintenance] Remove all community Keycloak from fleet (one-time, run before RHBK deploy)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/cleanup-community-keycloak.yml $(VAULT_ARGS)

lab-reset: ## [maintenance] Reset lab for a single seat (SEAT=20)
	@if [ -z "$(SEAT)" ]; then \
		echo ""; \
		echo "  Usage: make lab-reset SEAT=<number>"; \
		echo "  Example: make lab-reset SEAT=20"; \
		echo ""; \
		echo "  Removes all student-installed logging operators, LokiStack,"; \
		echo "  synced groups, and test pods. NEVER touches MAS components."; \
		echo ""; \
		exit 1; \
	fi
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/reset-lab.yml $(VAULT_ARGS) -e seat=$(SEAT)

lab-reset-fleet: ## [maintenance] Reset lab for all seats (SEAT_START, SEAT_END optional)
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/reset-lab.yml $(VAULT_ARGS) \
		$(if $(SEAT_START),-e seat_start=$(SEAT_START)) \
		$(if $(SEAT_END),-e seat_end=$(SEAT_END))

# ═══════════════════════════════════════════════════════════════════════
# Quality
# ═══════════════════════════════════════════════════════════════════════

.PHONY: lint test test-cov lab-test lab-test-fleet lab-test-ansible encrypt-secrets decrypt-secrets clean validate-roles check-operatorhub

check-operatorhub: ## [quality] Check OperatorHub health and available operators across fleet
	$(ANSIBLE_PLAYBOOK) $(PLAYBOOK_DIR)/check-operatorhub.yml $(VAULT_ARGS)

validate-roles: ## [quality] Verify all include_role/import_role references resolve to installed roles
	@echo "Validating role references..."
	@errors=0; \
	for ref in $$(grep -rh 'name:.*ibm\.mas_devops\.' roles/ playbooks/ --include='*.yml' --include='*.yaml' \
		| grep -v '^\s*#' | grep -v 'msg:' | grep -v 'debug:' \
		| sed -n 's/.*name:\s*\(ibm\.mas_devops\.[a-z_]*\).*/\1/p' | sort -u); do \
		role_name=$$(echo "$$ref" | sed 's/ibm\.mas_devops\.//'); \
		if [ ! -d "collections/ansible_collections/ibm/mas_devops/roles/$$role_name" ]; then \
			echo "  MISSING: $$ref (no role at collections/.../roles/$$role_name)"; \
			errors=$$((errors + 1)); \
		fi; \
	done; \
	for ref in $$(grep -rh 'name:' roles/ playbooks/ --include='*.yml' --include='*.yaml' \
		| grep -E '^\s+name:\s+[a-z_]+\s*$$' | grep -v 'ibm\.' | grep -v 'kubernetes\.' | grep -v 'ansible\.' \
		| sed -n 's/.*name:\s*\([a-z_]*\)\s*$$/\1/p' | sort -u); do \
		if [ ! -d "roles/$$ref" ]; then \
			echo "  MISSING: $$ref (no role at roles/$$ref)"; \
			errors=$$((errors + 1)); \
		fi; \
	done; \
	if [ $$errors -gt 0 ]; then \
		echo "FAILED: $$errors role reference(s) could not be resolved"; \
		exit 1; \
	else \
		echo "OK: all role references resolve"; \
	fi

lint: validate-roles ## [quality] Run yamllint, ansible-lint, and role validation
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
