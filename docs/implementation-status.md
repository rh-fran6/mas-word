# Implementation Status

> **Last updated:** 2026-08-17 (Lab accounts role, S3 pre-provisioning, Showroom content rewrite, runtime automation overhaul, lab reset playbook, seat range filter)

---

## Phase 1: Infrastructure — COMPLETE

| Component | Status | Notes |
|---|---|---|
| Project Structure | COMPLETE | Makefile, ansible.cfg, linting config, pre-commit hooks |
| Cluster Topology Config | COMPLETE | 3 categories (facilitator, hub, seat) with counts, sizing, autoscaling |
| ROSA Defaults Config | COMPLETE | Version 4.17, stable channel, configurable async timing |
| Custom Filter Plugin | COMPLETE | `build_cluster_list()` + `to_cluster_list` with credential validation, infra_state support, bastion field passthrough, unit tested (30 cases) |
| Preflight Role | COMPLETE | CLI checks, ROSA login, credential validation, topology constraints |
| AWS Infra Role | COMPLETE | VPC, subnet, NAT gateway, IGW provisioning per account |
| ROSA Account Setup Role | COMPLETE | `rosa init` + account-roles per account |
| Cluster Create | COMPLETE | Async parallel `rosa create cluster` with poll/wait |
| Cluster Wait Ready | COMPLETE | Polls `rosa describe` until state=ready |
| MachinePool Autoscaling | COMPLETE | Configurable min/max replicas per category |
| Post-Provision Verify | COMPLETE | Report generation, state assertions |
| Fleet Status Check | COMPLETE | `make status` with per-cluster state/API/console/version |
| Cluster Destroy | COMPLETE | Async parallel delete with readiness polling |
| IAM Cleanup | COMPLETE | Operator roles + OIDC provider deletion |
| Infrastructure State | COMPLETE | `infra_state.yml` auto-generated, auto-loaded |
| Secret Management | COMPLETE | Vault encrypt/decrypt, gitignored, .example templates |
| Credential Consolidation | COMPLETE | Single source of truth: `secrets/cluster-credentials.yml` holds all per-cluster credentials (AWS, admin, api_url, bastion) and identity (purpose, seat_number, aws_account_id, enabled) |
| Per-Cluster ROSA Tokens | COMPLETE | ROSA tokens extracted from bastion hosts via SSH (`rosa token`), isolated via per-cluster OCM_CONFIG files; global `rosa-token.yml` removed from cluster-ready path |
| Preflight Script | COMPLETE | 189 checks across 10 accounts (bash) |

### Phase 1 Playbooks

| Playbook | Status |
|---|---|
| `preflight.yml` | COMPLETE |
| `setup-infra.yml` | COMPLETE |
| `provision.yml` | COMPLETE |
| `destroy.yml` | COMPLETE |
| `destroy-infra.yml` | COMPLETE |
| `status.yml` | COMPLETE |
| `deploy.yml` | COMPLETE | Scenario dispatch (greenfield, aws-ready, cluster-ready) |

### Phase 1 Roles

| Role | Status |
|---|---|
| `rosa_preflight` | COMPLETE |
| `rosa_cluster` (create, wait_ready, machinepool, workshop_machinepool, verify, status, destroy, destroy_cleanup, discover_rosa_tokens) | COMPLETE |
| `aws_infra` (create, verify, destroy) | COMPLETE |
| `rosa_account_setup` | COMPLETE |
| `scenario_preflight` (greenfield, aws-ready, cluster-ready) | COMPLETE |

---

## Phase 2: Application — IN PROGRESS

### Phase 2 Overview

| Phase | Name | Status |
|-------|------|--------|
| 0 | Discovery | COMPLETE |
| 1 | Skeleton (config, CLI, secrets, tests) | COMPLETE |
| 2 | Showroom Content | COMPLETE |
| 3 | Ansible Roles (17 roles, 10 playbooks) | COMPLETE |
| 4 | Operations & AgnosticV | COMPLETE |
| 5 | Integration & CI/CD | COMPLETE |
| 6 | Testing (rehearsal dry-run) | IN PROGRESS |
| 7 | Hardening (security review, rotation) | NOT STARTED |
| 8 | Event Prep (final validation) | NOT STARTED |

### Phase 2 Playbooks

| Playbook | Status |
|---|---|
| `prepare-cluster.yml` | TESTED_PARTIAL | Hub cluster completes full pipeline (rc=0); facilitator/seats tested through mas_core |
| `prepare-fleet.yml` | TESTED_PARTIAL | Bastion SSH preflight, per-cluster ROSA token extraction, machinepool creation all verified; parallel launch works |
| `validate-cluster.yml` | IMPLEMENTED_NOT_TESTED |
| `validate-fleet.yml` | IMPLEMENTED_NOT_TESTED |
| `repair-cluster.yml` | IMPLEMENTED_NOT_TESTED |
| `rotate-credentials.yml` | IMPLEMENTED_NOT_TESTED |
| `reset-exercises.yml` | IMPLEMENTED_NOT_TESTED |
| `reset-lab.yml` | COMPLETE | Resets student-installed components (logging operators, LokiStack, CLF, groups); protects MAS, Keycloak, LDAP, Showroom |
| `_reset-lab-single.yml` | COMPLETE | Per-cluster reset tasks called by `reset-lab.yml` |
| `decommission-workshop.yml` | IMPLEMENTED_NOT_TESTED |
| `deploy-cluster-ready.yml` | COMPLETE | Parallel 3-play playbook (add_host + strategy:free), per-cluster KUBECONFIG isolation, EFS filesystem discovery from AWS, AWS credential passthrough |
| `_prepare-single-cluster.yml` | COMPLETE | oc login + KUBECONFIG isolation + K8S_AUTH env vars + retry logic + parallel EFS provisioning (aws_efs + efs_csi_driver) + granular per-section readiness checks (identity, lab_accounts, S3, student_accounts, showroom skip when already in place) |
| `_validate-single-cluster.yml` | IMPLEMENTED_NOT_TESTED |

### Phase 2 Roles (21 roles)

| Role | Status | Notes |
|---|---|---|
| aws_efs | COMPLETE | EFS filesystem + NFS security group + mount targets per cluster VPC |
| aws_s3_bucket | COMPLETE | Per-cluster S3 bucket for Loki with encryption + lifecycle |
| efs_csi_driver | COMPLETE | AWS EFS CSI Driver Operator + `efs` StorageClass (RWX) with `uid: 0`/`gid: 0` matching IBM `ocp_efs` role; root identity on access points allows Db2 `chown`; auto-replaces SC if UID/GID wrong (DEC-X-011) |
| acm_hub | COMPLETE | ACM operator + MultiClusterHub on hub cluster; source=redhat-operators, channel dynamically resolved from components.yaml, subscription diagnostics in rescue block (DEC-X-008) |
| config_validation | COMPLETE | Pydantic schema validation |
| cluster_preflight | COMPLETE | OCP connectivity, namespace checks, bastion SSH connectivity |
| event_metadata | COMPLETE | Namespace + ConfigMap + labels |
| acm_registration | COMPLETE | Multi-auth support, disabled by default |
| mas_prerequisites | COMPLETE | Entitlement, cert-manager, MongoDB, SLS, DRO |
| mas_core | COMPLETE | MAS Suite CR, workspace config, self-signed CA ClusterIssuer for MAS 9.2+ (DEC-X-013) |
| maximo_manage | COMPLETE | Manage app install via IBM roles; pre-Db2 `db2u-scc` SCC + PSA namespace labeling for ROSA HCP; stale Db2 auto-cleanup for both Db2uCluster and Db2uInstance CR types; structured diagnostic rescue block (DEC-X-010, DEC-X-011, DEC-X-012) |
| logging_operator | COMPLETE | Logging + Loki operator subscriptions (NOT pre-installed — student exercise) |
| loki_stack | COMPLETE | LokiStack CR with S3 backend (NOT pre-installed — student exercise) |
| log_forwarding | COMPLETE | ClusterLogForwarder to Loki (NOT pre-installed — student exercise) |
| identity_demo | COMPLETE | Keycloak + OpenLDAP + LDAP federation + OIDC |
| lab_accounts | COMPLETE | Per-seat Keycloak user (`lab-seat-XX`) with scoped RBAC for operator exercises |
| mas_edge | COMPLETE | MVI Edge (disabled by default) |
| student_accounts | COMPLETE | Account creation, password management |
| sample_workloads | COMPLETE | Demo assets deployment |
| showroom | COMPLETE | Antora-based workshop content with lab credentials + S3 info |
| event_readiness | COMPLETE | Fleet readiness checks |
| environment_report | COMPLETE | Status reporting |

### Phase 2 CLI

| Component | Status |
|---|---|
| CLI entry point (`cli/main.py`) | COMPLETE |
| Config commands | COMPLETE |
| Cluster commands | IMPLEMENTED_NOT_TESTED |
| Fleet commands | IMPLEMENTED_NOT_TESTED |
| Student commands | IMPLEMENTED_NOT_TESTED |
| Secret commands | COMPLETE |
| Report commands | IMPLEMENTED_NOT_TESTED |
| Config loader | COMPLETE |
| Config schema (Pydantic) | COMPLETE |
| Secret providers (5 backends) | COMPLETE |

### Phase 2 Tests

| Test Suite | Count | Status |
|---|---|---|
| Config loader tests | 14 | PASS |
| Config validation tests | 10 | PASS |
| Secret provider tests | 31 | PASS |
| Filter plugin tests | 42 | PASS | Includes 12 `seat_range()` tests |
| Scenario preflight tests | 24 | PASS |
| Parallel playbook tests | 11 | PASS |
| ACM hub configuration tests | 5 | PASS |
| Db2 security & diagnostics tests | 10 | PASS |
| EFS StorageClass UID/GID tests | 3 | PASS | uid=0/gid=0 matching IBM ocp_efs role |
| Cluster profile tests | 11 | PASS |
| Lab readiness tests | 11 | PASS |
| Structure/syntax checks | 167 | PASS |

### Phase 2 Supporting Content

| Component | Status |
|---|---|
| Showroom content (10 pages + runtime automation) | COMPLETE | Landing page with credentials, hands-on operator install (Ex 5), LDAP-to-Maximo sync + group sync (Ex 6), Keycloak login (Ex 1) |
| ACM manifests (6 files) | COMPLETE |
| AgnosticV catalog (16 files) | SCAFFOLDED |
| Operational runbooks (13 files) | IMPLEMENTED_NOT_TESTED |
| Public content (21 files) | IMPLEMENTED_NOT_TESTED |
| CI/CD pipeline (3 workflow files) | IMPLEMENTED_NOT_TESTED |
| Documentation (35+ docs) | COMPLETE |

---

## Cross-Phase: Deployment Scenarios — COMPLETE

Three independent deployment scenarios for administrators arriving at different starting points.

| Scenario | Make Target | Description | Status |
|----------|-------------|-------------|--------|
| Greenfield | `make deploy-greenfield` | Fresh AWS accounts — VPC + ROSA + app | COMPLETE |
| AWS Ready | `make deploy-aws-ready` | AWS infra exists — ROSA + app | COMPLETE |
| Cluster Ready | `make deploy-cluster-ready INSTANCE_TYPE=m5.2xlarge` | Clusters running — workshop autoscaler + app | COMPLETE |

### Scenario Components

| Component | Status | Notes |
|-----------|--------|-------|
| `scenario_preflight` role | COMPLETE | Dispatcher + 3 scenario task files + shared Phase 2 field validation |
| `workshop_machinepool` action | COMPLETE | Selectable instance type, autoscaling, idempotent check-then-create |
| `deploy.yml` playbook | COMPLETE | Single entry point with `deployment_scenario` parameter dispatch |
| `_deploy-greenfield.yml` | COMPLETE | aws_infra → rosa_account_setup → rosa_cluster → Phase 2 |
| `_deploy-aws-ready.yml` | COMPLETE | aws_infra verify → rosa_account_setup → rosa_cluster → Phase 2 |
| `_deploy-cluster-ready.yml` | COMPLETE | Sequential fallback via `make deploy SCENARIO=cluster-ready` |
| `deploy-cluster-ready.yml` | COMPLETE | Parallel 3-play playbook via `make deploy-cluster-ready` (add_host + strategy:free) |
| Makefile targets (12) | COMPLETE | `wizard`, `deploy`, `deploy-*` (3), `validate-*` (3), `lab-reset`, `lab-reset-fleet`, `lab-test`, `lab-test-fleet` |
| Deploy wizard | COMPLETE | Interactive scenario selection, parameter tables, validate/deploy dispatch |
| Scenario preflight tests (24) | PASS | Role structure, validation coverage, action registration, playbook validation, EFS existence check |
| Parallel playbook tests (11) | PASS | 3-play structure, strategy:free, add_host, python interpreter, KUBECONFIG isolation, ACM hub exclusion, per-cluster EFS provisioning, AWS credential passthrough, no-pause guard |
| ACM hub configuration tests (5) | PASS | Source=redhat-operators, channel matches components.yaml, dynamic channel resolution, subscription diagnostics, CSV-based readiness |
| Db2 security & diagnostics tests (10) | PASS | SCC template exists, required capabilities, SCC before db2 role, namespace PSA labels, rescue captures status/pods/PVCs, ROSA HCP common causes, extended wait timeout, service account grants, stale Db2 cleanup ordering, stale PVC deletion |
| EFS StorageClass UID/GID tests (3) | PASS | Defaults include uid/gid 700, StorageClass includes uid/gid parameters, auto-replace on UID mismatch |

### Scenario Preflight Checks

| Check | Greenfield | AWS Ready | Cluster Ready |
|-------|:---:|:---:|:---:|
| CLI tools (rosa, aws) | Y | Y | Y |
| CLI tools (oc/kubectl) | — | — | Y |
| Credentials & config validation | Y | Y | Y |
| ROSA auth (offline token) | Y | Y | Y |
| Facilitator count == 1 (credential-derived) | Y | Y | Y |
| Initial replicas >= 2 | Y | Y | — |
| AWS account validation (STS) | Y | Y | — |
| AWS infrastructure exists | — | Y | — |
| VPC conflict check | Y | — | — |
| Subnet IDs available | — | Y | — |
| ROSA quota (advisory) | Y | Y | — |
| Cluster existence & health | — | — | Y |
| API reachability | — | — | Y |
| api_url populated | — | — | Y |
| admin_password (defaults to cluster-admin) | — | — | Y |
| Machinepool instance type | — | — | Y |
| EFS filesystem existence (advisory) | — | — | Y |
| Purpose field valid | Y | Y | Y |
| Seat number for attendees | Y | Y | Y |

---

## Cross-Phase: Per-Purpose Component Gating — COMPLETE

Cluster purpose determines which components are installed. Resolved at runtime by `_resolve-cluster-profile.yml`.

| Component | Facilitator | Attendee/Spare | Hub |
|-----------|:-----------:|:--------------:|:---:|
| config_validation | Y | Y | Y |
| cluster_preflight | Y | Y | Y |
| event_metadata | Y | Y | Y |
| acm_registration | default off | default off | Y |
| mas_prerequisites | Y | Y | — |
| mas_core | Y | Y | — |
| maximo_manage | Y | Y | — |
| logging_operator | disabled | disabled | — |
| loki_stack | disabled | disabled | — |
| log_forwarding | disabled | disabled | — |
| identity_demo | Y | Y | — |
| lab_accounts | Y | Y | — |
| mas_edge | default off | default off | — |
| student_accounts | Y | Y | — |
| sample_workloads | Y | Y | — |
| showroom | Y | Y | — |
| event_readiness | full checks | full checks | API only |
| environment_report | Y | Y | Y |

### Gating Implementation

| File | Purpose Gating |
|------|---------------|
| `_resolve-cluster-profile.yml` | Maps purpose → enablement flags (single source of truth) |
| `_prepare-single-cluster.yml` | `when:` conditions on every role using resolved flags + per-section readiness checks (identity, lab_accounts, S3, student_accounts, showroom) |
| `prepare-cluster.yml` | Resolves profile in pre_tasks before role execution |
| `_validate-single-cluster.yml` | Resolves profile so hub gets API-only readiness checks |
| `decommission-workshop.yml` | Gates MAS/Logging/Identity/Student/Showroom removal on purpose |
| `repair-cluster.yml` | Gates all MAS-stack repairs on purpose |

---

## Cross-Phase: Lab Session Readiness Test — COMPLETE

Facilitator-facing validation that every component a student interacts with during the guided lab session is operational.

| Component | Status | Notes |
|-----------|--------|-------|
| `scripts/lab-readiness-test.sh` | COMPLETE | 43 checks across 6 exercises + infrastructure, rich diagnostics, fleet mode |
| `playbooks/lab-readiness.yml` | COMPLETE | Ansible alternative via `kubernetes.core.k8s_info`, YAML report output |
| Makefile targets | COMPLETE | `lab-test`, `lab-test-fleet`, `lab-test-ansible` |
| htpasswd secret fix | COMPLETE | Runtime `readiness/validate.yml` aligned to `masworld-htpasswd-secret` |
| Lab readiness tests | COMPLETE | 11 pytest cases verifying script, playbook, consistency |

### Exercise Coverage

| Exercise | Bash Script Checks | Playbook Checks |
|----------|-------------------|-----------------|
| 1: Access & Readiness | API, Console, MAS Suite, Manage, htpasswd, namespace, RoleBinding, nodes | API, Console, Suite, Manage, htpasswd, namespace, RoleBinding, nodes |
| 2: Navigation & Search | MAS namespaces, CSVs, Subscriptions | MAS namespaces, CSVs, Subscriptions |
| 3: ACM Fleet Management | Event ConfigMap | Event ConfigMap |
| 4: Updates | ClusterVersion, PackageManifest, InstallPlans | ClusterVersion, InstallPlans |
| 5: Observability | STUDENT_EXERCISE — student installs operators, deploys LokiStack, configures CLF | Validates all 3 CSVs, LokiStack Ready, CLF Ready, UIPlugin, collector pods |
| 6: Identity Integration | OAuth, Keycloak, LDAP users/groups, realm, OIDC, RBAC, group sync | OAuth, Keycloak, LDAP, realm, OIDC, mas-admins/mas-users groups |
| Infrastructure | Showroom pod/route, Db2, lab account CRB, S3 credentials CM | Showroom pod, lab account, S3 ConfigMap |

---

## Planned / Not Started

| Feature | Priority | Notes |
|---|---|---|
| Rehearsal dry-run (Phase 6) | HIGH | IN PROGRESS — MAS 9.2 upgrade with fresh IBM collection (DEC-X-012); EFS uid=0/gid=0 for Db2 chown VALIDATED on seat-01 (DEC-X-011); Db2 SCC for ROSA HCP COMPLETE (DEC-X-010); 160 tests pass, 1 skipped |
| Security hardening (Phase 7) | HIGH | Credential rotation, backup procedures |
| Event preparation (Phase 8) | HIGH | Final validation, facilitator runbook walkthrough |
| `cluster_prefix` regex validation | Medium | Prevents shell metacharacter injection |
| ~~MachinePool idempotency check~~ | ~~Low~~ | ~~Implemented in `workshop_machinepool` action~~ |
| Container image for execution | Low | Would remove localhost-only limitation |
| Continuous fleet monitoring | Low | Dashboard or alerting for fleet health |
