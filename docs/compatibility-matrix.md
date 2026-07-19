# Compatibility Matrix — MAS World 2026

**Status**: VERIFIED (from official documentation)  
**Date**: 2026-07-19  
**Target Deployment**: August 17, 2026

---

## 1. Platform Baseline

| Component | Selected Version | Channel / Catalog | Support Status | Source |
|-----------|-----------------|-------------------|----------------|--------|
| OpenShift Container Platform | **4.22** (EUS) | — | Full Support (GA Jun 9, 2026) | access.redhat.com/support/policy/updates/openshift |
| IBM MAS | **9.1.x** | `9.1.x` | GA — Recommended | ibm-mas.github.io/cli/catalogs |
| IBM MAS Catalog | **v9-260625-amd64** (or latest available) | — | Current monthly release | ibm-mas.github.io/cli/catalogs |
| RHACM | **2.16** (or 2.17 if verified) | — | GA (Mar 10, 2026) | access.redhat.com/articles/7136928 |
| OpenShift Logging | **6.6** | `stable-6.6` | Current (Jul 14, 2026) | access.redhat.com/support/policy/updates/openshift_operators |
| Loki Operator | **6.6** | `stable-6.6` | Current (Jul 14, 2026) | access.redhat.com/support/policy/updates/openshift_operators |
| OpenShift GitOps | **1.21** | `gitops-1.21` or `latest` | Current (Jun 2026) | docs.redhat.com/en/documentation/red_hat_openshift_gitops |

---

## 2. MAS Prerequisites

| Prerequisite | Version | Notes | Source |
|-------------|---------|-------|--------|
| MongoDB | **7.0** or **8.0** CE | Deployed in-cluster by `mas install` | ibm-mas.github.io/ansible-devops/roles/mongodb |
| IBM SLS | **3.12.x** | Bundled with catalog | ibm-mas.github.io/cli/catalogs/v9-260326-amd64 |
| cert-manager | Red Hat Certificate Manager Operator | Cluster-scoped | ibm-mas.github.io/ansible-devops/roles/cert_manager |
| IBM Data Reporter (DRO) | Bundled | Replaces deprecated UDS | ibm-mas.github.io/cli/catalogs |
| Cloud Native PostgreSQL | **1.25.x** | Bundled with catalog | ibm-mas.github.io/cli/catalogs |

---

## 3. Maximo Manage Database Options

| Database | Minimum Version | Recommended for Workshop | Source |
|----------|---------------|-------------------------|--------|
| IBM Db2 | **11.5** Standard Edition | Yes — in-cluster via Db2U operator | ibm.com/docs/en/masv-and-l/cd |
| Oracle Database | 19c (19.3) | No — external dependency | ibm.com/docs/en/masv-and-l/cd |
| MS SQL Server | 2019 | No — external dependency | ibm.com/docs/en/masv-and-l/cd |
| IBM Db2 Warehouse | In-cluster or standalone | Alternative — via Db2U operator | ibm.com/docs/en/masv-and-l/cd |

**Workshop decision**: Use Db2 installed inside each cluster via `mas install`.
This provides full isolation per attendee with no shared database service.

---

## 4. Storage Requirements

| Requirement | Class | AWS Recommendation |
|-------------|-------|-------------------|
| ReadWriteOnce (RWO) | Default block storage | `gp3-csi` |
| ReadWriteMany (RWX) | Shared filesystem | `efs` (Amazon EFS CSI) |

Both RWO and RWX storage classes must exist before MAS installation.

---

## 5. MAS Installation Method

| Method | Tool | Recommended | Source |
|--------|------|-------------|--------|
| MAS CLI | `mas install` (container or `uvx`) | **Yes** — automates all prerequisites | ibm-mas.github.io/cli/guides/install |
| Ansible Collection | `ibm.mas_devops` v37.10.0 | For custom automation wrapping | ibm-mas.github.io/ansible-devops |
| OperatorHub manual | Manual subscription + Suite CR | No — error-prone for fleet | ibm.com/docs |

**Workshop approach**: Use `ibm.mas_devops` Ansible collection within our
automation roles for maximum control and idempotency, wrapping the same
automation that `mas install` uses internally.

---

## 6. MAS Administrative Permission Mode

| Mode | Workshop Suitability | Notes |
|------|---------------------|-------|
| **Cluster** (default) | **Selected** | Full functionality, DNS integration, all cert types |
| Namespaced | Not suitable | No DNS integration, limited cert types |
| Minimal | Not suitable | Cannot manage application lifecycle from MAS UI |

---

## 7. OpenShift Logging Stack

| Component | Version | API | Notes |
|-----------|---------|-----|-------|
| Logging Operator | **6.6** | — | Single operator for log collection config |
| Loki Operator | **6.6** | `loki.grafana.com/v1` | LokiStack CR |
| ClusterLogForwarder | — | **`observability.openshift.io/v1`** | NEW API — old `logging.openshift.io/v1` is removed in 6.x |
| Log Collector | **Vector** | — | Fluentd removed in 6.x |
| Cluster Observability Operator | Required | — | Required third operator in 6.x stack |

### Critical API Change

The ClusterLogForwarder API moved from `logging.openshift.io/v1` to
`observability.openshift.io/v1` in Logging 6.x. The old API is **removed**,
not deprecated. The `ClusterLogging` CR is eliminated — its fields merged
into `ClusterLogForwarder`.

### LokiStack Configuration

```yaml
apiVersion: loki.grafana.com/v1
kind: LokiStack
metadata:
  name: logging-loki
  namespace: openshift-logging
spec:
  size: 1x.extra-small       # Suitable for workshop (< production)
  storage:
    schemas:
      - version: v13
        effectiveDate: "2024-01-01"
    secret:
      name: logging-loki-s3
      type: s3
  storageClassName: gp3-csi
  tenants:
    mode: openshift-logging
```

### S3 Storage Secret Format

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: logging-loki-s3
  namespace: openshift-logging
stringData:
  access_key_id: "<AWS_ACCESS_KEY_ID>"
  access_key_secret: "<AWS_SECRET_ACCESS_KEY>"
  bucketnames: "<S3_BUCKET_NAME>"
  endpoint: "https://s3.<REGION>.amazonaws.com"
  region: "<REGION>"
```

---

## 8. RHACM API Versions

| Resource | apiVersion | Notes |
|----------|-----------|-------|
| ManagedClusterSet | `cluster.open-cluster-management.io/v1beta2` | v1beta1 deprecated |
| ManagedClusterSetBinding | `cluster.open-cluster-management.io/v1beta2` | — |
| Placement | `cluster.open-cluster-management.io/v1beta1` | Replaces deprecated PlacementRule |
| PlacementDecision | `cluster.open-cluster-management.io/v1beta1` | Auto-created |
| Policy | `policy.open-cluster-management.io/v1` | — |
| ConfigurationPolicy | `policy.open-cluster-management.io/v1` | — |
| PlacementBinding | `policy.open-cluster-management.io/v1` | — |
| PolicySet | `policy.open-cluster-management.io/v1beta1` | — |

---

## 9. Showroom Deployment

| Component | Version | Source |
|-----------|---------|--------|
| Showroom Helm chart | `showroom-single-pod` v2.1.8 | github.com/rhpds/showroom-deployer |
| UI Theme | `rhdp_showroom_theme` v2.0.3 | github.com/rhpds/rhdp_showroom_theme |
| Content container | `quay.io/rhpds/showroom-content:v1.4.2` | — |
| Terminal container | `quay.io/rhpds/openshift-showroom-terminal-ocp:latest` | Pin to digest |
| Wetty container | `quay.io/rhpds/wetty:v2.7.6` | — |
| Git cloner init | `quay.io/rhpds/git-cloner:v1.1.5` | — |
| Antora builder init | `quay.io/rhpds/antora:v1.3.0` | — |

### Key Showroom Conventions

- `site.yml` at repo root (not `default-site.yml`)
- Content in `content/modules/ROOT/pages/`
- `ui-config.yml` for split-pane tabs
- `${DOMAIN}` placeholder in tab URLs resolved at runtime
- AsciiDoc attributes in `content/antora.yml` for variable injection
- `role="execute"` on code blocks for click-to-terminal
- AgnosticD collection `agnosticd.showroom` v1.5.1+ for deployment

---

## 10. MAS Edge Assessment

**Finding**: There is no standalone product called "MAS Edge." The term
refers to **Maximo Visual Inspection Edge (MVI Edge)**, which:

- Runs outside OpenShift on standalone hardware with Docker
- Requires NVIDIA GPUs (16GB+ VRAM)
- Is an add-on for AI vision inspection, not relevant to the workshop exercises

**Decision**: MAS Edge is **disabled by default** (`components.mas_edge.enabled: false`).
If workshop content references edge concepts, it will be discussion-only,
not a deployed component.

---

## 11. Version Pinning Strategy

For the event release:

| Artifact | Pinning Method |
|----------|---------------|
| OCP version | Cluster provisioner controls this |
| MAS catalog | Specific catalog tag (e.g., `v9-260625-amd64`) |
| Operator channels | Pinned channel (e.g., `9.1.x`, `stable-6.6`) |
| Ansible collections | Pinned in `requirements.yml` |
| Container images | Digest-pinned where possible |
| Showroom images | Tag + digest |
| Python dependencies | Pinned in `pyproject.toml` ranges |

---

## 12. Unverified Items

| Item | Status | Impact |
|------|--------|--------|
| RHACM 2.17 exact OCP support matrix | Requires Red Hat login | Use 2.16 if 2.17 unconfirmed |
| OCP 4.22 support in MAS v9-260625 catalog | Catalog lists 4.16-4.21 | May need 4.21 instead of 4.22 |
| Oracle 21c / SQL Server 2022 for Manage | IBM SPCR inaccessible | Not relevant — using Db2 |
| LokiStack `1x.pico` size | Unconfirmed in Red Hat docs | Using `1x.extra-small` |
| MVI Edge NVIDIA Ampere support | Docs returned 403 | Not deploying Edge |

### Critical Note on OCP 4.22 vs MAS

The latest verified MAS catalog (`v9-260625`) supports OCP 4.16–4.21.
**OCP 4.22 support is UNVERIFIED for MAS.** If clusters are provisioned
on 4.22, verify MAS catalog compatibility first. Fallback: use OCP 4.21.
