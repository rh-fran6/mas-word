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