# ROSA HCP Multi-Cluster Provisioning — Implementation Prompt

> **Purpose:** This file captures the complete end-to-end implementation specification for the ROSA HCP Multi-Cluster Provisioning system. It is dynamically updated as the build progresses — if a design change or pivot occurs, previous entries are revised in-place rather than appended.
>
> **Last updated:** 2026-07-23

---

## 1. Objective

Build an Ansible-based automation system that provisions a fleet of Red Hat OpenShift on AWS (ROSA) Hosted Control Plane (HCP) clusters across multiple, isolated AWS accounts. The fleet consists of three cluster categories — Facilitator, Hub, and Seat — each with distinct sizing and scaling profiles, designed to support instructor-led workshops and demos on the Red Hat Demo Platform (RHDP).

## 2. System Requirements

### 2.1 Cluster Categories

| Category | Purpose | Count | Instance Type | Worker Replicas | Autoscaling |
|---|---|---|---|---|---|
| Facilitator | Instructor/facilitator cluster | 1 (fixed) | m5.xlarge | 2 initial | 2–4 |
| Hub | Hub/management cluster | Configurable (default 1) | m5.2xlarge | 2 initial | 2–6 |
| Seat | Participant/demo-user clusters | Configurable (default 5) | m5.large | 2 initial | 2–4 |

### 2.2 Per-Cluster AWS Isolation

Each cluster is provisioned in a **separate AWS account** with its own:
- AWS Access Key ID / Secret Access Key
- AWS Region
- VPC Subnet IDs (private subnets with NAT gateway) — **now optional** when using `make setup-infra`, as subnet IDs are auto-discovered from `infra_state`

Credential isolation is enforced at the Ansible task level via `environment:` blocks, ensuring no cross-account credential leakage.

### 2.3 Naming Convention

- Pattern: `{cluster_prefix}-{category}-{index}`
- Seats are zero-padded: `seat-01`, `seat-02`, ..., `seat-99`
- Other categories use plain integers: `facilitator-1`, `hub-1`
- Default prefix: `lab`

### 2.4 AWS Infrastructure Automation

The system includes automated AWS infrastructure provisioning and teardown, eliminating the need for pre-existing VPCs and subnets.

**New Roles:**
- `roles/aws_infra/` — Creates, verifies, and destroys VPC networking (VPC, subnets, NAT gateway, internet gateway, route tables) per AWS account. Persists infrastructure state to `group_vars/all/infra_state.yml` for downstream consumption.
- `roles/rosa_account_setup/` — Runs `rosa init` and `rosa create account-roles --hosted-cp` per AWS account, ensuring each account is ready for ROSA HCP cluster provisioning.

**New Playbooks:**
- `playbooks/setup-infra.yml` — Provisions VPC networking across all accounts and runs ROSA account setup. Outputs `infra_state.yml` containing VPC IDs, subnet IDs, and other infrastructure metadata.
- `playbooks/destroy-infra.yml` — Tears down all VPC networking resources created by `setup-infra.yml`, cleaning up per-account infrastructure.

**New Configuration:**
- `group_vars/all/aws_infra_defaults.yml` — Defines default VPC and subnet configuration (VPC CIDR `10.0.0.0/16`, subnet CIDRs, AZ configuration, default region `us-east-2`).

**Infrastructure State:**
- `group_vars/all/infra_state.yml` — Auto-generated file persisting infrastructure state (VPC IDs, subnet IDs per account). Auto-loaded by Ansible as a group_vars file, making subnet IDs available to `build_cluster_list()` without manual credential entry.

**Modified Filter Plugin:**
- `build_cluster_list()` now accepts an optional 4th parameter `infra_state`, enabling auto-resolution of `subnet_ids` from infrastructure state when they are not explicitly provided in credentials.

**New Makefile Targets:**
- `make preflight` — Comprehensive preflight validation (CLI tools, credentials, AWS connectivity, ROSA login, VPC quota). Supports `MODE=infra`, `MODE=provision`, or `MODE=all` (default)
- `make setup-infra` — Run infrastructure provisioning across all accounts (runs preflight first)
- `make verify-infra` — Verify existing infrastructure state
- `make destroy-infra` — Destroy infrastructure with confirmation prompt
- `make destroy-infra-auto` — Destroy infrastructure without confirmation
- `make provision` — Provision all ROSA HCP clusters (runs preflight first)
- `make deploy` — Full end-to-end: preflight → setup-infra → provision

## 3. Architecture

### 3.1 Execution Model

- Runs entirely on `localhost` — all `rosa` and `aws` CLI commands execute locally
- Remote AWS accounts are targeted via per-cluster environment variables
- No SSH to remote hosts; no inventory beyond localhost

### 3.2 Data Flow

```
cluster_topology.yml  +  cluster-credentials.yml  +  infra_state.yml (optional)
         |                        |                        |
         +--- build_cluster_list() filter plugin ----------+
                                                    |
                                          cluster_definitions[]
                                          (flat list, one dict per cluster)
                                          (subnet_ids auto-resolved from infra_state if not in credentials)
                                                    |
                                          loop + environment: per item
                                                    |
                                          rosa CLI with per-cluster AWS creds
```

### 3.3 Custom Filter Plugin

`plugins/filter/cluster_helpers.py` — `build_cluster_list()`:
- Merges topology definition (categories, counts, sizing) with per-cluster credentials
- Accepts optional 4th parameter `infra_state` for auto-resolving `subnet_ids` from infrastructure state
- Sorts categories alphabetically for deterministic ordering
- Validates every generated cluster name has matching credentials
- Raises `ValueError` on missing credentials (fail-fast before any cluster creation)

### 3.4 Async Parallel Provisioning

1. `create.yml` fires all `rosa create cluster` commands with `async/poll:0` — near-simultaneous launch
2. `async_status` with `until` waits for each CLI invocation to return
3. `wait_ready.yml` polls `rosa describe cluster` per-cluster until state is `ready`

## 4. Provisioning Workflow

### Full Lifecycle

```
make preflight     →  validates everything before creating resources
make setup-infra   →  creates VPCs, subnets, NAT gateways, enrolls ROSA accounts
make provision     →  creates ROSA HCP clusters
make deploy        →  does all three in sequence (preflight → setup-infra → provision)
make destroy       →  destroys ROSA clusters
make destroy-infra →  tears down VPCs and networking
```

### Infrastructure Setup (setup-infra)

```
make setup-infra
  └── playbooks/setup-infra.yml
        ├── role: aws_infra (per account)
        │     ├── create VPC (CIDR 10.0.0.0/16)
        │     ├── create subnets (public + private per AZ)
        │     ├── create internet gateway
        │     ├── create NAT gateway
        │     ├── configure route tables
        │     └── persist state to infra_state.yml
        └── role: rosa_account_setup (per account)
              ├── rosa init
              └── rosa create account-roles --hosted-cp
```

### Cluster Provisioning (provision)

```
make provision
  └── playbooks/provision.yml
        ├── pre_tasks: assert Ansible >= 2.14
        ├── role: rosa_preflight
        │     ├── verify rosa CLI installed
        │     ├── verify aws CLI installed
        │     ├── rosa login with offline token
        │     ├── validate required variables
        │     ├── validate facilitator count == 1
        │     ├── validate initial_replicas >= 2 per category
        │     ├── build_cluster_list (validates credential mapping, auto-resolves subnet_ids from infra_state)
        │     └── aws sts get-caller-identity per cluster
        ├── role: rosa_cluster (action=create)
        │     ├── build cluster definitions
        │     ├── rosa create cluster (async, all clusters)
        │     └── wait for async jobs to complete
        ├── role: rosa_cluster (action=wait_ready)
        │     └── poll rosa describe until state=ready
        ├── role: rosa_cluster (action=create_admin)
        │     ├── check for existing cluster-admin user
        │     ├── generate random admin password
        │     └── rosa create admin --cluster --password
        ├── role: rosa_cluster (action=save_credentials)
        │     ├── gather api_url via rosa describe cluster
        │     ├── merge admin_password + api_url into existing credentials
        │     └── write updated secrets/cluster-credentials.yml
        ├── role: rosa_cluster (action=machinepool)
        │     └── rosa create machinepool with autoscaling
        └── role: rosa_cluster (action=verify)
              ├── gather cluster details via rosa describe
              ├── build verification report
              ├── generate cluster-report.txt
              └── assert all clusters state == ready
```

## 5. Destruction Workflow

### Cluster Destruction (destroy)

```
make destroy
  └── playbooks/destroy.yml
        ├── pre_tasks: confirmation prompt (unless auto_confirm=true)
        ├── role: rosa_preflight (re-validate)
        ├── role: rosa_cluster (action=destroy)
        │     ├── get cluster IDs for IAM cleanup
        │     ├── rosa delete cluster (async, all clusters)
        │     ├── wait for delete commands
        │     └── poll until clusters fully removed
        └── role: rosa_cluster (action=destroy_cleanup)
              ├── delete operator roles
              └── delete OIDC providers
```

### Infrastructure Destruction (destroy-infra)

```
make destroy-infra
  └── playbooks/destroy-infra.yml
        ├── pre_tasks: confirmation prompt (unless auto_confirm=true)
        └── role: aws_infra (action=destroy, per account)
              ├── delete NAT gateway
              ├── release Elastic IPs
              ├── delete subnets
              ├── delete route tables
              ├── detach and delete internet gateway
              ├── delete VPC
              └── clean up infra_state.yml
```

## 6. Secret Management

- Secrets stored in `secrets/` directory (gitignored)
- `.example` templates committed for reference
- **`secrets/cluster-credentials.yml`** — Single source of truth for ALL per-cluster credentials AND identity (AWS keys, account IDs, admin passwords, api_url, purpose, seat_number, enabled). Used by Phase 1 playbooks directly and by Phase 2 CLI/playbooks via the `to_cluster_list` filter.
- **`secrets/masworld-secrets.yml`** — IBM credentials only (entitlement key, MAS license, pull secret). Uses `file://` references.
- Ansible Vault encryption supported: `make encrypt-secrets` / `make decrypt-secrets`
- `no_log: true` on all tasks handling credentials
- Vault password passed at runtime: `VAULT_ARGS="--ask-vault-pass"`

## 7. Testing Strategy

| Layer | Mechanism | Command |
|---|---|---|
| YAML linting | yamllint + ansible-lint | `make lint` |
| Playbook syntax | `ansible-playbook --syntax-check` | `make test` |
| Filter plugin unit tests | pytest (7 test cases) | `make test` |
| Preflight script | CLI tools, credentials, AWS connectivity, ROSA login, VPC quota | `make preflight` |
| Preflight playbook | Live credential + CLI checks via Ansible | `make validate` |
| Post-provision verification | Assert all clusters state=ready | Part of `make provision` |

## 8. Configuration Surface

| File | Purpose |
|---|---|
| `group_vars/all/cluster_topology.yml` | Cluster categories, counts, instance types, autoscaling |
| `group_vars/all/rosa_defaults.yml` | ROSA version, channel, async timing |
| `group_vars/all/aws_infra_defaults.yml` | VPC CIDR (`10.0.0.0/16`), subnet CIDRs, AZ configuration, default region (`us-east-2`) |
| `group_vars/all/infra_state.yml` | Auto-generated infrastructure state (VPC IDs, subnet IDs per account) |
| `secrets/rosa-token.yml` | ROSA offline access token |
| `secrets/cluster-credentials.yml` | Single source of truth: per-cluster AWS credentials, account IDs, admin passwords, api_url, purpose, seat_number, enabled |
| `ansible.cfg` | Ansible configuration |
| `.yamllint.yml` | YAML lint rules |
| `.pre-commit-config.yaml` | Pre-commit hooks |

## 9. Prerequisites

- **rosa CLI** >= 1.2.x
- **AWS CLI** >= 2.x
- **ansible-core** >= 2.14
- **Python** >= 3.9
- **pre-commit** >= 3.0
- Valid ROSA offline access token
- Per-cluster AWS accounts enrolled in ROSA (VPCs/subnets auto-provisioned via `make setup-infra`, or pre-existing)
- Sufficient EC2 quotas per account

## 10. Current Implementation State

The core system is fully implemented:
- [x] Project structure and Makefile
- [x] Cluster topology configuration
- [x] Custom filter plugin with unit tests
- [x] Preflight validation role
- [x] Async parallel cluster creation
- [x] Cluster readiness polling
- [x] MachinePool autoscaling setup
- [x] Post-provision verification and reporting
- [x] Async parallel cluster destruction with IAM cleanup
- [x] Fleet status checking
- [x] Secret management (Vault support)
- [x] Pre-commit hooks and linting
- [x] Helper scripts (credential template generator, preflight validation)
- [x] Documentation (architecture, config guide, AWS prerequisites, troubleshooting)
- [x] AWS infrastructure automation (`roles/aws_infra/` — VPC, subnets, NAT/IGW per account)
- [x] ROSA account setup automation (`roles/rosa_account_setup/` — rosa init, account-roles)
- [x] Infrastructure provisioning playbook (`playbooks/setup-infra.yml`)
- [x] Infrastructure destruction playbook (`playbooks/destroy-infra.yml`)
- [x] Infrastructure state management (`group_vars/all/infra_state.yml`, auto-loaded)
- [x] Infrastructure state filter plugin support (`build_cluster_list()` optional `infra_state` parameter)

## 11. Design Principles

1. **Fail fast** — Preflight checks catch missing credentials, invalid topology, and CLI issues before any cluster creation begins
2. **Idempotent** — `rosa create cluster` skips existing clusters; re-running `make provision` is safe
3. **Credential isolation** — Per-cluster `environment:` blocks prevent cross-account leakage
4. **Parallel execution** — Async/poll:0 pattern ensures all clusters start provisioning simultaneously
5. **No secrets in logs** — `no_log: true` on all credential-handling tasks
6. **Deterministic ordering** — Categories sorted alphabetically; seats zero-padded for consistent iteration

---

## 12. Phase 2 — MAS World Application Layer

Phase 2 takes the provisioned ROSA HCP clusters from Phase 1 and installs IBM Maximo Application Suite, logging/observability, identity integration, student accounts, and Showroom workshop content.

> **Full Phase 2 specification**: See `docs/masworld-specification.md` for the complete 2400+ line authoritative specification covering all MAS World requirements, acceptance criteria, component configuration, security requirements, testing strategy, and operational runbooks.

### Phase 2 Targets

| Target | Description |
|---|---|
| `mas-prepare-fleet` | Prepare entire fleet (all enabled clusters) |
| `mas-prepare-cluster` | Prepare a single cluster (`CLUSTER=seat-01`) |
| `mas-validate-fleet` | Validate fleet readiness |
| `mas-validate-cluster` | Validate single cluster (`CLUSTER=seat-01`) |
| `mas-repair-cluster` | Repair a failed cluster |
| `mas-create-students` | Create student accounts |
| `mas-rotate-credentials` | Rotate student passwords |
| `mas-reset-exercises` | Reset lab exercises |
| `mas-decommission` | Decommission workshop |

### End-to-End Targets

| Target | Description |
|---|---|
| `workshop` | Full pipeline: preflight → infra → clusters → prepare-fleet → validate |
| `teardown` | Full reverse: decommission → destroy clusters → destroy infra |

### Phase 2 Configuration

Phase 2 uses a layered YAML config system in `config/`:
- `config/defaults.yaml` — Base defaults for all environments
- `config/event.yaml` — Event-specific overrides
- `config/components.yaml` — Component enable/disable
- `config/environments/{dev,rehearsal,event}.yaml` — Environment overrides

Cluster inventory comes from `secrets/cluster-credentials.yml` (shared with Phase 1) — each entry includes `purpose`, `seat_number`, `aws_account_id`, and `enabled` alongside the AWS credentials.

### Phase 2 Secrets

- `secrets/cluster-credentials.yml` — Single source of truth for all per-cluster credentials (AWS keys, admin passwords, api_url). Shared with Phase 1.
- `secrets/masworld-secrets.yml` — IBM credentials only (entitlement key, MAS license, pull secret references)
- `secrets/entitlement.dat` — IBM entitlement key
- `secrets/license.dat` — IBM MAS license file
- `secrets/pullsecret.json` — OpenShift pull secret

### Phase 2 Roles (17 roles in `roles/`)

config_validation, cluster_preflight, event_metadata, acm_registration, mas_prerequisites, mas_core, maximo_manage, logging_operator, loki_stack, log_forwarding, identity_demo, mas_edge, student_accounts, sample_workloads, showroom, event_readiness, environment_report

### Phase 2 CLI

Python CLI (`cli/`) with Click-based `mas-world` command providing config, fleet, student, secret, and report management subcommands.

---

*This prompt will be updated as the system evolves. See `docs/changelog.md` for a chronological record of changes.*
