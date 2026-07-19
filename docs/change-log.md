# Project Change Log

This file records every user instruction that changes or clarifies the project.

## Entry format

### TASK-YYYYMMDD-NNN

- Date:
- Original instruction:
- Classification:
- Specification impact:
- `prompt.md` sections changed:
- Decisions created or updated:
- Workarounds created or updated:
- Execution status:
- Validation evidence:

---

### TASK-20260719-001

- Date: 2026-07-19
- Original instruction: "remember that each cluster will have keycloak installed. and this keyclock will be used to demo idp integration and ldap sync to the demo attendees. did the code capture that?"
- Classification: Requirement clarification and gap fix
- Specification impact: Sections 19 (Identity and Keycloak) already required LDAP group synchronization and Keycloak as IdP. The implementation was missing OpenLDAP deployment, LDAP user federation in Keycloak, and OIDC wiring to OpenShift OAuth.
- `prompt.md` sections changed: None (Section 19 already covers LDAP sync and OIDC). No specification change needed — this was an implementation gap, not a spec gap.
- Decisions created or updated: DEC-002 (Keycloak per-cluster) confirmed — each cluster gets its own Keycloak + OpenLDAP for isolation.
- Workarounds created or updated: None
- Execution status: IMPLEMENTED_NOT_TESTED
- Validation evidence: `roles/identity_demo/defaults/main.yml` updated with LDAP config variables, 4 demo users, 2 groups. `roles/identity_demo/tasks/main.yml` updated with OpenLDAP deployment, Keycloak LDAP user federation, OpenShift OAuth OIDC provider wiring. `mas-world-2026-showroom/content/modules/ROOT/pages/06-identity.adoc` rewritten with LDAP sync exercises and OIDC integration exercises.

### TASK-20260719-002

- Date: 2026-07-19
- Original instruction: "add the necessary gitignore"
- Classification: New requirement — repository hygiene
- Specification impact: Added `.gitignore` requirement to repository architecture section.
- `prompt.md` sections changed: Section 5.0 (new) — Git ignore rules
- Decisions created or updated: None
- Workarounds created or updated: None
- Execution status: IMPLEMENTED_NOT_TESTED
- Validation evidence: `.gitignore` created at monorepo root covering Python artifacts, venvs, test caches, IDE files, OS files, Ansible retry files, credential material (keys, kubeconfigs, .env, vault files, entitlement keys), generated reports, Molecule state, Claude Code state.

### TASK-20260719-003

- Date: 2026-07-19
- Original instruction: "proceed with runtime automation"
- Classification: Implementation — Showroom runtime automation (prompt.md Section 22.2)
- Specification impact: None — implements existing requirement
- `prompt.md` sections changed: None
- Decisions created or updated: None
- Workarounds created or updated: None
- Execution status: IMPLEMENTED_NOT_TESTED
- Validation evidence: 17 playbooks created across 6 modules (readiness/1, navigation/3, acm/1, updates/4, observability/4, identity/4) plus `requirements.txt` and `packages.txt`. All playbooks use `hosts: localhost`, `connection: local`, `gather_facts: false`. No secrets in any playbook. Files in both `mas-world-2026-showroom/runtime-automation/` and `mas-world-2026-automation/showroom/runtime-automation/`.

### TASK-20260719-004

- Date: 2026-07-19
- Original instruction: "tackle all and follow any sequence that makes the most sense" (referring to: git init + pre-commit hooks, CLI command implementation, operational runbooks, AgnosticV catalog)
- Classification: Implementation — multiple existing requirements (Sections 5.0, 14, 28, prompt.md AgnosticV sections)
- Specification impact: None — implements existing requirements
- `prompt.md` sections changed: None
- Decisions created or updated: None
- Workarounds created or updated: AgnosticV catalog marked MANUAL_FALLBACK_SKILL_UNAVAILABLE (existing-cluster model not supported by catalog-builder skill)
- Execution status: IMPLEMENTED_NOT_TESTED
- Validation evidence:
  - **Git & pre-commit**: `.pre-commit-config.yaml` (gitleaks, yamllint, ansible-lint, ruff, shellcheck, pre-commit-hooks), `.yamllint.yml`, `.ansible-lint.yml`, `.gitleaks.toml`. Git repo already initialized.
  - **CLI commands**: 6 command files rewritten (2,234 total lines). seats.py (assign/replace/unassign/show/export-map with YAML-backed assignments), cluster.py (prepare/validate/repair via ansible-playbook), fleet.py (ThreadPoolExecutor parallel preparation), students.py (crypto-secure password gen via `secrets`, secret-provider integration, HTML access cards), exercises.py (runtime-automation playbook dispatch), reports.py (fleet-status dashboard, seat-report). Config group unchanged (already implemented).
  - **Operational runbooks**: 13 files across 7 directories in mas-world-2026-operations/: 4 runbooks (pre-event, event-morning, during-event, post-event), 3 checklists, 2 repair procedures, 1 incident template, 1 seat-assignment guide, 1 dashboard guide, 1 cost-report template. All reference `masworld` CLI commands. No credentials.
  - **AgnosticV catalog**: 16 files in mas-world-2026-agnosticv/: 3 catalog items (event/dev/rehearsal), 4 variable files (common + 3 env overrides), 3 workload references (post-provision with 14 roles, showroom, teardown), 2 access-data templates, 1 schema (85 variable definitions), 2 docs (RHDP integration model, existing-cluster workflow gap). All use `secret://` references.
