# ============================================================================
# MAS World 2026 Automation — Makefile
# ============================================================================
# Usage:  make <target> [VAR=value ...]
# Run `make` or `make help` to list all available targets.
# ============================================================================

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
ANSIBLE_ARGS     ?=
CLUSTER          ?=
ENVIRONMENT      ?= development
SEAT             ?=
SCENARIO         ?= default
MODULE           ?=

VENV             := .venv
PYTHON           := $(VENV)/bin/python
PIP              := $(VENV)/bin/pip
ACTIVATE         := . $(VENV)/bin/activate

SHOWROOM_DIR     := ../mas-world-2026-showroom
GITLEAKS_CONFIG  := ../.gitleaks.toml
YAMLLINT_CONFIG  := ../.yamllint.yml
PRE_COMMIT_CFG   := ../.pre-commit-config.yaml

# ============================================================================
#  Setup
# ============================================================================

.PHONY: setup
setup: ## Create venv, install all deps, pre-commit hooks, and Ansible Galaxy collections
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e '.[dev]'
	$(ACTIVATE) && ansible-galaxy collection install -r requirements.yml --force
	$(ACTIVATE) && pre-commit install --config $(PRE_COMMIT_CFG)
	@echo ""
	@echo "Setup complete. Activate the venv with:  source $(VENV)/bin/activate"

.PHONY: setup-dev
setup-dev: setup ## Same as setup plus molecule and additional development tools
	$(PIP) install molecule molecule-plugins[docker] tox pre-commit
	@echo ""
	@echo "Dev setup complete."

# ============================================================================
#  Configuration
# ============================================================================

.PHONY: config-validate
config-validate: ## Validate configuration against schema (ENVIRONMENT)
	$(PYTHON) -c "from cli.config.validator import validate_config; validate_config('config/environments/$(ENVIRONMENT).yaml')"

.PHONY: config-render
config-render: ## Render effective config with secrets redacted (ENVIRONMENT)
	$(PYTHON) -c "\
		from cli.config.loader import load_effective_config; \
		from cli.config.validator import redact_secrets; \
		import yaml, sys; \
		cfg = load_effective_config('config/environments/$(ENVIRONMENT).yaml'); \
		yaml.dump(redact_secrets(cfg), sys.stdout, default_flow_style=False) \
	"

.PHONY: config-diff
config-diff: ## Compare two environment configs (ENV_A, ENV_B)
	@test -n "$(ENV_A)" || (echo "ERROR: ENV_A is required. Usage: make config-diff ENV_A=development ENV_B=rehearsal" && exit 1)
	@test -n "$(ENV_B)" || (echo "ERROR: ENV_B is required. Usage: make config-diff ENV_A=development ENV_B=rehearsal" && exit 1)
	diff --color -u \
		<($(PYTHON) -c "\
			from cli.config.loader import load_effective_config; \
			from cli.config.validator import redact_secrets; \
			import yaml, sys; \
			cfg = load_effective_config('config/environments/$(ENV_A).yaml'); \
			yaml.dump(redact_secrets(cfg), sys.stdout, default_flow_style=False) \
		") \
		<($(PYTHON) -c "\
			from cli.config.loader import load_effective_config; \
			from cli.config.validator import redact_secrets; \
			import yaml, sys; \
			cfg = load_effective_config('config/environments/$(ENV_B).yaml'); \
			yaml.dump(redact_secrets(cfg), sys.stdout, default_flow_style=False) \
		") || true

# ============================================================================
#  Linting and Static Analysis
# ============================================================================

.PHONY: lint
lint: ## Run ansible-lint, yamllint, and ruff
	ansible-lint playbooks/ roles/
	yamllint -c $(YAMLLINT_CONFIG) playbooks/ roles/ config/
	python -m ruff check cli/ plugins/ tests/

.PHONY: lint-fix
lint-fix: ## Run ruff with auto-fix
	python -m ruff check --fix cli/ plugins/ tests/

.PHONY: typecheck
typecheck: ## Run mypy type checking on CLI and plugins
	python -m mypy cli/ plugins/

# ============================================================================
#  Tests
# ============================================================================

.PHONY: test
test: ## Run pytest suite
	python -m pytest tests/ -v

.PHONY: test-cov
test-cov: ## Run pytest with coverage report
	python -m pytest tests/ -v --cov=cli --cov=plugins --cov-report=term-missing --cov-report=html

# ============================================================================
#  Cluster Preparation
# ============================================================================

.PHONY: prepare-cluster
prepare-cluster: ## Prepare a single cluster (requires CLUSTER, optional ENVIRONMENT)
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required. Usage: make prepare-cluster CLUSTER=seat-01" && exit 1)
	ansible-playbook playbooks/prepare-cluster.yml \
		-e masworld_cluster_id=$(CLUSTER) \
		-e @config/environments/$(ENVIRONMENT).yaml \
		$(ANSIBLE_ARGS)

.PHONY: prepare-fleet
prepare-fleet: ## Prepare the full fleet (optional ENVIRONMENT)
	ansible-playbook playbooks/prepare-fleet.yml \
		-e @config/environments/$(ENVIRONMENT).yaml \
		$(ANSIBLE_ARGS)

.PHONY: repair-cluster
repair-cluster: ## Repair a single cluster (requires CLUSTER)
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required. Usage: make repair-cluster CLUSTER=seat-01" && exit 1)
	ansible-playbook playbooks/repair-cluster.yml \
		-e masworld_cluster_id=$(CLUSTER) \
		-e @config/environments/$(ENVIRONMENT).yaml \
		$(ANSIBLE_ARGS)

# ============================================================================
#  Validation
# ============================================================================

.PHONY: validate
validate: ## Validate a cluster or the full fleet (optional CLUSTER, ENVIRONMENT)
	@if [ -n "$(CLUSTER)" ]; then \
		ansible-playbook playbooks/validate-cluster.yml \
			-e masworld_cluster_id=$(CLUSTER) \
			-e @config/environments/$(ENVIRONMENT).yaml \
			$(ANSIBLE_ARGS); \
	else \
		ansible-playbook playbooks/validate-fleet.yml \
			-e @config/environments/$(ENVIRONMENT).yaml \
			$(ANSIBLE_ARGS); \
	fi

.PHONY: report
report: ## Generate environment report for a cluster (requires CLUSTER)
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required. Usage: make report CLUSTER=seat-01" && exit 1)
	ansible-playbook playbooks/validate-cluster.yml \
		-e masworld_cluster_id=$(CLUSTER) \
		-e @config/environments/$(ENVIRONMENT).yaml \
		-t environment_report \
		$(ANSIBLE_ARGS)

# ============================================================================
#  Student Accounts
# ============================================================================

.PHONY: create-students
create-students: ## Create student accounts on a cluster (requires CLUSTER)
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required. Usage: make create-students CLUSTER=seat-01" && exit 1)
	ansible-playbook playbooks/prepare-cluster.yml \
		-e masworld_cluster_id=$(CLUSTER) \
		-e @config/environments/$(ENVIRONMENT).yaml \
		-t student_accounts \
		$(ANSIBLE_ARGS)

.PHONY: disable-students
disable-students: ## Disable student accounts on a cluster (requires CLUSTER)
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required. Usage: make disable-students CLUSTER=seat-01" && exit 1)
	ansible-playbook playbooks/decommission-workshop.yml \
		-e masworld_cluster_id=$(CLUSTER) \
		-e @config/environments/$(ENVIRONMENT).yaml \
		-t disable_students \
		$(ANSIBLE_ARGS)

.PHONY: export-cards
export-cards: ## Export attendee access cards (requires CLUSTER)
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required. Usage: make export-cards CLUSTER=seat-01" && exit 1)
	$(PYTHON) -m cli.main export-access-cards \
		--cluster $(CLUSTER) \
		--environment $(ENVIRONMENT)

# ============================================================================
#  Credential Rotation
# ============================================================================

.PHONY: rotate-credentials
rotate-credentials: ## Rotate student credentials on a cluster (requires CLUSTER)
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required." && exit 1)
	ansible-playbook playbooks/rotate-credentials.yml \
		-e masworld_cluster_id=$(CLUSTER) \
		-e masworld_seat_number=$(SEAT) \
		-e @config/environments/$(ENVIRONMENT).yaml \
		$(ANSIBLE_ARGS)

# ============================================================================
#  Exercise Management
# ============================================================================

.PHONY: reset-exercises
reset-exercises: ## Reset exercises on a cluster (requires CLUSTER, optional MODULE)
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required." && exit 1)
	ansible-playbook playbooks/reset-exercises.yml \
		-e masworld_cluster_id=$(CLUSTER) \
		-e @config/environments/$(ENVIRONMENT).yaml \
		$(if $(MODULE),-e masworld_reset_module=$(MODULE)) \
		$(ANSIBLE_ARGS)

# ============================================================================
#  Seat Assignment
# ============================================================================

.PHONY: assign-seat
assign-seat: ## Assign a seat to a cluster (requires SEAT and CLUSTER)
	@test -n "$(SEAT)" || (echo "ERROR: SEAT is required. Usage: make assign-seat SEAT=12 CLUSTER=seat-12" && exit 1)
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required. Usage: make assign-seat SEAT=12 CLUSTER=seat-12" && exit 1)
	$(PYTHON) -m cli.main assign-seat \
		--seat $(SEAT) \
		--cluster $(CLUSTER) \
		--environment $(ENVIRONMENT)

.PHONY: replace-seat
replace-seat: ## Replace a seat with a spare cluster (requires SEAT and CLUSTER)
	@test -n "$(SEAT)" || (echo "ERROR: SEAT is required. Usage: make replace-seat SEAT=12 CLUSTER=spare-02" && exit 1)
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required. Usage: make replace-seat SEAT=12 CLUSTER=spare-02" && exit 1)
	$(PYTHON) -m cli.main replace-seat \
		--seat $(SEAT) \
		--cluster $(CLUSTER) \
		--environment $(ENVIRONMENT)

.PHONY: export-seats
export-seats: ## Export the current seat map
	$(PYTHON) -m cli.main export-seat-map \
		--environment $(ENVIRONMENT)

# ============================================================================
#  Showroom
# ============================================================================

.PHONY: showroom-build
showroom-build: ## Build the Antora Showroom site
	@test -d "$(SHOWROOM_DIR)" || (echo "ERROR: Showroom directory not found at $(SHOWROOM_DIR)" && exit 1)
	cd $(SHOWROOM_DIR) && npx antora site.yml

.PHONY: showroom-preview
showroom-preview: showroom-build ## Build Showroom and serve locally on port 8080
	@echo "Serving Showroom at http://localhost:8080"
	cd $(SHOWROOM_DIR) && npx http-server build/site -p 8080 -c-1

# ============================================================================
#  Security
# ============================================================================

.PHONY: secret-scan
secret-scan: ## Scan for secrets with gitleaks
	gitleaks detect --config $(GITLEAKS_CONFIG) --source .. --verbose

.PHONY: pre-commit
pre-commit: ## Run all pre-commit hooks against staged files
	pre-commit run --config $(PRE_COMMIT_CFG) --all-files

# ============================================================================
#  Molecule
# ============================================================================

.PHONY: molecule-test
molecule-test: ## Run molecule tests (optional SCENARIO, default: default)
	cd roles/ && molecule test -s $(SCENARIO)

.PHONY: molecule-list
molecule-list: ## List available molecule scenarios
	@find roles/ -path '*/molecule/*/molecule.yml' 2>/dev/null \
		| sed 's|roles/||;s|/molecule/|  scenario: |;s|/molecule.yml||' \
		| sort \
		|| echo "No molecule scenarios found."

# ============================================================================
#  Docs
# ============================================================================

.PHONY: docs-links
docs-links: ## Check for broken links in markdown documentation
	@echo "Checking for broken internal links in docs/..."
	@find docs/ -name '*.md' -exec grep -oHn '\[.*\](\([^)]*\))' {} \; \
		| grep -v 'http' \
		| while IFS=: read -r file line match; do \
			target=$$(echo "$$match" | sed 's/.*](\(.*\))/\1/' | sed 's/#.*//'); \
			if [ -n "$$target" ] && [ ! -f "$$target" ] && [ ! -f "docs/$$target" ]; then \
				echo "BROKEN: $$file:$$line -> $$target"; \
			fi; \
		done; \
		echo "Link check complete."

# ============================================================================
#  CI Helpers
# ============================================================================

.PHONY: ci-lint
ci-lint: lint typecheck config-validate ## Combined lint pipeline (lint + typecheck + config-validate)
	@echo "CI lint passed."

.PHONY: ci-test
ci-test: test secret-scan ## Combined test pipeline (test + secret-scan)
	@echo "CI test passed."

# ============================================================================
#  Decommission
# ============================================================================

.PHONY: decommission
decommission: ## Decommission the workshop environment (ENVIRONMENT)
	ansible-playbook playbooks/decommission-workshop.yml \
		-e @config/environments/$(ENVIRONMENT).yaml \
		$(ANSIBLE_ARGS)

# ============================================================================
#  Cleanup
# ============================================================================

.PHONY: clean
clean: ## Remove Python caches, Ansible retry files, and build artifacts
	find . -name '*.retry' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '.pytest_cache' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '.mypy_cache' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name 'htmlcov' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '.coverage' -delete 2>/dev/null || true
	find . -name '*.egg-info' -type d -exec rm -rf {} + 2>/dev/null || true

.PHONY: clean-all
clean-all: clean ## Remove everything including the venv
	rm -rf $(VENV)

# ============================================================================
#  Help
# ============================================================================

.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "MAS World 2026 Automation"
	@echo "========================="
	@echo ""
	@echo "Usage:  make <target> [VAR=value ...]"
	@echo ""
	@echo "Variables:"
	@echo "  CLUSTER       Cluster identifier         (e.g. seat-01)"
	@echo "  SEAT          Seat number                 (e.g. 12)"
	@echo "  ENVIRONMENT   Environment name            (default: development)"
	@echo "  MODULE        Exercise module to reset    (e.g. observability)"
	@echo "  SCENARIO      Molecule scenario           (default: default)"
	@echo "  ANSIBLE_ARGS  Extra ansible-playbook args (e.g. --check)"
	@echo "  ENV_A / ENV_B Environments for config-diff"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""
