# Decision Log

Records architectural and implementation decisions with rationale.

# Architecture and Implementation Decisions

## Decision format

### ADR-NNN — Title

- Status: proposed | accepted | superseded
- Date:
- Context:
- Decision:
- Alternatives considered:
- Consequences:
- Related requirements:

## Format

Each entry: decision, date, options considered, chosen option, rationale, consequences.

---

## Decisions

### DEC-001: Database Architecture — Db2 Per-Cluster

- **Date**: 2026-07-15
- **Context**: 50 attendees each need MAS with a backing database. Options: shared Db2 instance, per-cluster Db2 via `mas install`.
- **Decision**: Per-cluster Db2 installed by `mas install` (embedded).
- **Rationale**: Workshop isolation — one attendee's actions cannot affect another. Clean teardown per cluster. `ibm.mas_devops` supports this natively.
- **Consequences**: Higher aggregate resource usage. Each cluster provisions its own Db2 instance.

### DEC-002: Keycloak Deployment — Per-Cluster

- **Date**: 2026-07-15
- **Context**: Identity provider for student access. Options: central Keycloak on hub, per-cluster Keycloak.
- **Decision**: Per-cluster Keycloak.
- **Rationale**: Isolation between attendees. Simpler RBAC (each cluster manages its own users). No single point of failure for identity.
- **Consequences**: More Keycloak instances to manage. Credential rotation must iterate over all clusters.

### DEC-003: S3 Bucket Isolation — Per-Cluster

- **Date**: 2026-07-15
- **Context**: Loki log storage needs S3 backend. Options: shared bucket with key prefixes, one bucket per cluster.
- **Decision**: One bucket per cluster.
- **Rationale**: Clean teardown — delete bucket deletes all logs. No cross-contamination. Simpler IAM policies.
- **Consequences**: Up to 56 S3 buckets (50 attendee + 5 spare + 1 facilitator). Bucket naming: `mas-world-2026-{cluster-id}`.

### DEC-004: Logging Stack — Observability API v1

- **Date**: 2026-07-15
- **Context**: OpenShift Logging 6.x moved from `logging.openshift.io/v1` to `observability.openshift.io/v1`. Fluentd removed; Vector only. Cluster Observability Operator (COO) now required alongside Logging and Loki operators.
- **Decision**: Use `observability.openshift.io/v1` API, Vector collector, 3 operators (Logging 6.6 + Loki 6.6 + COO).
- **Rationale**: Forward-compatible. The old API is deprecated in 6.x.
- **Consequences**: Ansible roles must use the new API group. LokiStack CR uses `loki.grafana.com/v1`.

### DEC-005: MAS Edge (MVI Edge) — Disabled

- **Date**: 2026-07-15
- **Context**: MAS Edge is actually Maximo Visual Inspection Edge, runs outside OpenShift on Docker with NVIDIA GPUs.
- **Decision**: Disabled by default in configuration schema (`components.mas_edge.enabled: false`).
- **Rationale**: Not relevant to the MAS workshop scope. Requires GPU hardware not available in RHDP clusters.
- **Consequences**: No MVI Edge roles needed. Config schema retains the field for future flexibility.

### DEC-006: Target OCP Version — 4.21

- **Date**: 2026-07-15
- **Context**: MAS 9.1.x catalog (v9-260625-amd64) explicitly supports OCP 4.16-4.21. OCP 4.22 EUS is available but unverified for MAS.
- **Decision**: Target OCP 4.21 as safe default.
- **Rationale**: Using an unverified OCP version risks MAS operator install failures. 4.21 is the latest verified version.
- **Consequences**: Must confirm RHDP cluster provisioning targets 4.21. Documented as risk R-011 in risk register.

### DEC-007: RHDP Skills Usage — Skill-First Workflow

- **Date**: 2026-07-15
- **Context**: RHDP Skills Marketplace plugins are installed (showroom, agnosticv, health). prompt.md Section 4 mandates attempting skills before manual implementation.
- **Decision**: Use `showroom:create-lab` for all Showroom content generation, `showroom:verify-content` for validation. Document any manual fallbacks with `MANUAL_FALLBACK_SKILL_UNAVAILABLE` and reason.
- **Rationale**: Skills encode Red Hat standards (AsciiDoc structure, role="execute", acronym handling, nav format). Using them ensures compliance and reduces manual review.
- **Consequences**: Content generation depends on skill availability. AgnosticV skills deferred (catalog entry not yet in scope).
