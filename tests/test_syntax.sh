#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PASS=0
FAIL=0
WARN=0

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }
warn() { echo "  WARN: $1"; WARN=$((WARN + 1)); }

# ═══════════════════════════════════════════════════════════════════════
# 1. Project Structure Checks
# ═══════════════════════════════════════════════════════════════════════

echo "=== 1. Project Structure Checks ==="

REQUIRED_FILES=(
  "ansible.cfg"
  "Makefile"
  "pyproject.toml"
  "requirements.yml"
  "galaxy.yml"
  ".ansible-lint"
  ".yamllint.yml"
  ".pre-commit-config.yaml"
  ".gitignore"
  "CLAUDE.md"
  "README.md"
  "prompt.md"
)

for f in "${REQUIRED_FILES[@]}"; do
  if [ -f "$f" ]; then
    pass "$f exists"
  else
    fail "$f missing"
  fi
done

REQUIRED_DIRS=(
  "playbooks"
  "roles"
  "plugins/filter"
  "cli"
  "config"
  "group_vars/all"
  "secrets"
  "tests"
  "docs"
  "scripts"
  "showroom"
  "acm"
  "operations"
)

for d in "${REQUIRED_DIRS[@]}"; do
  if [ -d "$d" ]; then
    pass "$d/ exists"
  else
    fail "$d/ missing"
  fi
done

# ═══════════════════════════════════════════════════════════════════════
# 2. Config File Checks
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo "=== 2. Config File Checks ==="

CONFIG_FILES=(
  "config/defaults.yaml"
  "config/event.yaml"
  "config/components.yaml"
  "group_vars/all/cluster_topology.yml"
  "group_vars/all/rosa_defaults.yml"
  "group_vars/all/aws_infra_defaults.yml"
)

for f in "${CONFIG_FILES[@]}"; do
  if [ -f "$f" ]; then
    pass "$f exists"
  else
    fail "$f missing"
  fi
done

# Check environment config files
ENV_CONFIGS=(dev rehearsal event)
for env in "${ENV_CONFIGS[@]}"; do
  if [ -f "config/environments/${env}.yaml" ]; then
    pass "config/environments/${env}.yaml exists"
  else
    warn "config/environments/${env}.yaml missing (optional)"
  fi
done

# Check secret templates
SECRET_TEMPLATES=(
  "secrets/rosa-token.yml.example"
  "secrets/cluster-credentials.yml.example"
  "secrets/masworld-secrets.yml.example"
)

for f in "${SECRET_TEMPLATES[@]}"; do
  if [ -f "$f" ]; then
    pass "$f exists"
  else
    fail "$f missing"
  fi
done

# ═══════════════════════════════════════════════════════════════════════
# 3. Role Structure Checks
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo "=== 3. Role Structure Checks ==="

PHASE1_ROLES=(rosa_preflight rosa_cluster aws_infra rosa_account_setup scenario_preflight)
PHASE2_ROLES=(
  config_validation cluster_preflight event_metadata acm_registration
  mas_prerequisites mas_core maximo_manage logging_operator loki_stack
  log_forwarding identity_demo mas_edge student_accounts sample_workloads
  showroom event_readiness environment_report
)

ALL_ROLES=("${PHASE1_ROLES[@]}" "${PHASE2_ROLES[@]}")

for role in "${ALL_ROLES[@]}"; do
  if [ -f "roles/$role/tasks/main.yml" ]; then
    pass "roles/$role/tasks/main.yml exists"
  else
    fail "roles/$role/tasks/main.yml missing"
  fi
  if [ -f "roles/$role/defaults/main.yml" ] || [ -f "roles/$role/vars/main.yml" ]; then
    pass "roles/$role has defaults or vars"
  else
    warn "roles/$role has no defaults/main.yml or vars/main.yml"
  fi
done

# ═══════════════════════════════════════════════════════════════════════
# 4. Phase 1 Playbook Syntax Checks
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo "=== 4. Phase 1 Playbook Syntax Checks ==="

PHASE1_EXTRAS="-e @secrets/cluster-credentials.yml.example -e @secrets/rosa-token.yml.example"
PHASE1_PLAYBOOKS=(preflight.yml setup-infra.yml provision.yml destroy.yml destroy-infra.yml status.yml deploy.yml)

for pb in "${PHASE1_PLAYBOOKS[@]}"; do
  if [ -f "playbooks/$pb" ]; then
    EXTRAS="$PHASE1_EXTRAS"
    if [ "$pb" = "deploy.yml" ]; then
      EXTRAS="$EXTRAS -e deployment_scenario=greenfield"
    fi
    # shellcheck disable=SC2086
    if ansible-playbook "playbooks/$pb" --syntax-check $EXTRAS > /dev/null 2>&1; then
      pass "playbooks/$pb syntax OK"
    else
      fail "playbooks/$pb syntax FAILED"
    fi
  else
    fail "playbooks/$pb not found"
  fi
done

# ═══════════════════════════════════════════════════════════════════════
# 5. Phase 2 Playbook Syntax Checks
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo "=== 5. Phase 2 Playbook Syntax Checks ==="

PHASE2_PLAYBOOKS=(
  prepare-cluster.yml prepare-fleet.yml
  validate-cluster.yml validate-fleet.yml
  repair-cluster.yml rotate-credentials.yml
  reset-exercises.yml decommission-workshop.yml
)

for pb in "${PHASE2_PLAYBOOKS[@]}"; do
  if [ -f "playbooks/$pb" ]; then
    if ansible-playbook "playbooks/$pb" --syntax-check > /dev/null 2>&1; then
      pass "playbooks/$pb syntax OK"
    else
      fail "playbooks/$pb syntax FAILED"
    fi
  else
    fail "playbooks/$pb not found"
  fi
done

# ═══════════════════════════════════════════════════════════════════════
# 6. Python Module Checks
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo "=== 6. Python Module Checks ==="

PYTHON=${PYTHON:-python3}

PYTHON_MODULES=(
  "cli"
  "cli.config.loader"
  "cli.config.schema"
  "cli.secrets.provider"
  "cli.secrets.file_provider"
  "cli.secrets.env_provider"
)

for mod in "${PYTHON_MODULES[@]}"; do
  if $PYTHON -c "import $mod" 2>/dev/null; then
    pass "import $mod"
  else
    fail "import $mod failed"
  fi
done

# Check filter plugins are importable
if $PYTHON -c "import plugins.filter.cluster_helpers" 2>/dev/null; then
  pass "import plugins.filter.cluster_helpers"
else
  fail "import plugins.filter.cluster_helpers failed"
fi

if $PYTHON -c "import plugins.filter.masworld" 2>/dev/null; then
  pass "import plugins.filter.masworld"
else
  fail "import plugins.filter.masworld failed"
fi

# Check CLI entry point is defined
if $PYTHON -c "from cli.main import cli" 2>/dev/null; then
  pass "CLI entry point (cli.main:cli) importable"
else
  fail "CLI entry point (cli.main:cli) import failed"
fi

# ═══════════════════════════════════════════════════════════════════════
# 7. Filter Plugin FQCN Check
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo "=== 7. Filter Namespace Checks ==="

if grep -rq 'masworld\.automation\.' playbooks/ roles/ --include='*.yml' 2>/dev/null; then
  fail "Stale FQCN filter references (masworld.automation.*) found"
else
  pass "No FQCN filter references (masworld.automation.*) found"
fi

# ═══════════════════════════════════════════════════════════════════════
# 8. End-to-End Workflow Wiring Checks
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo "=== 8. End-to-End Workflow Wiring Checks ==="

# Check Makefile targets exist
EXPECTED_TARGETS=(
  setup preflight validate setup-infra provision status
  deploy-infra destroy destroy-auto destroy-infra destroy-infra-auto
  wizard deploy deploy-greenfield deploy-aws-ready deploy-cluster-ready
  validate-greenfield validate-aws-ready validate-cluster-ready
  mas-prepare-cluster mas-prepare-fleet mas-validate-cluster mas-validate-fleet
  mas-repair-cluster mas-create-students mas-rotate-credentials mas-reset-exercises
  mas-decommission deploy-mas workshop teardown lint test test-cov
  lab-test lab-test-fleet lab-test-ansible
  encrypt-secrets decrypt-secrets clean
)

for target in "${EXPECTED_TARGETS[@]}"; do
  if grep -q "^${target}:" Makefile; then
    pass "Makefile target '$target' defined"
  else
    fail "Makefile target '$target' missing"
  fi
done

# Check helper includes exist (used by fleet playbooks)
for inc in _prepare-single-cluster.yml _validate-single-cluster.yml _resolve-cluster-profile.yml; do
  if [ -f "playbooks/$inc" ]; then
    pass "playbooks/$inc (helper include) exists"
  else
    fail "playbooks/$inc (helper include) missing"
  fi
done

# Check preflight script exists and is executable
if [ -x "scripts/preflight.sh" ]; then
  pass "scripts/preflight.sh is executable"
else
  fail "scripts/preflight.sh missing or not executable"
fi

# Check deploy wizard script exists and is executable
if [ -x "scripts/deploy-wizard.sh" ]; then
  pass "scripts/deploy-wizard.sh is executable"
else
  fail "scripts/deploy-wizard.sh missing or not executable"
fi

# Check lab readiness test script exists and is executable
if [ -x "scripts/lab-readiness-test.sh" ]; then
  pass "scripts/lab-readiness-test.sh is executable"
else
  fail "scripts/lab-readiness-test.sh missing or not executable"
fi

# ═══════════════════════════════════════════════════════════════════════
# 9. Documentation Completeness
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo "=== 9. Documentation Completeness ==="

REQUIRED_DOCS=(
  architecture.md
  installation-guide.md
  configuration-guide.md
  configuration-reference.md
  developer-guide.md
  operator-guide.md
  cli-reference.md
  aws-account-prerequisites.md
  teardown-guide.md
  troubleshooting.md
  masworld-specification.md
  implementation-status.md
  decision-log.md
  changelog.md
  blockers.md
)

for doc in "${REQUIRED_DOCS[@]}"; do
  if [ -f "docs/$doc" ]; then
    pass "docs/$doc exists"
  else
    fail "docs/$doc missing"
  fi
done

# Check no stale change-log.md exists
if [ ! -f "docs/change-log.md" ]; then
  pass "docs/change-log.md removed (merged into changelog.md)"
else
  warn "docs/change-log.md still exists (should be merged into changelog.md)"
fi

# ═══════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed, $WARN warnings"
echo "═══════════════════════════════════════════════════"

if [ "$FAIL" -gt 0 ]; then
  echo "  SOME CHECKS FAILED"
  exit 1
else
  echo "  All checks passed."
  exit 0
fi
