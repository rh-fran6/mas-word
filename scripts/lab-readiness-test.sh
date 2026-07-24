#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
# MAS World 2026 — Lab Session Readiness Test
#
# Validates every component a student will interact with during the
# guided lab session, organized exercise-by-exercise in presentation
# order. Provides detailed diagnostics and troubleshooting commands
# on failure.
#
# Usage:
#   make lab-test CLUSTER=lab-seat-01
#   make lab-test-fleet
#
#   # Or directly:
#   bash scripts/lab-readiness-test.sh <cluster_id>
#   bash scripts/lab-readiness-test.sh --fleet
#   bash scripts/lab-readiness-test.sh --help
#
# Environment overrides (skip credential file parsing):
#   API_URL=https://api.xxx:6443 ADMIN_PASSWORD=xxx SEAT_NUMBER=01 \
#     bash scripts/lab-readiness-test.sh
# ═══════════════════════════════════════════════════════════════════════
set -uo pipefail

# ── Colors & Formatting ───────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
EXERCISE_RESULTS=()

pass() {
  echo -e "  ${GREEN}[PASS]${NC} $1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  local msg="$1"; shift
  echo -e "  ${RED}[FAIL]${NC} ${BOLD}${msg}${NC}"
  while [ $# -gt 0 ]; do
    case "$1" in
      Debug:*) echo -e "         ${DIM}$1${NC}" ;;
      *)       echo -e "         $1" ;;
    esac
    shift
  done
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

warn() {
  local msg="$1"; shift
  echo -e "  ${YELLOW}[WARN]${NC} ${msg}"
  while [ $# -gt 0 ]; do
    echo -e "         $1"
    shift
  done
  WARN_COUNT=$((WARN_COUNT + 1))
}

info() {
  echo -e "         ${CYAN}→${NC} $1"
}

section() {
  local exercise_num="$1"
  local title="$2"
  echo ""
  echo -e "  ${BOLD}── Exercise ${exercise_num}: ${title} ──${NC}"
  echo ""
}

record_exercise() {
  local name="$1"
  local before_pass="$2"
  local before_fail="$3"
  local before_warn="$4"
  local ex_pass=$((PASS_COUNT - before_pass))
  local ex_fail=$((FAIL_COUNT - before_fail))
  local ex_warn=$((WARN_COUNT - before_warn))
  local ex_total=$((ex_pass + ex_fail + ex_warn))
  local status="PASS"
  local detail=""
  if [ "$ex_fail" -gt 0 ]; then
    status="FAIL"
    detail=" — ${ex_fail} failed"
  elif [ "$ex_warn" -gt 0 ]; then
    status="WARN"
    detail=" — ${ex_warn} warning(s)"
  fi
  EXERCISE_RESULTS+=("$(printf "  %-42s %s (%d/%d)%s" "$name" "$status" "$ex_pass" "$ex_total" "$detail")")
}

show_help() {
  echo ""
  echo "  MAS World 2026 — Lab Session Readiness Test"
  echo "  ════════════════════════════════════════════"
  echo ""
  echo "  Usage:"
  echo "    $(basename "$0") <cluster_id>     Test a single cluster"
  echo "    $(basename "$0") --fleet          Test all enabled clusters"
  echo "    $(basename "$0") --help           Show this help"
  echo ""
  echo "  Via make:"
  echo "    make lab-test CLUSTER=lab-seat-01"
  echo "    make lab-test-fleet"
  echo ""
  echo "  Environment overrides:"
  echo "    API_URL          Cluster API URL (e.g. https://api.xxx:6443)"
  echo "    ADMIN_PASSWORD   cluster-admin password"
  echo "    SEAT_NUMBER      Seat number (e.g. 01)"
  echo ""
  exit 0
}

# ── Credential Loading ────────────────────────────────────────────────
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
CRED_FILE="${PROJECT_ROOT}/secrets/cluster-credentials.yml"

# Capture user-provided env overrides before any function call overwrites them
_ENV_API_URL="${API_URL:-}"
_ENV_ADMIN_PASSWORD="${ADMIN_PASSWORD:-}"
_ENV_SEAT_NUMBER="${SEAT_NUMBER:-}"
_ENV_CLUSTER_PURPOSE="${CLUSTER_PURPOSE:-}"

load_cluster_creds() {
  local cluster_id="$1"

  # Reset globals from any previous call
  API_URL=""
  ADMIN_PASSWORD=""
  SEAT_NUMBER=""
  CLUSTER_PURPOSE=""

  # Use env overrides if the user provided them at script startup
  if [ -n "$_ENV_API_URL" ] && [ -n "$_ENV_ADMIN_PASSWORD" ]; then
    API_URL="$_ENV_API_URL"
    ADMIN_PASSWORD="$_ENV_ADMIN_PASSWORD"
    SEAT_NUMBER="${_ENV_SEAT_NUMBER:-01}"
    CLUSTER_PURPOSE="${_ENV_CLUSTER_PURPOSE:-attendee}"
    return 0
  fi

  if [ ! -f "$CRED_FILE" ]; then
    echo -e "  ${RED}Error:${NC} Credential file not found: $CRED_FILE"
    echo "  Either create it or set API_URL + ADMIN_PASSWORD env vars."
    exit 1
  fi

  local in_cluster=false

  while IFS= read -r line; do
    if echo "$line" | grep -qE "^  ${cluster_id}:"; then
      in_cluster=true
      continue
    fi
    if $in_cluster; then
      if echo "$line" | grep -qE "^  [a-z]" && ! echo "$line" | grep -qE "^    "; then
        break
      fi
      local key val
      key=$(echo "$line" | sed -n 's/^    \([a-z_]*\):.*/\1/p')
      val=$(echo "$line" | sed -n 's/^    [a-z_]*: *"\{0,1\}\(.*\)"\{0,1\}$/\1/p' | sed 's/"$//')
      case "$key" in
        api_url)          API_URL="$val" ;;
        admin_password)   ADMIN_PASSWORD="$val" ;;
        seat_number)      SEAT_NUMBER="$val" ;;
        purpose)          CLUSTER_PURPOSE="$val" ;;
      esac
    fi
  done < "$CRED_FILE"

  if [ -z "$API_URL" ] || [ -z "$ADMIN_PASSWORD" ]; then
    echo -e "  ${RED}Error:${NC} Could not load api_url/admin_password for cluster '$cluster_id'"
    echo "  Check that '$cluster_id' exists in $CRED_FILE with api_url and admin_password set."
    exit 1
  fi

  SEAT_NUMBER="${SEAT_NUMBER:-01}"
  CLUSTER_PURPOSE="${CLUSTER_PURPOSE:-attendee}"
}

list_enabled_clusters() {
  if [ ! -f "$CRED_FILE" ]; then
    echo -e "  ${RED}Error:${NC} Credential file not found: $CRED_FILE"
    exit 1
  fi
  grep -E '^  [a-z].*:$' "$CRED_FILE" | sed 's/://;s/^ *//'
}

# ── Cluster Authentication ────────────────────────────────────────────
login_cluster() {
  if ! command -v oc &>/dev/null; then
    echo -e "  ${RED}Error:${NC} 'oc' CLI not found. Install it from https://mirror.openshift.com/pub/openshift-v4/clients/ocp/"
    exit 1
  fi

  # ACCEPTED RISK: password passed as CLI arg (visible in ps aux). oc CLI has no stdin alternative.
  # This script runs only on the operator's secured workstation; exposure window is milliseconds.
  if ! oc login "$API_URL" -u cluster-admin -p "$ADMIN_PASSWORD" --insecure-skip-tls-verify=true &>/dev/null; then
    echo -e "  ${RED}Error:${NC} Failed to log in to ${API_URL}"
    echo "  Verify the cluster is running and the admin password is correct."
    echo "  Try manually: oc login $API_URL -u cluster-admin -p <password>"
    exit 1
  fi
}

# ── Get cluster domain ────────────────────────────────────────────────
get_cluster_domain() {
  oc get ingresses.config.openshift.io cluster -o jsonpath='{.spec.domain}' 2>/dev/null || echo "unknown"
}

# ═══════════════════════════════════════════════════════════════════════
# EXERCISE CHECKS
# ═══════════════════════════════════════════════════════════════════════

run_exercise_1() {
  local bp=$PASS_COUNT bf=$FAIL_COUNT bw=$WARN_COUNT
  section "1" "Access & Readiness"
  local domain
  domain=$(get_cluster_domain)
  local padded_seat
  padded_seat=$(printf "%02d" "$SEAT_NUMBER")
  local student_user="user${padded_seat}"

  # 1.1 API reachable
  if oc whoami &>/dev/null; then
    pass "OpenShift API reachable (logged in as $(oc whoami))"
  else
    fail "OpenShift API unreachable" \
         "Debug: oc login $API_URL -u cluster-admin -p <password>"
  fi

  # 1.2 Console route
  local console_url
  console_url=$(oc get route console -n openshift-console -o jsonpath='{.spec.host}' 2>/dev/null)
  if [ -n "$console_url" ]; then
    pass "OpenShift Console route exists"
    info "https://${console_url}"
  else
    fail "OpenShift Console route not found" \
         "Expected: route 'console' in namespace 'openshift-console'" \
         "Debug: oc get routes -n openshift-console" \
         "Debug: oc get pods -n openshift-console"
  fi

  # 1.3 MAS Navigator URL
  local mas_url="https://admin.inst1.apps.${domain}"
  local mas_status
  mas_status=$(oc get suite inst1 -n mas-inst1-core -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
  if [ "$mas_status" = "True" ]; then
    pass "MAS Core Suite CR is Ready"
    info "${mas_url}"
  else
    local actual_conditions
    actual_conditions=$(oc get suite inst1 -n mas-inst1-core -o jsonpath='{range .status.conditions[*]}{.type}={.status} {end}' 2>/dev/null)
    fail "MAS Core Suite CR not Ready" \
         "Actual: ${actual_conditions:-resource not found}" \
         "Expected: Ready=True" \
         "Debug: oc get suite -n mas-inst1-core -o yaml" \
         "Debug: oc get pods -n mas-inst1-core --field-selector=status.phase!=Running"
  fi

  # 1.4 Manage workspace Ready
  local manage_status
  manage_status=$(oc get manageworkspace -n mas-inst1-manage -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
  if [ "$manage_status" = "True" ]; then
    pass "Maximo Manage workspace is Ready"
  else
    local manage_conditions
    manage_conditions=$(oc get manageworkspace -n mas-inst1-manage -o jsonpath='{range .items[0].status.conditions[*]}{.type}={.status} {end}' 2>/dev/null)
    fail "Maximo Manage workspace not Ready" \
         "Actual: ${manage_conditions:-resource not found}" \
         "Expected: Ready=True" \
         "Debug: oc get manageworkspace -n mas-inst1-manage -o yaml" \
         "Debug: oc get pods -n mas-inst1-manage --field-selector=status.phase!=Running"
  fi

  # 1.5 htpasswd secret
  if oc get secret masworld-htpasswd-secret -n openshift-config &>/dev/null; then
    pass "htpasswd authentication secret exists"
  else
    fail "htpasswd authentication secret missing" \
         "Expected: secret 'masworld-htpasswd-secret' in openshift-config" \
         "Debug: oc get secrets -n openshift-config | grep htpasswd" \
         "Debug: oc get oauth cluster -o yaml"
  fi

  # 1.6 Student namespace
  if oc get namespace "student-${padded_seat}" &>/dev/null; then
    pass "Student namespace student-${padded_seat} exists"
  else
    fail "Student namespace student-${padded_seat} missing" \
         "Debug: oc get namespaces | grep student"
  fi

  # 1.7 Student RoleBinding
  local rb_exists
  rb_exists=$(oc get rolebinding "${student_user}-admin" -n "student-${padded_seat}" -o name 2>/dev/null)
  if [ -n "$rb_exists" ]; then
    pass "Student ${student_user} has admin RoleBinding in student-${padded_seat}"
  else
    fail "Student ${student_user} RoleBinding missing" \
         "Expected: rolebinding/${student_user}-admin in student-${padded_seat}" \
         "Debug: oc get rolebindings -n student-${padded_seat}"
  fi

  # 1.8 Nodes Ready
  local total_nodes ready_nodes
  total_nodes=$(oc get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
  ready_nodes=$(oc get nodes --no-headers 2>/dev/null | grep -c ' Ready' || true)
  if [ "$total_nodes" -gt 0 ] && [ "$ready_nodes" -eq "$total_nodes" ]; then
    pass "All nodes Ready (${ready_nodes}/${total_nodes})"
  elif [ "$total_nodes" -eq 0 ]; then
    fail "No nodes found" \
         "Debug: oc get nodes -o wide"
  else
    fail "Not all nodes Ready (${ready_nodes}/${total_nodes})" \
         "Debug: oc get nodes -o wide" \
         "Debug: oc describe nodes | grep -A5 Conditions"
  fi

  record_exercise "Exercise 1: Access & Readiness" "$bp" "$bf" "$bw"
}

run_exercise_2() {
  local bp=$PASS_COUNT bf=$FAIL_COUNT bw=$WARN_COUNT
  section "2" "Navigation & Search"

  # 2.1 MAS core namespace
  if oc get namespace mas-inst1-core &>/dev/null; then
    pass "Namespace mas-inst1-core exists"
  else
    fail "Namespace mas-inst1-core missing" \
         "Debug: oc get namespaces | grep mas"
  fi

  # 2.2 MAS manage namespace
  if oc get namespace mas-inst1-manage &>/dev/null; then
    pass "Namespace mas-inst1-manage exists"
  else
    fail "Namespace mas-inst1-manage missing" \
         "Debug: oc get namespaces | grep mas"
  fi

  # 2.3 CSVs in mas-inst1-core
  local csv_count
  csv_count=$(oc get csv -n mas-inst1-core --no-headers 2>/dev/null | wc -l | tr -d ' ')
  if [ "$csv_count" -gt 0 ]; then
    pass "MAS operators installed (${csv_count} CSVs in mas-inst1-core)"
  else
    fail "No CSVs found in mas-inst1-core" \
         "Expected: at least 1 ClusterServiceVersion" \
         "Debug: oc get csv -n mas-inst1-core" \
         "Debug: oc get subscriptions -n mas-inst1-core"
  fi

  # 2.4 Subscriptions
  local sub_count
  sub_count=$(oc get subscriptions -n mas-inst1-core --no-headers 2>/dev/null | wc -l | tr -d ' ')
  if [ "$sub_count" -gt 0 ]; then
    pass "MAS subscriptions active (${sub_count} in mas-inst1-core)"
  else
    fail "No subscriptions found in mas-inst1-core" \
         "Debug: oc get subscriptions -n mas-inst1-core -o yaml"
  fi

  record_exercise "Exercise 2: Navigation & Search" "$bp" "$bf" "$bw"
}

run_exercise_3() {
  local bp=$PASS_COUNT bf=$FAIL_COUNT bw=$WARN_COUNT
  section "3" "ACM Fleet Management"

  # 3.1 Event ConfigMap
  local event_val
  event_val=$(oc get configmap masworld-event-marker -n masworld-system -o jsonpath='{.data.event}' 2>/dev/null)
  if [ "$event_val" = "mas-world-2026" ]; then
    pass "Event ConfigMap masworld-event-marker present and correct"
    info "event=${event_val}"
  elif [ -n "$event_val" ]; then
    fail "Event ConfigMap has wrong value" \
         "Actual: event=${event_val}" \
         "Expected: event=mas-world-2026" \
         "Debug: oc get configmap masworld-event-marker -n masworld-system -o yaml"
  else
    fail "Event ConfigMap masworld-event-marker not found" \
         "Expected: ConfigMap in namespace masworld-system" \
         "Debug: oc get configmaps -n masworld-system" \
         "Debug: oc get namespace masworld-system"
  fi

  # 3.2 masworld-system namespace
  if oc get namespace masworld-system &>/dev/null; then
    pass "Event namespace masworld-system exists"
  else
    fail "Event namespace masworld-system missing" \
         "Debug: oc get namespaces | grep masworld"
  fi

  record_exercise "Exercise 3: ACM Fleet Management" "$bp" "$bf" "$bw"
}

run_exercise_4() {
  local bp=$PASS_COUNT bf=$FAIL_COUNT bw=$WARN_COUNT
  section "4" "Updates"

  # 4.1 ClusterVersion
  local ocp_version
  ocp_version=$(oc get clusterversion version -o jsonpath='{.status.desired.version}' 2>/dev/null)
  if [ -n "$ocp_version" ]; then
    pass "OpenShift version: ${ocp_version}"
  else
    fail "ClusterVersion not accessible" \
         "Debug: oc get clusterversion version -o yaml"
  fi

  # 4.2 Update history
  local history_count
  history_count=$(oc get clusterversion version -o jsonpath='{.status.history}' 2>/dev/null | grep -c '"version"' || true)
  if [ "$history_count" -gt 0 ]; then
    pass "ClusterVersion has update history (${history_count} entries)"
  else
    warn "No update history found" \
         "This may be normal for new clusters"
  fi

  # 4.3 PackageManifest ibm-mas
  local pm_exists
  pm_exists=$(oc get packagemanifest ibm-mas -n openshift-marketplace -o name 2>/dev/null)
  if [ -n "$pm_exists" ]; then
    local channels
    channels=$(oc get packagemanifest ibm-mas -n openshift-marketplace -o jsonpath='{range .status.channels[*]}{.name}{" "}{end}' 2>/dev/null)
    pass "PackageManifest ibm-mas available"
    info "Channels: ${channels}"
  else
    warn "PackageManifest ibm-mas not found in openshift-marketplace" \
         "Students can still view existing subscriptions and CSVs" \
         "Debug: oc get packagemanifests -n openshift-marketplace | grep ibm"
  fi

  # 4.4 InstallPlans
  local ip_count
  ip_count=$(oc get installplan -n mas-inst1-core --no-headers 2>/dev/null | wc -l | tr -d ' ')
  if [ "$ip_count" -gt 0 ]; then
    pass "InstallPlans found in mas-inst1-core (${ip_count})"
  else
    warn "No InstallPlans in mas-inst1-core" \
         "This is normal if no updates are pending"
  fi

  record_exercise "Exercise 4: Updates" "$bp" "$bf" "$bw"
}

run_exercise_5() {
  local bp=$PASS_COUNT bf=$FAIL_COUNT bw=$WARN_COUNT
  section "5" "Observability & Logging"
  local domain
  domain=$(get_cluster_domain)
  local padded_seat
  padded_seat=$(printf "%02d" "$SEAT_NUMBER")

  # 5.1 Logging operator CSVs
  local logging_csvs
  logging_csvs=$(oc get csv -n openshift-logging --no-headers 2>/dev/null)
  local csv_succeeded
  csv_succeeded=$(echo "$logging_csvs" | grep -c "Succeeded" || true)
  local csv_total
  csv_total=$(echo "$logging_csvs" | grep -c "." || true)
  if [ "$csv_succeeded" -gt 0 ] && [ "$csv_succeeded" -eq "$csv_total" ]; then
    pass "Logging operators ready (${csv_succeeded} CSVs Succeeded)"
  elif [ "$csv_total" -gt 0 ]; then
    fail "Logging operators not all Succeeded (${csv_succeeded}/${csv_total})" \
         "Debug: oc get csv -n openshift-logging" \
         "Debug: oc get pods -n openshift-logging"
  else
    fail "No logging operator CSVs found" \
         "Expected: OpenShift Logging + Loki Operator in openshift-logging" \
         "Debug: oc get subscriptions -n openshift-logging"
  fi

  # 5.2 LokiStack Ready
  local loki_status
  loki_status=$(oc get lokistack -n openshift-logging -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
  if [ "$loki_status" = "True" ]; then
    pass "LokiStack CR is Ready"
  else
    local loki_conditions
    loki_conditions=$(oc get lokistack -n openshift-logging -o jsonpath='{range .items[0].status.conditions[*]}{.type}={.status}:{.reason} {end}' 2>/dev/null)
    fail "LokiStack CR not Ready" \
         "Actual: ${loki_conditions:-resource not found}" \
         "Expected: Ready=True" \
         "Debug: oc get lokistack -n openshift-logging -o yaml" \
         "Debug: oc get pods -n openshift-logging -l app.kubernetes.io/name=lokistack"
  fi

  # 5.3 ClusterLogForwarder Ready
  local clf_status
  clf_status=$(oc get clusterlogforwarder -n openshift-logging -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
  if [ "$clf_status" = "True" ]; then
    pass "ClusterLogForwarder CR is Ready"
  else
    local clf_conditions
    clf_conditions=$(oc get clusterlogforwarder -n openshift-logging -o jsonpath='{range .items[0].status.conditions[*]}{.type}={.status}:{.reason} {end}' 2>/dev/null)
    fail "ClusterLogForwarder CR not Ready" \
         "Actual: ${clf_conditions:-resource not found}" \
         "Expected: Ready=True" \
         "Debug: oc get clusterlogforwarder -n openshift-logging -o yaml" \
         "Debug: oc get pods -n openshift-logging -l app.kubernetes.io/component=collector"
  fi

  # 5.4 S3 storage secret
  local s3_secret
  s3_secret=$(oc get secret -n openshift-logging -l masworld.io/component=loki-s3 --no-headers 2>/dev/null | head -1)
  if [ -n "$s3_secret" ]; then
    pass "S3 storage secret exists for Loki"
  else
    fail "S3 storage secret missing for Loki" \
         "Expected: secret with label masworld.io/component=loki-s3 in openshift-logging" \
         "Debug: oc get secrets -n openshift-logging"
  fi

  # 5.5 Loki gateway service
  if oc get service logging-loki-gateway-http -n openshift-logging &>/dev/null; then
    pass "Loki gateway service exists"
  else
    fail "Loki gateway service missing" \
         "Expected: service/logging-loki-gateway-http in openshift-logging" \
         "Debug: oc get services -n openshift-logging"
  fi

  # 5.6 Grafana route
  local grafana_host
  grafana_host=$(oc get route -n openshift-logging -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].spec.host}' 2>/dev/null)
  if [ -z "$grafana_host" ]; then
    grafana_host=$(oc get route grafana -n openshift-logging -o jsonpath='{.spec.host}' 2>/dev/null)
  fi
  if [ -n "$grafana_host" ]; then
    pass "Grafana route exists"
    info "https://${grafana_host}"
  else
    warn "Grafana route not found in openshift-logging" \
         "Students may not be able to query logs via the Grafana UI" \
         "Debug: oc get routes -n openshift-logging"
  fi

  # 5.7 Student namespace for log-test pod
  if oc get namespace "student-${padded_seat}" &>/dev/null; then
    pass "Student namespace student-${padded_seat} ready for log exercises"
  else
    fail "Student namespace student-${padded_seat} missing (needed for log-test pod)" \
         "Debug: oc get namespaces | grep student"
  fi

  record_exercise "Exercise 5: Observability & Logging" "$bp" "$bf" "$bw"
}

run_exercise_6() {
  local bp=$PASS_COUNT bf=$FAIL_COUNT bw=$WARN_COUNT
  section "6" "Identity Provider Integration"
  local padded_seat
  padded_seat=$(printf "%02d" "$SEAT_NUMBER")
  local student_user="user${padded_seat}"

  # 6.1 OAuth has htpasswd provider
  local htpasswd_provider
  htpasswd_provider=$(oc get oauth cluster -o jsonpath='{.spec.identityProviders[?(@.type=="HTPasswd")].name}' 2>/dev/null)
  if [ -n "$htpasswd_provider" ]; then
    pass "OAuth has HTPasswd identity provider (${htpasswd_provider})"
  else
    fail "OAuth missing HTPasswd identity provider" \
         "Expected: identityProvider of type HTPasswd" \
         "Debug: oc get oauth cluster -o yaml"
  fi

  # 6.2 OAuth has masworld-keycloak (OpenID) provider
  local oidc_provider
  oidc_provider=$(oc get oauth cluster -o jsonpath='{.spec.identityProviders[?(@.type=="OpenID")].name}' 2>/dev/null)
  if echo "$oidc_provider" | grep -q "masworld-keycloak"; then
    pass "OAuth has masworld-keycloak OpenID provider"
  else
    warn "OAuth missing masworld-keycloak OpenID provider" \
         "Actual providers: $(oc get oauth cluster -o jsonpath='{range .spec.identityProviders[*]}{.name}({.type}) {end}' 2>/dev/null)" \
         "Students can still observe the HTPasswd provider" \
         "Debug: oc get oauth cluster -o yaml"
  fi

  # 6.3 Keycloak CR Ready
  local kc_status
  kc_status=$(oc get keycloak -n masworld-keycloak -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
  if [ "$kc_status" = "True" ]; then
    pass "Keycloak CR is Ready"
  else
    local kc_conditions
    kc_conditions=$(oc get keycloak -n masworld-keycloak -o jsonpath='{range .items[0].status.conditions[*]}{.type}={.status} {end}' 2>/dev/null)
    fail "Keycloak CR not Ready" \
         "Actual: ${kc_conditions:-resource not found}" \
         "Expected: Ready=True" \
         "Debug: oc get keycloak -n masworld-keycloak -o yaml" \
         "Debug: oc get pods -n masworld-keycloak"
  fi

  # 6.4 Keycloak route
  local kc_route
  kc_route=$(oc get route -n masworld-keycloak -o jsonpath='{.items[0].spec.host}' 2>/dev/null)
  if [ -n "$kc_route" ]; then
    pass "Keycloak route exists"
    info "https://${kc_route}"
  else
    fail "Keycloak route missing" \
         "Debug: oc get routes -n masworld-keycloak" \
         "Debug: oc get pods -n masworld-keycloak"
  fi

  # 6.5 OpenLDAP pod Running
  local ldap_phase
  ldap_phase=$(oc get pod -l app=openldap -n masworld-keycloak -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
  if [ "$ldap_phase" = "Running" ]; then
    pass "OpenLDAP pod is Running"
  else
    fail "OpenLDAP pod not Running" \
         "Actual phase: ${ldap_phase:-pod not found}" \
         "Expected: Running" \
         "Debug: oc get pods -n masworld-keycloak -l app=openldap -o wide" \
         "Debug: oc logs -n masworld-keycloak -l app=openldap --tail=20"
  fi

  # 6.6 LDAP users (4 expected)
  local ldap_user_count=0
  if [ "$ldap_phase" = "Running" ]; then
    local ldap_admin_pw
    ldap_admin_pw=$(oc get secret openldap-admin-secret -n masworld-keycloak -o jsonpath='{.data.LDAP_ADMIN_PASSWORD}' 2>/dev/null | base64 -d 2>/dev/null)
    if [ -n "$ldap_admin_pw" ]; then
      ldap_user_count=$(oc exec -n masworld-keycloak deploy/openldap -- \
        ldapsearch -x -H ldap://localhost:1389 \
        -D "cn=admin,dc=masworld,dc=example,dc=com" \
        -w "$ldap_admin_pw" \
        -b "ou=users,dc=masworld,dc=example,dc=com" \
        "(objectClass=inetOrgPerson)" dn 2>/dev/null | grep -c "^dn:" || true)
    fi
  fi
  if [ "$ldap_user_count" -eq 4 ]; then
    pass "LDAP directory has 4 demo users"
    info "alice.engineer, bob.technician, carol.planner, dave.supervisor"
  elif [ "$ldap_user_count" -gt 0 ]; then
    warn "LDAP directory has ${ldap_user_count} users (expected 4)" \
         "Debug: oc exec -n masworld-keycloak deploy/openldap -- ldapsearch -x -H ldap://localhost:1389 -b ou=users,dc=masworld,dc=example,dc=com '(objectClass=inetOrgPerson)' uid"
  else
    fail "LDAP directory unreachable or empty" \
         "Expected: 4 users in ou=users,dc=masworld,dc=example,dc=com" \
         "Debug: oc get pod -l app=openldap -n masworld-keycloak -o wide" \
         "Debug: oc get secret openldap-admin-secret -n masworld-keycloak"
  fi

  # 6.7 LDAP groups (2 expected)
  local ldap_group_count=0
  if [ "$ldap_phase" = "Running" ] && [ -n "${ldap_admin_pw:-}" ]; then
    ldap_group_count=$(oc exec -n masworld-keycloak deploy/openldap -- \
      ldapsearch -x -H ldap://localhost:1389 \
      -D "cn=admin,dc=masworld,dc=example,dc=com" \
      -w "$ldap_admin_pw" \
      -b "ou=groups,dc=masworld,dc=example,dc=com" \
      "(objectClass=groupOfNames)" dn 2>/dev/null | grep -c "^dn:" || true)
  fi
  if [ "$ldap_group_count" -eq 2 ]; then
    pass "LDAP directory has 2 demo groups"
    info "mas-admins (alice, dave), mas-users (bob, carol)"
  elif [ "$ldap_group_count" -gt 0 ]; then
    warn "LDAP directory has ${ldap_group_count} groups (expected 2)"
  else
    if [ "$ldap_phase" = "Running" ]; then
      warn "LDAP groups not found or unreachable"
    fi
  fi

  # 6.8 KeycloakRealmImport
  local realm_exists
  realm_exists=$(oc get keycloakrealmimport masworld-realm -n masworld-keycloak -o name 2>/dev/null)
  if [ -n "$realm_exists" ]; then
    pass "KeycloakRealmImport masworld-realm exists"
  else
    fail "KeycloakRealmImport masworld-realm missing" \
         "Debug: oc get keycloakrealmimport -n masworld-keycloak"
  fi

  # 6.9 OIDC client secret
  if oc get secret keycloak-oidc-client-secret -n openshift-config &>/dev/null; then
    pass "OIDC client secret exists in openshift-config"
  else
    fail "OIDC client secret missing" \
         "Expected: secret/keycloak-oidc-client-secret in openshift-config" \
         "Debug: oc get secrets -n openshift-config | grep keycloak"
  fi

  # 6.10 Student is NOT cluster-admin
  local is_cluster_admin
  is_cluster_admin=$(oc auth can-i create clusterrole --as="${student_user}" 2>/dev/null || true)
  if [ "$is_cluster_admin" = "no" ]; then
    pass "Student ${student_user} correctly denied cluster-admin"
  elif [ "$is_cluster_admin" = "yes" ]; then
    fail "Student ${student_user} has cluster-admin (SECURITY ISSUE)" \
         "Expected: students should NOT have cluster-admin" \
         "Debug: oc get clusterrolebinding | grep ${student_user}"
  else
    warn "Could not verify cluster-admin status for ${student_user}"
  fi

  record_exercise "Exercise 6: Identity Integration" "$bp" "$bf" "$bw"
}

run_hub_checks() {
  local bp=$PASS_COUNT bf=$FAIL_COUNT bw=$WARN_COUNT
  section "—" "ACM Hub Validation"

  # H.1 ACM namespace exists
  if oc get namespace open-cluster-management &>/dev/null; then
    pass "ACM namespace open-cluster-management exists"
  else
    fail "ACM namespace open-cluster-management missing" \
         "Expected: namespace created by ACM operator install" \
         "Debug: oc get namespaces | grep cluster-management" \
         "Debug: oc get csv -A | grep advanced-cluster-management"
  fi

  # H.2 MultiClusterHub CR Ready
  local mch_status
  mch_status=$(oc get multiclusterhub -n open-cluster-management -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
  if [ "$mch_status" = "Running" ]; then
    pass "MultiClusterHub is Running"
  else
    local mch_conditions
    mch_conditions=$(oc get multiclusterhub -n open-cluster-management -o jsonpath='{range .items[0].status.conditions[*]}{.type}={.status} {end}' 2>/dev/null)
    fail "MultiClusterHub not Running" \
         "Actual phase: ${mch_status:-resource not found}" \
         "Conditions: ${mch_conditions:-none}" \
         "Expected: phase=Running" \
         "Debug: oc get multiclusterhub -n open-cluster-management -o yaml" \
         "Debug: oc get pods -n open-cluster-management --field-selector=status.phase!=Running"
  fi

  # H.3 ACM operator CSV Succeeded
  local acm_csv_status
  acm_csv_status=$(oc get csv -n open-cluster-management --no-headers 2>/dev/null | grep -i 'advanced-cluster-management' | head -1)
  if echo "$acm_csv_status" | grep -q "Succeeded"; then
    local acm_csv_name
    acm_csv_name=$(echo "$acm_csv_status" | awk '{print $1}')
    pass "ACM operator CSV Succeeded (${acm_csv_name})"
  elif [ -n "$acm_csv_status" ]; then
    fail "ACM operator CSV not Succeeded" \
         "Actual: $(echo "$acm_csv_status" | awk '{print $1, $NF}')" \
         "Debug: oc get csv -n open-cluster-management"
  else
    fail "ACM operator CSV not found" \
         "Expected: advanced-cluster-management CSV in open-cluster-management" \
         "Debug: oc get csv -n open-cluster-management" \
         "Debug: oc get subscriptions -n open-cluster-management"
  fi

  # H.4 ManagedClusterSet for the workshop
  local mcs_exists
  mcs_exists=$(oc get managedclusterset mas-world-2026 -o name 2>/dev/null)
  if [ -n "$mcs_exists" ]; then
    pass "ManagedClusterSet mas-world-2026 exists"
  else
    warn "ManagedClusterSet mas-world-2026 not found" \
         "This is created when attendee clusters register with the hub" \
         "Debug: oc get managedclusterset"
  fi

  # H.5 Count registered ManagedClusters
  local mc_count
  mc_count=$(oc get managedcluster --no-headers 2>/dev/null | wc -l | tr -d ' ')
  if [ "$mc_count" -gt 0 ]; then
    local mc_available
    mc_available=$(oc get managedcluster --no-headers 2>/dev/null | grep -c 'True' || true)
    pass "Registered ManagedClusters: ${mc_count} (${mc_available} available)"
  else
    warn "No ManagedClusters registered yet" \
         "Clusters register when you run: make mas-prepare-fleet" \
         "Debug: oc get managedcluster -o wide"
  fi

  # H.6 ACM hub pods healthy
  local acm_total acm_running
  acm_total=$(oc get pods -n open-cluster-management --no-headers 2>/dev/null | wc -l | tr -d ' ')
  acm_running=$(oc get pods -n open-cluster-management --no-headers --field-selector=status.phase=Running 2>/dev/null | wc -l | tr -d ' ')
  if [ "$acm_total" -gt 0 ] && [ "$acm_running" -eq "$acm_total" ]; then
    pass "All ACM hub pods Running (${acm_running}/${acm_total})"
  elif [ "$acm_total" -gt 0 ]; then
    fail "Not all ACM hub pods Running (${acm_running}/${acm_total})" \
         "Debug: oc get pods -n open-cluster-management --field-selector=status.phase!=Running" \
         "Debug: oc get pods -n open-cluster-management -o wide"
  else
    fail "No pods found in open-cluster-management" \
         "Debug: oc get pods -n open-cluster-management"
  fi

  record_exercise "ACM Hub Validation" "$bp" "$bf" "$bw"
}

run_exercise_extra() {
  local bp=$PASS_COUNT bf=$FAIL_COUNT bw=$WARN_COUNT
  section "—" "Workshop Infrastructure"
  local padded_seat
  padded_seat=$(printf "%02d" "$SEAT_NUMBER")

  # Showroom pod
  local showroom_phase
  showroom_phase=$(oc get pod -l app.kubernetes.io/name=showroom -n showroom -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
  if [ "$showroom_phase" = "Running" ]; then
    pass "Showroom pod is Running"
  else
    fail "Showroom pod not Running" \
         "Actual: ${showroom_phase:-not found}" \
         "Debug: oc get pods -n showroom" \
         "Debug: oc logs -n showroom -l app.kubernetes.io/name=showroom --tail=20"
  fi

  # Showroom route
  local showroom_host
  showroom_host=$(oc get route -n showroom -l app.kubernetes.io/name=showroom -o jsonpath='{.items[0].spec.host}' 2>/dev/null)
  if [ -n "$showroom_host" ]; then
    pass "Showroom route accessible"
    info "https://${showroom_host}"
  else
    fail "Showroom route missing" \
         "Debug: oc get routes -n showroom"
  fi

  # Db2 pod
  local db2_phase
  db2_phase=$(oc get pod -l app=db2 -n mas-inst1-manage -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
  if [ -z "$db2_phase" ]; then
    db2_phase=$(oc get pod -l app=db2 -n db2 -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
  fi
  if [ "$db2_phase" = "Running" ]; then
    pass "Db2 database pod is Running"
  else
    warn "Db2 pod not confirmed Running (phase: ${db2_phase:-not found})" \
         "Manage may still work if Db2 is in a different namespace" \
         "Debug: oc get pods -A -l app=db2"
  fi

  # Exercise workloads namespace
  if oc get namespace masworld-exercises &>/dev/null; then
    pass "Exercise workloads namespace exists"
  else
    warn "Namespace masworld-exercises missing" \
         "Log-generator pods may not be deployed yet"
  fi

  # Log-generator pod for this seat
  local gen_phase
  gen_phase=$(oc get pod -l "app=log-generator" -n masworld-exercises -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
  if [ "$gen_phase" = "Running" ]; then
    pass "Log-generator pod running in masworld-exercises"
  elif [ -n "$gen_phase" ]; then
    warn "Log-generator pod phase: ${gen_phase}" \
         "Debug: oc get pods -n masworld-exercises -l app=log-generator"
  else
    warn "No log-generator pod found in masworld-exercises" \
         "Sample workloads may not be deployed yet"
  fi

  record_exercise "Workshop Infrastructure" "$bp" "$bf" "$bw"
}

# ═══════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════

print_summary() {
  local cluster_id="${1:-unknown}"
  local _total=$((PASS_COUNT + FAIL_COUNT + WARN_COUNT))
  local verdict="READY"
  local verdict_color="${GREEN}"

  if [ "$FAIL_COUNT" -gt 0 ]; then
    verdict="NOT READY"
    verdict_color="${RED}"
  elif [ "$WARN_COUNT" -gt 0 ]; then
    verdict="READY WITH WARNINGS"
    verdict_color="${YELLOW}"
  fi

  echo ""
  echo "  ═══════════════════════════════════════════════════════════════"
  echo -e "  ${BOLD}Lab Readiness Summary — ${cluster_id}${NC}"
  echo "  ═══════════════════════════════════════════════════════════════"
  for result in "${EXERCISE_RESULTS[@]}"; do
    local status_word
    status_word=$(echo "$result" | grep -oE '(PASS|FAIL|WARN)' | head -1)
    case "$status_word" in
      PASS) echo -e "${GREEN}${result}${NC}" ;;
      FAIL) echo -e "${RED}${result}${NC}" ;;
      WARN) echo -e "${YELLOW}${result}${NC}" ;;
      *)    echo "$result" ;;
    esac
  done
  echo "  ─────────────────────────────────────────────────────────────"
  echo -e "  Total: ${GREEN}${PASS_COUNT} passed${NC}, ${RED}${FAIL_COUNT} failed${NC}, ${YELLOW}${WARN_COUNT} warnings${NC}"
  echo -e "  Verdict: ${verdict_color}${BOLD}${verdict}${NC}"
  echo "  ═══════════════════════════════════════════════════════════════"
  echo ""
}

# ═══════════════════════════════════════════════════════════════════════
# SINGLE CLUSTER TEST
# ═══════════════════════════════════════════════════════════════════════

run_single_cluster() {
  local cluster_id="$1"

  load_cluster_creds "$cluster_id"

  local padded_seat
  padded_seat=$(printf "%02d" "$SEAT_NUMBER")

  echo ""
  echo "  ═══════════════════════════════════════════════════════════════"
  echo -e "  ${BOLD}MAS World 2026 — Lab Session Readiness Test${NC}"
  echo -e "  Cluster: ${CYAN}${cluster_id}${NC}  |  Seat: ${CYAN}${padded_seat}${NC}  |  Purpose: ${CYAN}${CLUSTER_PURPOSE}${NC}"
  echo "  ═══════════════════════════════════════════════════════════════"

  login_cluster

  if [ "$CLUSTER_PURPOSE" = "hub" ]; then
    run_hub_checks
    print_summary "$cluster_id"
    return 0
  fi

  run_exercise_1
  run_exercise_2
  run_exercise_3
  run_exercise_4
  run_exercise_5
  run_exercise_6
  run_exercise_extra

  print_summary "$cluster_id"
}

# ═══════════════════════════════════════════════════════════════════════
# FLEET TEST
# ═══════════════════════════════════════════════════════════════════════

run_fleet() {
  echo ""
  echo "  ═══════════════════════════════════════════════════════════════"
  echo -e "  ${BOLD}MAS World 2026 — Fleet Lab Readiness Test${NC}"
  echo "  ═══════════════════════════════════════════════════════════════"
  echo ""

  local clusters
  clusters=$(list_enabled_clusters)
  local fleet_results=()
  local total_clusters=0
  local passed_clusters=0
  local failed_clusters=0

  for cluster_id in $clusters; do
    PASS_COUNT=0
    FAIL_COUNT=0
    WARN_COUNT=0
    EXERCISE_RESULTS=()

    run_single_cluster "$cluster_id" || true
    total_clusters=$((total_clusters + 1))

    if [ "$FAIL_COUNT" -eq 0 ] && [ "$WARN_COUNT" -eq 0 ]; then
      fleet_results+=("$(printf "  %-25s ${GREEN}READY${NC}" "$cluster_id")")
      passed_clusters=$((passed_clusters + 1))
    elif [ "$FAIL_COUNT" -eq 0 ]; then
      fleet_results+=("$(printf "  %-25s ${YELLOW}READY WITH WARNINGS${NC}" "$cluster_id")")
      passed_clusters=$((passed_clusters + 1))
    else
      fleet_results+=("$(printf "  %-25s ${RED}NOT READY (${FAIL_COUNT} failures)${NC}" "$cluster_id")")
      failed_clusters=$((failed_clusters + 1))
    fi
  done

  echo ""
  echo "  ═══════════════════════════════════════════════════════════════"
  echo -e "  ${BOLD}Fleet Lab Readiness Summary${NC}"
  echo "  ═══════════════════════════════════════════════════════════════"
  for result in "${fleet_results[@]}"; do
    echo -e "$result"
  done
  echo "  ─────────────────────────────────────────────────────────────"
  echo -e "  ${total_clusters} clusters tested, ${GREEN}${passed_clusters} ready${NC}, ${RED}${failed_clusters} not ready${NC}"
  echo "  ═══════════════════════════════════════════════════════════════"
  if [ "$failed_clusters" -gt 0 ]; then
    echo ""
    echo -e "  ${YELLOW}Action required:${NC} Deploy Phase 2 applications before the workshop."
    echo "  Run: make mas-prepare-fleet"
  fi
  echo ""
}

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

case "${1:---help}" in
  --help|-h)   show_help ;;
  --fleet)     run_fleet ;;
  *)           run_single_cluster "$1" ;;
esac
