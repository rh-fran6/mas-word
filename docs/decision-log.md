# Decision Log

Architectural and design decisions for the MAS World 2026 Workshop Automation system. Each entry records context, options considered, decision, and rationale.

> **Last updated:** 2026-07-24

---

## DEC-001: Localhost-Only Execution Model

- **Date:** 2026-07-20
- **Context:** Need to provision clusters across multiple AWS accounts. Could use a bastion host per account, a central controller with SSH, or local execution.
- **Decision:** Run everything on localhost. Target remote AWS accounts via per-task `environment:` blocks with account-specific credentials.
- **Rationale:** ROSA CLI and AWS CLI are the only interfaces needed. No SSH infrastructure required. Simplifies deployment — operator only needs the CLIs installed locally. Per-task environment isolation prevents cross-account credential leakage.
- **Consequences:** Operator's machine must have all CLIs installed. Network access to AWS and ROSA APIs required from operator's workstation.

## DEC-002: Async/Poll:0 for Parallel Cluster Creation

- **Date:** 2026-07-20
- **Context:** ROSA cluster creation takes 15–30 minutes. Sequential creation of N clusters would take N * 15–30 minutes.
- **Decision:** Use Ansible's `async/poll:0` pattern to fire all `rosa create cluster` commands near-simultaneously, then poll for completion.
- **Rationale:** Reduces total provisioning time from O(N * 30min) to O(30min) since all clusters provision in parallel. The polling phase is sequential but lightweight (just checking async job status).
- **Consequences:** All AWS accounts must have sufficient quotas simultaneously. Error reporting is deferred until all async jobs are checked.

## DEC-003: Custom Filter Plugin over Jinja2 Logic

- **Date:** 2026-07-20
- **Context:** Need to merge topology config with per-cluster credentials into a flat list. Could use complex Jinja2 expressions or a Python filter plugin.
- **Decision:** Implement `build_cluster_list()` as a custom Ansible filter plugin in Python.
- **Rationale:** Python is clearer for the merge logic, allows proper error handling with `ValueError`, is unit-testable with pytest, and avoids brittle multi-line Jinja2 expressions.
- **Consequences:** Requires the plugin in `plugins/filter/` and `filter_plugins` path in `ansible.cfg`. Worth it for testability.

## DEC-004: Zero-Padded Seat Naming

- **Date:** 2026-07-20
- **Context:** Seat clusters need predictable, sortable names. Could use plain integers (`seat-1`) or zero-padded (`seat-01`).
- **Decision:** Zero-pad seat indices to two digits. Other categories use plain integers.
- **Rationale:** Ensures consistent sorting for fleets up to 99 seats. `seat-01` sorts before `seat-10` in both filesystem and API listings. Facilitator and hub counts are small enough that zero-padding is unnecessary.
- **Consequences:** Credential keys must match the zero-padded format. The filter plugin enforces this.

## DEC-005: Ansible Vault for Secret Management

- **Date:** 2026-07-20
- **Context:** Need to store AWS credentials and ROSA tokens. Could use external secret managers (Vault, AWS Secrets Manager) or Ansible Vault.
- **Decision:** Use Ansible Vault for encrypting `secrets/` files at rest.
- **Rationale:** Zero additional infrastructure. Integrates natively with Ansible. Sufficient for workshop/demo credentials that have limited lifetimes. Operators already know Ansible.
- **Consequences:** Vault password must be managed by the operator. Not suitable for automated rotation — acceptable for short-lived workshop credentials.

## DEC-006: Single Facilitator Cluster Constraint

- **Date:** 2026-07-20
- **Context:** Should the facilitator category allow multiple clusters?
- **Decision:** Enforce exactly 1 facilitator cluster via preflight assertion.
- **Rationale:** Workshop model assumes a single instructor. Multiple facilitator clusters would complicate the demo flow with no clear benefit. Enforcing count=1 prevents accidental misconfiguration.
- **Consequences:** Topology validation fails if `facilitator.count != 1`. If multi-facilitator is ever needed, the assertion must be relaxed.

## DEC-007: rosa_action Dispatch Pattern

- **Date:** 2026-07-20
- **Context:** The `rosa_cluster` role handles multiple lifecycle actions (create, wait, destroy, etc.). Could use separate roles or a single role with action dispatch.
- **Decision:** Single `rosa_cluster` role with a `rosa_action` variable that `include_tasks` the corresponding YAML file.
- **Rationale:** Keeps related logic in one role. The `main.yml` validates the action against a whitelist, then includes the matching task file. Avoids role explosion while keeping individual actions in focused, readable files.
- **Consequences:** All actions share role defaults/vars. New actions require adding the task file and updating `rosa_valid_actions`.

## DEC-008: Identical CIDRs Across All Accounts

- **Date:** 2026-07-20
- **Context:** Need to assign VPC CIDRs across multiple AWS accounts. Could use unique CIDRs per account or reuse the same CIDR everywhere.
- **Decision:** Use the same VPC CIDR (10.0.0.0/16) for all AWS accounts.
- **Rationale:** Safe because each account has fully isolated VPCs with no VPC peering between them. Simplifies configuration and makes the setup predictable.
- **Consequences:** If VPC peering between accounts is ever needed, CIDRs will need to be re-addressed. Acceptable trade-off for workshop/demo isolation model.

## DEC-009: AWS CLI Shell Commands for Infrastructure Automation

- **Date:** 2026-07-20
- **Context:** Need to automate AWS infrastructure provisioning (VPCs, subnets, NAT gateways). Could use the `amazon.aws` Ansible collection or AWS CLI via shell/command modules.
- **Decision:** Use AWS CLI via Ansible shell/command modules rather than the amazon.aws Ansible collection.
- **Rationale:** Consistency with existing project patterns (the project already uses shell commands for ROSA CLI operations), avoids adding amazon.aws collection as a dependency, and keeps the tooling uniform.
- **Consequences:** Relies on AWS CLI being installed and configured on the operator's machine. JSON output must be parsed with filters. Trades Ansible-native idempotency for tooling consistency.

## DEC-010: infra_state.yml Stored in group_vars/all/

- **Date:** 2026-07-20
- **Context:** Infrastructure provisioning creates resource IDs (VPC IDs, subnet IDs, etc.) that downstream plays need. Could store them in a dedicated state file, pass them via `set_fact`, or place them in `group_vars/`.
- **Decision:** Persist infrastructure state (VPC IDs, subnet IDs, etc.) to `group_vars/all/infra_state.yml`.
- **Rationale:** Files in `group_vars/all/` are auto-loaded by Ansible as variables, requiring no changes to existing playbooks. The state is immediately available to all plays.
- **Consequences:** The file is written by the infra provisioning play and read by all subsequent plays. Must not be checked into version control with real values. Ansible's variable precedence rules apply.

## DEC-011: Single NAT Gateway per VPC

- **Date:** 2026-07-20
- **Context:** Private subnets need NAT gateways for outbound internet access. Could deploy one NAT gateway per AZ for high availability or one per VPC for cost savings.
- **Decision:** Create one NAT gateway per VPC rather than one per AZ.
- **Rationale:** Cost optimization for workshop/demo environments. A single NAT gateway is sufficient for the expected workload. For production HA, this is configurable in `aws_infra_defaults.yml`.
- **Consequences:** Single point of failure for outbound traffic if the NAT gateway's AZ has issues. Acceptable for short-lived workshop environments. Production deployments should override to multi-AZ.

## DEC-012: subnet_ids Optional with Precedence Chain

- **Date:** 2026-07-20
- **Context:** Clusters need subnet IDs for deployment. Users may provide them manually in credential files, or they may be auto-discovered from infrastructure provisioning state.
- **Decision:** `subnet_ids` resolution follows the chain: credentials file > infra_state > error.
- **Rationale:** Maintains full backward compatibility — users who already have `subnet_ids` in their credentials file see no behavior change. New users benefit from auto-discovery via infra_state.
- **Consequences:** Explicit values in credentials always win, which may cause confusion if infra_state has different values. Error messaging must clearly indicate which source was checked when resolution fails.

## DEC-013: Default Region us-east-2

- **Date:** 2026-07-20
- **Context:** Need a sensible default AWS region for ROSA HCP deployments. Must be overridable at both global and per-account levels.
- **Decision:** Default AWS region is us-east-2, configurable at global level (`aws_infra_defaults.yml`) and per-account level (`aws_region` in credentials).
- **Rationale:** us-east-2 (Ohio) offers good ROSA HCP availability and competitive pricing. Per-account override enables multi-region workshops.
- **Consequences:** Operators in other geographies should override the default. Per-account `aws_region` enables mixed-region deployments but adds complexity to network topology.


---

## Phase 2: MAS World Application Layer

### DEC-P2-001: Database Architecture — Db2 Per-Cluster

- **Date**: 2026-07-15
- **Decision**: Per-cluster Db2 installed by `mas install` (embedded).
- **Rationale**: Workshop isolation — one attendee's actions cannot affect another. Clean teardown per cluster.
- **Consequences**: Higher aggregate resource usage. Each cluster provisions its own Db2 instance.

### DEC-P2-002: Keycloak Deployment — Per-Cluster

- **Date**: 2026-07-15
- **Decision**: Per-cluster Keycloak for identity management.
- **Rationale**: Isolation between attendees. Simpler RBAC. No single point of failure for identity.
- **Consequences**: Credential rotation must iterate over all clusters.

### DEC-P2-003: S3 Bucket Isolation — Per-Cluster

- **Date**: 2026-07-15
- **Decision**: One S3 bucket per cluster for Loki log storage.
- **Rationale**: Clean teardown — delete bucket deletes all logs. No cross-contamination.
- **Consequences**: Up to 56 S3 buckets. Bucket naming: `mas-world-2026-{cluster-id}`.

### DEC-P2-004: Logging Stack — Observability API v1

- **Date**: 2026-07-15
- **Decision**: Use `observability.openshift.io/v1` API, Vector collector, 3 operators (Logging 6.6 + Loki 6.6 + COO).
- **Rationale**: Forward-compatible. The old `logging.openshift.io/v1` API is deprecated in 6.x.

### DEC-P2-005: MAS Edge (MVI Edge) — Disabled

- **Date**: 2026-07-15
- **Decision**: Disabled by default (`components.mas_edge.enabled: false`).
- **Rationale**: Not relevant to workshop scope. Requires GPU hardware not available in RHDP clusters.

### DEC-P2-006: Target OCP Version — 4.21

- **Date**: 2026-07-15
- **Decision**: Target OCP 4.21 as safe default.
- **Rationale**: MAS 9.1.x catalog explicitly supports OCP 4.16-4.21. OCP 4.22 unverified.

### DEC-P2-007: RHDP Skills — Skill-First Workflow

- **Date**: 2026-07-15
- **Decision**: Use `showroom:create-lab` and `showroom:verify-content` skills. Document manual fallbacks with `MANUAL_FALLBACK_SKILL_UNAVAILABLE`.
- **Rationale**: Skills encode Red Hat standards for compliance.

### DEC-P2-008: File-Based Secret Provider

- **Date**: 2026-07-19
- **Decision**: Add `file` backend to secret provider abstraction. Secrets in gitignored YAML files under `secrets/` with `secret://` URI keys.
- **Rationale**: YAML files scale to 50+ clusters. Same `secret://` scheme works across all 5 backends.
- **Consequences**: Secrets unencrypted on disk. File permissions (0600) and gitignore provide protection.

### DEC-P2-009: Hub Cluster — Unified Credential Model

- **Date**: 2026-07-20
- **Decision**: Hub cluster uses same credential model as all other clusters in inventory. Removed separate `acm/hub-kubeconfig` secret path.
- **Rationale**: One credential model for all clusters simplifies onboarding.

---

## Cross-Phase Decisions

## Phase 6: Rehearsal & Fleet Operations

### DEC-P6-001: Bastion-Based ROSA Token Extraction

- **Date**: 2026-07-24
- **Context**: Each ROSA HCP cluster is provisioned inside an isolated Red Hat Demo Platform (RHDP) sandbox, each with its own OCM account and API token. A single global ROSA token (from `secrets/rosa-token.yml`) cannot authenticate against multiple sandbox OCM accounts.
- **Decision**: SSH into each cluster's bastion host at runtime to run `rosa token`, extracting per-cluster OCM tokens dynamically.
- **Rationale**: Each RHDP sandbox bastion host is pre-authenticated with the correct OCM token for its account. Extracting tokens via SSH eliminates the need for operators to manually gather and maintain 10+ separate OCM tokens. The bastion credentials (`bastion_host`, `bastion_username`, `bastion_password`) are stored alongside other per-cluster credentials in `secrets/cluster-credentials.yml`.
- **Consequences**: Requires bastion SSH connectivity from the operator's workstation. Bastion reachability must be validated before machinepool operations (added to `cluster_preflight` role). `secrets/rosa-token.yml` remains used for Phase 1 preflight only.

### DEC-P6-002: Per-Cluster OCM Config Isolation

- **Date**: 2026-07-24
- **Context**: The ROSA CLI stores authentication state in `~/.config/ocm/ocm.json`. When running `rosa login` for multiple clusters concurrently or sequentially, each login overwrites the previous session's token, causing race conditions and authentication failures.
- **Decision**: Set `OCM_CONFIG=/tmp/masworld-ocm-configs/<cluster-id>.json` per cluster, giving each cluster its own isolated OCM config file. Files are cleaned up after machinepool operations complete.
- **Rationale**: Complete isolation of OCM authentication state between clusters. No shared state to corrupt. Temp directory ensures cleanup even on failure.
- **Consequences**: Slightly more disk I/O (10 small JSON files). Cleanup task must run in an `always` block to prevent stale config accumulation.

### DEC-P6-003: Machinepool Name Length Limit

- **Date**: 2026-07-24
- **Context**: ROSA HCP enforces a 15-character maximum on NodePool names. The originally configured name `workshop-workers` (16 characters) was rejected at runtime with error: `NodePool name 'workshop-workers' is 16 characters long - its length exceeds the maximum length allowed of 15 characters`.
- **Decision**: Rename the workshop machinepool from `workshop-workers` to `workshop-pool` (13 characters).
- **Rationale**: Fits within the 15-character limit with 2 characters of headroom for future suffixes. The name remains descriptive and consistent across `rosa_defaults.yml` and `scenario_preflight/defaults/main.yml`.
- **Consequences**: Any documentation or external references to `workshop-workers` must be updated. All existing unit tests updated to use `workshop-pool`.

### DEC-P6-004: Per-Cluster EFS for RWX Storage

- **Date**: 2026-07-24
- **Context**: Db2 (prerequisite for Maximo Manage) requires RWX PVCs (`c-db2u-manage-backup`, `c-db2u-manage-meta`) but ROSA HCP only provisions EBS-backed RWO StorageClasses (`gp2-csi`, `gp3-csi`). No ROSA addon exists for EFS CSI.
- **Decision**: Provision one EFS filesystem per cluster's VPC with NFS security group and mount targets. Install `aws-efs-csi-driver-operator` from `redhat-operators` and create an `efs` StorageClass with `provisioningMode: efs-ap` for dynamic provisioning via EFS access points.
- **Rationale**: EFS is the only AWS-native RWX option. Per-cluster isolation prevents cross-account security issues. Access point provisioning mode allows dynamic PVC creation without pre-provisioning volumes.
- **Consequences**: EFS provisioning adds ~2-3 minutes per cluster in fleet preparation. EFS costs are minimal for workshop duration. Mount targets must exist in all private subnets where worker nodes run.

### DEC-P6-005: Per-Cluster S3 Buckets for Loki Log Backend

- **Date**: 2026-07-24
- **Context**: Loki requires an S3 backend for log storage. Each cluster runs in an isolated AWS account.
- **Decision**: Create one S3 bucket per non-hub cluster named `mas-world-2026-<cluster-id>-loki` using the existing `s3_bucket_name` filter. Buckets are encrypted (AES256), have 30-day lifecycle expiration, and block all public access.
- **Rationale**: Per-cluster buckets match the isolation model (one AWS account per cluster). Clean teardown without cross-account dependencies. 30-day expiration auto-cleans workshop logs.
- **Consequences**: S3 costs are negligible for workshop log volume. Bucket naming convention is enforced by filter plugin.

### DEC-P6-006: ACM Hub on Dedicated Hub Cluster

- **Date**: 2026-07-24
- **Context**: Advanced Cluster Management (ACM) is required for fleet management, policy enforcement, and observability aggregation. Hub cluster `lab-hub-1` was provisioned but had no ACM installed.
- **Decision**: Install ACM operator (`advanced-cluster-management`) and deploy `MultiClusterHub` on the hub cluster via the `acm_hub` role. Role is purpose-gated — only runs when `masworld_cluster_purpose == 'hub'`.
- **Rationale**: Dedicated hub avoids ACM overhead on attendee clusters. Hub API URL and admin credentials are passed to attendee clusters for `acm_registration`. `availabilityConfig: High` for workshop reliability.
- **Consequences**: ACM takes 10-15 minutes to fully deploy. Hub cluster preparation is longer than attendee clusters. Attendee registration may need retry if hub is still deploying.

---

## Cross-Phase Decisions

### DEC-X-001: Project Consolidation

- **Date**: 2026-07-23
- **Context**: Two separate repositories (`rosa-hcp-multi-build` for infrastructure, `maximo-world` for application) formed a sequential pipeline. Managing them separately complicated the end-to-end workflow.
- **Decision**: Merge `maximo-world` into `rosa-hcp-multi-build` as a single consolidated codebase.
- **Rationale**: Single Makefile with `make workshop` (end-to-end build) and `make teardown` (end-to-end reverse). Unified secrets, tests, CI/CD, and docs. Eliminates cross-repo coordination.
- **Consequences**: Larger repository. Two config systems coexist (`group_vars/all/` for Phase 1, `config/` for Phase 2). Filter plugins loaded via `filter_plugins` path, not Galaxy collection namespace.

### DEC-X-002: Eliminate config/clusters.yaml — Credential File as Single Source of Truth

- **Date**: 2026-07-23
- **Context**: `config/clusters.yaml` duplicated cluster identity data (purpose, seat_number, aws_account_id) that logically belongs with the per-cluster credentials. The `aws_account_id` must be known before provisioning for preflight checks, yet it was stored in a separate config file. The `credentials_key` indirection added unnecessary complexity.
- **Decision**: Eliminate `config/clusters.yaml`. Extend `secrets/cluster-credentials.yml` to include `aws_account_id`, `purpose`, `seat_number`, and `enabled` per cluster. The cluster credential key IS the cluster ID — no indirection needed.
- **Rationale**: Single source of truth for all per-cluster data. Eliminates three-file coordination (`clusters.yaml`, `cluster-credentials.yml`, `credentials.yaml`). AWS account ID available from the start for preflight validation. Simpler onboarding — populate one file per cluster, not two.
- **Consequences**: Event-level defaults (`admin_username`, `student_credential_profile`, `metadata`) stay in `config/defaults.yaml` and Pydantic model defaults. Phase 2 playbooks use `to_cluster_list` filter instead of `include_vars` on `clusters.yaml`.

### DEC-X-003: Three Deployment Scenarios with Scenario-Specific Preflight

- **Date**: 2026-07-23
- **Context**: The workshop pipeline assumed a monolithic green-field deployment. Administrators arrive at different starting points — some have fresh AWS accounts, some have AWS networking already built, some have running ROSA clusters and only need the demo application.
- **Decision**: Implement three independent deployment scenarios (greenfield, aws-ready, cluster-ready) accessed via a single `deploy.yml` playbook with `deployment_scenario` parameter dispatch. Each scenario has its own preflight checks in a `scenario_preflight` role and chains only the relevant pipeline steps. The cluster-ready scenario includes a selectable workshop machinepool instance type.
- **Rationale**: Avoids running unnecessary pipeline stages (e.g., VPC creation when AWS infra already exists). Each scenario validates only its own prerequisites, giving clear error messages when an assumption doesn't hold. Follows the existing role dispatch pattern (`rosa_action`, `infra_action`). Selectable instance type for the workshop machinepool allows administrators to right-size worker nodes for different demo workloads.
- **Consequences**: Four new Makefile targets (`deploy`, `deploy-greenfield`, `deploy-aws-ready`, `deploy-cluster-ready`). New `scenario_preflight` role with 3 scenario-specific task files. New `workshop_machinepool` action in `rosa_cluster` role. The `cluster-ready` scenario requires `INSTANCE_TYPE` parameter.
