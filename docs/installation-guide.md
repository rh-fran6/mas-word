# Installation Guide — MAS World 2026

**Status**: DRAFT — Phase 1
**Date**: 2026-07-19

---

## 1. Prerequisites

Install the following before proceeding. All items are required unless
marked optional.

| Prerequisite | Version | Purpose | Notes |
|---|---|---|---|
| Python | 3.11+ | CLI, configuration, orchestration | Required by `pyproject.toml` |
| ansible-core | 2.17.x | Playbook execution | Installed via pip |
| kubernetes.core | >=3.0.0, <4.0.0 | Kubernetes module support | Installed via `requirements.yml` |
| redhat.openshift | >=2.3.0, <3.0.0 | OpenShift-specific modules | Installed via `requirements.yml` |
| amazon.aws | >=7.0.0, <8.0.0 | AWS S3 and IAM automation | Installed via `requirements.yml` |
| community.crypto | >=2.18.0, <3.0.0 | Certificate and credential operations | Installed via `requirements.yml` |
| community.general | >=8.0.0, <9.0.0 | General-purpose modules | Installed via `requirements.yml` |
| ibm.mas_devops | v37.10.0 | MAS installation and configuration | Pinned version |
| `oc` CLI | 4.18+ | OpenShift cluster operations | Must match target cluster version range |
| AWS CLI | v2 | S3 bucket management, IAM operations | Required for logging object storage |
| Git | 2.x | Repository operations | Any recent version |
| Make | 3.x+ | Task runner | Optional if using `mas-world` CLI directly |
| pre-commit | 3.x | Secret scanning, linting hooks | Required for contributors |

Verify the essentials:

```bash
python3.11 --version
ansible --version
oc version --client
aws --version
git --version
```

---

## 2. Clone the Repository

```bash
git clone <REPO_URL> maximo-world
cd maximo-world
```

The monorepo contains the following top-level directories:

```text
maximo-world/
├──    # Ansible roles, playbooks, CLI
├── showroom/     # Attendee workshop content
├── public-content/
├── acm/          # ACM policies and fleet metadata
├── agnosticv/    # RHDP catalog configuration
├── operations/   # Runbooks and operational tooling
├── config/                      # Shared configuration files
└── docs/                        # Project documentation
```

---

## 3. Python Virtual Environment

Create and activate a virtual environment, then install the CLI and all
dependencies.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

This installs the `mas-world` CLI entry point (defined in `pyproject.toml`)
along with runtime dependencies (Click, Pydantic, PyYAML, Jinja2, boto3,
kubernetes, Rich, jsonschema, qrcode) and development dependencies (pytest,
ruff, mypy, ansible-lint, yamllint, molecule).

Verify the CLI is available:

```bash
mas-world --help
```

Expected output:

```text
Usage: mas-world [OPTIONS] COMMAND [ARGS]...

  MAS World 2026 — Fleet management CLI.

Options:
  --env [development|rehearsal|event]  Target environment.  [default: development]
  --config-dir PATH                    Configuration directory.
  -v, --verbose                        Enable verbose output.
  --help                               Show this message and exit.

Commands:
  cluster   Cluster preparation and validation.
  config    Configuration validation and rendering.
  exercise  Exercise reset operations.
  fleet     Fleet-wide preparation and validation.
  report    Fleet status and seat reports.
  seat      Seat assignment management.
  student   Student account lifecycle.
```

To install the optional HashiCorp Vault provider:

```bash
pip install -e ".[vault]"
```

---

## 4. Install Ansible Collections

Install the required Ansible Galaxy collections from the pinned
`requirements.yml`:

```bash
cd mas-world-2026-automation
ansible-galaxy collection install -r requirements.yml --force
```

The `ibm.mas_devops` collection is not listed in `requirements.yml` because
it requires IBM registry authentication. Install it separately:

```bash
ansible-galaxy collection install ibm.mas_devops:==37.10.0
```

Verify installed collections:

```bash
ansible-galaxy collection list | grep -E '(kubernetes|redhat|amazon|community|ibm)'
```

---

## 5. Configure the Secret Provider

The automation never stores secret values in configuration files. All
secrets are accessed at runtime through a pluggable provider abstraction.

Five providers are available:

| Provider | Config value | Use case | Backend |
|---|---|---|---|
| File-based secrets | `file` | Local development (recommended) | Files in `secrets/` directory, referenced via `file://` in `secrets/masworld-secrets.yml` |
| Environment variables | `env` | Local development (alternative) | Shell environment |
| Kubernetes Secrets | `k8s` | In-cluster execution | Kubernetes API |
| AWS Secrets Manager | `aws-sm` | Rehearsal and event | AWS Secrets Manager |
| HashiCorp Vault | `vault` | Optional enterprise | Vault KV v2 |

### 5.1 Select a Provider

The provider is set in the environment configuration file. For example,
`config/environments/development.yaml` uses:

```yaml
secrets:
  provider: env
```

The rehearsal and event environments use AWS Secrets Manager:

```yaml
secrets:
  provider: aws-sm
  config:
    aws_region: us-east-2
```

### 5.2 Secret References

Configuration files use `secret://` URI references instead of literal
values. The file `config/credentials.yaml` contains the project-wide
references:

```yaml
ibm:
  entitlement_key_ref: "secret://mas-world/ibm/entitlement-key"
  license_ref: "secret://mas-world/ibm/license"

aws:
  default_region: us-east-2
  access_key_id_ref: "secret://mas-world/aws/access-key-id"
  secret_access_key_ref: "secret://mas-world/aws/secret-access-key"

container_registry:
  pull_secret_ref: "secret://mas-world/registry/pull-secret"
```

Per-cluster administrative credentials use the same pattern:

```yaml
clusters:
  - id: seat-01
    connection:
      api_url: https://api.seat-01.example.com:6443
      admin_auth_method: kubeconfig
      admin_secret_ref: "secret://mas-world/clusters/seat-01/admin-kubeconfig"
```

### 5.3 Populate Secrets for Local Development (env provider)

When using the `env` provider, export secrets as environment variables.
The `secret://` path is transformed to an environment variable name by
uppercasing and replacing `/` and `-` with `_`:

```bash
# secret://mas-world/ibm/entitlement-key  ->  MAS_WORLD_IBM_ENTITLEMENT_KEY
export MAS_WORLD_IBM_ENTITLEMENT_KEY="<YOUR_IBM_ENTITLEMENT_KEY>"
export MAS_WORLD_IBM_LICENSE="<YOUR_IBM_LICENSE_CONTENT>"
export MAS_WORLD_AWS_ACCESS_KEY_ID="<YOUR_AWS_ACCESS_KEY_ID>"
export MAS_WORLD_AWS_ACCESS_KEY_SECRET="<YOUR_AWS_ACCESS_KEY_SECRET>"
export MAS_WORLD_ACM_HUB_KUBECONFIG="<YOUR_ACM_HUB_KUBECONFIG>"  # Optional; only if ACM registration is enabled
export MAS_WORLD_REGISTRY_PULL_SECRET="<YOUR_PULL_SECRET_JSON>"
export MAS_WORLD_CLUSTERS_SEAT_01_ADMIN_KUBECONFIG="<YOUR_KUBECONFIG>"
```

Never commit a `.env` file or shell script containing these values.
The `.gitignore` blocks `.env*` files as a defense-in-depth measure.

### 5.4 Populate Secrets for AWS Secrets Manager (aws-sm provider)

Store each secret in AWS Secrets Manager under the path used in the
`secret://` reference. Ensure the IAM principal running the automation
has `secretsmanager:GetSecretValue` permission for the required paths:

```bash
aws secretsmanager create-secret \
  --name "mas-world/ibm/entitlement-key" \
  --secret-string "<YOUR_IBM_ENTITLEMENT_KEY>" \
  --region us-east-2

aws secretsmanager create-secret \
  --name "mas-world/clusters/seat-01/admin-kubeconfig" \
  --secret-string file:///path/to/seat-01-kubeconfig \
  --region us-east-2
```

---

## 6. Configure Environment Files

### 6.1 Configuration Precedence

Configuration is merged in this order. Later layers override earlier ones:

```text
config/defaults.yaml                           <- Base defaults for all environments
   |
config/environments/<env>.yaml                 <- Environment-specific overrides
   |
config/event.yaml                              <- Event-level overrides
   |
secrets/cluster-credentials.yml (per-cluster)  <- Cluster identity and credentials
   |
CLI arguments                                  <- Runtime overrides (--env, --cluster, etc.)
```

The merge is deep: nested keys are merged, not replaced, unless the value
is a scalar or list.

### 6.2 Environment Files

Three environments are provided:

| Environment | File | Clusters | Concurrency | Secret provider | Shared passwords |
|---|---|---|---|---|---|
| development | `environments/development.yaml` | 1 attendee, 0 spare, 1 facilitator | 1 | `env` | Allowed (with warning) |
| rehearsal | `environments/rehearsal.yaml` | 5 attendee, 1 spare, 1 facilitator | 3 | `aws-sm` | Not allowed |
| event | `environments/event.yaml` | 50 attendee, 5 spare, 1 facilitator | 5 | `aws-sm` | Not allowed |

To use an environment, pass `--env` to any CLI command:

```bash
mas-world --env development config validate
mas-world --env rehearsal fleet prepare
mas-world --env event fleet validate
```

### 6.3 Component Configuration

Component versions and enablement are defined in `config/components.yaml`:

```yaml
components:
  openshift:
    version: "4.21"
  mas:
    version: "9.1.x"
    channel: "9.1.x"
    catalog_tag: "v9-260625-amd64"
  logging:
    channel: "stable-6.6"
  loki:
    channel: "stable-6.6"
  acm:
    version: "2.16"
```

Components can be enabled or disabled in `config/defaults.yaml` or
per-cluster overrides. Disabled components are reported as
`NOT_APPLICABLE` in readiness checks:

```yaml
components:
  mas_edge:
    enabled: false
```

---

## 7. Populate the Cluster Inventory

All per-cluster data lives in `secrets/cluster-credentials.yml` under
the `cluster_credentials:` key. This Ansible Vault encrypted file is the
single source of truth for cluster identity and credentials (AWS keys,
account IDs, purpose, seat_number, enabled, api_url, admin_password).

Each entry key matches the generated cluster name pattern:
`{cluster_prefix}-{category}-{index}` (e.g., `lab-seat-01`).

Edit `secrets/cluster-credentials.yml` to register each cluster:

```yaml
cluster_credentials:
  lab-seat-01:
    aws_access_key_id: "<YOUR_AWS_ACCESS_KEY_ID>"
    aws_secret_access_key: "<YOUR_AWS_SECRET_ACCESS_KEY>"
    aws_region: us-east-2
    enabled: true
    purpose: attendee
    seat_number: 1
    api_url: "https://api.lab-seat-01.example.com:6443"
    admin_password: "<YOUR_ADMIN_PASSWORD>"

  lab-facilitator-1:
    aws_access_key_id: "<YOUR_AWS_ACCESS_KEY_ID>"
    aws_secret_access_key: "<YOUR_AWS_SECRET_ACCESS_KEY>"
    aws_region: us-east-2
    enabled: true
    purpose: facilitator
    api_url: "https://api.lab-facilitator-1.example.com:6443"
    admin_password: "<YOUR_ADMIN_PASSWORD>"

  lab-spare-01:
    aws_access_key_id: "<YOUR_AWS_ACCESS_KEY_ID>"
    aws_secret_access_key: "<YOUR_AWS_SECRET_ACCESS_KEY>"
    aws_region: us-east-2
    enabled: true
    purpose: spare
    api_url: "https://api.lab-spare-01.example.com:6443"
    admin_password: "<YOUR_ADMIN_PASSWORD>"
```

Event-level defaults (admin_username, auth_method,
student_credential_profile) are defined in `config/defaults.yaml` and
do not need to be repeated per cluster.

---

## 8. Validate Configuration

Run validation before modifying any cluster. Validation checks for
duplicate IDs, missing secret references, count mismatches, invalid URLs,
and security violations.

```bash
mas-world --env development config validate
```

Expected output on success:

```text
Configuration validation PASSED
  Event:       mas-world-2026
  Environment: development
  Clusters:    2 (1 attendee, 0 spare, 1 facilitator)
  Components:  mas, logging, loki, acm, showroom (5 enabled)
  Secrets:     env provider
  Warnings:    0
  Errors:      0
```

To view the fully merged effective configuration with secrets redacted:

```bash
mas-world --env development config render
```

To compare two environments:

```bash
mas-world config diff --from development --to event
```

---

## 9. Prepare a Single Cluster

Start with a single reference cluster before scaling to the full fleet.
This is the recommended workflow for first-time setup and for validating
changes to roles or configuration.

```bash
mas-world --env development cluster prepare --cluster seat-01
```

This runs the `prepare-cluster.yml` playbook, which executes the
following roles in order:

| Order | Role | Purpose |
|---|---|---|
| 1 | `config_validation` | Validate merged configuration |
| 2 | `cluster_preflight` | Verify OpenShift version, capacity, connectivity |
| 3 | `event_metadata` | Apply event labels and namespace markers |
| 4 | `acm_registration` | Register cluster with ACM hub |
| 5 | `mas_prerequisites` | Install IBM Certificate Manager, MongoDB, SLS |
| 6 | `mas_core` | Install MAS Core operator and Suite CR |
| 7 | `maximo_manage` | Install and activate Maximo Manage |
| 8 | `logging_operator` | Install Red Hat OpenShift Logging Operator |
| 9 | `loki_stack` | Deploy LokiStack with S3 object storage |
| 10 | `log_forwarding` | Configure ClusterLogForwarder |
| 11 | `identity_demo` | Configure Keycloak and identity examples |
| 12 | `mas_edge` | Install MAS Edge (if enabled) |
| 13 | `student_accounts` | Create student user and RBAC |
| 14 | `sample_workloads` | Stage exercise data and sample applications |
| 15 | `showroom` | Deploy Showroom with per-seat parameters |
| 16 | `event_readiness` | Run all readiness checks |
| 17 | `environment_report` | Generate cluster readiness report |

To validate a prepared cluster without making changes:

```bash
mas-world --env development cluster validate --cluster seat-01
```

To repair a cluster that failed a readiness check:

```bash
mas-world --env development cluster repair --cluster seat-01
```

---

## 10. Prepare the Full Fleet

Once the reference cluster is validated, prepare the full fleet. The
fleet command processes clusters in parallel up to the configured
concurrency limit.

```bash
mas-world --env event fleet prepare --max-concurrent 5
```

The `--max-concurrent` flag overrides the value in the environment
configuration. Conservative concurrency is recommended to avoid
saturating AWS APIs, IBM registries, and the ACM hub.

| Environment | Default concurrency | Timeout per cluster |
|---|---|---|
| development | 1 | 240 minutes |
| rehearsal | 3 | 240 minutes |
| event | 5 | 240 minutes |

Each cluster is processed independently. A failure on one cluster does
not block other clusters. Failed clusters are retried up to the
configured `retry_count` (default: 3) with exponential backoff.

Preparation produces per-cluster log files and a summary report:

```text
Fleet preparation complete.
  Total:     56 clusters
  Ready:     50
  Spare:      5
  Failed:     1 (seat-37 — MAS prerequisites timeout)
  Duration:  3h 42m
```

---

## 11. Validate the Fleet

Run fleet-wide validation to confirm all assigned clusters meet
readiness requirements:

```bash
mas-world --env event fleet validate
```

Each cluster is checked against all enabled readiness gates:

```text
Fleet validation complete.
  READY:           50 clusters
  WARNING:          2 clusters (seat-12, seat-33 — elevated pod restart count)
  FAILED:           1 cluster  (seat-37 — LokiStack not ready)
  NOT_APPLICABLE:   0 clusters
  Spares available: 5
```

To generate a detailed fleet status report:

```bash
mas-world --env event report fleet-status
```

---

## 12. Post-Preparation Operations

### 12.1 Create Student Accounts

```bash
mas-world --env event student create
```

### 12.2 Validate Student Access

```bash
mas-world --env event student validate
```

### 12.3 Rotate Student Credentials

```bash
mas-world --env event student rotate
```

### 12.4 Assign Seats

```bash
mas-world --env event seat assign --seat 1 --cluster seat-01
```

### 12.5 Replace a Failed Seat with a Spare

```bash
mas-world --env event seat replace --seat 37 --cluster spare-01
```

### 12.6 Export the Seat Map

```bash
mas-world --env event seat export-map --format json
mas-world --env event seat export-map --format csv
```

### 12.7 Generate Attendee Access Cards

```bash
mas-world --env event student export-cards --output-dir ./access-cards
```

### 12.8 Reset an Exercise

```bash
mas-world --env event exercise reset --cluster seat-01 --module observability
```

---

## 13. Common Issues

| Symptom | Likely cause | Resolution |
|---|---|---|
| `mas-world: command not found` | CLI not installed or venv not active | Run `source .venv/bin/activate && pip install -e "."` |
| `Configuration validation FAILED: missing secret ref` | Secret not populated in provider | Populate the referenced secret (see section 5) |
| `Cluster preflight FAILED: API unreachable` | Incorrect API URL or expired credentials | Verify `api_url` in `secrets/cluster-credentials.yml` and refresh the admin credentials |
| `Cluster preflight FAILED: insufficient capacity` | Worker nodes below minimum requirements | Add worker nodes or reduce component enablement |
| `MAS prerequisites timeout` | IBM registry pull slow or unreachable | Verify `pull_secret_ref` and IBM registry connectivity; increase timeout |
| `LokiStack not ready` | S3 bucket missing or IAM permissions insufficient | Verify AWS credentials and bucket existence; check `aws.yaml` region |
| `Student login failed` | HTPasswd identity provider not synced | Run `mas-world student create` then `mas-world student validate` |
| `ansible-galaxy: ibm.mas_devops not found` | Collection not installed | Run `ansible-galaxy collection install ibm.mas_devops:==37.10.0` |
| `Permission denied` on kubeconfig temp file | Concurrent operations sharing temp path | Ensure each cluster operation uses an isolated temp directory (default behavior) |
| `Fleet preparation stalled` | Concurrency too high for API rate limits | Reduce `--max-concurrent` and retry |

---

## 14. Next Steps

| Document | Path | Purpose |
|---|---|---|
| Developer Guide | `docs/developer-guide.md` | Contributing, testing, CI/CD |
| Operator Guide | `docs/operator-guide.md` | Day-of-event operations, runbooks |
| Configuration Model | `docs/configuration-model.md` | Full configuration reference |
| Credential Lifecycle | `docs/credential-lifecycle.md` | Secret rotation and revocation |
| Compatibility Matrix | `docs/compatibility-matrix.md` | Pinned versions and support ranges |
| Architecture | `docs/architecture.md` | System design and topology diagrams |
| Troubleshooting Guide | `docs/troubleshooting-guide.md` | Extended diagnostics and recovery |
