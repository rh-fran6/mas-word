# Current Implemented State

This file describes what is actually implemented now, not merely planned.

Last updated: 2026-07-19

## Environment

- Monorepo at `maximo-world/` with 6 logical subdirectories
- `.gitignore` at monorepo root covering credentials, Python artifacts, IDE, OS, Ansible retry, generated reports
- Git repository initialized (`.git/` exists)
- Pre-commit hooks configured: `.pre-commit-config.yaml` (gitleaks, yamllint, ansible-lint, ruff, shellcheck, pre-commit-hooks)
- Linter configs: `.yamllint.yml`, `.ansible-lint.yml`, `.gitleaks.toml`

## Automation

- `mas-world-2026-automation/` contains:
  - `ansible.cfg`, `galaxy.yml`, `requirements.yml`, `pyproject.toml`, `Makefile`
  - 7 config YAML files + 3 environment configs (development, rehearsal, event)
  - CLI framework: `cli/main.py` + 7 fully implemented command groups (Click-based, 2,234 lines):
    - `config` — validate, render, diff (was already implemented)
    - `seats` — assign, replace, unassign, show, export-map (YAML-backed assignments)
    - `cluster` — prepare, validate, repair (ansible-playbook dispatch, dry-run support)
    - `fleet` — prepare (ThreadPoolExecutor parallel), validate (aggregated reports)
    - `students` — create (crypto-secure `secrets` module), rotate, disable, delete, validate, export-cards (HTML/JSON)
    - `exercises` — reset (runtime-automation playbook dispatch)
    - `reports` — fleet-status (dashboard), seat-report (comprehensive seat map)
  - Config schema (Pydantic v2): `cli/config/schema.py`, loader, validator
  - Secret provider abstraction: 4 backends (env, k8s, aws-sm, vault) with `secret://` URI scheme
  - Filter plugins: `plugins/filter/masworld.py`
  - 17 Ansible roles (defaults/main.yml + tasks/main.yml each)
  - 10 playbooks (8 main + 2 helper task files)
  - 30 unit tests in `tests/unit/`
- Status: SCAFFOLDED — no live cluster testing performed

## Maximo

- `roles/mas_prerequisites/` — delegates to `ibm.mas_devops` (cert_manager, mongodb, sls)
- `roles/mas_core/` — delegates to `ibm.mas_devops` (ibm_catalogs, suite_install, suite_config)
- `roles/maximo_manage/` — delegates to `ibm.mas_devops` (db2, suite_db2_setup_for_manage, suite_app_install, suite_app_configure)
- `roles/mas_edge/` — disabled by default, stub implementation
- Status: SCAFFOLDED — requires IBM entitlement key (blocker B-01) and live cluster

## ACM

- `mas-world-2026-acm/` and `mas-world-2026-automation/acm/` contain:
  - `namespace.yml` — `mas-world-2026-policies`
  - `managedclusterset.yml` — `mas-world-2026` (v1beta2 API)
  - `placement.yml` — 3 Placement resources (attendee, all, facilitator)
  - `policy-mas-world-baseline.yml` — 5 ConfigurationPolicies + PlacementBinding
  - `policy-demo-drift.yml` — facilitator-only drift demo
  - `managedcluster-labels.yml` — label schema documentation
- `roles/acm_registration/` — creates ManagedCluster, assigns labels and ManagedClusterSet
- Status: SCAFFOLDED — requires ACM hub cluster (blocker B-04)

## Logging and Loki

- `roles/logging_operator/` — 3 namespaces, 3 operator Subscriptions (Logging stable-6.6, COO stable, Loki stable-6.6)
- `roles/loki_stack/` — S3 Secret (no_log), LokiStack CR (`loki.grafana.com/v1`, `1x.extra-small`)
- `roles/log_forwarding/` — ClusterLogForwarder CR (`observability.openshift.io/v1`), dynamic inputRefs
- Status: SCAFFOLDED — requires S3 credentials (blocker B-03) and live cluster

## Identity

- `roles/identity_demo/` — deploys per-cluster:
  - Keycloak operator (community-operators, fast channel)
  - Keycloak CR instance (`k8s.keycloak.org/v2alpha1`)
  - OpenLDAP server (bitnami/openldap:2.6) with 4 pre-populated demo users and 2 groups
  - KeycloakRealmImport with LDAP user federation (UserStorageProvider with attribute mappers + group mapper)
  - OIDC client for OpenShift OAuth integration
  - OpenShift OAuth CR patched to include Keycloak as OpenID Connect identity provider
  - Full chain: LDAP → Keycloak → OpenShift OAuth → MAS
- `roles/student_accounts/` — htpasswd generation, OAuth CR patching, namespace + RBAC per seat
- Status: SCAFFOLDED — requires live cluster (blocker B-02)

## Showroom

- `mas-world-2026-showroom/` contains:
  - `site.yml`, `ui-config.yml` (Terminal, Console, Maximo, Grafana tabs)
  - `content/antora.yml` with ocp_version, mas_version attributes
  - `content/modules/ROOT/nav.adoc` — 10 navigation entries
  - 10 content pages: index, 01-access-readiness, 02-navigation-search, 03-acm-fleet-management, 04-updates, 05-observability, 06-identity (with LDAP sync + OIDC exercises), 07-production-architecture, 08-troubleshooting, 99-conclusion
  - Runtime automation: 17 playbooks across 6 modules:
    - `readiness/validate.yml` — 14-category infrastructure check
    - `navigation/{prepare,validate,solve}.yml` — MAS namespace/CR exploration
    - `acm/validate.yml` — event marker ConfigMap check
    - `updates/{prepare,validate,solve,reset}.yml` — version/channel inspection
    - `observability/{prepare,validate,solve,reset}.yml` — log-test pod lifecycle + Loki queries
    - `identity/{prepare,validate,solve,reset}.yml` — Keycloak/LDAP/OIDC/RBAC chain
  - `requirements.txt` (kubernetes Python package) and `packages.txt` (openldap-clients)
  - Partials directory (empty)
- Also mirrored in `mas-world-2026-automation/showroom/`
- `roles/showroom/` — Helm-based deployment (showroom-single-pod), cluster-specific userVariables
- Showroom verify-content result: 0 Critical, 0 High, 2 Warning (intentional naming deviations)
- Status: SCAFFOLDED — content and runtime automation written, not tested on live cluster

## Student Access

- `roles/student_accounts/` — per-seat password generation, htpasswd, OAuth, namespace, RBAC
- `roles/sample_workloads/` — log-generator pod, navigation exercise, exercise ConfigMaps
- CLI: `masworld student create/rotate/disable/delete/validate/export-cards` — fully implemented
- CLI: `masworld seat assign/replace/unassign/show/export-map` — fully implemented with YAML-backed assignments
- Status: SCAFFOLDED — requires live cluster

## Operations

- `mas-world-2026-operations/` contains 13 files:
  - `runbooks/`: pre-event.md, event-morning.md, during-event.md, post-event.md
  - `checklists/`: pre-event-checklist.md, event-morning-checklist.md, event-day-checklist.md
  - `repair-procedures/`: cluster-repair.md, spare-replacement.md
  - `incident-templates/`: incident-report.md
  - `seat-assignment/`: seat-assignment-guide.md
  - `fleet-dashboard/`: dashboard-guide.md
  - `cost-reporting/`: cost-report-template.md
- All runbooks reference `masworld` CLI commands, include timing estimates, escalation procedures
- Status: IMPLEMENTED_NOT_TESTED — content written, not exercised against live environment

## AgnosticV Catalog

- `mas-world-2026-agnosticv/` contains 16 files:
  - `catalog/`: 3 catalog items (event, development, rehearsal)
  - `vars/`: common.yml (81 shared defaults) + 3 environment overrides
  - `workloads/`: post-provision (14 roles), showroom, teardown
  - `access-data/`: user-info-template, access-card-template
  - `schemas/`: catalog-schema.yml (85 variable definitions)
  - `docs/`: rhdp-integration-model.md, existing-cluster-workflow.md
- All marked MANUAL_FALLBACK_SKILL_UNAVAILABLE (catalog-builder skill does not support existing-cluster model)
- All pinned versions consistent with automation config
- Status: SCAFFOLDED — requires RHDP platform team integration

## Testing

- 30 unit tests: `tests/unit/test_config_loader.py`, `test_config_validation.py`, `test_secret_provider.py`
- Tests not executed this session (no `pytest` run)
- No integration tests against live clusters
- No security/negative tests
- Status: SCAFFOLDED

## CI/CD

- `.github/workflows/ci.yml` — 6-job PR validation pipeline:
  - lint-and-validate (yamllint, ansible-lint, ruff, shellcheck, config YAML parse)
  - secret-scan (gitleaks with `.gitleaks.toml`)
  - unit-tests (pytest, uploads results artifact)
  - validate-manifests (kubeconform on ACM manifests)
  - validate-showroom (Antora build, nav.adoc xref validation)
  - docs-links (broken relative link detection in Markdown)
- `.github/workflows/release.yml` — manual dispatch with semver validation, tag creation, GitHub Release
- `.github/dependabot.yml` — weekly pip and github-actions dependency updates
- Status: IMPLEMENTED_NOT_TESTED (not yet pushed to GitHub)

## Public Content

- `mas-world-2026-public-content/` — 21 files, all sanitized (no credentials):
  - `README.md` — repo overview with conference-vs-production disclaimer
  - `operators/` — 3 Subscription YAMLs (Logging stable-6.6, Loki stable-6.6, COO stable)
  - `logging/` — LokiStack CR, ClusterLogForwarder CR, sample log generator pod, 10 LogQL query examples
  - `identity/` — Keycloak OIDC client, OAuth patch snippet, LDAPSyncConfig, 3 RBAC examples
  - `architecture/` — 3 Mermaid diagrams (system context, logging topology, identity chain)
  - `production-guidance/` — logging sizing/HA/SIEM, identity HA/IdP selection, MAS operations/DR
  - `troubleshooting/` — 12 common issues with diagnosis/resolution, organized `oc` diagnostic commands
  - `mas-edge/` — Visual Inspection Edge overview
- Status: IMPLEMENTED_NOT_TESTED

## Testing

- 39 unit tests: all passing (verified 2026-07-19)
  - `test_config_loader.py` — 14 tests (deep merge, redaction, config loading)
  - `test_config_validation.py` — 10 tests (schema validation, embedded key detection)
  - `test_secret_provider.py` — 15 tests (ref parsing, conversions, env provider CRUD)
- No integration tests against live clusters
- No security/negative tests
- No Molecule test scenarios
- Status: Unit tests IMPLEMENTED_AND_TESTED; integration tests NOT_STARTED

## Known Gaps

- No live cluster testing — all roles are SCAFFOLDED
- Molecule test scenarios not created
- CI/CD pipeline not yet pushed to GitHub for execution
- AgnosticV catalog requires RHDP platform team review for existing-cluster integration
- `no-commit-to-branch` hook re-enabled — work on feature branches going forward
