# Project Instructions

## Master specification

The authoritative implementation specification is located at:

- `prompt.md` — Phase 1 (Infrastructure) + Phase 2 summary
- `docs/masworld-specification.md` — Full Phase 2 (MAS World Application Layer) specification

Before beginning or continuing implementation:

1. Read `prompt.md` in full.
2. Treat its requirements and acceptance criteria as mandatory.
3. Read the current implementation status in:
   - `docs/implementation-status.md`
   - `docs/decision-log.md`
4. Do not claim that a feature has been tested unless test evidence exists.
5. Never commit credentials, kubeconfigs, tokens, passwords, entitlement keys,
   license secrets, or private keys.
6. Use configuration and secret references rather than hard-coded
   environment-specific values.

## Project structure

This is a consolidated project with two phases:

- **Phase 1 (Infrastructure)**: AWS VPC networking + ROSA HCP cluster provisioning
  - Playbooks: `preflight.yml`, `setup-infra.yml`, `provision.yml`, `destroy.yml`, `destroy-infra.yml`, `status.yml`
  - Roles: `rosa_preflight`, `rosa_cluster`, `aws_infra`, `rosa_account_setup`
  - Config: `group_vars/all/` (cluster topology, AWS defaults, infrastructure state, ROSA defaults)
  - Secrets: `secrets/cluster-credentials.yml`, `secrets/rosa-token.yml` (Phase 1 preflight only)

- **Phase 2 (Application)**: MAS World workshop environment
  - Playbooks: `prepare-*.yml`, `validate-*.yml`, `repair-cluster.yml`, `rotate-credentials.yml`, `reset-exercises.yml`, `decommission-workshop.yml`
  - Roles: 17 MAS-related roles (config_validation through environment_report)
  - Config: `config/` directory (layered YAML with environment overrides — cluster inventory comes from `secrets/cluster-credentials.yml`)
  - Secrets: `secrets/masworld-secrets.yml` (IBM creds only), `secrets/entitlement.dat`, `secrets/license.dat`, `secrets/pullsecret.json`
  - CLI: `cli/` (Python Click-based `mas-world` command)

## Key files

- `Makefile` — All targets organized by phase (run `make help` to see them)
- `ansible.cfg` — Ansible configuration
- `requirements.yml` — Galaxy collections
- `pyproject.toml` — Python package config with CLI entry point and dependencies
- `group_vars/all/infra_state.yml` — **Real provisioned AWS infrastructure state — DO NOT MODIFY**
- `secrets/cluster-credentials.yml` — **Single source of truth for ALL per-cluster credentials AND identity (AWS keys, account IDs, admin passwords, api_url, purpose, seat_number, bastion_host, bastion_username, bastion_password) — DO NOT expose**

## Rules

- Update `docs/implementation-status.md` after significant implementation work
- Update `docs/decision-log.md` for architecture decisions
- Run `make lint` before committing
- Do not place raw credentials in any file outside `secrets/`
