# Current Implemented State

This file describes what is actually implemented now, not merely planned.

Last updated: 2026-07-19

## Environment

- Monorepo at `maximo-world/` with 6 logical subdirectories
- `.gitignore` at monorepo root covering credentials, Python artifacts, IDE, OS, Ansible retry, generated reports
- No git repository initialized yet (no `.git/`)

## Automation

- `mas-world-2026-automation/` contains:
  - `ansible.cfg`, `galaxy.yml`, `requirements.yml`, `pyproject.toml`, `Makefile`
  - 7 config YAML files + 3 environment configs (development, rehearsal, event)
  - CLI framework: `cli/main.py` + 7 command group stubs (Click-based)
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
  - Runtime automation directories: readiness, navigation, acm, updates, observability, identity (empty, awaiting implementation)
  - Partials directory (empty)
- Also mirrored in `mas-world-2026-automation/showroom/`
- `roles/showroom/` — Helm-based deployment (showroom-single-pod), cluster-specific userVariables
- Showroom verify-content result: 0 Critical, 0 High, 2 Warning (intentional naming deviations)
- Status: SCAFFOLDED — content written, runtime automation not yet implemented

## Student Access

- `roles/student_accounts/` — per-seat password generation, htpasswd, OAuth, namespace, RBAC
- `roles/sample_workloads/` — log-generator pod, navigation exercise, exercise ConfigMaps
- Status: SCAFFOLDED — requires live cluster

## Testing

- 30 unit tests: `tests/unit/test_config_loader.py`, `test_config_validation.py`, `test_secret_provider.py`
- Tests not executed this session (no `pytest` run)
- No integration tests against live clusters
- No security/negative tests
- Status: SCAFFOLDED

## Known Gaps

- No `git init` — repository not initialized
- Runtime automation playbooks (solve, validate, reset per module) not implemented
- AgnosticV catalog not created (conditional on RHDP delivery model)
- CI/CD pipelines not implemented
- No live cluster testing — all roles are SCAFFOLDED
- Seat assignment tooling (CLI commands) are stubs only
- Access card generation not implemented
- Fleet dashboard/reporting not implemented
- Operational runbooks not created
- Public content repository empty
- Operations repository empty
- Pre-commit hooks and secret scanning not configured
- Molecule test scenarios not created
