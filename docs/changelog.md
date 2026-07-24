# Changelog

> **Last updated:** 2026-07-24
>
> All notable changes to the MAS World 2026 Workshop Automation system.
> Format: `[YYYY-MM-DD] Category: Description`

---

## [2026-07-24] Phase 6 — EFS Storage, S3 Buckets, ACM Hub

### Added
- **`aws_efs` role** — Provisions EFS filesystem + NFS security group + mount targets per cluster VPC. Idempotent check-then-create pattern using AWS CLI. Results accumulated in `_cluster_efs_ids` dict. (See DEC-P6-004)
- **`aws_s3_bucket` role** — Creates per-cluster S3 bucket for Loki log backend with AES256 encryption, 30-day lifecycle expiration, and public access block. Naming via `s3_bucket_name` filter. (See DEC-P6-005)
- **`efs_csi_driver` role** — Installs `aws-efs-csi-driver-operator` via OLM and creates `efs` StorageClass with `provisioningMode: efs-ap`. Runs as first role in cluster preparation. (See DEC-P6-004)
- **`acm_hub` role** — Installs ACM operator + MultiClusterHub on hub cluster. Purpose-gated to only run on `hub` clusters. Waits for MCH to reach `Running` state. (See DEC-P6-006)
- **EFS block in `prepare-fleet.yml`** — Provisions EFS infrastructure for all clusters before launching parallel preparation.
- **S3 block in `prepare-fleet.yml`** — Creates S3 buckets for all non-hub clusters before launching parallel preparation.
- **Per-cluster vars** — Fleet playbook now writes `masworld_efs_filesystem_id`, `masworld_loki_s3_*`, `masworld_acm_hub_*`, and AWS credential vars into per-cluster var files.

### Changed
- **`prepare-cluster.yml`** — Added `efs_csi_driver` as first role and `acm_hub` before `acm_registration`.
- **`_prepare-single-cluster.yml`** — Added `efs_csi_driver` and `acm_hub` includes with same gating.

### Resolved Blockers
- B-003 (S3 Buckets), B-004 (ACM Hub), B-006 (Worker Scaling), B-007 (ROSA Token), B-008 (RWX Storage)

---

## [2026-07-24] Phase 6 Rehearsal — Bastion SSH + Machinepool

### Added
- **Bastion SSH connectivity preflight** — `cluster_preflight` role now validates SSH connectivity to each cluster's bastion host when `masworld_bastion_host` is defined. Results displayed in a PASS/FAIL table.
- **Bastion-based ROSA token extraction** — `prepare-fleet.yml` now extracts per-cluster OCM tokens by SSHing into each bastion host and running `rosa token`, replacing the global `rosa-token.yml` approach for fleet operations. (See DEC-P6-001)
- **Per-cluster OCM config isolation** — Each cluster uses an isolated `OCM_CONFIG` file under `/tmp/masworld-ocm-configs/` to prevent race conditions during concurrent `rosa login` sessions. Configs are cleaned up after use. (See DEC-P6-002)
- **Bastion credentials in cluster-credentials.yml** — Added `bastion_host`, `bastion_username`, `bastion_password` fields to the per-cluster credential schema. Automatically available via `to_cluster_list` filter.

### Changed
- **Workshop machinepool name** — Renamed from `workshop-workers` (16 chars) to `workshop-pool` (13 chars) to comply with ROSA HCP's 15-character NodePool name limit. Updated in `rosa_defaults.yml` and `scenario_preflight/defaults/main.yml`. (See DEC-P6-003)
- **`prepare-fleet.yml`** — Rewritten machinepool block to use dict-based approach (`_cluster_rosa_tokens`, `_cluster_bastion_ok`, `_cluster_has_workshop_pool`) instead of deeply nested `.item.item.item` chains. Report distinguishes "bastion unreachable" vs "already exists" vs "created" vs "FAILED".

### Security
- **Fact caching** — Changed from `jsonfile` to `memory` in `ansible.cfg` to prevent secrets from persisting to disk in `.cache/ansible_facts/`.
- **`no_log` coverage** — Added `no_log: true` to the parallel cluster launch task in `prepare-fleet.yml`.
- **Secret file permissions** — Added `fix-permissions` Makefile target to set `chmod 0600` on all files in `secrets/`.

### Fixed
- **`identity_demo` idempotency** — Keycloak admin, OpenLDAP admin, and OIDC client secrets now use check-then-create pattern. Passwords are only generated on first run; subsequent runs reuse existing secrets.

---

## [2026-07-23] Eliminate config/clusters.yaml — Single Source of Truth

### Changed
- **`secrets/cluster-credentials.yml`** — Now the single source of truth for ALL per-cluster credentials AND identity. Added `aws_account_id`, `purpose`, `seat_number`, `enabled` fields to each entry. Eliminates the need for a separate cluster inventory file.
- **`config/clusters.yaml`** — **DELETED**. All cluster identity data now lives in `cluster-credentials.yml`.
- **`ConfigLoader`** — No longer loads `clusters.yaml`. Builds cluster inventory from `secrets/cluster-credentials.yml` directly.
- **`ClusterConfig` schema** — Removed `credentials_key` field (cluster ID is now the credential key). Changed defaults: `api_url=""`, `admin_auth_method=password`, `admin_username=cluster-admin`.
- **`_resolve_cluster_vars()`** — Uses `cluster_cfg.id` instead of `credentials_key` for credential lookup.
- **`build_cluster_list()` filter** — Now passes through `aws_account_id`.
- **New `to_cluster_list` filter** — Transforms `cluster_credentials` dict into a list for Phase 2 fleet playbooks.
- **Fleet playbooks** — `prepare-fleet.yml` and `validate-fleet.yml` now load from `cluster-credentials.yml` via `to_cluster_list` filter.
- **Validator** — Removed `admin_secret_ref` PLACEHOLDER check (password auth clusters don't use secret refs).

---

## [2026-07-23] Auto-update Cluster Credentials After Provisioning

### Added
- **`create_admin` action** — New `rosa_cluster` role action that creates a cluster-admin user on each cluster via `rosa create admin` with a generated random password. Skips clusters that already have an admin.
- **`save_credentials` action** — New `rosa_cluster` role action that persists `api_url` and `admin_password` back to `secrets/cluster-credentials.yml` after provisioning. Uses the same write-back pattern as `aws_infra` uses for `infra_state.yml`.
- **Automated provisioning pipeline** — `make provision` now runs: preflight → create → wait_ready → **create_admin** → **save_credentials** → machinepool → verify. No manual credential entry required.

---

## [2026-07-23] Credential Consolidation

### Changed
- **Single source of truth** — `secrets/cluster-credentials.yml` is now the single source of truth for ALL per-cluster credentials: AWS keys, admin passwords, and api_url. After cluster provisioning, admin credentials are added to this same file.
- **masworld-secrets.yml simplified** — Stripped to IBM credentials only (entitlement key, MAS license, pull secret). Removed all per-cluster AWS keys and admin passwords.
- **config/credentials.yaml** — Removed unused `aws:` section (no code consumed these references).
- **config/clusters.yaml** — Added `credentials_key` field mapping cluster IDs to keys in `cluster-credentials.yml`. Removed `admin_secret_ref` (admin password now read from `cluster-credentials.yml`).
- **CLI credential resolution** — `_resolve_cluster_vars()` now loads admin password and Loki S3 keys directly from `cluster-credentials.yml` via `credentials_key` lookup.
- **Filter plugin** — `build_cluster_list()` now passes through `admin_password` and `api_url` if present in cluster credentials.
- **Schema** — Added `credentials_key` to `ClusterConfig`, made `admin_secret_ref` optional.

---

## [2026-07-23] Project Consolidation

### Changed
- **Project merge** — Consolidated `maximo-world` (Phase 2: MAS application layer) into `rosa-hcp-multi-build` (Phase 1: infrastructure). Single codebase with unified Makefile, secrets, tests, and docs.
- **Secrets consolidation** — Phase 2 secrets merged into `secrets/masworld-secrets.yml` (was separate `shared.yaml` + `clusters.yaml`). Phase 1 secrets (`rosa-token.yml`, `cluster-credentials.yml`) unchanged.
- **Filter namespace** — All `masworld.automation.pad` FQCN filter references replaced with `pad` (filters loaded via `filter_plugins` path, not Galaxy collection).
- **Lint configs merged** — `.ansible-lint`, `.yamllint.yml`, `.pre-commit-config.yaml` merged from both projects.
- **Makefile rewritten** — Organized by phase (Setup, Phase 1 Infrastructure, Phase 2 Application, End-to-End, Quality). Added `make workshop` (full 5-step build) and `make teardown` (full 3-step reverse).
- **README.md** — Rewritten for consolidated project.
- **Documentation** — 21 docs copied from maximo-world, 10 overlapping docs merged (Phase 2 content appended).

---

## [2026-07-22] Comprehensive Preflight & Deploy Target

### Added
- **scripts/preflight.sh** — Full ROSA HCP preflight validation (189 checks across 10 accounts):
  - CLI tools (rosa, aws, ansible-playbook, python3, jq, oc)
  - Secrets & config file existence
  - Credential format validation (placeholder detection, key/secret mismatch)
  - AWS STS connectivity per account
  - ROSA login and token validation
  - ROSA HCP enablement via `rosa verify quota` per account
  - SCP policy validation via `rosa verify permissions` per account
  - Service-linked roles (ELB mandatory, EFS informational)
  - ROSA HCP account roles (3 required: Installer, Support, Worker)
  - 11 AWS service quotas per account with actual values and minimums
  - Existing VPC count and project VPC detection per account
  - vCPU requirement summary computed from topology
  - Infrastructure state check (infra_state.yml)
  - Parallelized per-account checks for performance (~90s for 10 accounts)
- **make preflight** — Runs preflight checks (supports `MODE=infra`, `MODE=provision`, `MODE=all`)
- **make deploy-infra** — Combined target: preflight → setup-infra → provision

### Changed
- **make setup-infra** — Now runs preflight automatically before infrastructure creation
- **make provision** — Now runs preflight automatically before cluster provisioning

---

## [2026-07-22] AWS Infrastructure Automation

### Added
- **aws_infra role** — Automated VPC, subnet, IGW, NAT gateway, route table creation per AWS account
- **rosa_account_setup role** — Automated `rosa init` and `rosa create account-roles --hosted-cp` per account
- **setup-infra.yml playbook** — End-to-end infrastructure provisioning
- **destroy-infra.yml playbook** — Infrastructure teardown with confirmation
- **aws_infra_defaults.yml** — Configurable VPC CIDR, subnet layout, AZ config, default region (us-east-2)
- **infra_state.yml** — Auto-generated infrastructure state file for subnet ID resolution
- **Makefile targets** — setup-infra, verify-infra, destroy-infra, destroy-infra-auto

### Changed
- **build_cluster_list() filter** — Now accepts optional `infra_state` parameter; subnet_ids resolved from infra_state when not in credentials
- **subnet_ids** — Now optional in cluster-credentials.yml; auto-populated by `make setup-infra`

---

## [2026-07-20] Phase 2 — Live Cluster Testing (seat-01)

### Tested
- Config validation, preflight, event metadata, IBM entitlement Secret, IBM operator CatalogSource, cert-manager, MongoDB, SLS: all PASS
- DRO: IN_PROGRESS (blocked by insufficient CPU)
- MAS Core Suite CR: CREATED but readiness BLOCKED (5 pods Pending, 7.8 CPU requested vs 7.0 allocatable)

### Fixed
- OAuth token exchange for ROSA HCP clusters in `prepare-cluster.yml`
- Docker config JSON base64 encoding in `mas_prerequisites`
- IBM operator catalog added before SLS installation
- `mas_config_dir` changed to persistent `/tmp/masworld-config-<cluster>/`
- MAS domain auto-detect moved from IBM role to our `mas_core` role pre-task
- DRO (Data Reporter Operator) added to prerequisites
- Entitlement key comment line stripped from `secrets/entitlement.dat`
- FileSecretProvider `_resolve_value()` strips comment lines from `file://` references

---

## [2026-07-20] Phase 2 — Hub Credential Model Simplification

### Changed
- Hub cluster now uses same credential model as all other clusters (removed separate `acm/hub-kubeconfig` secret path)
- Decision DEC-009 added to decision log

---

## [2026-07-19] Phase 2 — Initial Implementation

### Added
- **17 Ansible roles** — config_validation through environment_report (MAS install, logging, identity, showroom, student accounts)
- **10 playbooks** — prepare-cluster, prepare-fleet, validate-cluster, validate-fleet, repair-cluster, rotate-credentials, reset-exercises, decommission-workshop (+ 2 helper includes)
- **Python CLI** (`cli/`) — Click-based `mas-world` command with config, fleet, student, secret, and report subcommands
- **Config system** — Layered YAML config in `config/` (defaults, event, clusters, components, environment overrides)
- **Secret provider abstraction** — 5 backends (env, file, k8s, aws-sm, vault) with `secret://` URI scheme
- **Showroom content** — 10-page Antora-based workshop content with runtime automation (17 playbooks across 6 modules)
- **ACM manifests** — Namespace, ManagedClusterSet, Placement, 2 policies, label schema
- **AgnosticV catalog** — 3 catalog items (event/dev/rehearsal), variable files, workloads, schemas
- **Operational runbooks** — 4 runbooks, 3 checklists, 2 repair procedures, incident template
- **Public content** — Example manifests, architecture diagrams, production guidance, troubleshooting
- **CI/CD** — GitHub Actions CI pipeline (6 jobs), release workflow, Dependabot config
- **Unit tests** — 55 tests covering config loader, config validation, secret providers
- **Documentation** — 30+ docs: threat model, installation guide, developer guide, operator guide, and more

---

## [2026-07-20] Initial Release (Phase 1)

### Added
- **Project scaffold** — Makefile, ansible.cfg, .yamllint.yml, .pre-commit-config.yaml, .gitignore
- **Cluster topology configuration** — 3 categories (facilitator, hub, seat) with counts, sizing, autoscaling
- **Custom filter plugin** — `build_cluster_list()` with credential validation, unit tested (7 cases)
- **Preflight role** — CLI checks, ROSA login, credential validation, topology constraints
- **Cluster lifecycle role** — create, wait_ready, machinepool, verify, status, destroy, destroy_cleanup
- **Playbooks** — provision.yml, destroy.yml, status.yml, preflight.yml
- **Async parallel provisioning** — All clusters start provisioning simultaneously via async/poll:0
- **Post-provision verification** — Report generation, state assertions
- **Destruction with IAM cleanup** — Operator roles and OIDC provider cleanup
- **Secret management** — Ansible Vault encrypt/decrypt, .example templates
- **Documentation** — architecture.md, configuration-guide.md, aws-account-prerequisites.md, troubleshooting.md
