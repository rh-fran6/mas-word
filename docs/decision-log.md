# Decision Log

Architectural and design decisions for the MAS World 2026 Workshop Automation system. Each entry records context, options considered, decision, and rationale.

> **Last updated:** 2026-08-09

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

### DEC-X-004: Per-Cluster ROSA Tokens via Bastion SSH (No Global Token)

- **Date**: 2026-07-26
- **Context**: Each ROSA HCP cluster lives in its own OCM account. A single global ROSA token (`secrets/rosa-token.yml`) cannot see clusters across different OCM accounts, causing `rosa list clusters` to return `[]` and all ROSA CLI operations (machinepool creation, describe, status) to fail with "no cluster with identifier". The bastion hosts for each cluster are already logged into their respective OCM accounts.
- **Decision**: For the `cluster-ready` scenario, extract per-cluster ROSA tokens by SSH-ing into each cluster's bastion host (`rosa token`), then use isolated `OCM_CONFIG` files (`/tmp/rosa-cluster-ocm-configs/<cluster>.json`) for all ROSA CLI commands. Remove `secrets/rosa-token.yml` from the `deploy.yml` vars_files for cluster-ready; greenfield/aws-ready scenarios retain the global token for initial provisioning.
- **Rationale**: Matches the existing pattern in `prepare-fleet.yml` which already extracts per-cluster tokens via bastion SSH. Each cluster's bastion is authoritative for its OCM account. `OCM_CONFIG` isolation prevents cross-cluster login conflicts when running commands sequentially. No additional credentials or files to manage — bastion fields are already in `cluster-credentials.yml`.
- **Consequences**: `sshpass` is a hard CLI requirement for `cluster-ready`. Bastion fields (`bastion_host`, `bastion_username`, `bastion_password`) must be populated in `cluster-credentials.yml`. New `discover_rosa_tokens.yml` task file handles token extraction and ROSA cluster discovery. All `rosa_cluster` task files use `OCM_CONFIG` environment variable.

### DEC-X-005: Parallel Cluster Operations via add_host + strategy:free

- **Date**: 2026-08-08
- **Context**: The cluster-ready deployment pipeline processed 7+ clusters sequentially using `include_tasks` + `loop:`. Each cluster's wait-for-nodes (up to 20 min), prepare (17 roles), and validate phases ran one at a time. Wall time was the sum of all clusters. Since everything ran on `hosts: localhost`, Ansible's `forks = 10` had no effect.
- **Decision**: Replace the sequential loop with a 3-play playbook (`deploy-cluster-ready.yml`). Play 1 runs preflight and fleet ops on localhost, then registers each cluster as a dynamic host via `add_host` into a `cluster_fleet` group. Play 2 targets `cluster_fleet` with `strategy: free`, running per-cluster wait/prepare/validate in parallel. Play 3 aggregates results on localhost.
- **Rationale**: `strategy: free` isolates each host's fact namespace, eliminating variable collisions (`masworld_api_token`, `_resolved_purpose`, etc.). The existing task files (`_prepare-single-cluster.yml`, `_wait-machinepool-nodes.yml`, `_validate-single-cluster.yml`) reference `cluster.id`, `cluster.api_url`, etc., which resolve from the host var unchanged — no refactoring needed. Wall time drops from O(N × T) to O(T) where T is the slowest cluster.
- **Consequences**: Dynamic hosts require explicit `ansible_python_interpreter: "{{ ansible_playbook_python }}"` in `add_host` (they don't inherit from localhost inventory). Per-cluster KUBECONFIG files (`/tmp/kubeconfig-<cluster-id>`) prevent `oc login` races. The sequential fallback (`_deploy-cluster-ready.yml`) is preserved via `make deploy SCENARIO=cluster-ready`.

### DEC-X-006: Per-Cluster KUBECONFIG Isolation for Parallel oc CLI

- **Date**: 2026-08-08
- **Context**: IBM MAS DevOps roles (MongoDB, cert_manager, common_services) use raw `oc` CLI commands (`oc adm policy add-scc-to-user`, `oc get pods`, `oc get subs`) that read kubeconfig context, not K8S_AUTH environment variables. When running `oc login` for multiple clusters in parallel, all hosts write to `~/.kube/config`, causing race conditions and cross-cluster authentication failures.
- **Decision**: Set `KUBECONFIG=/tmp/kubeconfig-{{ cluster.id }}` in the `oc login` task and propagate it to the role deployment block's `environment:` dictionary alongside the existing `K8S_AUTH_*` variables.
- **Rationale**: Each cluster gets its own kubeconfig file. The `oc` CLI reads `KUBECONFIG` environment variable, so IBM MAS DevOps roles see the correct cluster context without code changes. Temp directory ensures cleanup.
- **Consequences**: Up to N kubeconfig files in `/tmp/`. Negligible disk usage. Files can be cleaned up in post-play tasks or by `make clean`.

### DEC-X-007: Replace `pause` with `wait_for` in Vendored IBM Roles

- **Date**: 2026-08-08
- **Context**: Ansible's `strategy: free` rejects the `pause` module because it bypasses the host loop ("The 'pause' module bypasses the host loop, which is currently not supported in the free strategy"). The vendored IBM MAS DevOps collection uses `pause` in `db2` (delete_db2_operand_request.yml) and `suite_db2_setup_for_manage` (apply-db2-config-settings.yml), both reachable during parallel cluster-ready deployment.
- **Decision**: Replace all `pause: minutes: N` tasks with `ansible.builtin.wait_for: timeout: N*60` in the vendored collection. The `wait_for` module with only a `timeout` parameter acts as a per-host sleep that works in all strategies.
- **Rationale**: `wait_for` is the standard Ansible-native alternative. It operates within the host loop, so each host sleeps independently. Functionally identical to `pause` for time-based waits. No behavioral change for `strategy: linear` (the default).
- **Consequences**: Vendored collection is patched — must re-apply if the IBM collection is updated. A regression test (`test_no_pause_module_in_pipeline_ibm_roles`) catches any re-introduction of `pause` in pipeline-reachable roles.

### DEC-X-008: ACM Operator Source and Channel Resolution

- **Date**: 2026-08-08
- **Context**: The ACM hub operator Subscription was created with `source: redhat-marketplace` and `channel: release-2.13`. The operator deployment never appeared (60 retries, 15 min timeout). The `redhat-marketplace` CatalogSource does not contain the `advanced-cluster-management` package — it is published in `redhat-operators` (confirmed via the Red Hat gitops-catalog reference implementation). The channel `release-2.13` was also stale relative to `components.yaml` which specified ACM `2.16` (not yet released; latest available is `2.15`).
- **Decision**: Fix the CatalogSource to `redhat-operators`. Derive the channel from `components.yaml` at runtime (`release-` + `masworld_components.components.acm.version`), falling back to the defaults file value. Update `components.yaml` to ACM `2.15`. Add Subscription health diagnostics to the rescue block (query Subscription and InstallPlan state, report common causes).
- **Rationale**: Dynamic channel resolution from `components.yaml` prevents configuration drift — the same pattern used for logging, loki, and MAS channels. The diagnostic rescue block eliminates the previous "unknown error" message that gave no clue about the actual failure. A regression test (`test_acm_channel_matches_components`) ensures the defaults file stays in sync with `components.yaml`.
- **Consequences**: Updating the ACM version now requires changing only `components.yaml` — the role defaults and runtime resolution adapt automatically. The `test_acm_operator_source_is_redhat_operators` test prevents a repeat of the CatalogSource error. Additionally, operator readiness detection was changed from a Deployment label check (`app=multiclusterhub-operator`) to a ClusterServiceVersion phase check — the label didn't match the actual OLM-managed deployment, causing timeouts even when the operator was running. The CSV `Succeeded` phase is the authoritative OLM signal.

### DEC-X-009: Parallel EFS Provisioning in Cluster-Ready Path

- **Date**: 2026-08-08
- **Context**: The `efs_csi_driver` role requires `masworld_efs_filesystem_id` to install the EFS CSI driver operator and create the `efs` StorageClass (used by DB2 for RWX storage). This variable was only populated in `prepare-fleet.yml`, which runs the `aws_efs` role sequentially on localhost and stores the IDs in a runtime fact. The `deploy-cluster-ready.yml` parallel playbook didn't run `aws_efs`, so `masworld_efs_filesystem_id` was always empty and the `efs_csi_driver` role was silently skipped.
- **Decision**: (1) Add an EFS preflight check to `scenario_preflight/tasks/cluster-ready.yml` (Phase 7) that queries AWS for existing EFS filesystems per non-hub cluster and reports FOUND/NOT FOUND as advisory information. (2) Move the full EFS stack (`aws_efs` + `efs_csi_driver`) into `_prepare-single-cluster.yml` so it runs per-cluster in the parallel phase (`strategy: free`). Each cluster calls `aws_efs` (idempotent create-or-find) to provision its own EFS filesystem, then `efs_csi_driver` installs the CSI operator and creates the StorageClass. No EFS provisioning in Play 1 — only the advisory preflight check.
- **Rationale**: Per-cluster parallel provisioning aligns with the model used by all other operations in `_prepare-single-cluster.yml`. Each cluster uses its own AWS credentials with no shared state, so there's no contention. The `aws_efs` role is fully idempotent — it checks for existing resources before creating, so running it per-cluster is safe. The preflight check gives operators advance visibility without blocking provisioning. Sequential EFS provisioning in Play 1 was a bottleneck that scaled linearly with fleet size; parallel provisioning takes wall-clock time of the slowest single cluster.
- **Consequences**: The cluster-ready path is fully self-contained and parallel for EFS — no prior `prepare-fleet.yml` run required. DB2 installation succeeds because the `efs` StorageClass is always created. The preflight summary reports EFS status per cluster. Regression tests (`test_efs_provisioned_per_cluster_in_parallel`, `test_aws_credentials_passed_to_dynamic_hosts`, `test_cluster_ready_checks_efs_existence`, `test_cluster_ready_efs_check_excludes_hub`) prevent reintroduction.

### DEC-X-010: Db2 SecurityContextConstraints for ROSA HCP

- **Date**: 2026-08-08
- **Context**: The Db2uCluster CR stuck in `NotReady/Processing` state across all 6 non-hub clusters for 2+ hours. The Db2u operator CSV was `Succeeded`, the CR was created correctly with `efs` and `gp3-csi` storage classes, but the Formation never progressed. The Db2u operator's own CSV documentation explicitly requires a `db2u-scc` SecurityContextConstraints with `allowPrivilegedContainer: true` and specific Linux capabilities (`SYS_RESOURCE`, `IPC_OWNER`, `SYS_NICE`, etc.). Neither the vendored `ibm.mas_devops.db2` role nor any project role created this SCC. On standard OCP, the operator may auto-create it; on ROSA HCP, the stricter managed security model prevents Db2 pods from starting without an explicit SCC grant.
- **Decision**: (1) Add pre-Db2 tasks in `maximo_manage/tasks/main.yml` that create the `db2u-scc` SCC (matching the operator's CSV documentation) and grant it to the `db2u-operator`, `db2u`, and `default` service accounts in the `db2u` namespace. (2) Label the `db2u` namespace with `pod-security.kubernetes.io/enforce: privileged` to prevent Pod Security Admission from blocking privileged init containers. (3) Improve the rescue block with Db2uCluster status, pod state, PVC state, and actionable diagnostic commands. (4) Extend the vendored db2 role's wait timeout from 24 retries (2 hours) to 36 retries (3 hours) for ROSA HCP + EFS latency.
- **Rationale**: The SCC is documented as a requirement by IBM in the operator's CSV. Creating it before the Db2 role runs ensures the operator's pods have the security context they need. The namespace labels prevent PSA from blocking pods that the SCC allows. The diagnostic rescue block eliminates the previous generic "unknown error" message — operators now see the actual Db2 state, pod phases, pending PVCs, and specific `oc` commands to run. The extended timeout accounts for ROSA HCP managed node constraints and EFS mount latency.
- **Consequences**: The SCC is idempotent (`state: present`), safe to re-apply. Regression tests verify SCC template existence, ordering (before db2 role), required capabilities, namespace labeling, diagnostic capture, and extended wait timeout (8 new tests in `TestDb2SecurityAndDiagnostics`).

### DEC-X-011: EFS Access Point UID/GID for Db2 Compatibility

- **Date**: 2026-08-08
- **Context**: After resolving the SCC issue (DEC-X-010), the Db2 `instdb` job pods continued to fail across all 6 non-hub clusters with `chown: changing ownership of '/mnt/blumeta0/db2': Operation not permitted`. The instdb job runs as UID 700 and calls `chown` on the meta volume (EFS/NFS). NFS does not honor Linux capabilities (`CAP_CHOWN`) — only root (UID 0) can chown on NFS. EFS access points enforce user identity: all NFS operations appear as the configured UID regardless of the container's actual UID. With the default UID 50000 (or even UID 700), the `chown` fails because the effective NFS user is not root. IBM's own `ocp_efs` role uses `uid: "0"` and `gid: "0"` to enforce root identity on access points, which allows chown to succeed. The meta volume requires RWX (ReadWriteMany) — even single-member Db2 has multiple pods (engine, LDAP, management, restore) needing concurrent access, so EBS (RWO only) cannot replace EFS for meta.
- **Decision**: (1) Set `masworld_efs_uid: "0"` and `masworld_efs_gid: "0"` in `efs_csi_driver/defaults/main.yml` (matching IBM's `ocp_efs` role). (2) Set `masworld_efs_directory_perms: "777"` so the access point root directory is accessible by any UID. (3) Add auto-replace logic: if the existing StorageClass has wrong `uid`, delete and recreate it (StorageClass parameters are immutable). (4) Add pre-Db2 cleanup in `maximo_manage/tasks/main.yml`: if a Db2uCluster exists in `NotReady` state, delete the CR, PVCs, and Formation-created SCC, then wait up to 30 minutes for PVC deletion. (5) The vendored `ibm.mas_devops.db2` role then recreates everything with correct EFS access points.
- **Rationale**: With `uid: "0"` on EFS access points, all NFS operations are performed as root. Root can call `chown` on NFS. The Db2 instdb job's `chown(path, 700, 700)` succeeds because EFS sees it as a root request. Subsequent access by UID 700 also works because root can access any file. This matches IBM's reference implementation (`ocp_efs` role). Validated on seat-01 cluster — Db2uCluster reached `Ready` state within ~13 minutes after applying the fix.
- **Consequences**: New clusters get correct EFS access points from the start. Re-runs on broken clusters auto-clean and recreate. Re-runs on healthy clusters are no-ops. Regression tests verify UID/GID defaults (0/0), StorageClass parameters, replace-on-mismatch logic, stale cleanup ordering, and PVC deletion.

### DEC-X-012: MAS 9.2 Upgrade with Unmodified IBM Collection

- **Date**: 2026-08-08
- **Context**: Workshop originally targeted MAS 9.1.x with a vendored `ibm.mas_devops` 37.10.0 collection that had 6 local patches. User wants MAS 9.2 and does not want to maintain a fork of IBM's collection — the environment preparation roles should adapt to work with the IBM collection as-shipped. MAS 9.2 requires MongoDB 8.0, uses `9.2.x` operator channels, and lets the collection auto-detect the IBM catalog tag and Db2 version from the catalog.
- **Decision**: (1) Delete the vendored collection; install fresh `ibm.mas_devops >=37.12.0` via `requirements.yml`. (2) Add a `patch-collection` Makefile target that applies a minimal post-install `sed` fix for the `regex_search` boolean conditional bug (upstream unfixed as of 37.12.1, breaks ansible-core ≥2.17). (3) Remove hardcoded `catalog_tag` and `catalog_image` — pass `masworld_mas_catalog_source` as empty string so the collection uses its built-in default. (4) Update all version pins: MAS `9.2.x`, MongoDB `8.0`, remove Db2 version pin. (5) Add `default(omit, true)` to `mas_catalog_version` vars so empty strings are omitted. (6) Extend stale Db2 cleanup to handle both `Db2uCluster` and `Db2uInstance` CRs (future-proofing for `db2u_kind` changes).
- **Rationale**: Using the collection as-is avoids fork maintenance burden. The `regex_search` patch is 2 lines applied via Python regex substitution with negative lookahead (idempotent). The `patch-collection` target is wired into `make setup` so it runs automatically on every install. Removing catalog/Db2 version pins lets the collection's built-in defaults (which are tested by IBM against each MAS release) drive the correct versions. MongoDB 8.0 is the default for MAS 9.2. The dual CR type cleanup handles the possibility that a future collection version switches from `Db2uCluster` to `Db2uInstance`.
- **Consequences**: `make setup` is the single command to install + patch the collection. The patch must be re-verified on each collection upgrade. Environment preparation roles (EFS, SCC, namespace labels) are unchanged — they are orthogonal to MAS version.

### DEC-X-013: Self-Signed CA ClusterIssuer for MAS 9.2

- **Date**: 2026-08-09
- **Context**: MAS 9.2's `suite_install` role defaults `issuerKind: ClusterIssuer` in the Suite CR (line 143-149 of `suite_install/tasks/main.yml`). This tells the MAS operator to look for a ClusterIssuer, but no ClusterIssuer exists on the cluster. The IBM collection expects one of: (a) running `suite_dns` role which creates a Let's Encrypt ACME ClusterIssuer via Route53/Cloudflare/CIS, (b) setting `MAS_CLUSTER_ISSUER` env var pointing to a pre-existing ClusterIssuer, or (c) manual cert management (`MAS_MANUAL_CERT_MGMT=true`). We use auto-generated ROSA cluster domains (no custom DNS), so `suite_dns` is not applicable. The result was the MAS operator failing with `'dict object' has no attribute 'caSecretName'` in its internal `setup-internal-issuer.yml` because it expected to find a ClusterIssuer with a CA secret.
- **Decision**: Create a self-signed CA ClusterIssuer chain in `mas_core/tasks/main.yml` before calling `suite_install`. Three resources: (1) `mas-selfsigned-issuer` (bootstrap ClusterIssuer, type selfSigned), (2) `mas-ca-certificate` (root CA Certificate in cert-manager cluster resource namespace), (3) `mas-ca-clusterissuer` (CA ClusterIssuer referencing the CA secret). Pass `mas_cluster_issuer: "mas-ca-clusterissuer"` to `suite_install`. Auto-detect `cert_manager_cluster_resource_namespace` using the same logic as the IBM collection's `detect_cert_manager.yml` common task.
- **Rationale**: This is the standard cert-manager pattern for self-signed CA hierarchies. MAS 9.2 is correctly designed to require a ClusterIssuer — it is used in production with Let's Encrypt via `suite_dns`. For lab/workshop deployments without custom DNS, a self-signed CA is the appropriate substitute. The ClusterIssuer creation is idempotent. MAS 9.2 HAS been successfully installed with this collection — the issue was our deployment not providing a ClusterIssuer, which is a prerequisite, not a bug in the collection.
- **Consequences**: All clusters get a self-signed CA ClusterIssuer. MAS-issued certificates use this CA. Browser trust warnings will appear (self-signed) — acceptable for workshop environments. If custom DNS is later needed, the self-signed issuer can be replaced with a Let's Encrypt issuer via `suite_dns`.

## DEC-014: ROSA HCP IDP Wiring via ROSA CLI Instead of OAuth CR Patch

- **Date**: 2026-08-12
- **Context**: On ROSA HCP (Hosted Control Plane), the `oauths.config.openshift.io/cluster` resource is immutable from the guest cluster. A ValidatingAdmissionPolicy blocks all create/update/delete operations with "Please ask your administrator to modify the resource in the HostedCluster object." This affects both the `identity_demo` role (OIDC IDP for Keycloak) and `student_accounts` role (htpasswd IDP for workshop students). Three options: (a) patch the HostedCluster CR on the management cluster (not accessible on ROSA — Red Hat manages it), (b) use the OCM REST API directly, (c) use the `rosa` CLI which wraps the OCM API.
- **Decision**: Detect ROSA HCP via `Infrastructure.status.controlPlaneTopology == 'External'`, then use `rosa create idp` (type `openid` for Keycloak, type `htpasswd` for students) instead of patching the OAuth CR. The ROSA token is obtained from each cluster's bastion host via SSH (same pattern as `discover_rosa_tokens.yml`). Per-cluster OCM config files isolate cross-account ROSA sessions. Non-HCP clusters retain the direct OAuth CR patch as a fallback.
- **Rationale**: The `rosa` CLI is already a project dependency (used for cluster provisioning and machinepools). Reusing the bastion SSH token extraction pattern is consistent with existing code. The Infrastructure CR check is reliable and fast. Supporting both paths ensures the roles work on both ROSA HCP and self-managed OpenShift.
- **Consequences**: Roles require `sshpass` and `rosa` CLI on the control node (already dependencies). Each IDP creation takes ~5s extra for bastion SSH + ROSA login. Idempotency is handled by checking `rosa list idp` before creating. Password rotation for htpasswd on HCP requires deleting and recreating the IDP via ROSA CLI.
