# Known Limitations — MAS World 2026

**Status**: DRAFT — Phase 0
**Date**: 2026-07-19

---

## Summary

| ID | Limitation | Impact | Workaround | Status |
|---|---|---|---|---|
| LIM-01 | ROSA HCP OAuth restrictions | Cannot modify OAuth CR directly | Alternative IDP configuration paths | DOCUMENTED |
| LIM-02 | Keycloak uses community operator | Not production-supported | Acceptable for workshop demonstration | ACCEPTED |
| LIM-03 | Workshop sizing does not equal production | Attendees may assume demo sizing is sufficient | Clear documentation and callouts in every module | DOCUMENTED |
| LIM-04 | MAS installation requires 2-4 hours | Cannot install during live session | Pre-install on all clusters before event | MITIGATED |
| LIM-05 | MAS requires cluster-admin for install | Cannot use least-privilege during install phase | Restrict cluster-admin to automation only | ACCEPTED |
| LIM-06 | Db2 per-cluster resource consumption | High aggregate resource usage across fleet | Minimal Db2 configuration; monitor node capacity | ACCEPTED |
| LIM-07 | S3 static IAM keys if IRSA unavailable | Long-lived credentials require rotation | Automated rotation and post-event revocation | MITIGATED |
| LIM-08 | No multi-tenancy within cluster | One student per cluster; high cluster count | Configuration-driven fleet sizing | ACCEPTED |
| LIM-09 | MAS update exercise time constraint | Full update cannot complete in 20 minutes | Inspection-based approach with pre-staged state | MITIGATED |
| LIM-10 | OCP 4.22 unverified for MAS | Latest MAS catalog supports 4.16-4.21 only | Pin clusters to OCP 4.21 | MITIGATED |
| LIM-11 | ACM attendee access is view-only | Attendees cannot interact with ACM directly | Presenter-led demonstration; attendee verifies on own cluster | ACCEPTED |
| LIM-12 | Conference network dependency | All access through conference WiFi | Bandwidth planning; offline fallback materials | RISK_ACCEPTED |
| LIM-13 | MAS Edge (MVI Edge) disabled | Requires NVIDIA GPUs not available | Disabled by default; inspect-only if enabled | ACCEPTED |
| LIM-14 | AgnosticV catalog manual fallback | Skill-generated catalog not yet available | Manual implementation following RHDP conventions | IN_PROGRESS |

---

## Detailed Limitations

### LIM-01: ROSA HCP OAuth Restrictions

**Category**: Platform
**Severity**: Medium
**Affected modules**: Identity

ROSA with Hosted Control Planes (HCP) does not allow direct modification of the OAuth custom resource on the cluster. The OAuth server runs on the hosted control plane, which is managed by Red Hat and not accessible to cluster administrators.

**Impact**: Standard OpenShift IDP configuration workflows that modify the `OAuth` CR (e.g., adding an HTPasswd or OIDC identity provider via `oc edit oauth cluster`) do not work on HCP clusters. Workshop instructions that reference this workflow must be adapted.

**Workaround**: Use the ROSA CLI (`rosa create idp`) or the OCM API to configure identity providers. Alternatively, use the pre-configured Keycloak OIDC integration that is set up by the preparation automation. The identity module clearly identifies which configuration paths are available on HCP versus self-managed clusters.

**Decision record**: `docs/decision-log.md` — IDP configuration approach

---

### LIM-02: Keycloak Operator (Community)

**Category**: Software
**Severity**: Low
**Affected modules**: Identity

The workshop uses the Keycloak Operator from OperatorHub (community distribution) rather than Red Hat Single Sign-On (RHSSO) or Red Hat Build of Keycloak (RHBK). The community operator is not covered by a Red Hat support subscription.

**Impact**: The Keycloak instance used in the workshop is not production-supported. Attendees should not assume the demonstrated deployment model is suitable for production without evaluating RHBK or an equivalent enterprise-supported identity provider.

**Workaround**: Acceptable for a workshop demonstration environment. The identity module includes a production considerations section that recommends RHBK or an external enterprise identity provider for production deployments.

---

### LIM-03: Workshop Sizing Does Not Equal Production

**Category**: Architecture
**Severity**: Medium
**Affected modules**: All

Workshop resource allocations are minimized to reduce cost and provisioning time across the fleet. This applies to every major component.

| Component | Workshop Sizing | Production Minimum |
|---|---|---|
| LokiStack | `1x.extra-small` | `1x.medium` or larger |
| Keycloak | 1 replica, 512Mi memory | HA, 2+ replicas, 2Gi+ memory |
| Db2 | Minimal config, ~8GB RAM, 4 CPU | HA, 32GB+ RAM, 8+ CPU |
| Loki retention | 24-48 hours | 30-90 days or longer |
| S3 lifecycle | 7-day expiration | Retention per compliance policy |
| MAS Manage | Single replica | HA, multiple replicas |

**Impact**: Attendees may incorrectly use workshop sizing as a reference for production deployments.

**Workaround**: Every module that deploys or configures a component includes a clearly marked production considerations section. The public content repository includes a dedicated production-versus-demo architecture guide. Showroom callout blocks distinguish demo values from production recommendations.

---

### LIM-04: MAS Installation Time

**Category**: Operational
**Severity**: High
**Affected modules**: All (dependency)

Maximo Application Suite installation, including MAS Core, Maximo Manage, Db2, and all prerequisites, requires approximately 2-4 hours per cluster depending on cluster performance and registry pull times.

**Impact**: MAS cannot be installed during the live workshop session. All clusters must be fully prepared before the event. This means the preparation automation must complete successfully across the entire fleet (50 attendee + 5 spare + 1 facilitator clusters) with adequate time for validation and remediation.

**Workaround**: Pre-install MAS on all clusters using the fleet preparation automation. Begin preparation at least 72 hours before the event to allow for retries and spare replacement. The fleet orchestrator supports configurable concurrency (default: 5 clusters) and retry with exponential backoff.

---

### LIM-05: MAS Requires Cluster-Admin for Installation

**Category**: Security
**Severity**: Medium
**Affected modules**: MAS installation (automation only)

MAS installation requires cluster-admin privileges to install CRDs, create cluster-scoped resources, configure operators, and set up required namespaces.

**Impact**: The automation service account used for cluster preparation must have cluster-admin access. This cannot be reduced to a namespace-scoped role during the installation phase.

**Workaround**: Cluster-admin credentials are used only by the preparation automation and are never exposed to attendees, Showroom, or browser terminals. Credentials are retrieved at runtime from the configured secret provider, cached in memory only, and removed after each cluster operation. Post-installation, attendee accounts use a restricted `basic-user` ClusterRole with namespace-scoped `admin` in their assigned namespace only.

---

### LIM-06: Db2 Per-Cluster Resource Consumption

**Category**: Capacity
**Severity**: Medium
**Affected modules**: MAS prerequisites, fleet sizing

Each attendee cluster runs its own Db2 instance as the Maximo Manage database. The minimal workshop configuration consumes approximately 8GB RAM and 4 CPU cores per instance.

**Impact**: Across the full fleet of 56 clusters, aggregate Db2 resource consumption is significant (~448GB RAM, 224 CPU cores). Worker nodes must be sized to accommodate Db2 alongside MAS Core, Manage, logging, and Keycloak.

**Workaround**: Use minimal Db2 configuration for workshop purposes. Worker node sizing (instance type, count) must account for Db2 resource requirements during capacity planning. The cluster preflight checks validate available schedulable CPU and memory before installation proceeds. See `docs/decision-log.md` for the database architecture decision.

---

### LIM-07: S3 Static IAM Keys

**Category**: Security
**Severity**: Medium
**Affected modules**: Observability (Loki object storage)

If IRSA (IAM Roles for Service Accounts) or pod identity is not available or not configured for the cluster platform, LokiStack requires static IAM access keys to authenticate to S3.

**Impact**: Static IAM access keys are long-lived credentials that must be securely stored, rotated, and revoked. If compromised, they could allow unauthorized access to log data in S3.

**Workaround**: When static keys are required:

- Keys are generated automatically by the preparation automation
- Keys are stored in the configured secret provider (AWS Secrets Manager)
- Each cluster receives a unique IAM user scoped to its own S3 bucket only
- Keys are injected into the cluster as a Kubernetes Secret
- Automated rotation is supported via `rotate-student-credentials`
- All keys are revoked during post-event teardown
- Cross-bucket access is verified by negative security tests (SEC-05)

Prefer IRSA or pod identity where the platform supports it.

---

### LIM-08: No Multi-Tenancy Within Cluster

**Category**: Architecture
**Severity**: Low
**Affected modules**: Fleet sizing, cost

The workshop uses a one-student-per-cluster model. Each attendee receives a dedicated OpenShift cluster with their own MAS, Db2, logging, and Keycloak instances.

**Impact**: The fleet requires 50 attendee clusters plus spares, which increases infrastructure cost and preparation time compared to a shared-cluster model.

**Workaround**: This is an intentional architecture decision. MAS does not support lightweight multi-tenancy within a single cluster for the workshop use case. A dedicated cluster per attendee provides full isolation, eliminates noisy-neighbor effects, and ensures each attendee has an independent environment for all exercises. Fleet size is configuration-driven and can be adjusted for development (1 cluster) or rehearsal (5 clusters) without code changes.

---

### LIM-09: MAS Update Exercise Time Constraint

**Category**: Content
**Severity**: Medium
**Affected modules**: Updates

A full MAS update (operator upgrade, operand reconciliation, database migration) can take 30-90 minutes depending on the update path and cluster performance. The workshop allocates 20 minutes for the updates module.

**Impact**: Attendees cannot initiate and complete a full MAS update during the session.

**Workaround**: The updates module uses an inspection-based approach:

1. Examine a pre-staged update that has already completed on the facilitator cluster
2. Review the update status history, operator versions, and reconciliation events
3. Inspect the update plan and compatibility requirements
4. Discuss production update procedures including backup, maintenance windows, rollback, and change approval
5. Optionally initiate a small configuration change that completes quickly to demonstrate lifecycle behavior

The module clearly states that a full update takes significantly longer and describes the production change management process.

---

### LIM-10: OCP 4.22 Unverified for MAS

**Category**: Compatibility
**Severity**: High
**Affected modules**: All (platform dependency)

As of 2026-07-19, the latest IBM MAS operator catalog supports OpenShift versions 4.16 through 4.21. OpenShift 4.22 has not been verified or listed as supported by IBM.

**Impact**: Clusters running OCP 4.22 may encounter unsupported operator installation failures, CRD incompatibilities, or runtime issues with MAS components.

**Workaround**: Pin all workshop clusters to OpenShift 4.21. The cluster preflight checks validate the OpenShift version against the compatibility matrix and will fail clusters running unsupported versions. See `docs/compatibility-matrix.md` for the full version support matrix.

---

### LIM-11: ACM Attendee Access Is Presenter-Led Only

**Category**: Content
**Severity**: Low
**Affected modules**: ACM Fleet Management

Attendees do not receive direct access to the ACM hub console or API. The ACM demonstration is led entirely by the presenter from the facilitator cluster.

**Impact**: Attendees watch the fleet management demonstration on the presenter's screen rather than interacting with ACM themselves. This limits hands-on engagement for the ACM module.

**Workaround**: After the presenter-led demonstration, attendees verify a safe propagated resource (e.g., an event marker ConfigMap) on their own cluster. This confirms that ACM policy propagation reached their environment without requiring attendees to have any ACM administrative access. The attendee exercise takes approximately 2 minutes and has validation and solve automation.

**Security justification**: Granting attendees any level of ACM hub access would require a thorough security review. Even read-only ACM access could expose fleet topology, cluster credentials, policy details, and other attendee cluster information. The presenter-led model eliminates this risk entirely.

---

### LIM-12: Conference Network Dependency

**Category**: Operational
**Severity**: High
**Affected modules**: All (access dependency)

All attendee access to workshop environments (Showroom, OpenShift console, Maximo, browser terminals, Loki) goes through the conference venue WiFi network.

**Impact**: Network congestion, bandwidth limitations, or WiFi outages at the venue could degrade or prevent attendee access to their environments. With 50 attendees simultaneously accessing browser-based consoles and terminals, bandwidth consumption is significant.

**Workaround**:

- Coordinate with venue network team for bandwidth allocation
- Test network capacity during rehearsal if venue access is available
- Pre-pull container images on all clusters to minimize download during the session
- Minimize large data transfers in attendee exercises
- Prepare offline reference materials as backup
- Identify a backup network access method (mobile hotspot, wired connection for presenter)
- Include network troubleshooting in the event runbook

---

### LIM-13: MAS Edge (MVI Edge) Disabled by Default

**Category**: Component
**Severity**: Low
**Affected modules**: MAS Edge

Maximo Visual Inspection (MVI) Edge requires NVIDIA GPU-equipped nodes for inference workloads. Workshop clusters do not include GPU nodes.

**Impact**: MVI Edge cannot be deployed or demonstrated in a functional state on the workshop clusters.

**Workaround**: MAS Edge is disabled by default in the component configuration (`components.mas_edge.enabled: false`). If a cluster with GPU nodes is available, MAS Edge can be enabled via cluster-specific override. When disabled, readiness checks report MAS Edge as `NOT_APPLICABLE` rather than `FAIL`. The workshop content includes a brief description of MAS Edge capabilities and architecture without requiring a live deployment.

---

### LIM-14: AgnosticV Catalog — Manual Fallback

**Category**: Tooling
**Severity**: Medium
**Affected modules**: RHDP integration

The AgnosticV catalog configuration was scaffolded using manual implementation rather than the RHDP Skills Marketplace `/agnosticv:catalog-builder` skill. The skill-generated catalog is not yet available due to the existing-cluster integration model not being natively supported by the catalog builder.

**Impact**: The catalog structure may not match the latest RHDP conventions generated by the skill. Manual maintenance is required until the skill supports the existing-cluster workflow.

**Workaround**: The catalog was implemented following current RHDP documentation and AgnosticV schema conventions. The implementation is marked as `MANUAL_FALLBACK_SKILL_UNAVAILABLE` in `docs/rhdp-skills-execution-log.md`. Once the catalog builder skill supports existing-cluster workflows, the catalog should be regenerated and validated. The `/agnosticv:validator` skill is used to validate the manually created catalog against the AgnosticV schema.

**Gaps documented**:

1. Existing-cluster integration model not supported by catalog builder
2. RHDP platform team coordination required for cluster pool registration
3. Boundary between AgnosticV catalog and external fleet provisioning requires clarification

See `docs/workarounds.md` for full details.
