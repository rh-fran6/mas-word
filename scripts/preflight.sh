#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# ROSA HCP Multi-Cluster — Preflight Validation
#
# Validates everything required before creating infrastructure or clusters.
# Run with:  make preflight
#            make preflight MODE=infra      (infra-only checks)
#            make preflight MODE=provision   (provision-only checks)
#            make preflight MODE=all         (both, default)
###############################################################################

MODE="${1:-all}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SECRETS_DIR="${PROJECT_ROOT}/secrets"
GROUP_VARS="${PROJECT_ROOT}/group_vars/all"

PASS=0
FAIL=0
WARN=0
ERRORS=()
WARNINGS=()

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

pass() {
  echo -e "  ${GREEN}[PASS]${NC} $1"
  PASS=$((PASS + 1))
}

fail() {
  echo -e "  ${RED}[FAIL]${NC} $1"
  FAIL=$((FAIL + 1))
  ERRORS+=("$1")
}

warn() {
  echo -e "  ${YELLOW}[WARN]${NC} $1"
  WARN=$((WARN + 1))
  WARNINGS+=("$1")
}

info() {
  echo -e "  ${CYAN}[INFO]${NC} $1"
}

section() {
  echo ""
  echo -e "${BOLD}── $1 ──${NC}"
}

###############################################################################
# 1. CLI Tools
###############################################################################
section "CLI Tools"

check_cli() {
  local name="$1"
  local cmd="$2"
  local version_cmd="${3:-}"
  if command -v "$cmd" > /dev/null 2>&1; then
    if [ -n "$version_cmd" ]; then
      local ver
      ver=$(eval "$version_cmd" 2>/dev/null | head -1 || echo "unknown")
      pass "$name ($ver)"
    else
      pass "$name"
    fi
  else
    fail "$name is not installed"
  fi
}

# Detect best Python — prefer highest version available
PYTHON=""
for candidate in python3.14 python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" > /dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done

if [ -n "$PYTHON" ]; then
  PYTHON_VER=$($PYTHON --version 2>/dev/null)
  pass "python ($PYTHON_VER via $PYTHON)"
else
  fail "python3 is not installed"
  PYTHON="python3"
fi

# Detect best pip — prefer pip3, fall back to pip, fall back to python -m pip
PIP=""
if command -v pip3 > /dev/null 2>&1; then
  PIP="pip3"
elif command -v pip > /dev/null 2>&1; then
  PIP="pip"
fi

if [ -n "$PIP" ]; then
  PIP_VER=$($PIP --version 2>/dev/null | head -1)
  pass "$PIP ($PIP_VER)"
elif $PYTHON -m pip --version > /dev/null 2>&1; then
  PIP="$PYTHON -m pip"
  PIP_VER=$($PYTHON -m pip --version 2>/dev/null | head -1)
  pass "pip via $PYTHON -m pip ($PIP_VER)"
else
  fail "pip is not installed — needed for 'make setup'"
fi

# Core — required for infrastructure and cluster provisioning
check_cli "rosa CLI" "rosa" "rosa version"
check_cli "aws CLI" "aws" "aws --version"
check_cli "ansible-playbook" "ansible-playbook" "ansible --version"
check_cli "ansible-vault" "ansible-vault" "ansible-vault --version"
check_cli "jq" "jq" "jq --version"

# OpenShift clients — needed post-cluster-creation
if command -v oc > /dev/null 2>&1; then
  pass "oc CLI ($(oc version --client 2>/dev/null | head -1 || echo 'installed'))"
else
  warn "oc CLI not installed — needed post-cluster-creation to interact with OpenShift"
fi

if command -v kubectl > /dev/null 2>&1; then
  pass "kubectl ($(kubectl version --client -o json 2>/dev/null | jq -r '.clientVersion.gitVersion // "installed"' 2>/dev/null || echo 'installed'))"
else
  info "kubectl not installed — oc includes kubectl functionality"
fi

# Development & testing tools — warn only, not required for provisioning
check_optional_cli() {
  local name="$1"
  local cmd="$2"
  local version_cmd="${3:-}"
  local hint="${4:-$PIP install $cmd}"
  if command -v "$cmd" > /dev/null 2>&1; then
    if [ -n "$version_cmd" ]; then
      local ver
      ver=$(eval "$version_cmd" 2>/dev/null | head -1 || echo "unknown")
      pass "$name ($ver)"
    else
      pass "$name"
    fi
  else
    warn "$name not installed — needed for 'make test' ($hint)"
  fi
}

check_optional_cli "ansible-lint" "ansible-lint" "ansible-lint --version"
check_optional_cli "yamllint" "yamllint" "yamllint --version"
check_optional_cli "pre-commit" "pre-commit" "pre-commit --version"

PYTEST_FOUND=false
for py_candidate in "$PYTHON" python3 python3.14 python3.13 python3.12 python3.11; do
  if command -v "$py_candidate" > /dev/null 2>&1 && $py_candidate -m pytest --version > /dev/null 2>&1; then
    PYTEST_VER=$($py_candidate -m pytest --version 2>/dev/null | head -1)
    if [ "$py_candidate" = "$PYTHON" ]; then
      pass "pytest ($PYTEST_VER)"
    else
      pass "pytest ($PYTEST_VER via $py_candidate)"
    fi
    PYTEST_FOUND=true
    break
  fi
done
if [ "$PYTEST_FOUND" = false ]; then
  warn "pytest not found — run 'make setup' or '$PIP install pytest'"
fi

###############################################################################
# 2. Secrets Files
###############################################################################
section "Secrets Files"

if [ -f "${SECRETS_DIR}/rosa-token.yml" ]; then
  pass "rosa-token.yml exists"
else
  fail "rosa-token.yml not found — copy from rosa-token.yml.example and add your token"
fi

if [ -f "${SECRETS_DIR}/cluster-credentials.yml" ]; then
  pass "cluster-credentials.yml exists"
else
  fail "cluster-credentials.yml not found — run scripts/generate-credentials-template.sh or copy from .example"
fi

# Check secret file permissions (should be 0600, not world-readable)
PERM_WARN=0
for secret_file in "${SECRETS_DIR}"/*.yml "${SECRETS_DIR}"/*.yaml "${SECRETS_DIR}"/*.json "${SECRETS_DIR}"/*.dat; do
  if [ -f "$secret_file" ]; then
    file_perms=$(stat -f "%Lp" "$secret_file" 2>/dev/null || stat -c "%a" "$secret_file" 2>/dev/null || echo "")
    if [ -n "$file_perms" ] && [ "$file_perms" != "600" ]; then
      warn "$(basename "$secret_file") has permissions $file_perms (expected 600) — run 'make fix-permissions'"
      PERM_WARN=$((PERM_WARN + 1))
    fi
  fi
done
if [ "$PERM_WARN" -eq 0 ]; then
  pass "All secret files have restrictive permissions (0600)"
fi

###############################################################################
# 3. Configuration Files
###############################################################################
section "Configuration Files"

for cfg in cluster_topology.yml rosa_defaults.yml aws_infra_defaults.yml; do
  if [ -f "${GROUP_VARS}/${cfg}" ]; then
    pass "$cfg exists"
  else
    fail "$cfg not found in group_vars/all/"
  fi
done

###############################################################################
# 4. YAML & Credential Validation (via Python)
###############################################################################
section "Credential Validation"

if [ -f "${SECRETS_DIR}/rosa-token.yml" ] && [ -f "${SECRETS_DIR}/cluster-credentials.yml" ] && [ -f "${GROUP_VARS}/cluster_topology.yml" ]; then

VALIDATION_OUTPUT=$(PROJECT_ROOT="$PROJECT_ROOT" python3 << 'PYEOF'
import yaml, sys, os, json

project_root = os.environ.get("PROJECT_ROOT", ".")
secrets_dir = os.path.join(project_root, "secrets")
group_vars = os.path.join(project_root, "group_vars", "all")

results = {"pass": [], "fail": [], "warn": []}

try:
    with open(os.path.join(secrets_dir, "rosa-token.yml")) as f:
        token_data = yaml.safe_load(f)
    token = token_data.get("rosa_token", "")
    if not token or token == "REPLACE_ME" or token == "eyJhbG...your-token-here":
        results["fail"].append("rosa_token is a placeholder — get yours from https://console.redhat.com/openshift/token/rosa")
    elif len(token) < 100:
        results["warn"].append(f"rosa_token seems short ({len(token)} chars) — verify it's a valid offline token")
    else:
        results["pass"].append("rosa_token looks valid (JWT format)")
except Exception as e:
    results["fail"].append(f"Cannot parse rosa-token.yml: {e}")

try:
    with open(os.path.join(group_vars, "cluster_topology.yml")) as f:
        topo = yaml.safe_load(f)
    prefix = topo.get("cluster_prefix", "")
    categories = topo.get("cluster_categories", {})
    if not prefix:
        results["fail"].append("cluster_prefix is empty in cluster_topology.yml")
    else:
        results["pass"].append(f"cluster_prefix: {prefix}")

    if "facilitator" not in categories:
        results["fail"].append("Missing 'facilitator' category in cluster_topology.yml")
    elif categories["facilitator"].get("count", 0) != 1:
        results["fail"].append("Facilitator count must be exactly 1")
    else:
        results["pass"].append("facilitator category: count=1")

    expected_names = []
    for cat in sorted(categories.keys()):
        cfg = categories[cat]
        count = cfg.get("count", 0)
        for i in range(1, count + 1):
            idx = f"{i:02d}" if cat == "seat" else str(i)
            expected_names.append(f"{prefix}-{cat}-{idx}")
    results["pass"].append(f"Topology expects {len(expected_names)} clusters: {', '.join(expected_names)}")

except Exception as e:
    results["fail"].append(f"Cannot parse cluster_topology.yml: {e}")
    expected_names = []

try:
    with open(os.path.join(secrets_dir, "cluster-credentials.yml")) as f:
        creds_data = yaml.safe_load(f)
    creds = creds_data.get("cluster_credentials", {})

    if not creds:
        results["fail"].append("cluster_credentials is empty")
    else:
        results["pass"].append(f"Found {len(creds)} credential entries")

    missing = [n for n in expected_names if n not in creds]
    if missing:
        results["fail"].append(f"Missing credentials for: {', '.join(missing)}")

    extra = [n for n in creds if n not in expected_names]
    if extra:
        results["warn"].append(f"Extra credentials (not in topology): {', '.join(extra)}")

    for name, c in creds.items():
        key_id = c.get("aws_access_key_id", "")
        secret = c.get("aws_secret_access_key", "")
        region = c.get("aws_region", "")

        issues = []
        if not key_id or "REPLACE_ME" in key_id or "EXAMPLE" in key_id:
            issues.append("access_key_id is placeholder")
        if not secret or "REPLACE_ME" in secret or "EXAMPLE" in secret:
            issues.append("secret_access_key is placeholder")
        if key_id and secret and key_id == secret:
            issues.append("access_key_id and secret_access_key are identical (likely a paste error)")
        if not key_id.startswith("AKIA") and key_id and "REPLACE" not in key_id:
            issues.append(f"access_key_id doesn't start with AKIA (got {key_id[:8]}...)")
        if not region:
            issues.append("aws_region is empty")

        if issues:
            results["fail"].append(f"{name}: {'; '.join(issues)}")
        else:
            results["pass"].append(f"{name}: credentials format OK (region={region})")

except Exception as e:
    results["fail"].append(f"Cannot parse cluster-credentials.yml: {e}")

print(json.dumps(results))
PYEOF
)

  while IFS= read -r msg; do
    pass "$msg"
  done < <(echo "$VALIDATION_OUTPUT" | python3 -c "import sys,json; [print(m) for m in json.load(sys.stdin)['pass']]" 2>/dev/null)

  while IFS= read -r msg; do
    fail "$msg"
  done < <(echo "$VALIDATION_OUTPUT" | python3 -c "import sys,json; [print(m) for m in json.load(sys.stdin)['fail']]" 2>/dev/null)

  while IFS= read -r msg; do
    warn "$msg"
  done < <(echo "$VALIDATION_OUTPUT" | python3 -c "import sys,json; [print(m) for m in json.load(sys.stdin)['warn']]" 2>/dev/null)

else
  info "Skipping credential validation — required files are missing"
fi

###############################################################################
# 5. AWS Connectivity (per account)
###############################################################################
section "AWS Connectivity"

ACCOUNT_LIST=""
if [ -f "${SECRETS_DIR}/cluster-credentials.yml" ] && command -v aws > /dev/null 2>&1; then

  ACCOUNT_LIST=$(PROJECT_ROOT="$PROJECT_ROOT" python3 << 'PYEOF'
import yaml, os, json
secrets_dir = os.path.join(os.environ.get("PROJECT_ROOT", "."), "secrets")
with open(os.path.join(secrets_dir, "cluster-credentials.yml")) as f:
    data = yaml.safe_load(f)
creds = data.get("cluster_credentials", {})
for name, c in creds.items():
    kid = c.get("aws_access_key_id", "")
    sec = c.get("aws_secret_access_key", "")
    reg = c.get("aws_region", "us-east-2")
    if kid and sec and "REPLACE_ME" not in kid and "EXAMPLE" not in kid and kid != sec:
        print(json.dumps({"name": name, "key": kid, "secret": sec, "region": reg}))
PYEOF
)

  if [ -z "$ACCOUNT_LIST" ]; then
    info "No valid credentials to test — fix credential issues above first"
  else
    ACCT_COUNT=0
    ACCT_FAIL=0
    while IFS= read -r entry; do
      name=$(echo "$entry" | jq -r '.name')
      key=$(echo "$entry" | jq -r '.key')
      secret=$(echo "$entry" | jq -r '.secret')
      region=$(echo "$entry" | jq -r '.region')

      STS_OUTPUT=$(AWS_ACCESS_KEY_ID="$key" \
                   AWS_SECRET_ACCESS_KEY="$secret" \
                   AWS_DEFAULT_REGION="$region" \
                   aws sts get-caller-identity --output json 2>&1) && STS_RC=0 || STS_RC=$?

      if [ "$STS_RC" -eq 0 ]; then
        ACCT_ID=$(echo "$STS_OUTPUT" | jq -r '.Account')
        pass "${name}: AWS Account ${ACCT_ID} (${region})"
        ACCT_COUNT=$((ACCT_COUNT + 1))
      else
        fail "${name}: AWS authentication failed — check access key and secret"
        ACCT_FAIL=$((ACCT_FAIL + 1))
      fi
    done <<< "$ACCOUNT_LIST"

    if [ "$ACCT_COUNT" -gt 0 ] && [ "$ACCT_FAIL" -eq 0 ]; then
      info "All $ACCT_COUNT AWS accounts authenticated successfully"
    fi
  fi
else
  info "Skipping AWS connectivity — prerequisites missing"
fi

###############################################################################
# 6. ROSA Login
###############################################################################
section "ROSA Login"

_ROSA_LOGGED_IN=false
if [ -f "${SECRETS_DIR}/rosa-token.yml" ] && command -v rosa > /dev/null 2>&1; then
  ROSA_TOKEN=$(python3 -c "
import yaml
with open('${SECRETS_DIR}/rosa-token.yml') as f:
    print(yaml.safe_load(f).get('rosa_token', ''))
" 2>/dev/null)

  if [ -n "$ROSA_TOKEN" ] && [ "$ROSA_TOKEN" != "REPLACE_ME" ]; then
    # ACCEPTED RISK: token passed as CLI arg (visible in ps aux). rosa CLI has no stdin alternative.
    # This script runs only on the operator's secured workstation; exposure window is milliseconds.
    if rosa login --token="$ROSA_TOKEN" > /dev/null 2>&1; then
      WHOAMI=$(rosa whoami 2>/dev/null || echo "")
      pass "ROSA login successful"
      _ROSA_LOGGED_IN=true
      if [ -n "$WHOAMI" ]; then
        info "$(echo "$WHOAMI" | grep -E 'Account|User|Email' | head -3 | tr '\n' ' ')"
      fi
    else
      fail "ROSA login failed — token may be expired. Refresh at https://console.redhat.com/openshift/token/rosa"
    fi
  else
    info "Skipping ROSA login — token not set"
  fi
else
  info "Skipping ROSA login — prerequisites missing"
fi

###############################################################################
# 7. Per-Account ROSA HCP Checks (parallelized)
#
# Checks per account:
#   - rosa verify quota (ROSA enablement + quota baseline)
#   - rosa verify permissions (SCP policies)
#   - Service-linked roles (ELB mandatory, EFS optional)
#   - ROSA HCP account roles (3 required for HCP)
#   - AWS service quotas with actual values
#   - Existing VPC count and project VPC detection
###############################################################################
section "Per-Account ROSA HCP Checks (parallelized)"

if [ -n "$ACCOUNT_LIST" ] && command -v aws > /dev/null 2>&1; then

  # Compute vCPU requirements from topology
  VCPU_REQS=$(PROJECT_ROOT="$PROJECT_ROOT" python3 << 'PYEOF'
import yaml, os, json
group_vars = os.path.join(os.environ.get("PROJECT_ROOT", "."), "group_vars", "all")
with open(os.path.join(group_vars, "cluster_topology.yml")) as f:
    topo = yaml.safe_load(f)

vcpu_map = {
    "m5.large": 2, "m5.xlarge": 4, "m5.2xlarge": 8, "m5.4xlarge": 16,
    "m6a.large": 2, "m6a.xlarge": 4, "m6a.2xlarge": 8, "m6a.4xlarge": 16,
    "m6i.large": 2, "m6i.xlarge": 4, "m6i.2xlarge": 8, "m6i.4xlarge": 16,
    "m7i.large": 2, "m7i.xlarge": 4, "m7i.2xlarge": 8, "m7i.4xlarge": 16,
    "r5.large": 2, "r5.xlarge": 4, "r5.2xlarge": 8, "r5.4xlarge": 16,
    "r6a.large": 2, "r6a.xlarge": 4, "r6a.2xlarge": 8, "r6a.4xlarge": 16,
    "c5.large": 2, "c5.xlarge": 4, "c5.2xlarge": 8, "c5.4xlarge": 16,
    "t3.large": 2, "t3.xlarge": 4, "t3.2xlarge": 8,
}
categories = topo.get("cluster_categories", {})
reqs = {}
for cat, cfg in categories.items():
    itype = cfg.get("instance_type", "m5.xlarge")
    replicas = cfg.get("initial_replicas", 2)
    max_replicas = cfg.get("autoscaling", {}).get("max_replicas", replicas)
    vcpus = vcpu_map.get(itype, 0)
    reqs[cat] = {
        "instance_type": itype, "vcpus_per_instance": vcpus,
        "initial_replicas": replicas, "max_replicas": max_replicas,
        "min_vcpus": vcpus * replicas, "max_vcpus": vcpus * max_replicas,
    }
print(json.dumps(reqs))
PYEOF
)

  TMPDIR_CHECKS=$(mktemp -d)
  trap 'rm -rf '"${TMPDIR_CHECKS}"'' EXIT

  # Launch one background check per account
  check_one_account() {
    local entry="$1"
    local outfile="$2"
    local name key secret region
    name=$(echo "$entry" | jq -r '.name')
    key=$(echo "$entry" | jq -r '.key')
    secret=$(echo "$entry" | jq -r '.secret')
    region=$(echo "$entry" | jq -r '.region')

    local category
    category=$(echo "$name" | sed -E 's/^[^-]+-([a-z]+)-.*/\1/')
    local vcpu_min vcpu_max inst_type
    vcpu_min=$(echo "$VCPU_REQS" | jq -r --arg cat "$category" '.[$cat].min_vcpus // 32')
    vcpu_max=$(echo "$VCPU_REQS" | jq -r --arg cat "$category" '.[$cat].max_vcpus // 64')
    inst_type=$(echo "$VCPU_REQS" | jq -r --arg cat "$category" '.[$cat].instance_type // "unknown"')

    exec > "$outfile" 2>&1

    export AWS_ACCESS_KEY_ID="$key"
    export AWS_SECRET_ACCESS_KEY="$secret"
    export AWS_DEFAULT_REGION="$region"

    echo "HEADER|${name} (${region})"

    # rosa verify quota
    if rosa verify quota --region="$region" > /dev/null 2>&1; then
      echo "PASS|${name}: ROSA HCP enabled & quota baseline OK"
    else
      echo "WARN|${name}: ROSA quota check warning — verify ROSA is enabled at https://console.aws.amazon.com/rosa"
    fi

    # rosa verify permissions / SCP
    if rosa verify permissions --region="$region" > /dev/null 2>&1; then
      echo "PASS|${name}: SCP policies OK"
    else
      echo "FAIL|${name}: SCP check failed — AWS Organization may restrict required services"
    fi

    # ELB service-linked role (mandatory)
    if aws iam get-role --role-name AWSServiceRoleForElasticLoadBalancing --query 'Role.RoleName' --output text > /dev/null 2>&1; then
      echo "PASS|${name}: ELB service-linked role exists"
    else
      echo "FAIL|${name}: ELB service-linked role missing — run: aws iam create-service-linked-role --aws-service-name elasticloadbalancing.amazonaws.com"
    fi

    # EFS service-linked role (created by rosa init)
    if aws iam get-role --role-name AWSServiceRoleForAmazonElasticFileSystem --query 'Role.RoleName' --output text > /dev/null 2>&1; then
      echo "PASS|${name}: EFS service-linked role exists"
    else
      echo "INFO|${name}: EFS service-linked role missing — created by 'rosa init'"
    fi

    # ROSA HCP account roles (3 for HCP: Installer, Support, Worker)
    local role_count
    # shellcheck disable=SC2016
    role_count=$(aws iam list-roles \
      --query 'length(Roles[?contains(RoleName, `HCP-ROSA`) || (contains(RoleName, `ManagedOpenShift`) && contains(RoleName, `HCP`))])' \
      --output text 2>/dev/null) || role_count="0"
    if [ "$role_count" -ge 3 ]; then
      echo "PASS|${name}: ${role_count} ROSA HCP account roles found"
    elif [ "$MODE" = "provision" ]; then
      echo "FAIL|${name}: ${role_count}/3 ROSA HCP account roles — run 'make setup-infra' first"
    else
      echo "INFO|${name}: ${role_count}/3 ROSA HCP account roles — will be created by 'make setup-infra'"
    fi

    # --- Service Quotas ---
    echo "HEADER|${name} — Quotas (${region})"

    check_quota() {
      local svc="$1" code="$2" label="$3" min_req="$4"
      local val
      val=$(aws service-quotas get-service-quota \
        --service-code "$svc" --quota-code "$code" \
        --query 'Quota.Value' --output text 2>/dev/null) || val=""
      if [ -z "$val" ] || [ "$val" = "None" ]; then
        echo "WARN|${name}: ${label} — could not retrieve"
      else
        local int_val=${val%.*}
        if [ "$int_val" -ge "$min_req" ]; then
          echo "PASS|${name}: ${label} = ${val} (need ${min_req})"
        else
          echo "FAIL|${name}: ${label} = ${val} — need at least ${min_req}"
        fi
      fi
    }

    # EC2 On-Demand Standard vCPUs (L-1216C47A) — ROSA HCP needs ≥32 per cluster
    check_quota "ec2" "L-1216C47A" "EC2 vCPUs [${inst_type} needs ${vcpu_min}-${vcpu_max}]" "$vcpu_min"

    # VPCs per Region (L-F678F1CE)
    check_quota "vpc" "L-F678F1CE" "VPCs per Region" 1

    # Internet Gateways (L-A4707A72)
    check_quota "vpc" "L-A4707A72" "Internet Gateways" 1

    # NAT Gateways per AZ (L-FE5A380F)
    check_quota "vpc" "L-FE5A380F" "NAT Gateways per AZ" 1

    # Elastic IPs (L-0263D0A3)
    check_quota "ec2" "L-0263D0A3" "Elastic IPs" 1

    # Network Load Balancers (L-69A177A2) — ROSA creates NLBs for API
    check_quota "elasticloadbalancing" "L-69A177A2" "Network Load Balancers" 1

    # Application Load Balancers (L-53DA6B97)
    check_quota "elasticloadbalancing" "L-53DA6B97" "Application Load Balancers" 1

    # EBS gp2 Storage TiB (L-D18FCD1D)
    check_quota "ebs" "L-D18FCD1D" "EBS gp2 Storage (TiB)" 1

    # EBS gp3 Storage TiB (L-7A658B76)
    check_quota "ebs" "L-7A658B76" "EBS gp3 Storage (TiB)" 1

    # Security Groups per Region (L-E79EC296)
    check_quota "vpc" "L-E79EC296" "Security Groups" 10

    # Network Interfaces (L-DF5E4CA3)
    check_quota "vpc" "L-DF5E4CA3" "Network Interfaces" 250

    # --- Existing Infrastructure ---
    local vpc_count our_vpc
    vpc_count=$(aws ec2 describe-vpcs --query 'length(Vpcs[])' --output text 2>/dev/null) || vpc_count="-1"
    our_vpc=$(aws ec2 describe-vpcs \
      --filters "Name=tag:Project,Values=rosa-hcp-multi-build" \
      --query 'Vpcs[0].VpcId' --output text 2>/dev/null) || our_vpc="None"

    if [ "$vpc_count" = "-1" ]; then
      echo "WARN|${name}: Could not check VPC count"
    elif [ "$our_vpc" != "None" ] && [ -n "$our_vpc" ]; then
      echo "PASS|${name}: ${vpc_count} VPCs (project VPC ${our_vpc} exists)"
    elif [ "$vpc_count" -ge 4 ]; then
      echo "WARN|${name}: ${vpc_count} VPCs — default limit 5, may need increase"
    else
      echo "PASS|${name}: ${vpc_count} VPCs (headroom OK)"
    fi
  }

  # Launch all account checks in parallel
  PIDS=()
  ACCT_FILES=()
  IDX=0
  while IFS= read -r entry; do
    outfile="${TMPDIR_CHECKS}/acct_${IDX}.out"
    ACCT_FILES+=("$outfile")
    check_one_account "$entry" "$outfile" &
    PIDS+=($!)
    IDX=$((IDX + 1))
  done <<< "$ACCOUNT_LIST"

  # Wait for all to complete
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
  done

  # Collect and display results in order
  for outfile in "${ACCT_FILES[@]}"; do
    if [ -f "$outfile" ]; then
      while IFS='|' read -r level msg; do
        case "$level" in
          HEADER) echo ""; info "${BOLD}${msg}${NC}" ;;
          PASS)   pass "$msg" ;;
          FAIL)   fail "$msg" ;;
          WARN)   warn "$msg" ;;
          INFO)   info "$msg" ;;
        esac
      done < "$outfile"
    fi
  done

else
  info "Skipping per-account checks — prerequisites missing"
fi

###############################################################################
# 8. vCPU Requirement Summary
###############################################################################
section "vCPU Requirements (from topology)"

if [ -f "${GROUP_VARS}/cluster_topology.yml" ]; then
  VCPU_REQS_DISPLAY=$(PROJECT_ROOT="$PROJECT_ROOT" python3 << 'PYEOF'
import yaml, os, json
group_vars = os.path.join(os.environ.get("PROJECT_ROOT", "."), "group_vars", "all")
with open(os.path.join(group_vars, "cluster_topology.yml")) as f:
    topo = yaml.safe_load(f)

vcpu_map = {
    "m5.large": 2, "m5.xlarge": 4, "m5.2xlarge": 8, "m5.4xlarge": 16,
    "m6a.large": 2, "m6a.xlarge": 4, "m6a.2xlarge": 8, "m6a.4xlarge": 16,
    "m6i.large": 2, "m6i.xlarge": 4, "m6i.2xlarge": 8, "m6i.4xlarge": 16,
    "m7i.large": 2, "m7i.xlarge": 4, "m7i.2xlarge": 8, "m7i.4xlarge": 16,
    "r5.large": 2, "r5.xlarge": 4, "r5.2xlarge": 8, "r5.4xlarge": 16,
    "c5.large": 2, "c5.xlarge": 4, "c5.2xlarge": 8, "c5.4xlarge": 16,
}
categories = topo.get("cluster_categories", {})
for cat in sorted(categories.keys()):
    cfg = categories[cat]
    itype = cfg.get("instance_type", "m5.xlarge")
    replicas = cfg.get("initial_replicas", 2)
    max_rep = cfg.get("autoscaling", {}).get("max_replicas", replicas)
    vcpus = vcpu_map.get(itype, 0)
    print(f"  {cat}: {itype} ({vcpus} vCPUs) x {replicas}-{max_rep} replicas = {vcpus*replicas}-{vcpus*max_rep} vCPUs per account")
PYEOF
)
  echo "$VCPU_REQS_DISPLAY"
fi

###############################################################################
# 9. Infrastructure State (provision mode)
###############################################################################
if [ "$MODE" = "provision" ] || [ "$MODE" = "all" ]; then
  section "Infrastructure State"

  INFRA_STATE="${GROUP_VARS}/infra_state.yml"
  if [ -f "$INFRA_STATE" ]; then
    SUBNET_COUNT=$(python3 -c "
import yaml
with open('${INFRA_STATE}') as f:
    state = yaml.safe_load(f) or {}
    state = state.get('infra_state', state)
count = sum(1 for v in state.values() if isinstance(v, dict) and v.get('private_subnet_ids'))
print(count)
" 2>/dev/null || echo "0")
    pass "infra_state.yml exists (${SUBNET_COUNT} accounts with subnet IDs)"
  else
    if [ "$MODE" = "provision" ]; then
      warn "infra_state.yml not found — run 'make setup-infra' first, or provide subnet_ids in credentials"
    else
      info "infra_state.yml not found — will be created by 'make setup-infra'"
    fi
  fi

  HAS_MANUAL_SUBNETS=$(python3 -c "
import yaml, os
path = os.path.join('${SECRETS_DIR}', 'cluster-credentials.yml')
with open(path) as f:
    data = yaml.safe_load(f)
creds = data.get('cluster_credentials', {})
count = sum(1 for c in creds.values() if c.get('subnet_ids') and 'REPLACE_ME' not in c.get('subnet_ids', ''))
print(count)
" 2>/dev/null || echo "0")

  if [ "$HAS_MANUAL_SUBNETS" -gt 0 ]; then
    info "${HAS_MANUAL_SUBNETS} accounts have manually-specified subnet_ids in credentials"
  fi
fi

###############################################################################
# Summary
###############################################################################
echo ""
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo -e "  ${GREEN}Passed: ${PASS}${NC}   ${RED}Failed: ${FAIL}${NC}   ${YELLOW}Warnings: ${WARN}${NC}"
echo -e "${BOLD}══════════════════════════════════════════${NC}"

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo -e "${RED}${BOLD}Errors that must be fixed:${NC}"
  for err in "${ERRORS[@]}"; do
    echo -e "  ${RED}•${NC} $err"
  done
fi

if [ "$WARN" -gt 0 ]; then
  echo ""
  echo -e "${YELLOW}${BOLD}Warnings (non-blocking):${NC}"
  for w in "${WARNINGS[@]}"; do
    echo -e "  ${YELLOW}•${NC} $w"
  done
fi

echo ""
if [ "$FAIL" -gt 0 ]; then
  echo -e "${RED}Preflight FAILED — fix the errors above before proceeding.${NC}"
  exit 1
else
  echo -e "${GREEN}Preflight PASSED — ready to proceed.${NC}"
  exit 0
fi
