#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════════════
# MAS World 2026 — Interactive Deployment Wizard
# ═══════════════════════════════════════════════════════════════════════
# Guides the user through scenario selection, shows required parameters,
# and offers to run validation or full deployment.
#
# Usage:  make wizard
#         bash scripts/deploy-wizard.sh

# ── Colors (matches preflight.sh) ─────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ── Helpers ───────────────────────────────────────────────────────────
header() {
  echo ""
  echo -e "${BOLD}  $1${NC}"
  echo -e "${DIM}  $(printf '═%.0s' $(seq 1 ${#1}))${NC}"
  echo ""
}

info() { echo -e "  ${CYAN}$1${NC}"; }
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
err()  { echo -e "  ${RED}✗${NC} $1"; }

divider() {
  echo -e "  ${DIM}─────────────────────────────────────────────────────${NC}"
}

trap 'echo ""; echo -e "  ${YELLOW}Cancelled.${NC}"; echo ""; exit 0' INT

# ── Parameter Tables ──────────────────────────────────────────────────

show_params_greenfield() {
  echo -e "  ${BOLD}Scenario 1: Greenfield${NC}"
  echo -e "  ${DIM}Fresh AWS accounts — build VPC, ROSA clusters, and demo app${NC}"
  echo ""
  echo -e "  ${BOLD}Per-Cluster Credential Fields${NC}  (secrets/cluster-credentials.yml)"
  echo ""
  echo -e "  ┌──────────────────────────┬────────────┬──────────────────────────────┐"
  echo -e "  │ Field                    │ Status     │ Notes                        │"
  echo -e "  ├──────────────────────────┼────────────┼──────────────────────────────┤"
  echo -e "  │ aws_access_key_id        │ ${RED}REQUIRED${NC}   │ AWS IAM access key           │"
  echo -e "  │ aws_secret_access_key    │ ${RED}REQUIRED${NC}   │ AWS IAM secret key           │"
  echo -e "  │ aws_region               │ ${RED}REQUIRED${NC}   │ e.g. us-east-2               │"
  echo -e "  │ aws_account_id           │ ${DIM}Optional${NC}   │ Used for billing fallback    │"
  echo -e "  │ purpose                  │ ${RED}REQUIRED${NC}   │ facilitator/hub/attendee     │"
  echo -e "  │ seat_number              │ ${YELLOW}REQUIRED*${NC}  │ * attendee clusters only     │"
  echo -e "  │ enabled                  │ ${DIM}Optional${NC}   │ Defaults to true             │"
  echo -e "  │ subnet_ids               │ ${GREEN}Auto${NC}       │ Created by setup-infra       │"
  echo -e "  │ api_url                  │ ${GREEN}Auto${NC}       │ Populated after provisioning │"
  echo -e "  │ admin_password           │ ${GREEN}Auto${NC}       │ Populated after provisioning │"
  echo -e "  └──────────────────────────┴────────────┴──────────────────────────────┘"
  echo ""
  echo -e "  ${BOLD}Other Required Files${NC}"
  echo -e "  │ secrets/rosa-token.yml   │ ROSA offline access token"
  echo ""
  echo -e "  ${BOLD}Pipeline${NC}: AWS Infra → ROSA Enrollment → Cluster Provision"
  echo -e "           → Machinepool → Demo Application"
}

show_params_aws_ready() {
  echo -e "  ${BOLD}Scenario 2: AWS-Ready${NC}"
  echo -e "  ${DIM}AWS networking exists — provision ROSA clusters and demo app${NC}"
  echo ""
  echo -e "  ${BOLD}Per-Cluster Credential Fields${NC}  (secrets/cluster-credentials.yml)"
  echo ""
  echo -e "  ┌──────────────────────────┬────────────┬──────────────────────────────┐"
  echo -e "  │ Field                    │ Status     │ Notes                        │"
  echo -e "  ├──────────────────────────┼────────────┼──────────────────────────────┤"
  echo -e "  │ aws_access_key_id        │ ${RED}REQUIRED${NC}   │ AWS IAM access key           │"
  echo -e "  │ aws_secret_access_key    │ ${RED}REQUIRED${NC}   │ AWS IAM secret key           │"
  echo -e "  │ aws_region               │ ${RED}REQUIRED${NC}   │ e.g. us-east-2               │"
  echo -e "  │ aws_account_id           │ ${DIM}Optional${NC}   │ Used for billing fallback    │"
  echo -e "  │ purpose                  │ ${RED}REQUIRED${NC}   │ facilitator/hub/attendee     │"
  echo -e "  │ seat_number              │ ${YELLOW}REQUIRED*${NC}  │ * attendee clusters only     │"
  echo -e "  │ enabled                  │ ${DIM}Optional${NC}   │ Defaults to true             │"
  echo -e "  │ subnet_ids               │ ${RED}REQUIRED${NC}   │ From existing VPC subnets    │"
  echo -e "  │ api_url                  │ ${GREEN}Auto${NC}       │ Populated after provisioning │"
  echo -e "  │ admin_password           │ ${GREEN}Auto${NC}       │ Populated after provisioning │"
  echo -e "  └──────────────────────────┴────────────┴──────────────────────────────┘"
  echo ""
  echo -e "  ${BOLD}Other Required Files${NC}"
  echo -e "  │ secrets/rosa-token.yml   │ ROSA offline access token"
  echo ""
  echo -e "  ${BOLD}Prerequisites${NC}: VPCs, subnets, NAT gateways must already exist"
  echo -e "  ${BOLD}Pipeline${NC}: Verify Infra → ROSA Enrollment → Cluster Provision"
  echo -e "           → Machinepool → Demo Application"
}

show_params_cluster_ready() {
  echo -e "  ${BOLD}Scenario 3: Cluster-Ready${NC}"
  echo -e "  ${DIM}ROSA clusters running — add workshop autoscaler and demo app${NC}"
  echo ""
  echo -e "  ${BOLD}Per-Cluster Credential Fields${NC}  (secrets/cluster-credentials.yml)"
  echo ""
  echo -e "  ┌──────────────────────────┬────────────┬──────────────────────────────┐"
  echo -e "  │ Field                    │ Status     │ Notes                        │"
  echo -e "  ├──────────────────────────┼────────────┼──────────────────────────────┤"
  echo -e "  │ aws_access_key_id        │ ${RED}REQUIRED${NC}   │ AWS IAM access key           │"
  echo -e "  │ aws_secret_access_key    │ ${RED}REQUIRED${NC}   │ AWS IAM secret key           │"
  echo -e "  │ aws_region               │ ${RED}REQUIRED${NC}   │ e.g. us-east-2               │"
  echo -e "  │ aws_account_id           │ ${DIM}Optional${NC}   │ Not used in this scenario    │"
  echo -e "  │ purpose                  │ ${RED}REQUIRED${NC}   │ facilitator/hub/attendee     │"
  echo -e "  │ seat_number              │ ${YELLOW}REQUIRED*${NC}  │ * attendee clusters only     │"
  echo -e "  │ enabled                  │ ${DIM}Optional${NC}   │ Defaults to true             │"
  echo -e "  │ subnet_ids               │ ${DIM}Not used${NC}   │ Clusters already provisioned │"
  echo -e "  │ api_url                  │ ${RED}REQUIRED${NC}   │ OpenShift API URL            │"
  echo -e "  │ admin_password           │ ${RED}REQUIRED${NC}   │ cluster-admin password       │"
  echo -e "  └──────────────────────────┴────────────┴──────────────────────────────┘"
  echo ""
  echo -e "  ${BOLD}Other Required Files${NC}"
  echo -e "  │ secrets/rosa-token.yml   │ ROSA offline access token"
  echo ""
  echo -e "  ${BOLD}Additional Parameter${NC}"
  echo -e "  │ INSTANCE_TYPE            │ Workshop machinepool instance type (e.g. m5.2xlarge)"
  echo ""
  echo -e "  ${BOLD}Prerequisites${NC}: All ROSA clusters must be in 'ready' state"
  echo -e "  ${BOLD}Pipeline${NC}: Verify Clusters → Workshop Machinepool → Demo Application"
}

# ── Side-by-Side Comparison ───────────────────────────────────────────

show_comparison() {
  echo -e "  ${BOLD}Parameter Requirements by Scenario${NC}"
  echo ""
  echo -e "  ┌──────────────────────────┬────────────┬───────────┬───────────────┐"
  echo -e "  │ Field                    │ Greenfield │ AWS-Ready │ Cluster-Ready │"
  echo -e "  ├──────────────────────────┼────────────┼───────────┼───────────────┤"
  echo -e "  │ aws_access_key_id        │ ${RED}REQUIRED${NC}   │ ${RED}REQUIRED${NC}  │ ${RED}REQUIRED${NC}      │"
  echo -e "  │ aws_secret_access_key    │ ${RED}REQUIRED${NC}   │ ${RED}REQUIRED${NC}  │ ${RED}REQUIRED${NC}      │"
  echo -e "  │ aws_region               │ ${RED}REQUIRED${NC}   │ ${RED}REQUIRED${NC}  │ ${RED}REQUIRED${NC}      │"
  echo -e "  │ aws_account_id           │ ${DIM}Optional${NC}   │ ${DIM}Optional${NC}  │ ${DIM}Optional${NC}      │"
  echo -e "  │ purpose                  │ ${RED}REQUIRED${NC}   │ ${RED}REQUIRED${NC}  │ ${RED}REQUIRED${NC}      │"
  echo -e "  │ seat_number              │ ${YELLOW}REQUIRED*${NC}  │ ${YELLOW}REQUIRED*${NC} │ ${YELLOW}REQUIRED*${NC}     │"
  echo -e "  │ enabled                  │ ${DIM}Optional${NC}   │ ${DIM}Optional${NC}  │ ${DIM}Optional${NC}      │"
  echo -e "  │ subnet_ids               │ ${GREEN}Auto${NC}       │ ${RED}REQUIRED${NC}  │ ${DIM}Not used${NC}      │"
  echo -e "  │ api_url                  │ ${GREEN}Auto${NC}       │ ${GREEN}Auto${NC}      │ ${RED}REQUIRED${NC}      │"
  echo -e "  │ admin_password           │ ${GREEN}Auto${NC}       │ ${GREEN}Auto${NC}      │ ${RED}REQUIRED${NC}      │"
  echo -e "  ├──────────────────────────┼────────────┼───────────┼───────────────┤"
  echo -e "  │ INSTANCE_TYPE            │ ${DIM}Optional${NC}   │ ${DIM}Optional${NC}  │ ${RED}REQUIRED${NC}      │"
  echo -e "  └──────────────────────────┴────────────┴───────────┴───────────────┘"
  echo -e "  ${DIM}  * Required only for clusters with purpose=attendee${NC}"
  echo -e "  ${DIM}  Auto = populated automatically during deployment${NC}"
}

# ── Action Menu ───────────────────────────────────────────────────────

run_action_menu() {
  local scenario="$1"
  local instance_type="${2:-}"

  echo ""
  divider
  echo ""
  echo -e "  ${BOLD}What would you like to do?${NC}"
  echo ""

  local PS3=$'\n  Your choice: '
  local actions=("Validate — Run preflight checks only (no deployment)"
                 "Deploy   — Run preflight checks + full deployment"
                 "Back     — Choose a different scenario"
                 "Quit")

  select _action in "${actions[@]}"; do
    case $REPLY in
      1)
        echo ""
        echo -e "  ${CYAN}Running ${scenario} validation...${NC}"
        echo ""
        case "$scenario" in
          greenfield)    exec make validate-greenfield ;;
          aws-ready)     exec make validate-aws-ready ;;
          cluster-ready) exec make validate-cluster-ready INSTANCE_TYPE="${instance_type}" ;;
        esac
        ;;
      2)
        echo ""
        echo -e "  ${CYAN}Starting ${scenario} deployment...${NC}"
        echo ""
        case "$scenario" in
          greenfield)    exec make deploy-greenfield ;;
          aws-ready)     exec make deploy-aws-ready ;;
          cluster-ready) exec make deploy-cluster-ready INSTANCE_TYPE="${instance_type}" ;;
        esac
        ;;
      3)
        return 0
        ;;
      4)
        echo ""
        echo -e "  ${YELLOW}Goodbye.${NC}"
        echo ""
        exit 0
        ;;
      *)
        echo -e "  ${RED}Invalid choice. Try again.${NC}"
        ;;
    esac
  done
}

# ── Main Loop ─────────────────────────────────────────────────────────

main() {
  while true; do
    header "MAS World 2026 — Deployment Wizard"

    echo -e "  ${BOLD}Select a deployment scenario:${NC}"
    echo ""

    local PS3=$'\n  Your choice: '
    local scenarios=("Greenfield     — Fresh AWS accounts, build everything"
                     "AWS-Ready      — AWS infra exists, provision ROSA + app"
                     "Cluster-Ready  — Clusters running, add autoscaler + app"
                     "Compare All    — Side-by-side parameter comparison"
                     "Quit")

    select scenario in "${scenarios[@]}"; do
      case $REPLY in
        1)
          echo ""
          divider
          echo ""
          show_params_greenfield
          run_action_menu "greenfield"
          break
          ;;
        2)
          echo ""
          divider
          echo ""
          show_params_aws_ready
          run_action_menu "aws-ready"
          break
          ;;
        3)
          echo ""
          divider
          echo ""
          show_params_cluster_ready
          echo ""
          local instance_type=""
          read -rp "  Workshop machinepool instance type (e.g. m5.2xlarge): " instance_type
          if [[ -z "$instance_type" ]]; then
            echo -e "  ${RED}Instance type is required for cluster-ready scenario.${NC}"
            break
          fi
          echo -e "  ${GREEN}✓${NC} Instance type: ${instance_type}"
          run_action_menu "cluster-ready" "$instance_type"
          break
          ;;
        4)
          echo ""
          divider
          echo ""
          show_comparison
          echo ""
          echo -e "  ${DIM}Press Enter to return to scenario selection...${NC}"
          read -r
          break
          ;;
        5)
          echo ""
          echo -e "  ${YELLOW}Goodbye.${NC}"
          echo ""
          exit 0
          ;;
        *)
          echo -e "  ${RED}Invalid choice. Try 1-5.${NC}"
          ;;
      esac
    done
  done
}

main
