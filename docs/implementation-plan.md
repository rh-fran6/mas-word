# Implementation Plan — MAS World 2026

**Status**: DRAFT — Phase 0
**Date**: 2026-07-19

---

## Phase 0 — Discovery (Current)

### Deliverables

| Document | Status |
|----------|--------|
| `docs/discovery-report.md` | COMPLETE |
| `docs/compatibility-matrix.md` | IN PROGRESS (awaiting research) |
| `docs/risk-register.md` | COMPLETE |
| `docs/architecture.md` | COMPLETE |
| `docs/configuration-model.md` | COMPLETE |
| `docs/credential-lifecycle.md` | COMPLETE |
| `docs/implementation-plan.md` | This document |

### Actions

- [x] Inspect current workspace
- [x] Create directory structure
- [x] Write discovery report
- [x] Write risk register
- [x] Write architecture document
- [x] Write configuration model
- [x] Write credential lifecycle design
- [ ] Complete compatibility matrix (pending research)
- [x] Write implementation plan

---

## Phase 1 — Skeleton

### 1.1 Python Project Setup

```text

├── pyproject.toml          # Project metadata, dependencies, CLI entry points
├── requirements.yml        # Ansible Galaxy requirements
├── ansible.cfg             # Ansible configuration
├── galaxy.yml              # Collection metadata
└── Makefile                # Development tasks
```

Key dependencies:
- Python ≥ 3.11
- ansible-core ≥ 2.15
- click (CLI framework)
- pydantic (configuration validation)
- pyyaml (YAML parsing)
- jinja2 (template rendering)
- boto3 (AWS SDK)
- kubernetes (K8s client)
- qrcode (access card QR codes)
- pytest (testing)

### 1.2 Configuration Schemas

Implement JSON Schema files in `schemas/` and corresponding Pydantic models
in `cli/config/schema.py` for:

- `event-config.schema.json`
- `fleet-config.schema.json`
- `cluster-config.schema.json`
- `credentials-config.schema.json`
- `components-config.schema.json`
- `student-profiles.schema.json`
- `assignments.schema.json`

### 1.3 Secret Provider Skeleton

Implement the `SecretProvider` abstract base class and concrete providers:

- `EnvSecretProvider` — reads from environment variables
- `K8sSecretProvider` — reads from Kubernetes Secrets
- `AWSSecretsManagerProvider` — reads from AWS Secrets Manager
- `VaultSecretProvider` — stub for HashiCorp Vault

### 1.4 CLI Skeleton

Implement the `mas-world` CLI with subcommands (initially returning
"not implemented" for most):

```bash
mas-world validate-config
mas-world render-effective-config
mas-world show-config-differences
mas-world prepare-fleet
mas-world prepare-cluster
mas-world validate-fleet
mas-world validate-cluster
mas-world repair-cluster
mas-world reset-exercise
mas-world create-student-accounts
mas-world rotate-student-credentials
mas-world disable-student-accounts
mas-world delete-student-accounts
mas-world validate-student-access
mas-world export-attendee-access-cards
mas-world assign-seat
mas-world replace-seat
mas-world unassign-seat
mas-world show-seat
mas-world export-seat-map
mas-world generate-seat-report
```

### 1.5 Ansible Role Skeletons

Create `tasks/main.yml`, `defaults/main.yml`, and `meta/main.yml` for all
17 roles with documented variable interfaces.

### 1.6 Test Framework

```text
tests/
├── conftest.py
├── unit/
│   ├── test_config_loader.py
│   ├── test_config_validation.py
│   ├── test_secret_provider.py
│   ├── test_secret_redaction.py
│   ├── test_inventory.py
│   ├── test_seat_assignment.py
│   ├── test_password_generation.py
│   └── test_credential_profiles.py
├── integration/
│   └── ...
└── security/
    └── ...
```

### 1.7 CI Skeleton

GitHub Actions workflows (or equivalent):

- `lint.yml` — YAML, Ansible, Python, shell linting
- `test.yml` — Unit tests, schema validation
- `security.yml` — Secret scanning, dependency scanning
- `showroom.yml` — Showroom build validation

---

## Phase 2 — Single Reference Cluster

### Prerequisites

- At least one OpenShift cluster accessible
- IBM Entitlement Key available (B-01)
- MAS License available (B-02)
- AWS credentials available (B-03)

### Implementation Order

1. `config_validation` role — validate configuration completeness
2. `cluster_preflight` role — detect and validate cluster state
3. `event_metadata` role — apply labels and markers
4. `acm_registration` role — register with ACM hub
5. `mas_prerequisites` role — cert-manager, MongoDB, storage
6. `mas_core` role — MAS Core operator and Suite CR
7. `maximo_manage` role — Manage installation and activation
8. `logging_operator` role — Logging Operator installation
9. `loki_stack` role — Loki Operator and LokiStack CR
10. `log_forwarding` role — ClusterLogForwarder
11. `identity_demo` role — Keycloak and identity resources
12. `student_accounts` role — accounts and RBAC
13. `sample_workloads` role — exercise data
14. `showroom` role — Showroom installation
15. `event_readiness` role — readiness checks
16. `environment_report` role — cluster report

### Validation

After each role:
- Verify idempotency (rerun produces no changes)
- Verify cleanup does not break dependent components
- Record timing data

After all roles:
- Run full readiness check
- Verify student login
- Verify Showroom loads
- Verify Maximo accessible
- Verify Loki log query
- Verify ACM registration

---

## Phase 3 — Student Identity and Access

1. Implement password generation (cryptographically secure)
2. Implement HTPasswd identity provider configuration
3. Implement RBAC (ClusterRoleBindings, RoleBindings)
4. Implement positive access tests (student can access their namespace)
5. Implement negative access tests (student cannot access other namespaces)
6. Implement access card generation
7. Implement credential rotation
8. Test credential lifecycle end-to-end

---

## Phase 4 — ACM Hub

1. Create ManagedClusterSet
2. Implement cluster import automation
3. Apply labels to managed clusters
4. Create Placement and PlacementBinding
5. Create governance policies (inform mode)
6. Stage deliberate drift on facilitator cluster
7. Implement remediation demonstration
8. Test full ACM demo flow
9. Document presenter steps

---

## Phase 5 — Showroom

1. Create `site.yml` and `ui-config.yml`
2. Create `index.adoc` (readiness check page)
3. Create `access-readiness.adoc`
4. Create `navigation-search.adoc` with runtime automation
5. Create `acm-fleet-management.adoc`
6. Create `updates.adoc` with runtime automation
7. Create `observability.adoc` with runtime automation
8. Create `identity.adoc` with runtime automation
9. Create `production-architecture.adoc`
10. Create `troubleshooting.adoc`
11. Create `conclusion.adoc`
12. Create `nav.adoc`
13. Implement all validate/solve/reset scripts
14. Test Showroom build
15. Test with parameterized variables

---

## Phase 6 — Small Fleet Rollout

1. Configure rehearsal environment (5 + 1 clusters)
2. Run `prepare-fleet` with concurrency 3
3. Verify all clusters reach READY
4. Test seat assignment for all 5 seats
5. Test spare replacement
6. Test credential rotation across fleet
7. Test exercise reset across fleet
8. Record timing and bottleneck data
9. Tune concurrency and timeouts

---

## Phase 7 — Full Rehearsal

1. Scale to event fleet size (50 + 5 + 1)
2. Full fleet preparation
3. Full seat assignment
4. Simulated attendee load test
5. Full ACM demo walkthrough
6. Full exercise sequence per module
7. Spare replacement drill
8. Credential rotation drill
9. Incident response drill
10. Support workflow test
11. Document lessons learned

---

## Phase 8 — Event Release

1. Freeze all versions
2. Pin container images to digests
3. Pin operator channels to specific versions
4. Generate immutable release tag
5. Full fleet re-validation
6. Final credential rotation
7. Generate final seat map
8. Generate access cards
9. Produce acceptance report
10. Final runbook review with all facilitators

---

## Parallel Work Streams

Work that can proceed without external blockers:

| Stream | Blocked By |
|--------|-----------|
| Configuration schemas and validation | Nothing |
| Secret provider abstraction | Nothing |
| CLI framework | Nothing |
| Ansible role skeletons | Nothing |
| Showroom content structure | Nothing |
| ACM policy manifests (templates) | Nothing |
| Public content examples | Nothing |
| Operational runbooks | Nothing |
| Unit tests | Nothing |
| CI pipelines | Nothing |
| Fleet orchestration logic | Nothing |
| Seat assignment logic | Nothing |
| Access card generation | Nothing |

Work that requires external resources:

| Stream | Blocked By |
|--------|-----------|
| MAS installation roles | B-01 (IBM Key), B-02 (License), B-04 (Cluster) |
| Logging/Loki roles | B-03 (AWS), B-04 (Cluster) |
| ACM registration | B-04 (Cluster), B-05 (ACM Hub) |
| Identity/Keycloak | B-04 (Cluster) |
| Integration tests | B-04 (Cluster) |
| Fleet rehearsal | All blockers resolved |
