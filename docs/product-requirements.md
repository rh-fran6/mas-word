# Product Requirements Document — MAS World 2026

**Status**: DRAFT — Phase 0
**Date**: 2026-07-19

---

## 1. Problem Statement

MAS World 2026 is a conference workshop scheduled for August 17, 2026, where
up to 50 attendees will each work through hands-on exercises on IBM Maximo
Application Suite running on individual OpenShift clusters. Each attendee
cluster must be fully configured with MAS Core, Maximo Manage, OpenShift
Logging with Loki, identity provider integration, and Red Hat Showroom-based
guided instructions.

Manual setup of 50+ identically configured clusters is infeasible given the
complexity of each environment (MAS installation alone takes 2-4 hours per
cluster) and the need for consistent, validated, secure configurations across
the fleet.

This project delivers an automated, idempotent, secure, and observable system
that transforms pre-provisioned OpenShift clusters into fully prepared workshop
environments through configuration-driven automation. The system must support
fleet sizes from 1 (development) to 50+ (event) without code changes, handle
failures gracefully with spare-cluster replacement, and enforce attendee
isolation throughout.

---

## 2. Target Users

| Role | Person(s) | Count | Primary Interactions |
|------|-----------|-------|---------------------|
| **Attendee** | Conference participants | Up to 50 | Access Showroom, run guided exercises, use OCP console, access Maximo, query logs |
| **Presenter** | Ernie Steagall (ONEOK) | 1 | Drive live demonstrations, share screen, present ACM fleet management |
| **Lab Owner** | Francis Anyaegbu (Red Hat) | 1 | Run fleet automation, manage seat assignments, support attendees, own environment |
| **Observability Lead** | Myles Vivian (Cohesive) | 1 | Own observability content, support attendees during logging exercises |
| **Platform Engineer** | Automation operator | 1-2 | Configure environments, run CI, manage secrets, validate fleet |

---

## 3. User Stories

### 3.1 Attendee Stories

| ID | Story | Acceptance |
|----|-------|------------|
| US-01 | As an attendee, I want a pre-configured environment so I can focus on learning rather than setup. | Cluster is READY with all components installed before the session begins. |
| US-02 | As an attendee, I want clear instructions with validation so I know I completed exercises correctly. | Every exercise has a validate button or command that reports PASS or FAIL with guidance. |
| US-03 | As an attendee, I want a solve button so I can recover if I get stuck. | Every critical exercise has solve automation that completes the task for the attendee. |
| US-04 | As an attendee, I want my environment isolated from others so my mistakes do not affect other attendees. | RBAC prevents cross-namespace access; S3 policies prevent cross-bucket access; negative tests prove isolation. |

### 3.2 Presenter Stories

| ID | Story | Acceptance |
|----|-------|------------|
| US-05 | As a presenter, I want a reliable ACM demonstration so I can show fleet management without risk of failure. | ACM demo uses a safe ConfigMap drift on the facilitator cluster only; repeatable; no impact on attendee clusters. |
| US-06 | As a presenter, I want a controlled MAS update exercise so attendees can observe update behavior in bounded time. | Update exercise uses a pre-staged or scoped component update that completes within 20 minutes. |

### 3.3 Lab Owner Stories

| ID | Story | Acceptance |
|----|-------|------------|
| US-07 | As a lab owner, I want one-command fleet preparation so I can set up the environment efficiently. | `masworld fleet prepare --env event` prepares all clusters with configurable concurrency. |
| US-08 | As a lab owner, I want spare cluster replacement so I can handle failures without attendee impact. | `masworld seat replace --seat N --cluster spare-M` completes transactional replacement in under 10 minutes. |
| US-09 | As a lab owner, I want credential rotation so I can respond to security incidents during the event. | `masworld student rotate --seat N` generates new credentials, updates the cluster, and regenerates the access card. |
| US-10 | As a lab owner, I want exercise reset so I can help stuck attendees start fresh. | `masworld exercise reset --cluster seat-N --module observability` returns the exercise to its initial state. |

### 3.4 Facilitator Stories

| ID | Story | Acceptance |
|----|-------|------------|
| US-11 | As a facilitator, I want a fleet dashboard so I can monitor environment health during the event. | Fleet status report shows READY/WARNING/FAILED counts, per-cluster status, and last validation time. |
| US-12 | As a facilitator, I want operational runbooks so I can handle common issues without escalation. | Runbooks cover pre-event, event morning, during-event, and post-event procedures. |

### 3.5 Platform Engineer Stories

| ID | Story | Acceptance |
|----|-------|------------|
| US-13 | As a platform engineer, I want configuration-driven automation so I can use different fleet sizes without code changes. | Changing `fleet.attendee_cluster_count` from 50 to 5 requires only a configuration change. |
| US-14 | As a platform engineer, I want schema-validated configuration so errors are caught before clusters are modified. | Pydantic validation detects duplicate IDs, missing references, invalid combinations, and embedded secrets. |
| US-15 | As a platform engineer, I want idempotent operations so I can safely rerun automation after failures. | Running `masworld cluster prepare` twice on the same cluster produces the same result without errors. |

---

## 4. Functional Requirements

| ID | Requirement | Priority | Status | Notes |
|----|-------------|----------|--------|-------|
| FR-01 | Automated cluster preparation pipeline (16 stages from preflight to readiness) | Must | SCAFFOLDED | 17 Ansible roles implemented as scaffolds |
| FR-02 | MAS Core and Maximo Manage installation via supported IBM automation | Must | SCAFFOLDED | Depends on IBM entitlement key and license |
| FR-03 | OpenShift Logging Operator and Loki installation with S3 backend | Must | SCAFFOLDED | Logging 6.6, Loki 6.6, bucket-per-cluster |
| FR-04 | Identity provider configuration (Keycloak, OAuth, LDAP group sync) | Must | SCAFFOLDED | Keycloak deployment mode decision required |
| FR-05 | ACM registration, labeling, ManagedClusterSet, and governance policies | Must | SCAFFOLDED | ACM 2.16+ on hub cluster |
| FR-06 | Student account creation with htpasswd, RBAC, and namespace isolation | Must | IMPLEMENTED_NOT_TESTED | Pydantic profiles, generation logic implemented |
| FR-07 | Seat assignment and transactional spare replacement | Must | IMPLEMENTED_NOT_TESTED | CLI commands implemented, rollback logic present |
| FR-08 | Showroom deployment with per-cluster parameterization and runtime automation | Must | SCAFFOLDED | Showroom content structure created |
| FR-09 | Readiness validation with per-check PASS/WARNING/FAIL/NOT_APPLICABLE | Must | SCAFFOLDED | 16 check categories defined |
| FR-10 | Student credential rotation (generate, deploy, validate, regenerate card) | Must | IMPLEMENTED_NOT_TESTED | SecretProvider integration implemented |
| FR-11 | Per-module exercise reset (observability, identity, updates, navigation) | Must | SCAFFOLDED | Runtime automation directory structure created |
| FR-12 | Attendee access card generation (seat number, URLs, credentials) | Should | IMPLEMENTED_NOT_TESTED | CSV, JSON, individual card formats |
| FR-13 | Fleet status dashboard (cluster counts by status, last validated) | Should | SCAFFOLDED | Report command group implemented |
| FR-14 | ACM drift demonstration (ConfigMap removal on facilitator, policy enforcement) | Must | SCAFFOLDED | Policy hierarchy designed |
| FR-15 | MAS update exercise (pre-staged or scoped update within 20 min) | Must | SCAFFOLDED | Exercise design documented |
| FR-16 | Post-event teardown (disable accounts, revoke credentials, cleanup S3) | Should | SCAFFOLDED | Decommission playbook created |
| FR-17 | Configuration validation before any cluster modification | Must | IMPLEMENTED_NOT_TESTED | Pydantic model validators active |
| FR-18 | Secret provider abstraction (env, K8s, AWS SM, Vault) | Must | IMPLEMENTED_NOT_TESTED | ABC + 4 providers implemented |
| FR-19 | Layered YAML configuration with deep merge | Must | IMPLEMENTED_NOT_TESTED | Config loader implemented |
| FR-20 | Resume from last completed stage after interruption | Must | SCAFFOLDED | State tracking design documented |
| FR-21 | Parallel fleet preparation with concurrency control | Must | SCAFFOLDED | ThreadPoolExecutor design documented |
| FR-22 | Structured JSON logging with secret redaction | Must | IMPLEMENTED_NOT_TESTED | Redaction patterns defined |

---

## 5. Non-Functional Requirements

| ID | Requirement | Description | Measure |
|----|-------------|-------------|---------|
| NFR-01 | **Idempotency** | All operations must be safe to rerun. A second execution on an already-configured cluster must produce no errors and no unintended changes. | Zero errors on second run of `masworld cluster prepare` against a fully prepared cluster. |
| NFR-02 | **Security** | No credentials in Git, logs, CI artifacts, reports, or support bundles. RBAC isolation between attendees. Secret redaction in all output. | Pre-commit secret scanning passes. Negative RBAC tests pass. Log grep for known secret patterns returns zero matches. |
| NFR-03 | **Scalability** | Support fleet sizes from 1 to 50+ clusters through configuration only. No code changes required to change fleet size. | `fleet.attendee_cluster_count` change from 50 to 5 requires only `config/environments/` file change. |
| NFR-04 | **Observability** | Structured logs for every operation. Per-cluster log files. Fleet-level metrics (duration, success rate, retry count). | JSON log output parseable by standard tools. Per-cluster logs in `logs/clusters/`. Fleet summary report generated. |
| NFR-05 | **Reliability** | Retry transient failures with exponential backoff. Resume from last completed stage. Spare clusters available for replacement. Failure in one cluster does not block others. | 3 retries with 30s/60s/120s backoff. State file tracks completed stages. Spare replacement completes in under 10 minutes. |
| NFR-06 | **Configurability** | All environment-specific values (URLs, counts, versions, credentials, features) supplied through validated configuration. No hard-coded values in code. | Grep for hard-coded cluster URLs, passwords, or account IDs in playbooks and roles returns zero matches. |
| NFR-07 | **Auditability** | Every fleet operation produces a timestamped record. Credential lifecycle events are logged (without secret values). | Structured event log for each operation. Credential rotation events traceable. |
| NFR-08 | **Recoverability** | A failed cluster can be repaired without full reinstallation. A failed seat can be replaced with a spare. Partial preparation can resume. | `masworld cluster repair` fixes individual missing resources. `masworld seat replace` completes transactional swap. |
| NFR-09 | **Performance** | Fleet preparation of 50 clusters completes within 24 hours with max concurrency of 5. Individual cluster preparation completes within 4 hours. | 50 clusters / 5 concurrent = 10 batches x 4 hours max = 40 hours worst case; expected 12-20 hours with retries. |
| NFR-10 | **Portability** | Same automation code works for development (1 cluster), rehearsal (5 clusters), and event (50 clusters). | Three environment configs in `config/environments/` with no code forks. |

---

## 6. Constraints

| ID | Constraint | Impact |
|----|-----------|--------|
| C-01 | OpenShift clusters are pre-provisioned externally. Cluster provisioning is out of scope. | Automation must accept any compatible OpenShift cluster via inventory configuration. |
| C-02 | MAS installation requires cluster-admin privileges. | Automation must use cluster-admin for installation phases but must not expose cluster-admin to attendees or Showroom. |
| C-03 | MAS installation takes 2-4 hours per cluster. | Fleet preparation of 50 clusters requires 12-40 hours depending on concurrency. Must start well before event day. |
| C-04 | Conference WiFi is the sole network path for attendees. | Showroom, OCP console, and Maximo must be accessible over public internet. No VPN dependencies for attendees. |
| C-05 | OpenShift 4.22 (EUS) is the target platform version. OCP 4.23 is not verified for MAS 9.1.x compatibility. | Pin to OCP 4.22. Do not accept clusters running unverified versions without explicit override. |
| C-06 | IBM entitlement key and MAS license are required but not stored in the repository. | Secret provider must resolve IBM credentials at runtime. Placeholder references used in configuration. |
| C-07 | ROSA HCP clusters may have OAuth configuration limitations. | Identity module must document HCP-specific restrictions and provide alternative inspection exercises. |
| C-08 | 20-minute session time for the MAS update exercise. | Full MAS update is infeasible. Must use a pre-staged or scoped update exercise. |
| C-09 | Attendees must not have cluster-admin or ACM administrative access. | RBAC profiles must enforce restrictions. Negative security tests must validate isolation. |
| C-10 | All versions must be pinned for the event release. No floating channels, `latest` tags, or unpinned images. | Compatibility matrix documents all pinned versions. CI enforces pinned references. |

---

## 7. External Dependencies

| ID | Dependency | Owner | Required For | Risk |
|----|-----------|-------|-------------|------|
| DEP-01 | Red Hat Demo Platform (RHDP) | Red Hat | Showroom hosting, catalog integration | Showroom template changes could require content updates |
| DEP-02 | AWS Account(s) | Event organizer | S3 buckets for Loki, Secrets Manager, IAM | Account limits, billing, cross-account access |
| DEP-03 | IBM Entitlement and MAS License | IBM / Event organizer | MAS Core and Manage installation | Entitlement key expiry, license capacity for 50+ instances |
| DEP-04 | ACM Hub Cluster | Red Hat / Event organizer | Fleet management, policy propagation, demonstrations | Hub availability, managed cluster capacity |
| DEP-05 | DNS and Ingress | Cloud / Event organizer | Cluster access, route resolution | DNS propagation delay, certificate issuance |
| DEP-06 | Container Registries | Red Hat, IBM | Operator images, MAS images | Registry rate limits, network access from event venue |
| DEP-07 | Pre-provisioned OpenShift Clusters | External provisioner | Base infrastructure | Cluster count, readiness timing, version compatibility |
| DEP-08 | Conference Network | Event venue | Attendee access to all services | Bandwidth, firewall rules, WiFi capacity for 50+ users |
| DEP-09 | Git Hosting | Organization | Source control, CI/CD, public content | Repository access, webhook delivery |
| DEP-10 | MongoDB (in-cluster) | Deployed by MAS automation | MAS prerequisite | Storage capacity, operator compatibility |
| DEP-11 | Db2 Operator | IBM | Maximo Manage database | Operator availability in catalog, storage requirements |

---

## 8. Success Criteria

The following criteria map to the acceptance criteria defined in the master
specification (Section 34). Each criterion must have documented evidence
before the project is accepted.

### 8.1 Automation and Idempotency

| ID | Criterion | Spec Ref |
|----|-----------|----------|
| SC-01 | A compatible OpenShift cluster can be prepared with one command. | AC-1 |
| SC-02 | The preparation process is idempotent (safe to rerun). | AC-2 |
| SC-03 | A failed run can resume from the last completed stage. | AC-3 |
| SC-04 | Development, rehearsal, and event fleets use the same code with different configuration. | AC-16 |

### 8.2 Configurability

| ID | Criterion | Spec Ref |
|----|-----------|----------|
| SC-05 | Cluster count is configuration-driven (no code changes for different sizes). | AC-4, AC-5 |
| SC-06 | Adding or removing a cluster requires inventory changes only. | AC-6 |
| SC-07 | Every cluster may use distinct administrative credentials. | AC-7 |
| SC-08 | Component enablement and versions are configuration-driven. | AC-17 |
| SC-09 | Configuration validation completes before any cluster is modified. | AC-18 |
| SC-10 | Disabled components are reported as NOT_APPLICABLE, not FAIL. | AC-44 |
| SC-11 | Configuration changes do not require source-code modifications. | AC-45 |

### 8.3 Security and Isolation

| ID | Criterion | Spec Ref |
|----|-----------|----------|
| SC-12 | Administrative credentials are retrieved only at runtime from a secret provider. | AC-8 |
| SC-13 | Attendees cannot access another attendee's environment. | AC-30 |
| SC-14 | Attendees have no ACM administrative access. | AC-31 |
| SC-15 | Attendee accounts are not cluster-admin. | AC-32 |
| SC-16 | Secret values do not appear in Git, logs, reports, CI artifacts, or support bundles. | AC-38 |
| SC-17 | Negative access tests prove attendee isolation. | AC-46 |
| SC-18 | S3 isolation is tested (one cluster cannot access another's data). | AC-47 |
| SC-19 | Quarantined clusters cannot be assigned. | AC-49 |

### 8.4 Student Accounts and Credentials

| ID | Criterion | Spec Ref |
|----|-----------|----------|
| SC-20 | Student usernames are generated from configurable templates. | AC-9 |
| SC-21 | Student passwords are generated or retrieved according to configurable profiles. | AC-10 |
| SC-22 | Student RBAC is configurable without modifying playbook code. | AC-11 |
| SC-23 | Shared student passwords are disabled by default. | AC-12 |
| SC-24 | Student credential rotation is tested. | AC-48 |

### 8.5 Seat Assignment

| ID | Criterion | Spec Ref |
|----|-----------|----------|
| SC-25 | Seat assignments can change without rebuilding the fleet. | AC-13 |
| SC-26 | A spare can replace an attendee cluster with one command. | AC-14 |
| SC-27 | Reassignment is transactional (rollback on failure). | AC-15 |
| SC-28 | Failed clusters are excluded from assignment. | AC-35 |
| SC-29 | A spare can replace a failed assigned environment. | AC-36 |

### 8.6 Component Readiness

| ID | Criterion | Spec Ref |
|----|-----------|----------|
| SC-30 | ACM registration and labeling is complete for all clusters. | AC-19 |
| SC-31 | Fleet policies show expected compliance. | AC-20 |
| SC-32 | ACM drift and remediation demonstration works reliably. | AC-21 |
| SC-33 | MAS Core is ready on every assignable cluster. | AC-22 |
| SC-34 | Maximo Manage is ready on every assignable cluster. | AC-23 |
| SC-35 | Database connectivity is validated. | AC-24 |
| SC-36 | Logging captures application, infrastructure, and audit logs. | AC-25 |
| SC-37 | Loki persists logs to supported object storage. | AC-26 |
| SC-38 | Historical logs remain queryable after a demo pod is deleted. | AC-27 |
| SC-39 | Identity exercises work within documented platform limitations. | AC-28 |

### 8.7 Showroom and Content

| ID | Criterion | Spec Ref |
|----|-----------|----------|
| SC-40 | Showroom is parameterized separately for every seat. | AC-29 |
| SC-41 | Every module has validation and solve automation. | AC-33 |
| SC-42 | Critical modules have reset automation. | AC-34 |
| SC-43 | Generated attendee materials contain only that attendee's credentials. | AC-37 |

### 8.8 Release and Operational Readiness

| ID | Criterion | Spec Ref |
|----|-----------|----------|
| SC-44 | CI passes all required tests. | AC-39 |
| SC-45 | A full rehearsal has been completed. | AC-40 |
| SC-46 | The event runbook has been reviewed by all three facilitators. | AC-41 |
| SC-47 | Teardown and credential revocation are tested. | AC-42 |
| SC-48 | The final release is pinned and reproducible. | AC-43 |
| SC-49 | The final acceptance report maps evidence to every criterion. | AC-50 |

---

## Appendix A. Workshop Module Summary

| Module | Duration | Type | Key Activities |
|--------|----------|------|---------------|
| Access and Readiness | 5 min | Attendee | One-click readiness check, verify all components |
| Navigation and Search | 10 min | Attendee | OCP console navigation, MAS navigation, resource search |
| Advanced Cluster Management | 10 min | Presenter-led | Fleet overview, labels, policies, drift remediation |
| MAS Updates | 20 min | Mixed | Pre-staged update observation, lifecycle inspection |
| Observability and Logging | 20 min | Attendee | Deploy log generator, query Loki, inspect historical logs |
| Identity Integration | 20 min | Attendee | Inspect Keycloak, OAuth config, LDAP group sync, test auth |
| Conclusion | 5 min | Attendee | Summary, production considerations, public resources |

## Appendix B. Environment Profiles

| Profile | Clusters | Spares | Facilitator | Use Case |
|---------|----------|--------|-------------|----------|
| Development | 1 | 0 | 1 | Local development and testing |
| Rehearsal | 5 | 1 | 1 | Integration testing and facilitator rehearsal |
| Event | 50 | 5 | 1 | MAS World 2026 production event |

## Appendix C. Glossary

| Term | Definition |
|------|-----------|
| ACM | Red Hat Advanced Cluster Management for Kubernetes |
| ClusterLogForwarder | OpenShift resource that routes collected logs to storage backends |
| Drift | Unintended deviation of cluster state from the desired configuration |
| Fleet | The complete set of clusters managed for the workshop event |
| LokiStack | Operator-managed Loki deployment for log storage and querying |
| MAS | IBM Maximo Application Suite |
| Manage | IBM Maximo Manage, the EAM application within MAS |
| ManagedClusterSet | ACM resource grouping related managed clusters |
| RHDP | Red Hat Demo Platform |
| Seat | A numbered attendee position mapped to a specific cluster |
| Showroom | Red Hat browser-based workshop delivery interface |
| Spare | A prepared cluster held in reserve for replacing failed attendee clusters |
