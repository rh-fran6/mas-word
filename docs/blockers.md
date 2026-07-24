# Blockers

> **Last updated:** 2026-07-24
>
> Tracks external dependencies and internal decisions that block implementation progress.
> Items are removed when resolved, with a note in `docs/changelog.md`.

---

## Active Blockers

### B-002: Secrets Must Be Populated Manually
- **Status:** Open
- **Impact:** Cannot run any playbooks until `secrets/rosa-token.yml` and `secrets/cluster-credentials.yml` are created from templates and populated with real values.
- **Owner:** Operator (pre-deployment)
- **Details:** `.example` templates exist but contain placeholder values. The `generate-credentials-template.sh` script generates the structure but credentials must come from the operator. Note: `subnet_ids` are no longer required in the credentials file. When using `make setup-infra`, VPC and subnets are created automatically and `subnet_ids` are auto-discovered from `infra_state.yml`.
- **Mitigation:** Preflight checks fail immediately with clear error messages if secrets are missing or incomplete.

### B-005: OCP Version Confirmation (4.21 vs 4.22)
- **Status:** Open
- **Impact:** MAS catalog only lists 4.16-4.21; OCP 4.22 unverified.
- **Owner:** Francis / IBM
- **Details:** Target 4.21 as safe default; document 4.22 risk in risk register.

---

## Resolved Blockers

### B-001: AWS Account Enrollment Required Before First Run
- **Status:** Resolved
- **Resolution:** `make setup-infra` now handles `rosa init` and `rosa create account-roles --hosted-cp` automatically via the `rosa_account_setup` role.

### B-E01: IBM Entitlement Key
- **Status:** Resolved
- **Resolution:** Key available in `secrets/entitlement.dat`.

### B-E02: Cluster API URLs and Kubeconfigs
- **Status:** Resolved
- **Resolution:** seat-01 live (ROSA OCP 4.20.27, us-east-2).

### B-003: S3 Bucket Names and Credentials Not Provisioned
- **Status:** Resolved (2026-07-24)
- **Resolution:** `aws_s3_bucket` role provisions per-cluster S3 buckets with encryption, lifecycle, and public access block. Integrated into `prepare-fleet.yml`. Bucket name generated via `s3_bucket_name` filter. Credentials passed via per-cluster vars.

### B-004: ACM Hub Cluster Not Identified
- **Status:** Resolved (2026-07-24)
- **Resolution:** Hub cluster identified as `lab-hub-1`. `acm_hub` role installs ACM operator + MultiClusterHub on hub cluster. Integrated into `prepare-cluster.yml` with purpose-based gating.

### B-006: Cluster Worker Node Scaling
- **Status:** Resolved (2026-07-24)
- **Resolution:** Workshop machinepool creation automated via bastion SSH + per-cluster ROSA token in `prepare-fleet.yml`. Pool: `workshop-pool` (m5.4xlarge, autoscale 3-8).

### B-007: ROSA CLI Token Expired
- **Status:** Resolved (2026-07-24)
- **Resolution:** Bastion-based ROSA token extraction eliminates need for local `rosa login`. Each cluster's token extracted via SSH to its bastion host.

### B-008: No RWX Storage Class for Db2/Manage
- **Status:** Resolved (2026-07-24)
- **Resolution:** `aws_efs` role provisions EFS filesystem + NFS security group + mount targets per cluster. `efs_csi_driver` role installs AWS EFS CSI Driver Operator and creates `efs` StorageClass with `provisioningMode: efs-ap`. Runs as first role in cluster preparation.

---

## Internal Decisions

| ID | Decision | Status | Impact |
|----|----------|--------|--------|
| D-01 | Database: Db2 per-cluster | DECIDED | Ansible roles assume per-cluster `mas install` with embedded Db2 |
| D-02 | Keycloak: per-cluster | DECIDED | Per-cluster simplifies RBAC; each cluster gets own Keycloak |
| D-03 | S3 buckets: per-cluster | DECIDED | Per-cluster for clean teardown |
| D-04 | Logging: Logging 6.6, Loki 6.6, COO | DECIDED | API: observability.openshift.io/v1 |
| D-05 | MAS Edge: disabled by default | DECIDED | Not relevant to workshop |
| D-06 | Spare cluster strategy | OPEN | Hot spare vs cold spare vs no spare |
| D-07 | Student credential rotation policy | OPEN | Rotate daily vs per-session vs never |
