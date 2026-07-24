[feature/public-content-and-cicd 8d305ac] New Baseline commit: MAS World 2026 workshop automation
 397 files changed, 17969 insertions(+), 8465 deletions(-)
 rename .ansible-lint.yml => .ansible-lint (79%)
 create mode 100644 .secrets.baseline
 create mode 100644 Makefile
 create mode 100644 README.md
 rename mas-world-2026-automation/cli/__init__.py => acm/demo-assets/.gitkeep (100%)
 rename mas-world-2026-automation/cli/commands/__init__.py => acm/gitops/.gitkeep (100%)
 rename mas-world-2026-automation/cli/config/__init__.py => acm/labels/.gitkeep (100%)
 rename {mas-world-2026-automation/acm => acm}/managedcluster-labels.yml (100%)
 rename {mas-world-2026-automation/acm => acm}/managedclusterset.yml (100%)
 rename mas-world-2026-automation/cli/inventory/__init__.py => acm/managedclustersets/.gitkeep (100%)
 rename {mas-world-2026-automation/acm => acm}/namespace.yml (100%)
 rename {mas-world-2026-automation/acm => acm}/placement.yml (100%)
 rename mas-world-2026-automation/cli/orchestration/__init__.py => acm/placements/.gitkeep (100%)
 rename mas-world-2026-automation/cli/reporting/__init__.py => acm/policies/baseline/.gitkeep (100%)
 rename mas-world-2026-automation/cli/secrets/__init__.py => acm/policies/drift/.gitkeep (100%)
 rename {mas-world-2026-automation/acm => acm}/policy-demo-drift.yml (100%)
 rename {mas-world-2026-automation/acm => acm}/policy-mas-world-baseline.yml (100%)
 rename {mas-world-2026-agnosticv => agnosticv}/README.md (100%)
 rename {mas-world-2026-agnosticv => agnosticv}/access-data/access-card-template.yml (100%)
 rename {mas-world-2026-agnosticv => agnosticv}/access-data/user-info-template.yml (100%)
 rename {mas-world-2026-agnosticv => agnosticv}/catalog/mas-world-2026-dev.yml (93%)
 rename {mas-world-2026-agnosticv => agnosticv}/catalog/mas-world-2026-rehearsal.yml (92%)
 rename {mas-world-2026-agnosticv => agnosticv}/catalog/mas-world-2026-workshop.yml (93%)
 rename {mas-world-2026-agnosticv => agnosticv}/docs/existing-cluster-workflow.md (100%)
 rename {mas-world-2026-agnosticv => agnosticv}/docs/rhdp-integration-model.md (98%)
 rename {mas-world-2026-agnosticv => agnosticv}/schemas/catalog-schema.yml (95%)
 rename {mas-world-2026-agnosticv => agnosticv}/vars/common.yml (94%)
 rename {mas-world-2026-agnosticv => agnosticv}/vars/development.yml (100%)
 rename {mas-world-2026-agnosticv => agnosticv}/vars/event.yml (100%)
 rename {mas-world-2026-agnosticv => agnosticv}/vars/rehearsal.yml (100%)
 rename {mas-world-2026-agnosticv => agnosticv}/workloads/mas-world-post-provision.yml (95%)
 rename {mas-world-2026-agnosticv => agnosticv}/workloads/mas-world-showroom.yml (100%)
 rename {mas-world-2026-agnosticv => agnosticv}/workloads/mas-world-teardown.yml (97%)
 rename mas-world-2026-automation/ansible.cfg => ansible.cfg (56%)
 rename {mas-world-2026-automation/plugins => cli}/__init__.py (100%)
 rename {mas-world-2026-automation/plugins/filter => cli/commands}/__init__.py (100%)
 create mode 100644 cli/commands/cluster.py
 rename {mas-world-2026-automation/cli => cli}/commands/config.py (79%)
 rename {mas-world-2026-automation/cli => cli}/commands/exercises.py (99%)
 rename {mas-world-2026-automation/cli => cli}/commands/fleet.py (88%)
 rename {mas-world-2026-automation/cli => cli}/commands/reports.py (92%)
 rename {mas-world-2026-automation/cli => cli}/commands/seats.py (93%)
 rename {mas-world-2026-automation/cli => cli}/commands/students.py (94%)
 rename {mas-world-2026-automation/tests => cli/config}/__init__.py (100%)
 rename {mas-world-2026-automation/cli => cli}/config/loader.py (71%)
 rename {mas-world-2026-automation/cli => cli}/config/schema.py (90%)
 rename {mas-world-2026-automation/cli => cli}/config/validator.py (57%)
 rename {mas-world-2026-automation/tests/unit => cli/inventory}/__init__.py (100%)
 rename {mas-world-2026-automation/cli => cli}/main.py (99%)
 create mode 100644 cli/orchestration/__init__.py
 create mode 100644 cli/reporting/__init__.py
 create mode 100644 cli/secrets/__init__.py
 rename {mas-world-2026-automation/cli => cli}/secrets/aws_sm_provider.py (93%)
 rename {mas-world-2026-automation/cli => cli}/secrets/env_provider.py (100%)
 create mode 100644 cli/secrets/file_provider.py
 rename {mas-world-2026-automation/cli => cli}/secrets/k8s_provider.py (96%)
 rename {mas-world-2026-automation/cli => cli}/secrets/provider.py (93%)
 rename {mas-world-2026-automation/cli => cli}/secrets/vault_provider.py (90%)
 rename {mas-world-2026-automation/config => config}/aws.yaml (100%)
 rename {mas-world-2026-automation/config => config}/components.yaml (90%)
 rename {mas-world-2026-automation/config => config}/credentials.yaml (59%)
 rename {mas-world-2026-automation/config => config}/defaults.yaml (96%)
 rename {mas-world-2026-automation/config => config}/environments/development.yaml (67%)
 rename {mas-world-2026-automation/config => config}/environments/event.yaml (100%)
 rename {mas-world-2026-automation/config => config}/environments/rehearsal.yaml (100%)
 rename {mas-world-2026-automation/config => config}/event.yaml (100%)
 rename {mas-world-2026-automation/config => config}/showroom.yaml (66%)
 create mode 100644 docs/aws-account-prerequisites.md
 delete mode 100644 docs/change-log.md
 create mode 100644 docs/changelog.md
 create mode 100644 docs/cluster-onboarding-guide.md
 create mode 100644 docs/configuration-guide.md
 create mode 100644 docs/masworld-specification.md
 create mode 100644 docs/troubleshooting.md
 rename mas-world-2026-automation/galaxy.yml => galaxy.yml (100%)
 create mode 100644 group_vars/all/aws_infra_defaults.yml
 create mode 100644 group_vars/all/cluster_topology.yml
 create mode 100644 group_vars/all/infra_state.yml
 create mode 100644 group_vars/all/rosa_defaults.yml
 create mode 120000 inventories/group_vars
 create mode 100644 inventories/localhost.yml
 delete mode 100644 mas-world-2026-automation/Makefile
 delete mode 100644 mas-world-2026-automation/cli/commands/cluster.py
 delete mode 100644 mas-world-2026-automation/config/clusters.yaml
 delete mode 100644 mas-world-2026-automation/playbooks/_prepare-single-cluster.yml
 delete mode 100644 mas-world-2026-automation/playbooks/_validate-single-cluster.yml
 delete mode 100644 mas-world-2026-automation/playbooks/prepare-cluster.yml
 delete mode 100644 mas-world-2026-automation/playbooks/prepare-fleet.yml
 delete mode 100644 mas-world-2026-automation/playbooks/repair-cluster.yml
 delete mode 100644 mas-world-2026-automation/tests/conftest.py
 delete mode 100644 mas-world-2026-automation/tests/unit/test_secret_provider.py
 delete mode 100644 mas-world-2026-showroom/content/antora.yml
 delete mode 100644 mas-world-2026-showroom/content/modules/ROOT/nav.adoc
 delete mode 100644 mas-world-2026-showroom/content/modules/ROOT/pages/01-access-readiness.adoc
 delete mode 100644 mas-world-2026-showroom/content/modules/ROOT/pages/02-navigation-search.adoc
 delete mode 100644 mas-world-2026-showroom/content/modules/ROOT/pages/03-acm-fleet-management.adoc
 delete mode 100644 mas-world-2026-showroom/content/modules/ROOT/pages/04-updates.adoc
 delete mode 100644 mas-world-2026-showroom/content/modules/ROOT/pages/05-observability.adoc
 delete mode 100644 mas-world-2026-showroom/content/modules/ROOT/pages/06-identity.adoc
 delete mode 100644 mas-world-2026-showroom/content/modules/ROOT/pages/07-production-architecture.adoc
 delete mode 100644 mas-world-2026-showroom/content/modules/ROOT/pages/08-troubleshooting.adoc
 delete mode 100644 mas-world-2026-showroom/content/modules/ROOT/pages/99-conclusion.adoc
 delete mode 100644 mas-world-2026-showroom/content/modules/ROOT/pages/index.adoc
 delete mode 100644 mas-world-2026-showroom/runtime-automation/acm/validate.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/identity/prepare.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/identity/reset.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/identity/solve.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/identity/validate.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/navigation/prepare.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/navigation/solve.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/navigation/validate.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/observability/prepare.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/observability/reset.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/observability/solve.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/observability/validate.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/packages.txt
 delete mode 100644 mas-world-2026-showroom/runtime-automation/readiness/validate.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/requirements.txt
 delete mode 100644 mas-world-2026-showroom/runtime-automation/updates/prepare.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/updates/reset.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/updates/solve.yml
 delete mode 100644 mas-world-2026-showroom/runtime-automation/updates/validate.yml
 delete mode 100644 mas-world-2026-showroom/site.yml
 delete mode 100644 mas-world-2026-showroom/ui-config.yml
 rename {mas-world-2026-automation/molecule => molecule}/config_validation/converge.yml (98%)
 rename {mas-world-2026-automation/molecule => molecule}/config_validation/molecule.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/config_validation/prepare.yml (99%)
 rename {mas-world-2026-automation/molecule => molecule}/config_validation/verify.yml (99%)
 rename {mas-world-2026-automation/molecule => molecule}/conftest.py (100%)
 rename {mas-world-2026-automation/molecule => molecule}/event_metadata/converge.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/event_metadata/molecule.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/event_metadata/verify.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/event_readiness/converge.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/event_readiness/molecule.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/event_readiness/prepare.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/event_readiness/verify.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/requirements.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/sample_workloads/converge.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/sample_workloads/molecule.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/sample_workloads/verify.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/student_accounts/converge.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/student_accounts/molecule.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/student_accounts/prepare.yml (100%)
 rename {mas-world-2026-automation/molecule => molecule}/student_accounts/verify.yml (100%)
 rename {mas-world-2026-operations => operations}/checklists/event-day-checklist.md (100%)
 rename {mas-world-2026-operations => operations}/checklists/event-morning-checklist.md (100%)
 rename {mas-world-2026-operations => operations}/checklists/pre-event-checklist.md (99%)
 rename {mas-world-2026-operations => operations}/cost-reporting/cost-report-template.md (100%)
 rename {mas-world-2026-operations => operations}/fleet-dashboard/dashboard-guide.md (100%)
 rename {mas-world-2026-operations => operations}/incident-templates/incident-report.md (100%)
 rename {mas-world-2026-operations => operations}/repair-procedures/cluster-repair.md (100%)
 rename {mas-world-2026-operations => operations}/repair-procedures/spare-replacement.md (100%)
 rename {mas-world-2026-operations => operations}/runbooks/during-event.md (100%)
 rename {mas-world-2026-operations => operations}/runbooks/event-morning.md (100%)
 rename {mas-world-2026-operations => operations}/runbooks/post-event.md (99%)
 rename {mas-world-2026-operations => operations}/runbooks/pre-event.md (100%)
 rename {mas-world-2026-operations => operations}/seat-assignment/seat-assignment-guide.md (100%)
 create mode 100644 playbooks/_deploy-aws-ready.yml
 create mode 100644 playbooks/_deploy-cluster-ready.yml
 create mode 100644 playbooks/_deploy-greenfield.yml
 create mode 100644 playbooks/_prepare-single-cluster.yml
 create mode 100644 playbooks/_resolve-cluster-profile.yml
 create mode 100644 playbooks/_validate-single-cluster.yml
 rename {mas-world-2026-automation/playbooks => playbooks}/decommission-workshop.yml (74%)
 create mode 100644 playbooks/deploy.yml
 create mode 100644 playbooks/destroy-infra.yml
 create mode 100644 playbooks/destroy.yml
 create mode 100644 playbooks/lab-readiness.yml
 create mode 100644 playbooks/preflight.yml
 create mode 100644 playbooks/prepare-cluster.yml
 create mode 100644 playbooks/prepare-fleet.yml
 create mode 100644 playbooks/provision.yml
 create mode 100644 playbooks/repair-cluster.yml
 rename {mas-world-2026-automation/playbooks => playbooks}/reset-exercises.yml (100%)
 rename {mas-world-2026-automation/playbooks => playbooks}/rotate-credentials.yml (100%)
 create mode 100644 playbooks/setup-infra.yml
 create mode 100644 playbooks/status.yml
 rename {mas-world-2026-automation/playbooks => playbooks}/validate-cluster.yml (100%)
 rename {mas-world-2026-automation/playbooks => playbooks}/validate-fleet.yml (80%)
 create mode 100644 plugins/__init__.py
 create mode 100644 plugins/filter/__init__.py
 create mode 100644 plugins/filter/cluster_helpers.py
 rename {mas-world-2026-automation/plugins => plugins}/filter/masworld.py (100%)
 rename {mas-world-2026-public-content => public-content}/README.md (100%)
 rename {mas-world-2026-public-content => public-content}/architecture/identity-topology.md (100%)
 rename {mas-world-2026-public-content => public-content}/architecture/logging-topology.md (100%)
 rename {mas-world-2026-public-content => public-content}/architecture/system-context.md (100%)
 rename {mas-world-2026-public-content => public-content}/identity/keycloak-oidc-client.yaml (100%)
 rename {mas-world-2026-public-content => public-content}/identity/ldap-group-sync.yaml (100%)
 rename {mas-world-2026-public-content => public-content}/identity/openshift-oauth-oidc.yaml (100%)
 rename {mas-world-2026-public-content => public-content}/identity/rbac-examples.yaml (100%)
 rename {mas-world-2026-public-content => public-content}/logging/clusterlogforwarder-example.yaml (100%)
 rename {mas-world-2026-public-content => public-content}/logging/logql-queries.md (100%)
 rename {mas-world-2026-public-content => public-content}/logging/lokistack-example.yaml (100%)
 rename {mas-world-2026-public-content => public-content}/logging/sample-log-generator.yaml (100%)
 rename {mas-world-2026-public-content => public-content}/mas-edge/overview.md (100%)
 rename {mas-world-2026-public-content => public-content}/operators/cluster-observability-operator.yaml (100%)
 rename {mas-world-2026-public-content => public-content}/operators/loki-operator.yaml (100%)
 rename {mas-world-2026-public-content => public-content}/operators/openshift-logging-operator.yaml (100%)
 rename {mas-world-2026-public-content => public-content}/production-guidance/identity-production.md (100%)
 rename {mas-world-2026-public-content => public-content}/production-guidance/logging-production.md (100%)
 rename {mas-world-2026-public-content => public-content}/production-guidance/mas-operations.md (100%)
 rename {mas-world-2026-public-content => public-content}/troubleshooting/common-issues.md (100%)
 rename {mas-world-2026-public-content => public-content}/troubleshooting/diagnostic-commands.md (100%)
 rename mas-world-2026-automation/pyproject.toml => pyproject.toml (80%)
 rename mas-world-2026-automation/requirements.yml => requirements.yml (89%)
 create mode 100644 roles/acm_hub/defaults/main.yml
 create mode 100644 roles/acm_hub/meta/main.yml
 create mode 100644 roles/acm_hub/tasks/main.yml
 rename {mas-world-2026-automation/roles => roles}/acm_registration/defaults/main.yml (63%)
 create mode 100644 roles/acm_registration/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/acm_registration/tasks/main.yml (54%)
 create mode 100644 roles/aws_efs/defaults/main.yml
 create mode 100644 roles/aws_efs/meta/main.yml
 create mode 100644 roles/aws_efs/tasks/main.yml
 create mode 100644 roles/aws_infra/defaults/main.yml
 create mode 100644 roles/aws_infra/tasks/build_definitions.yml
 create mode 100644 roles/aws_infra/tasks/create.yml
 create mode 100644 roles/aws_infra/tasks/create_account_infra.yml
 create mode 100644 roles/aws_infra/tasks/destroy.yml
 create mode 100644 roles/aws_infra/tasks/destroy_account_infra.yml
 create mode 100644 roles/aws_infra/tasks/main.yml
 create mode 100644 roles/aws_infra/tasks/verify.yml
 create mode 100644 roles/aws_infra/vars/main.yml
 create mode 100644 roles/aws_s3_bucket/defaults/main.yml
 create mode 100644 roles/aws_s3_bucket/meta/main.yml
 create mode 100644 roles/aws_s3_bucket/tasks/main.yml
 rename {mas-world-2026-automation/roles => roles}/cluster_preflight/defaults/main.yml (100%)
 create mode 100644 roles/cluster_preflight/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/cluster_preflight/tasks/main.yml (83%)
 create mode 100644 roles/cluster_preflight/templates/.gitkeep
 rename {mas-world-2026-automation/roles => roles}/config_validation/defaults/main.yml (77%)
 create mode 100644 roles/config_validation/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/config_validation/tasks/main.yml (89%)
 create mode 100644 roles/efs_csi_driver/defaults/main.yml
 create mode 100644 roles/efs_csi_driver/meta/main.yml
 create mode 100644 roles/efs_csi_driver/tasks/main.yml
 rename {mas-world-2026-automation/roles => roles}/environment_report/defaults/main.yml (100%)
 create mode 100644 roles/environment_report/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/environment_report/tasks/main.yml (98%)
 rename {mas-world-2026-automation/roles => roles}/event_metadata/defaults/main.yml (100%)
 create mode 100644 roles/event_metadata/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/event_metadata/tasks/main.yml (97%)
 rename {mas-world-2026-automation/roles => roles}/event_readiness/defaults/main.yml (100%)
 create mode 100644 roles/event_readiness/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/event_readiness/tasks/main.yml (95%)
 rename {mas-world-2026-automation/roles => roles}/identity_demo/defaults/main.yml (100%)
 create mode 100644 roles/identity_demo/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/identity_demo/tasks/main.yml (86%)
 rename {mas-world-2026-automation/roles => roles}/log_forwarding/defaults/main.yml (100%)
 create mode 100644 roles/log_forwarding/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/log_forwarding/tasks/main.yml (89%)
 rename {mas-world-2026-automation/roles => roles}/logging_operator/defaults/main.yml (100%)
 create mode 100644 roles/logging_operator/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/logging_operator/tasks/main.yml (94%)
 rename {mas-world-2026-automation/roles => roles}/loki_stack/defaults/main.yml (100%)
 create mode 100644 roles/loki_stack/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/loki_stack/tasks/main.yml (90%)
 rename {mas-world-2026-automation/roles => roles}/mas_core/defaults/main.yml (93%)
 create mode 100644 roles/mas_core/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/mas_core/tasks/main.yml (75%)
 rename {mas-world-2026-automation/roles => roles}/mas_edge/defaults/main.yml (100%)
 create mode 100644 roles/mas_edge/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/mas_edge/tasks/main.yml (91%)
 rename {mas-world-2026-automation/roles => roles}/mas_prerequisites/defaults/main.yml (100%)
 create mode 100644 roles/mas_prerequisites/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/mas_prerequisites/tasks/main.yml (60%)
 rename {mas-world-2026-automation/roles => roles}/maximo_manage/defaults/main.yml (93%)
 create mode 100644 roles/maximo_manage/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/maximo_manage/tasks/main.yml (90%)
 create mode 100644 roles/rosa_account_setup/defaults/main.yml
 create mode 100644 roles/rosa_account_setup/tasks/build_definitions.yml
 create mode 100644 roles/rosa_account_setup/tasks/main.yml
 create mode 100644 roles/rosa_cluster/defaults/main.yml
 create mode 100644 roles/rosa_cluster/tasks/_create_admin_single.yml
 create mode 100644 roles/rosa_cluster/tasks/build_definitions.yml
 create mode 100644 roles/rosa_cluster/tasks/create.yml
 create mode 100644 roles/rosa_cluster/tasks/create_admin.yml
 create mode 100644 roles/rosa_cluster/tasks/destroy.yml
 create mode 100644 roles/rosa_cluster/tasks/destroy_cleanup.yml
 create mode 100644 roles/rosa_cluster/tasks/machinepool.yml
 create mode 100644 roles/rosa_cluster/tasks/main.yml
 create mode 100644 roles/rosa_cluster/tasks/save_credentials.yml
 create mode 100644 roles/rosa_cluster/tasks/status.yml
 create mode 100644 roles/rosa_cluster/tasks/verify.yml
 create mode 100644 roles/rosa_cluster/tasks/wait_ready.yml
 create mode 100644 roles/rosa_cluster/tasks/workshop_machinepool.yml
 create mode 100644 roles/rosa_cluster/templates/cluster-report.j2
 create mode 100644 roles/rosa_cluster/vars/main.yml
 create mode 100644 roles/rosa_preflight/defaults/main.yml
 create mode 100644 roles/rosa_preflight/tasks/main.yml
 rename {mas-world-2026-automation/roles => roles}/sample_workloads/defaults/main.yml (100%)
 create mode 100644 roles/sample_workloads/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/sample_workloads/tasks/main.yml (90%)
 create mode 100644 roles/scenario_preflight/defaults/main.yml
 create mode 100644 roles/scenario_preflight/tasks/_validate-phase2-fields.yml
 create mode 100644 roles/scenario_preflight/tasks/aws-ready.yml
 create mode 100644 roles/scenario_preflight/tasks/cluster-ready.yml
 create mode 100644 roles/scenario_preflight/tasks/greenfield.yml
 create mode 100644 roles/scenario_preflight/tasks/main.yml
 create mode 100644 roles/scenario_preflight/vars/main.yml
 rename {mas-world-2026-automation/roles => roles}/showroom/defaults/main.yml (89%)
 create mode 100644 roles/showroom/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/showroom/tasks/main.yml (92%)
 rename {mas-world-2026-automation/roles => roles}/student_accounts/defaults/main.yml (75%)
 create mode 100644 roles/student_accounts/meta/main.yml
 rename {mas-world-2026-automation/roles => roles}/student_accounts/tasks/main.yml (94%)
 create mode 100644 runtime.md
 create mode 100644 schemas/.gitkeep
 create mode 100755 scripts/deploy-wizard.sh
 create mode 100755 scripts/generate-credentials-template.sh
 create mode 100755 scripts/lab-readiness-test.sh
 create mode 100755 scripts/preflight.sh
 create mode 100644 secrets/.gitkeep
 create mode 100644 secrets/cluster-credentials.yml.example
 create mode 100644 secrets/masworld-secrets.yml.example
 create mode 100644 secrets/rosa-token.yml.example
 rename {mas-world-2026-automation/showroom => showroom}/content/antora.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/content/modules/ROOT/nav.adoc (100%)
 rename {mas-world-2026-automation/showroom => showroom}/content/modules/ROOT/pages/01-access-readiness.adoc (100%)
 rename {mas-world-2026-automation/showroom => showroom}/content/modules/ROOT/pages/02-navigation-search.adoc (100%)
 rename {mas-world-2026-automation/showroom => showroom}/content/modules/ROOT/pages/03-acm-fleet-management.adoc (100%)
 rename {mas-world-2026-automation/showroom => showroom}/content/modules/ROOT/pages/04-updates.adoc (100%)
 rename {mas-world-2026-automation/showroom => showroom}/content/modules/ROOT/pages/05-observability.adoc (100%)
 rename {mas-world-2026-automation/showroom => showroom}/content/modules/ROOT/pages/06-identity.adoc (100%)
 rename {mas-world-2026-automation/showroom => showroom}/content/modules/ROOT/pages/07-production-architecture.adoc (100%)
 rename {mas-world-2026-automation/showroom => showroom}/content/modules/ROOT/pages/08-troubleshooting.adoc (100%)
 rename {mas-world-2026-automation/showroom => showroom}/content/modules/ROOT/pages/99-conclusion.adoc (100%)
 rename {mas-world-2026-automation/showroom => showroom}/content/modules/ROOT/pages/index.adoc (100%)
 create mode 100644 showroom/content/modules/ROOT/partials/.gitkeep
 create mode 100644 showroom/docs/.gitkeep
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/acm/validate.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/identity/prepare.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/identity/reset.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/identity/solve.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/identity/validate.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/navigation/prepare.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/navigation/solve.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/navigation/validate.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/observability/prepare.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/observability/reset.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/observability/solve.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/observability/validate.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/packages.txt (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/readiness/validate.yml (99%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/requirements.txt (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/updates/prepare.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/updates/reset.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/updates/solve.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/runtime-automation/updates/validate.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/site.yml (100%)
 rename {mas-world-2026-automation/showroom => showroom}/ui-config.yml (100%)
 create mode 100644 tests/__init__.py
 create mode 100644 tests/conftest.py
 create mode 100644 tests/integration/.gitkeep
 create mode 100644 tests/security/.gitkeep
 create mode 100644 tests/test_filters.py
 create mode 100644 tests/test_scenario_preflight.py
 create mode 100755 tests/test_syntax.sh
 create mode 100644 tests/test_variables.yml
 create mode 100644 tests/unit/__init__.py
 rename {mas-world-2026-automation/tests => tests}/unit/test_config_loader.py (99%)
 rename {mas-world-2026-automation/tests => tests}/unit/test_config_validation.py (95%)
 create mode 100644 tests/unit/test_secret_provider.py
