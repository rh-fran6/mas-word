# MAS World 2026 — Workshop Automation

End-to-end automation for provisioning ROSA HCP clusters across multiple AWS accounts and installing IBM Maximo Application Suite for instructor-led workshops.

## Architecture

| Phase | What | Tooling |
|-------|------|---------|
| **Phase 1 — Infrastructure** | AWS VPC networking + ROSA HCP cluster provisioning across 10 isolated AWS accounts | Ansible + AWS CLI + ROSA CLI |
| **Phase 2 — Application** | MAS 9.1.x install, logging, identity, student accounts, Showroom workshop content | Ansible + OpenShift CLI + Python CLI |

**Fleet layout:** 1 facilitator + 1 hub + 8 seats, all in us-east-2, each in a separate AWS account.

## Prerequisites

- **rosa CLI** >= 1.2.x
- **AWS CLI** >= 2.x
- **ansible-core** >= 2.14
- **Python** >= 3.9
- **oc** (OpenShift CLI)
- Valid ROSA offline access token
- Per-cluster AWS accounts with sufficient EC2 quotas

## Quick Start

```bash
# 1. Install all dependencies
make setup

# 2. Configure secrets
cp secrets/rosa-token.yml.example secrets/rosa-token.yml
cp secrets/cluster-credentials.yml.example secrets/cluster-credentials.yml
cp secrets/masworld-secrets.yml.example secrets/masworld-secrets.yml
# Edit all three files with real values

# 3. Full end-to-end workshop build-out
make workshop
```

## Makefile Targets

Run `make help` to see all targets organized by category.

### Setup

| Target | Description |
|--------|-------------|
| `make setup` | Install Python deps, Galaxy collections, pre-commit hooks |

### Phase 1 — Infrastructure

| Target | Description |
|--------|-------------|
| `make preflight` | Validate CLI tools, credentials, AWS connectivity, ROSA login, quotas |
| `make setup-infra` | Create VPCs, subnets, NAT gateways, enroll ROSA accounts |
| `make provision` | Provision all ROSA HCP clusters |
| `make status` | Check fleet cluster status |
| `make deploy-infra` | Full Phase 1: preflight → infra → clusters |
| `make destroy` | Destroy ROSA clusters (with confirmation) |
| `make destroy-infra` | Destroy AWS infrastructure (with confirmation) |

### Phase 2 — Application (MAS World)

| Target | Description |
|--------|-------------|
| `make mas-prepare-cluster CLUSTER=seat-01` | Prepare a single cluster |
| `make mas-prepare-fleet` | Prepare entire fleet |
| `make mas-validate-cluster CLUSTER=seat-01` | Validate a single cluster |
| `make mas-validate-fleet` | Validate fleet readiness |
| `make mas-repair-cluster CLUSTER=seat-01` | Repair a failed cluster |
| `make mas-create-students` | Create student accounts |
| `make mas-rotate-credentials` | Rotate student passwords |
| `make mas-reset-exercises` | Reset lab exercises |
| `make mas-decommission` | Decommission workshop |

### End-to-End

| Target | Description |
|--------|-------------|
| `make workshop` | **Full build-out:** preflight → infra → clusters → prepare fleet → validate |
| `make teardown` | **Full teardown:** decommission → destroy clusters → destroy infra |

### Quality

| Target | Description |
|--------|-------------|
| `make lint` | Run yamllint + ansible-lint |
| `make test` | Lint + syntax checks + unit tests |
| `make test-cov` | Tests with coverage report |
| `make encrypt-secrets` | Encrypt secrets with ansible-vault |
| `make decrypt-secrets` | Decrypt secrets for editing |

## Configuration

### Phase 1 — Infrastructure Config (`group_vars/all/`)

| File | Purpose |
|------|---------|
| `cluster_topology.yml` | Cluster categories, counts, instance types, autoscaling |
| `rosa_defaults.yml` | ROSA version, channel, async timing |
| `aws_infra_defaults.yml` | VPC CIDR, subnet layout, AZ config |
| `infra_state.yml` | Auto-generated infrastructure state (do not edit) |

### Phase 2 — Application Config (`config/`)

| File | Purpose |
|------|---------|
| `defaults.yaml` | Base defaults for all environments |
| `event.yaml` | Event-specific overrides |
| `components.yaml` | Component enable/disable flags |
| `environments/*.yaml` | Environment overrides (dev, rehearsal, event) |

### Secrets (`secrets/`)

| File | Purpose |
|------|---------|
| `rosa-token.yml` | ROSA offline access token |
| `cluster-credentials.yml` | Single source of truth: per-cluster AWS credentials, account IDs, purpose, seat numbers, admin passwords, API URLs |
| `masworld-secrets.yml` | IBM credentials (entitlement key, MAS license, pull secret) |
| `entitlement.dat` | IBM entitlement key |
| `license.dat` | IBM MAS license file |
| `pullsecret.json` | OpenShift pull secret |

All secrets are gitignored. `.example` templates are committed for reference.

## Project Structure

```
├── playbooks/              # Ansible playbooks (6 Phase 1 + 10 Phase 2)
├── roles/
│   ├── rosa_preflight/     # CLI checks, ROSA login, credential validation
│   ├── rosa_cluster/       # Cluster lifecycle (create, wait, destroy)
│   ├── aws_infra/          # VPC/subnet/NAT provisioning per account
│   ├── rosa_account_setup/ # ROSA account enrollment
│   └── (17 MAS roles)     # config_validation through environment_report
├── plugins/filter/         # Custom Jinja2 filters (cluster_helpers, masworld)
├── cli/                    # Python CLI (mas-world command)
├── config/                 # Phase 2 layered YAML config
├── group_vars/all/         # Phase 1 Ansible group vars
├── secrets/                # Credentials (gitignored)
├── tests/                  # Unit tests, syntax checks
├── docs/                   # Documentation (35+ docs)
├── showroom/               # Showroom workshop content (Antora)
├── acm/                    # ACM fleet management manifests
├── operations/             # Operational runbooks and checklists
├── agnosticv/              # RHDP AgnosticV catalog
├── public-content/         # Example manifests and guides
├── collections/            # Vendored Ansible collections
├── molecule/               # Molecule test scenarios
├── scripts/                # Helper scripts (preflight, credential generator)
└── .github/                # CI/CD workflows
```

## Documentation

- [Architecture](docs/architecture.md)
- [Installation Guide](docs/installation-guide.md)
- [Configuration Guide](docs/configuration-guide.md)
- [Configuration Reference](docs/configuration-reference.md)
- [Developer Guide](docs/developer-guide.md)
- [Operator Guide](docs/operator-guide.md)
- [CLI Reference](docs/cli-reference.md)
- [AWS Account Prerequisites](docs/aws-account-prerequisites.md)
- [Teardown Guide](docs/teardown-guide.md)
- [Troubleshooting](docs/troubleshooting.md)
- [MAS World Specification](docs/masworld-specification.md)

## Ansible Vault

```bash
# Encrypt secrets
make encrypt-secrets

# Run with vault password prompt
make provision VAULT_ARGS="--ask-vault-pass"

# Or with a password file
make provision VAULT_ARGS="--vault-password-file=~/.vault_pass"
```
