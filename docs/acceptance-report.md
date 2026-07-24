# Acceptance Report — MAS World 2026

**Status**: DRAFT — Pre-Release
**Date**: 2026-07-19

---

## Acceptance Criteria Mapping

Each criterion corresponds to Section 34 of `prompt.md`. Status labels follow the
project specification:

- **IMPLEMENTED_AND_TESTED** — Code exists and unit/integration tests pass.
- **IMPLEMENTED_NOT_TESTED** — Code exists but has not been validated on a live cluster.
- **SCAFFOLDED** — Structure, interfaces, or placeholders exist; implementation requires real data or clusters.
- **BLOCKED_EXTERNAL_DEPENDENCY** — Cannot proceed without IBM entitlement key, provisioned clusters, AWS credentials, or another external resource.
- **NOT_IMPLEMENTED** — Not yet built.

---

| # | Criterion | Status | Evidence / Notes |
|---|-----------|--------|------------------|
| 1 | Single command cluster preparation | IMPLEMENTED_NOT_TESTED | `prepare-cluster` playbook and CLI entry point exist; requires a live cluster to validate end-to-end |
| 2 | Idempotent process | IMPLEMENTED_NOT_TESTED | All roles use `state: present` and check-before-create patterns; not yet validated with repeated runs on a live cluster |
| 3 | Failed run can resume | SCAFFOLDED | Stage-tracking model defined in `config/` schema; resume logic scaffolded in orchestrator but untested |
| 4 | Configuration-driven cluster count | IMPLEMENTED_AND_TESTED | Fleet size read from `config/environments/*.yaml`; unit tests confirm 1, 5, and 50 cluster configs parse correctly |
| 5 | Changing 50 to 5 requires config only | IMPLEMENTED_AND_TESTED | `attendee_cluster_count` in environment YAML; no code changes required; unit tests validate |
| 6 | Adding/removing cluster requires inventory only | IMPLEMENTED_AND_TESTED | `secrets/cluster-credentials.yml` is the sole cluster source; inventory parser unit-tested |
| 7 | Distinct admin credentials per cluster | IMPLEMENTED_AND_TESTED | Each cluster entry carries its own `admin_secret_ref`; schema enforces uniqueness; unit tests pass |
| 8 | Admin credentials retrieved at runtime only | IMPLEMENTED_NOT_TESTED | Secret-provider abstraction resolves `secret://` URIs at runtime; not tested against a live secret store |
| 9 | Student usernames from configurable templates | IMPLEMENTED_AND_TESTED | `username_template` in credential profiles; Jinja2 rendering tested with multiple seat numbers |
| 10 | Student passwords generated per configurable profiles | IMPLEMENTED_AND_TESTED | `secrets.token_urlsafe` generator; profile-driven length and mode; unit tests pass |
| 11 | Student RBAC configurable without code changes | IMPLEMENTED_NOT_TESTED | RBAC defined in credential profiles (`cluster_role`, `namespaces`); roles read profiles at runtime; not applied to a live cluster |
| 12 | Shared passwords disabled by default | IMPLEMENTED_AND_TESTED | `allow_shared_password: false` is the schema default; validation rejects shared passwords unless explicitly enabled; unit tests confirm |
| 13 | Seat assignments changeable without fleet rebuild | IMPLEMENTED_NOT_TESTED | Assignment model is decoupled from cluster preparation; `assign-seat` and `unassign-seat` CLI commands exist |
| 14 | Spare replaces attendee cluster with one command | SCAFFOLDED | `replace-seat` CLI scaffolded; transactional logic outlined but not executed against real clusters |
| 15 | Transactional reassignment | SCAFFOLDED | Rollback steps defined in replacement workflow; no live test of failure-during-reassignment |
| 16 | Same code, different config for dev/rehearsal/event | IMPLEMENTED_AND_TESTED | Layered config: `defaults.yaml` < `environments/development.yaml` < `event.yaml`; precedence unit-tested |
| 17 | Component enablement configuration-driven | IMPLEMENTED_AND_TESTED | `components:` section with `enabled: true/false`; roles skip disabled components; unit tests validate |
| 18 | Config validation before cluster modification | IMPLEMENTED_AND_TESTED | `validate-config` CLI runs JSON Schema + Pydantic checks before any playbook executes; unit tests pass |
| 19 | All clusters registered and labeled in ACM | SCAFFOLDED | `acm_registration` role scaffolded with label application; requires ACM hub cluster |
| 20 | Fleet policies show expected compliance | SCAFFOLDED | Policy manifests created in `acm/` directory; not applied to a live hub |
| 21 | Safe ACM drift/remediation demo works | SCAFFOLDED | Drift ConfigMap and remediation policy defined; facilitator-cluster staging outlined; untested |
| 22 | MAS Core ready on every assignable cluster | BLOCKED_EXTERNAL_DEPENDENCY | `mas_core` role exists; requires IBM entitlement key and provisioned cluster |
| 23 | Maximo Manage ready on every assignable cluster | BLOCKED_EXTERNAL_DEPENDENCY | `maximo_manage` role exists; requires MAS Core and IBM entitlement key |
| 24 | Database connectivity validated | BLOCKED_EXTERNAL_DEPENDENCY | Db2 deployment role scaffolded; readiness check defined; requires live cluster |
| 25 | Logging captures app/infra/audit | IMPLEMENTED_NOT_TESTED | `logging_operator`, `loki_stack`, `log_forwarding` roles configure all three log types; requires live cluster |
| 26 | Loki persists to object storage | BLOCKED_EXTERNAL_DEPENDENCY | LokiStack CR references S3 secret; requires AWS credentials and provisioned cluster |
| 27 | Historical logs queryable after pod deletion | BLOCKED_EXTERNAL_DEPENDENCY | Exercise design complete; sample workload and query commands defined; requires Loki on a live cluster |
| 28 | Identity exercises work within platform limits | SCAFFOLDED | Keycloak and OpenLDAP roles scaffolded; HCP OAuth limitations documented; requires live cluster |
| 29 | Showroom parameterized per seat | IMPLEMENTED_NOT_TESTED | Showroom role injects per-seat variables (`seat_number`, endpoints, credentials); not deployed to a cluster |
| 30 | Attendees cannot access other environments | SCAFFOLDED | RBAC roles restrict namespace access; negative-test playbook defined; requires live cluster |
| 31 | Attendees have no ACM admin access | SCAFFOLDED | No ACM roles granted to attendee accounts; negative test defined; requires ACM hub |
| 32 | Attendee accounts not cluster-admin | IMPLEMENTED_AND_TESTED | Credential profile schema forbids `cluster-admin` for attendee profiles by default; validation unit-tested |
| 33 | Every module has validation and solve | SCAFFOLDED | `runtime-automation/` directories contain `validate.yml` and `solve.yml` stubs for each module |
| 34 | Critical modules have reset | SCAFFOLDED | `reset.yml` stubs exist for observability, updates, and identity modules |
| 35 | Failed clusters excluded from assignment | IMPLEMENTED_AND_TESTED | Assignment logic rejects clusters with `status != READY`; unit tests confirm |
| 36 | Spare can replace failed assigned environment | SCAFFOLDED | `replace-seat` workflow defined; requires live spare and failed cluster to test |
| 37 | Access cards contain only that attendee's credentials | IMPLEMENTED_NOT_TESTED | Card generator templates scoped to single seat; no cross-seat data included; manual review pending |
| 38 | Secrets not in git/logs/reports/CI/bundles | IMPLEMENTED_AND_TESTED | `.gitignore` blocks credential patterns; redaction filter tested; `gitleaks` in pre-commit; unit tests for redaction pass |
| 39 | CI passes all required tests | SCAFFOLDED | CI pipeline definition exists; linting and unit tests run locally; CI not yet connected to a runner |
| 40 | Full rehearsal completed | NOT_IMPLEMENTED | Requires provisioned fleet; scheduled for Phase 7 |
| 41 | Event runbook reviewed by all 3 facilitators | NOT_IMPLEMENTED | Runbook drafted in `docs/`; review not yet scheduled |
| 42 | Teardown and credential revocation tested | NOT_IMPLEMENTED | Teardown playbook scaffolded; not executed on a live environment |
| 43 | Final release pinned and reproducible | SCAFFOLDED | Version pinning strategy defined in `docs/bill-of-materials.md`; release tagging process documented; no release cut yet |
| 44 | Disabled components reported as NOT_APPLICABLE | IMPLEMENTED_AND_TESTED | Readiness checks return `NOT_APPLICABLE` for disabled components; unit tests confirm |
| 45 | Config changes don't require source code changes | IMPLEMENTED_AND_TESTED | All environment-specific values externalized to `config/`; roles and CLI read config at runtime; unit tests validate |
| 46 | Negative access tests prove isolation | SCAFFOLDED | Negative test playbooks defined for namespace, ACM, and secret access; require live cluster |
| 47 | S3 isolation tested | BLOCKED_EXTERNAL_DEPENDENCY | Per-cluster bucket design documented; IAM policy templates created; requires AWS credentials |
| 48 | Student credential rotation tested | IMPLEMENTED_NOT_TESTED | `rotate-student-credentials` CLI and playbook exist; not run against a live cluster |
| 49 | Quarantined clusters cannot be assigned | IMPLEMENTED_AND_TESTED | Assignment logic rejects clusters with `status == QUARANTINED`; unit tests confirm |
| 50 | Final acceptance report maps evidence to criteria | IMPLEMENTED_AND_TESTED | This document; updated with each phase |

---

## Summary by Status

| Status | Count |
|--------|-------|
| IMPLEMENTED_AND_TESTED | 15 |
| IMPLEMENTED_NOT_TESTED | 9 |
| SCAFFOLDED | 16 |
| BLOCKED_EXTERNAL_DEPENDENCY | 6 |
| NOT_IMPLEMENTED | 4 |
| **Total** | **50** |

---

## Path to Event Readiness

To move all 50 criteria to `IMPLEMENTED_AND_TESTED`:

1. **Obtain external dependencies** -- IBM entitlement key, provisioned OpenShift clusters,
   AWS credentials, ACM hub cluster. This unblocks 6 criteria.
2. **Execute Phase 2 (reference cluster)** -- Validates MAS, Logging, Loki, S3, Identity
   on a single cluster. Moves most `IMPLEMENTED_NOT_TESTED` and `SCAFFOLDED` items forward.
3. **Execute Phase 4 (ACM hub)** -- Validates ACM registration, policies, drift demo.
4. **Execute Phase 5 (Showroom)** -- Validates content rendering, tabs, runtime automation.
5. **Execute Phase 7 (full rehearsal)** -- Covers criteria 40, 41, 42, and validates
   all fleet-scale operations.
6. **Execute Phase 8 (event release)** -- Cuts pinned release, generates final access cards,
   produces this report in `FINAL` status.

---

## Document History

| Date | Author | Change |
|------|--------|--------|
| 2026-07-19 | Automation | Initial draft mapping all 50 criteria |
