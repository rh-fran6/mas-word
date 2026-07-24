# Risk Register

> **Last updated:** 2026-07-20

---

## Risk Matrix Key

| Likelihood | Description |
|---|---|
| Low | Unlikely to occur under normal operations |
| Medium | Possible under certain conditions |
| High | Likely to occur without explicit prevention |

| Impact | Description |
|---|---|
| Low | Minor inconvenience, self-recoverable |
| Medium | Workflow disruption, manual intervention needed |
| High | Data loss, security breach, or extended outage |

---

## Active Risks

| ID | Risk | Likelihood | Impact | Mitigation | Status |
|---|---|---|---|---|---|
| R-001 | AWS quota exhaustion blocks provisioning | Medium | Medium | Preflight checks validate credentials; documentation includes quota verification commands; operator must check quotas pre-workshop | Mitigated |
| R-002 | Credentials committed to git | Medium | High | `.gitignore` covers `secrets/`; `.example` templates committed; pre-commit hooks installed | Mitigated |
| R-003 | Partial fleet provisioning failure | Medium | Medium | `make provision` is idempotent — re-run after fixing the failed account | Accepted |
| R-004 | Workshop disrupted by accidental `make destroy` | Low | High | Destroy requires interactive "yes" confirmation; `destroy-auto` is explicitly named | Mitigated |
| R-005 | ROSA API rate limiting during large fleet operations | Low | Medium | Async pattern spreads initial requests; polling intervals are configurable | Accepted |
| R-006 | AWS access keys compromised | Low | High | Vault encryption available; `no_log: true` on all credential tasks; keys should be rotated post-workshop | Mitigated |
| R-007 | Cluster provisioning exceeds expected timeframe | Medium | Low | Timeout and retry values are configurable in `rosa_defaults.yml`; operator can monitor with `make status` | Accepted |
| R-008 | IAM cleanup fails after cluster destruction | Low | Medium | `destroy_cleanup.yml` uses `failed_when: false`; operator can run manual cleanup | Accepted |
| R-009 | Inconsistent cluster state after interrupted provision | Low | Medium | Re-running `make provision` handles existing clusters gracefully | Accepted |
| R-010 | Filter plugin breaks on unexpected topology input | Very Low | Medium | Comprehensive unit tests (7 cases); `ValueError` on missing credentials | Mitigated |
| R-011 | Running `make destroy-infra` while clusters still exist could orphan cluster resources | Medium | High | Always run `make destroy` to destroy all clusters before running `make destroy-infra`. The destroy-infra playbook includes a warning prompt but does not block execution | Mitigated |
| R-012 | NAT gateway cost accumulates if infrastructure is not destroyed after workshop | High | Medium | The teardown guide includes a post-workshop checklist that explicitly calls out `make destroy-infra`. The `make destroy-infra-auto` target can be used in automated cleanup scripts | Mitigated |

---

## Retired Risks

_None yet._


---

## Phase 2: MAS World Application Layer


**Status**: DRAFT — Phase 0
**Date**: 2026-07-19
**Last Updated**: 2026-07-19

---

## Risk Scoring

- **Likelihood**: Low / Medium / High
- **Impact**: Low / Medium / High / Critical
- **Risk Level**: Likelihood × Impact

---

## Active Risks

### R-001: MAS Installation Time Exceeds Preparation Window

| Field | Value |
|-------|-------|
| Likelihood | High |
| Impact | Critical |
| Risk Level | CRITICAL |
| Owner | Francis |

**Description**: MAS installation (Core + Manage + prerequisites) can take
2-4 hours per cluster. With 55+ clusters and limited concurrency, total
preparation time could exceed the available window.

**Mitigation**:
- Configure maximum parallel cluster preparation (default: 5)
- Stagger preparation across multiple days
- Pre-pull operator images to reduce pull time
- Use per-cluster timeout of 240 minutes with retry
- Maintain spare clusters to absorb failures
- Start preparation ≥72 hours before event

---

### R-002: IBM Entitlement Key Unavailable

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | Critical |
| Risk Level | HIGH |
| Owner | Francis |

**Description**: Without an IBM Entitlement Key, MAS operators cannot be
installed. This blocks Phase 2 entirely.

**Mitigation**:
- Escalate key acquisition immediately
- Build all non-MAS automation in parallel
- Design MAS roles to accept key at runtime via secret provider
- Test with placeholder configuration to validate automation flow

---

### R-003: Cluster Heterogeneity

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | High |
| Risk Level | HIGH |
| Owner | Francis |

**Description**: Provisioned clusters may have different OpenShift versions,
node counts, storage classes, or pre-existing resources. Automation must
handle variation.

**Mitigation**:
- Comprehensive preflight checks before any modifications
- Detect and record actual cluster state
- Fail fast with clear diagnostics on incompatible clusters
- Support cluster-specific configuration overrides

---

### R-004: MAS Update Exercise Unpredictability

| Field | Value |
|-------|-------|
| Likelihood | High |
| Impact | High |
| Risk Level | HIGH |
| Owner | Francis / Ernie |

**Description**: A full MAS update cannot reliably complete in the 20-minute
session allocation. If attempted live, it may leave clusters in a partially
updated state.

**Mitigation**:
- Use a pre-staged or inspection-based update exercise
- Demonstrate update initiation, then inspect a previously completed update
- Include rollback documentation
- Never depend on live update completion for session success

---

### R-005: S3 Bucket Creation Throttling

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | Medium |
| Risk Level | MEDIUM |
| Owner | Francis |

**Description**: Creating 55+ S3 buckets rapidly may trigger AWS API
throttling or account-level bucket limits (default: 100 per account).

**Mitigation**:
- Stagger bucket creation
- Verify account bucket limit in advance
- Request limit increase if needed
- Use exponential backoff on S3 API calls

---

### R-006: Conference Network Constraints

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | High |
| Risk Level | HIGH |
| Owner | All |

**Description**: 50 attendees simultaneously accessing OpenShift consoles,
Maximo UI, Showroom, and terminals through conference WiFi may cause latency
or timeouts.

**Mitigation**:
- Test with simulated concurrent load during rehearsal
- Minimize required bandwidth per attendee
- Provide fallback instructions for slow connections
- Pre-load static content where possible
- Document minimum bandwidth requirements

---

### R-007: ACM Hub Capacity Under Fleet Load

| Field | Value |
|-------|-------|
| Likelihood | Low |
| Impact | High |
| Risk Level | MEDIUM |
| Owner | Francis |

**Description**: An ACM hub managing 55+ clusters with policies, search
indexing, and governance may experience resource pressure.

**Mitigation**:
- Size ACM hub according to Red Hat guidelines
- Monitor hub resource usage during rehearsal
- Keep governance policies minimal (inform mode for most)
- Test search performance with full fleet

---

### R-008: Keycloak Resource Pressure (Per-Cluster Model)

| Field | Value |
|-------|-------|
| Likelihood | Low |
| Impact | Medium |
| Risk Level | LOW |
| Owner | Francis |

**Description**: Running Keycloak on every attendee cluster adds resource
overhead. May compete with MAS for CPU/memory.

**Mitigation**:
- Size Keycloak resource requests conservatively
- Monitor resource usage during reference cluster testing
- Have shared-Keycloak fallback design documented

---

### R-009: Student Credential Exposure

| Field | Value |
|-------|-------|
| Likelihood | Low |
| Impact | High |
| Risk Level | MEDIUM |
| Owner | Francis |

**Description**: Student passwords could leak through logs, Showroom
validation output, support bundles, or access card mishandling.

**Mitigation**:
- Secret redaction in all output paths
- Unique password per student (no shared passwords)
- Credential rotation capability
- Negative tests proving secrets don't appear in logs
- Access cards contain only that student's credentials

---

### R-010: Incomplete MAS Installation on Some Clusters

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | High |
| Risk Level | HIGH |
| Owner | Francis |

**Description**: Some clusters may fail MAS installation due to transient
errors, resource exhaustion, or IBM registry issues. Failed clusters cannot
be assigned to attendees.

**Mitigation**:
- 5 spare clusters (10% buffer)
- Repair automation for common failure modes
- Resume capability from last completed stage
- Clear READY/FAILED status tracking
- Spare replacement procedure tested and documented

---

### R-011: Version Incompatibility Discovered Late

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | Critical |
| Risk Level | HIGH |
| Owner | Francis |

**Description**: A version conflict between MAS, OpenShift, Logging, or ACM
discovered after development begins could require significant rework.

**Mitigation**:
- Complete compatibility matrix in Phase 0 before implementation
- Pin all versions explicitly
- Test on reference cluster before fleet rollout
- Monitor IBM and Red Hat release notes through August 2026

---

## Closed / Accepted Risks

_None yet._
