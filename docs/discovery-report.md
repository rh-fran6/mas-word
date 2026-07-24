# Discovery Report — MAS World 2026

**Status**: DRAFT — Phase 0
**Date**: 2026-07-19
**Author**: Platform Architecture Team

---

## 1. Repository Assessment

### Current State

The workspace is empty. No prior implementation, configuration, or automation
exists. All artifacts will be built from scratch.

### Proposed Repository Layout

A monorepo with independently deployable subdirectories was selected over
multiple Git repositories.

**Rationale**:
- Atomic cross-component changes during rapid development
- Single CI pipeline with targeted job triggers
- Shared configuration schemas and validation
- Simplified dependency management during the build phase
- Individual subdirectories can be extracted to separate repos post-event if needed

```text
maximo-world/
├── CLAUDE.md
├── prompt.md
├── docs/                              # Cross-cutting documentation
├──          # Ansible collection + CLI + fleet orchestration
├── showroom/           # Attendee-facing Showroom content
├── public-content/     # Sanitized reusable examples
├── acm/               # ACM policies, placements, demo assets
├── agnosticv/          # AgnosticV catalog items
├── operations/         # Runbooks, seat management, dashboards
```

### Repository Decision Record

| Factor | Multi-repo | Monorepo |
|--------|-----------|----------|
| Cross-component atomicity | Requires coordinated PRs | Single commit |
| CI complexity | Multiple pipelines | One pipeline, path filters |
| Schema sharing | Published package | Direct import |
| Deployment independence | Native | Achievable via subdirectory targeting |
| Access control | Native per-repo | Requires path-based rules |
| Post-event extraction | Already separate | Scriptable split |

**Decision**: Monorepo for development velocity. Extract if access-control
requirements emerge.

---

## 2. Infrastructure Assumptions

### What Must Exist Before Automation Runs

| Resource | Provider | Status |
|----------|----------|--------|
| OpenShift clusters (attendee, spare, facilitator) | External provisioner | ASSUMED — not provisioned by this project |
| ACM hub cluster | External provisioner | ASSUMED |
| AWS accounts with networking | AWS | ASSUMED |
| DNS and ingress per cluster | External provisioner | ASSUMED |
| Administrative credentials per cluster | External provisioner | ASSUMED |
| AWS credentials (IAM or workload identity) | AWS | ASSUMED |
| IBM Entitlement Key | IBM | BLOCKER — must be supplied |
| MAS license file | IBM | BLOCKER — must be supplied |
| Git hosting organization | GitHub/GitLab | ASSUMED |
| Container registry | quay.io / internal | ASSUMED |
| CI/CD service | GitHub Actions / Jenkins | ASSUMED |

### What This Project Builds

- Cluster configuration and preparation automation
- Fleet orchestration and management CLI
- MAS installation automation
- Logging/Loki configuration automation
- ACM registration, policies, and demo assets
- Identity/Keycloak configuration
- Student account lifecycle management
- Seat assignment and spare replacement
- Showroom workshop content and runtime automation
- Readiness validation framework
- Operational runbooks and tooling

---

## 3. Key Technical Decisions Required

### 3.1 MAS Version Selection

**Status**: PENDING RESEARCH

Decision factors:
- Must be a currently supported MAS version
- Must be compatible with chosen OpenShift version
- Must support the workshop exercises (Manage, updates, Edge)
- Installation must complete within the preparation window (< 4 hours)

### 3.2 OpenShift Version Selection

**Status**: PENDING RESEARCH

Decision factors:
- Must be supported by chosen MAS version
- Must be supported by RHACM version
- Must support current Logging/Loki operators
- ROSA HCP vs self-managed affects OAuth capabilities

### 3.3 Database Architecture for MAS

**Status**: REQUIRES ARCHITECTURE DECISION

Options evaluated:

| Option | Isolation | Cost | Complexity | Blast Radius |
|--------|-----------|------|------------|--------------|
| Db2 inside each cluster | Full | High (50× resources) | Low per cluster | Single seat |
| Shared RDS/Aurora with per-seat databases | Logical | Lower | Medium | Shared service |
| Shared Db2 on dedicated cluster | Logical | Medium | Medium | Shared service |

**Recommendation**: Db2 Warehouse Operator inside each cluster (if MAS supports it)
or AWS RDS with per-seat database isolation. Final decision requires MAS
documentation review for supported database configurations.

### 3.4 Keycloak Deployment Model

**Status**: REQUIRES ARCHITECTURE DECISION

Options:

| Option | Isolation | Resources | Failure Domain |
|--------|-----------|-----------|----------------|
| Per attendee cluster | Full | 50× Keycloak | Single seat |
| Shared on ACM hub | None | 1× Keycloak | All seats |
| Shared on dedicated cluster | None | 1× Keycloak | All seats |
| External managed (e.g., RHSSO) | Depends | External | External |

**Recommendation**: Per attendee cluster for workshop isolation. Keycloak is
lightweight enough that 50 instances are manageable. This avoids a single
point of failure affecting all attendees.

### 3.5 S3 Isolation Model

**Status**: DECIDED — Bucket per cluster

One S3 bucket per attendee cluster:
```text
mas-world-2026-seat-01-loki-<suffix>
```

Rationale:
- Clean IAM isolation per seat
- No risk of cross-tenant data access
- Simple lifecycle cleanup per seat
- Marginally more AWS resources but negligible cost

### 3.6 Logging API Selection

**Status**: PENDING RESEARCH

The OpenShift Logging stack has undergone significant API changes. Must verify:
- Whether `logging.openshift.io/v1` ClusterLogForwarder is current or deprecated
- Whether `observability.openshift.io/v1` is the current API
- Which log collector (Vector vs Fluentd) is current
- LokiStack API version and fields

---

## 4. Unanswered Dependencies

### External Blockers (Cannot Proceed Without)

| ID | Dependency | Owner | Impact |
|----|-----------|-------|--------|
| B-01 | IBM Entitlement Key | Francis / IBM | Cannot install MAS |
| B-02 | MAS License File | Francis / IBM | Cannot activate MAS |
| B-03 | AWS account credentials | Francis | Cannot create S3 buckets or IAM |
| B-04 | Cluster kubeconfigs/credentials | Provisioner | Cannot configure clusters |
| B-05 | ACM hub access | Francis | Cannot register managed clusters |

### Internal Decisions Needed

| ID | Decision | Impact |
|----|----------|--------|
| D-01 | Exact MAS version to pin | Affects all MAS automation |
| D-02 | Exact OpenShift version range | Affects preflight checks |
| D-03 | Database architecture | Affects MAS installation roles |
| D-04 | ROSA HCP or self-managed OCP | Affects OAuth/identity module |
| D-05 | Keycloak deployment topology | Affects identity role |
| D-06 | MAS Edge scope | Affects whether Edge role is implemented |
| D-07 | CI/CD platform (GitHub Actions vs other) | Affects pipeline implementation |

### Non-Blocking Research Items

| ID | Item | Status |
|----|------|--------|
| R-01 | MAS supported versions matrix | RESEARCHING |
| R-02 | RHACM API versions | RESEARCHING |
| R-03 | Logging/Loki current APIs | RESEARCHING |
| R-04 | Showroom template structure | RESEARCHING |
| R-05 | AgnosticV catalog schema | TODO |
| R-06 | AgnosticD workload conventions | TODO |

---

## 5. Scope Confirmation

### In Scope

1. Post-provisioning cluster configuration automation
2. MAS Core + Maximo Manage installation
3. Logging Operator + Loki + S3 configuration
4. ACM registration, policies, drift demo
5. Identity/Keycloak preconfiguration
6. MAS updates exercise (bounded, deterministic)
7. Student accounts, RBAC, credential lifecycle
8. Seat assignment and spare replacement
9. Showroom content (5 lab segments + readiness + conclusion)
10. Runtime validation, solve, and reset automation
11. Fleet orchestration CLI
12. Operational runbooks
13. CI/CD pipelines
14. Security controls and testing

### Out of Scope

1. OpenShift cluster provisioning
2. AWS account creation
3. DNS zone management
4. Network infrastructure
5. Full MAS update during live session
6. Production MAS sizing or HA
7. Long-term log retention / SIEM integration (discussed, not implemented)

---

## 6. Timeline Assessment

| Phase | Duration Estimate | Dependencies |
|-------|------------------|--------------|
| Phase 0 — Discovery | 1 day | None |
| Phase 1 — Skeleton | 1 day | Phase 0 |
| Phase 2 — Reference cluster | 3-5 days | Phase 1 + B-01..B-05 |
| Phase 3 — Student identity | 1 day | Phase 2 |
| Phase 4 — ACM hub | 1-2 days | Phase 2 + B-05 |
| Phase 5 — Showroom | 3-5 days | Phases 2-4 |
| Phase 6 — Small fleet | 2-3 days | Phase 5 |
| Phase 7 — Full rehearsal | 2-3 days | Phase 6 |
| Phase 8 — Event release | 1-2 days | Phase 7 |

**Critical path**: IBM credentials (B-01, B-02) and cluster access (B-04)
gate Phase 2. All automation scaffolding, schemas, Showroom content structure,
and non-cluster-dependent work can proceed in parallel.
