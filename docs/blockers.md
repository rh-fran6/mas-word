# Blockers

Tracks external dependencies and internal decisions that block implementation progress.

# External Blockers

Record missing credentials, capacity, approvals, product access, unsupported
versions, external dependencies, and other issues that block implementation.

## External Blockers

| ID | Blocker | Owner | Status | Impact | Workaround |
|----|---------|-------|--------|--------|------------|
| B-01 | IBM Entitlement Key not yet available | Francis | OPEN | Cannot run MAS install | Use `secret://` reference; test config/validation without key |
| B-02 | Cluster API URLs and kubeconfigs not provisioned | RHDP / Francis | OPEN | Cannot run any cluster-targeting playbooks | Use PLACEHOLDER values; validate schema only |
| B-03 | S3 bucket names and credentials not provisioned | Francis | OPEN | Cannot configure Loki S3 backend | Use `secret://` references; validate config shape |
| B-04 | ACM hub cluster not identified | Francis | OPEN | Cannot deploy ACM policies or test fleet management | Build manifests offline; validate YAML syntax |
| B-05 | OCP version confirmation (4.21 vs 4.22) | Francis / IBM | OPEN | MAS catalog only lists 4.16-4.21; OCP 4.22 unverified | Target 4.21 as safe default; document 4.22 risk in risk register |

## Internal Decisions

| ID | Decision | Status | Options | Impact |
|----|----------|--------|---------|--------|
| D-01 | Database architecture: Db2 per-cluster vs shared | DECIDED: per-cluster | Per-cluster (isolation) vs shared (resource efficiency) | Ansible roles assume per-cluster `mas install` with embedded Db2 |
| D-02 | Keycloak deployment model | DECIDED: per-cluster | Per-cluster (isolation) vs central (single IdP) | Per-cluster simplifies RBAC; each cluster gets own Keycloak |
| D-03 | S3 bucket isolation | DECIDED: per-cluster | One bucket per cluster vs shared with prefixes | Per-cluster for clean teardown |
| D-04 | Logging stack operator versions | DECIDED | Logging 6.6, Loki 6.6, COO required | API: observability.openshift.io/v1 |
| D-05 | MAS Edge (MVI Edge) inclusion | DECIDED: disabled | Include vs exclude | Disabled by default; not relevant to workshop |
| D-06 | Spare cluster strategy | OPEN | Hot spare vs cold spare vs no spare | Affects fleet.spare_cluster_count default |
| D-07 | Student credential rotation policy | OPEN | Rotate daily vs per-session vs never | Affects credential lifecycle automation |
