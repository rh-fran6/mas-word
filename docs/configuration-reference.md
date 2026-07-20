# Configuration Reference -- MAS World 2026

**Status**: DRAFT -- Phase 1
**Date**: 2026-07-19

---

## 1. Configuration Precedence

Configuration is loaded and merged in the following order. Later layers
override earlier layers.

```text
config/defaults.yaml                 Base defaults for all environments
       |
config/environments/<env>.yaml       Environment-specific overrides
       |
config/event.yaml                    Event-specific overrides
       |
config/clusters.yaml (per-cluster)   Cluster-specific overrides
       |
Command-line arguments               Runtime overrides
```

**Merge behavior**: deep merge. Nested mapping keys are merged recursively.
Scalar values and lists are replaced wholesale by the later layer.

The effective configuration after all layers are merged can be displayed with:

```bash
mas-world --env event config render
```

Secrets are redacted in all rendered output by default.

---

## 2. Configuration Files

### 2.1 `config/defaults.yaml`

**Purpose**: Base defaults that apply to all environments unless overridden by
a later layer.

**Location**: `mas-world-2026-automation/config/defaults.yaml`

#### `event` -- Event identity

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `event.id` | `str` | `"mas-world-2026"` | Unique event identifier. Used in labels, secret paths, and bucket names. |
| `event.name` | `str` | `"MAS World 2026"` | Human-readable event name. Appears in Showroom, reports, and access cards. |
| `event.date` | `str` (ISO 8601) | `"2026-08-17"` | Event date. Used for credential expiry and lifecycle scheduling. |
| `event.timezone` | `str` (IANA) | `"America/Chicago"` | Timezone for all event-relative scheduling. |

#### `fleet` -- Fleet sizing and orchestration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `fleet.attendee_cluster_count` | `int` | `1` | Expected number of attendee clusters. Validated against inventory. |
| `fleet.spare_cluster_count` | `int` | `0` | Expected number of spare clusters for failover. |
| `fleet.facilitator_cluster_count` | `int` | `1` | Expected number of facilitator clusters. |
| `fleet.require_exact_cluster_counts` | `bool` | `false` | When `true`, validation fails if inventory counts do not match exactly. |

#### `fleet.preparation` -- Parallel execution settings

| Key | Type | Default | Constraints | Description |
|-----|------|---------|-------------|-------------|
| `fleet.preparation.max_concurrent_clusters` | `int` | `1` | 1--50 | Maximum number of clusters prepared in parallel. |
| `fleet.preparation.per_cluster_timeout_minutes` | `int` | `240` | >= 30 | Timeout for a single cluster preparation run. |
| `fleet.preparation.retry_count` | `int` | `3` | >= 0 | Number of retries on transient failure. |
| `fleet.preparation.retry_backoff_base_seconds` | `int` | `30` | >= 1 | Base interval for exponential backoff between retries. |

#### `fleet.assignment` -- Seat numbering

| Key | Type | Default | Constraints | Description |
|-----|------|---------|-------------|-------------|
| `fleet.assignment.first_seat_number` | `int` | `1` | >= 1 | First seat number in generated assignments. |
| `fleet.assignment.seat_number_padding` | `int` | `2` | 1--4 | Zero-padding width for seat numbers in usernames and paths (e.g., `2` produces `01`, `02`). |
| `fleet.assignment.automatically_assign_spares` | `bool` | `false` | -- | When `true`, spares are automatically assigned to replace failed clusters. |

#### `components` -- Component enablement

Each component block supports at minimum an `enabled` boolean. Disabling a
component causes readiness checks to report `NOT_APPLICABLE` instead of
`FAIL`.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `components.mas.enabled` | `bool` | `true` | Enable MAS Core and Manage installation. |
| `components.mas.install_core` | `bool` | `true` | Install MAS Core operator and Suite CR. |
| `components.mas.install_manage` | `bool` | `true` | Install Maximo Manage application. |
| `components.logging.enabled` | `bool` | `true` | Enable OpenShift Logging Operator. |
| `components.logging.collect_application` | `bool` | `true` | Collect application-container logs. |
| `components.logging.collect_infrastructure` | `bool` | `true` | Collect infrastructure-component logs. |
| `components.logging.collect_audit` | `bool` | `true` | Collect Kubernetes API audit logs. |
| `components.loki.enabled` | `bool` | `true` | Enable Loki Operator and LokiStack. |
| `components.loki.object_storage_mode` | `str` | `"bucket-per-cluster"` | S3 isolation model. One of `bucket-per-cluster` or `shared-bucket`. |
| `components.keycloak.enabled` | `bool` | `true` | Enable Keycloak identity provider. |
| `components.keycloak.deployment_mode` | `str` | `"per-cluster"` | One of `per-cluster`, `shared`, or `external`. |
| `components.mas_edge.enabled` | `bool` | `false` | Enable MAS Edge. Disabled by default. |
| `components.showroom.enabled` | `bool` | `true` | Enable Showroom deployment. |
| `components.acm_registration.enabled` | `bool` | `true` | Enable ACM hub registration and labeling. |

#### `secrets` -- Secret provider

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `secrets.provider` | `str` | `"env"` | Secret backend. One of `env`, `k8s`, `aws-sm`, or `vault`. |
| `secrets.config` | `dict` | `{}` | Provider-specific settings (e.g., `aws_region` for `aws-sm`). |

#### `student_credentials` -- Credential policy

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `student_credentials.allow_shared_password` | `bool` | `false` | Allow a single shared password for all attendees. Emits a security warning when `true`. Blocked in the `event` environment. |
| `student_credentials.default_profile` | `str` | `"attendee-default"` | Default credential profile name applied to clusters that do not specify one. |

#### `student_credential_profiles` -- Reusable credential profiles

Each profile is a named mapping. Two profiles ship in defaults:

**`attendee-default`**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `username_template` | `str` | `"user{{ seat_number \| pad(2) }}"` | Jinja-style template for the OpenShift username. |
| `display_name_template` | `str` | `"MAS World Attendee {{ seat_number }}"` | Display name shown in the console. |
| `authentication_provider` | `str` | `"htpasswd"` | OAuth identity provider type. |
| `password.mode` | `str` | `"generated"` | One of `generated`, `secret-ref`, `external-idp`, `disabled`, `deterministic`. |
| `password.length` | `int` | `18` | Generated password length (12--64). |
| `password.secret_ref_template` | `str` | `"secret://mas-world/students/seat-{{ seat_number \| pad(2) }}"` | Secret path template for storing or retrieving the password. |
| `password.rotate_before_event` | `bool` | `true` | Rotate passwords during pre-event credential rotation. |
| `password.expire_after_event` | `bool` | `true` | Mark passwords for revocation after the event date. |
| `access.cluster_role` | `str` | `"basic-user"` | ClusterRole bound to the student. |
| `access.additional_cluster_roles` | `list[str]` | `[]` | Additional ClusterRoles. |
| `access.namespaces` | `list` | `[{name_template: "student-{{ seat_number \| pad(2) }}", role: "admin"}]` | Namespaces created for the student with the specified Role or ClusterRole. |
| `restrictions.allow_cluster_admin` | `bool` | `false` | Must be `false` for attendee profiles. Validated by Pydantic model. |
| `restrictions.allow_acm_access` | `bool` | `false` | Allow ACM hub administrative access. |
| `restrictions.allow_other_student_namespaces` | `bool` | `false` | Allow access to other students' namespaces. |
| `restrictions.allow_protected_secret_read` | `bool` | `false` | Allow reading protected Secrets (admin kubeconfigs, entitlement keys). |

**`facilitator`**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `username_template` | `str` | `"facilitator{{ index }}"` | Username template using a sequential index. |
| `password.mode` | `str` | `"generated"` | Generated with 24-character length. |
| `password.length` | `int` | `24` | Longer password for facilitator accounts. |
| `access.cluster_role` | `str` | `"cluster-admin"` | Full administrative access. |
| `restrictions.allow_cluster_admin` | `bool` | `true` | Facilitators receive cluster-admin. |

#### `logging_config` -- CLI and automation logging

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `logging_config.log_level` | `str` | `"info"` | Log level: `debug`, `info`, `warning`, or `error`. |
| `logging_config.structured` | `bool` | `true` | Emit structured JSON log lines. |
| `logging_config.per_cluster_log_dir` | `str` | `"logs/clusters"` | Directory for per-cluster log files. |
| `logging_config.redact_secrets` | `bool` | `true` | Redact values matching known secret patterns in all log output. |

---

### 2.2 `config/event.yaml`

**Purpose**: Event-specific overrides. Typically contains event identity and
session scheduling that does not change between environments.

**Location**: `mas-world-2026-automation/config/event.yaml`

| Key | Type | Description |
|-----|------|-------------|
| `event.id` | `str` | Event identifier (overrides default if set). |
| `event.name` | `str` | Event display name. |
| `event.date` | `str` | Event date (ISO 8601). |
| `event.timezone` | `str` | IANA timezone. |

This file may also contain:

| Key | Type | Description |
|-----|------|-------------|
| `delivery_team` | `list[dict]` | Team members. Each entry: `name`, `organization`, `role`. |
| `session.total_duration_minutes` | `int` | Total session length. |
| `session.segments` | `list[dict]` | Ordered list of session segments. Each entry: `id`, `title`, `duration_minutes`, `type`. |

**Segment types**: `attendee-exercise`, `presenter-demo`, `mixed`.

Example:

```yaml
delivery_team:
  - name: Ernie Steagall
    organization: ONEOK
    role: presenter
  - name: Francis Anyaegbu
    organization: Red Hat
    role: lab-owner
  - name: Myles Vivian
    organization: Cohesive
    role: observability-lead

session:
  total_duration_minutes: 120
  segments:
    - id: navigation-search
      title: "Navigation and Search"
      duration_minutes: 10
      type: attendee-exercise
    - id: acm-fleet
      title: "Advanced Cluster Management"
      duration_minutes: 10
      type: presenter-demo
    - id: updates
      title: "Updates"
      duration_minutes: 20
      type: attendee-exercise
    - id: observability
      title: "Observability and Logging"
      duration_minutes: 40
      type: mixed
    - id: identity
      title: "Identity Provider Integration"
      duration_minutes: 40
      type: mixed
```

---

### 2.3 `config/clusters.yaml`

**Purpose**: Per-cluster inventory. Every cluster that automation can target
must have an entry here. Clusters with `enabled: false` are skipped by all
fleet operations.

**Location**: `mas-world-2026-automation/config/clusters.yaml`

The top-level key is `clusters`, containing a list of cluster definitions.

| Key | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `id` | `str` | yes | -- | Unique cluster identifier (e.g., `seat-01`, `spare-01`, `facilitator-01`). |
| `enabled` | `bool` | no | `true` | Whether the cluster participates in fleet operations. |
| `purpose` | `str` | no | `"attendee"` | One of `attendee`, `spare`, or `facilitator`. |
| `seat_number` | `int` or `null` | no | `null` | Pre-assigned seat number. `null` for spares and facilitators. |
| `connection.api_url` | `str` | yes | -- | OpenShift API URL (e.g., `https://api.cluster.example.com:6443`). |
| `connection.admin_auth_method` | `str` | no | `"kubeconfig"` | One of `kubeconfig`, `token`, `username-password`, or `external`. |
| `connection.admin_secret_ref` | `str` | yes | -- | Secret reference for administrative credentials. Must match `secret://...` pattern or `PLACEHOLDER`. |
| `platform.provider` | `str` | no | `"aws"` | Cloud provider. |
| `platform.aws_account_id` | `str` | no | `"PLACEHOLDER"` | AWS account ID. |
| `platform.aws_region` | `str` | no | `"us-east-2"` | AWS region. |
| `endpoints.console_url` | `str` or `null` | no | `null` | OpenShift console URL. Populated by automation after preparation. |
| `endpoints.mas_url` | `str` or `null` | no | `null` | Maximo Application Suite URL. |
| `endpoints.showroom_url` | `str` or `null` | no | `null` | Showroom URL. |
| `endpoints.logging_url` | `str` or `null` | no | `null` | Logging dashboard URL. |
| `credentials.student_credential_profile` | `str` | no | `"attendee-default"` | Name of the credential profile to use for student accounts on this cluster. |
| `metadata` | `dict` | no | `{event: "mas-world-2026", environment: "workshop"}` | Arbitrary metadata applied as cluster labels. |
| `component_overrides` | `dict` | no | `{}` | Per-cluster component configuration overrides (see Section 3). |

Example entry:

```yaml
clusters:
  - id: seat-01
    enabled: true
    purpose: attendee
    seat_number: 1
    connection:
      api_url: "https://api.seat-01.example.com:6443"
      admin_auth_method: kubeconfig
      admin_secret_ref: "secret://mas-world/clusters/seat-01/admin-kubeconfig"
    platform:
      provider: aws
      aws_account_id: "111111111111"
      aws_region: us-east-2
    endpoints:
      console_url: null
      mas_url: null
      showroom_url: null
      logging_url: null
    credentials:
      student_credential_profile: attendee-default
    metadata:
      event: mas-world-2026
      environment: workshop
```

For large fleets, use the inventory generation command:

```bash
mas-world config generate-inventory --count 50 --spare 5
```

---

### 2.4 `config/credentials.yaml`

**Purpose**: Central registry of secret references for external services.
Contains only `secret://` references -- never actual secret values.

**Location**: `mas-world-2026-automation/config/credentials.yaml`

| Key | Type | Description |
|-----|------|-------------|
| `ibm.entitlement_key_ref` | `str` | Secret reference for the IBM container entitlement key. |
| `ibm.license_ref` | `str` | Secret reference for the MAS license file. |
| `aws.default_region` | `str` | AWS region for credential retrieval. |
| `aws.credentials_ref` | `str` | Secret reference for AWS access credentials. |
| `acm.hub_kubeconfig_ref` | `str` | Secret reference for the ACM hub cluster kubeconfig. |
| `container_registry.pull_secret_ref` | `str` | Secret reference for the container registry pull secret. |

Example:

```yaml
ibm:
  entitlement_key_ref: "secret://mas-world/ibm/entitlement-key"
  license_ref: "secret://mas-world/ibm/license"

aws:
  default_region: us-east-2
  credentials_ref: "secret://mas-world/aws/credentials"

acm:
  hub_kubeconfig_ref: "secret://mas-world/acm/hub-kubeconfig"

container_registry:
  pull_secret_ref: "secret://mas-world/registry/pull-secret"
```

---

### 2.5 `config/components.yaml`

**Purpose**: Component version pins and channel selections. Values are
populated from `docs/compatibility-matrix.md` and must be updated together.

**Location**: `mas-world-2026-automation/config/components.yaml`

| Key | Type | Description |
|-----|------|-------------|
| `components.openshift.minimum_version` | `str` | Minimum supported OpenShift version (e.g., `"4.18"`). |
| `components.openshift.maximum_version` | `str` | Maximum supported OpenShift version (e.g., `"4.22"`). |
| `components.mas.version` | `str` | Pinned MAS version (e.g., `"9.1.x"`). |
| `components.mas.channel` | `str` | OLM subscription channel (e.g., `"9.1.x"`). |
| `components.mas.catalog_tag` | `str` | IBM operator catalog image tag. |
| `components.mas.catalog_image` | `str` | Full catalog image reference. |
| `components.logging.channel` | `str` | Logging operator OLM channel (e.g., `"stable-6.6"`). |
| `components.loki.channel` | `str` | Loki operator OLM channel (e.g., `"stable-6.6"`). |
| `components.loki.api_version` | `str` | LokiStack API version (e.g., `"loki.grafana.com/v1"`). |
| `components.acm.version` | `str` | ACM version (e.g., `"2.16"`). |
| `components.gitops.channel` | `str` | OpenShift GitOps OLM channel. |
| `components.mongodb.version` | `str` | MongoDB version for MAS. |
| `components.sls.channel` | `str` | Suite License Service OLM channel. |
| `components.db2.version` | `str` | Db2 version for Maximo Manage. |

Example:

```yaml
components:
  openshift:
    minimum_version: "4.18"
    maximum_version: "4.22"

  mas:
    version: "9.1.x"
    channel: "9.1.x"
    catalog_tag: "v9-260625-amd64"
    catalog_image: "icr.io/cpopen/ibm-maximo-operator-catalog:v9-260625-amd64"

  logging:
    channel: "stable-6.6"

  loki:
    channel: "stable-6.6"
    api_version: "loki.grafana.com/v1"

  acm:
    version: "2.16"

  gitops:
    channel: "gitops-1.21"

  mongodb:
    version: "7.0"

  sls:
    channel: "3.x"

  db2:
    version: "11.5"
```

---

### 2.6 `config/aws.yaml`

**Purpose**: AWS-specific configuration for S3 object storage and IAM
resources used by the Loki logging backend.

**Location**: `mas-world-2026-automation/config/aws.yaml`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `aws.default_region` | `str` | `"us-east-2"` | AWS region for S3 buckets and IAM resources. |
| `aws.s3_bucket_prefix` | `str` | `"mas-world-2026"` | Prefix for generated S3 bucket names. |
| `aws.s3_encryption` | `str` | `"AES256"` | Server-side encryption algorithm. |
| `aws.s3_lifecycle_expiration_days` | `int` | `30` | Days until objects expire (>= 1). |

The full bucket naming template uses the pattern:

```text
{s3_bucket_prefix}-{cluster_id}-loki-{unique_suffix}
```

Example for cluster `seat-01`:

```text
mas-world-2026-seat-01-loki-a1b2c3
```

Additional S3 settings applied by automation (not user-configurable):

- Public access block: always enabled
- Versioning: disabled for workshop use
- Lifecycle rules: one rule per bucket, expiring objects after the configured
  number of days

---

### 2.7 `config/showroom.yaml`

**Purpose**: Showroom deployment configuration for the attendee workshop UI.

**Location**: `mas-world-2026-automation/config/showroom.yaml`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `showroom.template` | `str` | `"nookbag"` | Showroom template name. |
| `showroom.theme_version` | `str` | `"v2.0.3"` | Pinned Showroom theme version. |
| `showroom.title` | `str` | `"MAS World 2026 -- Maximo on OpenShift Workshop"` | Workshop title displayed in the Showroom header. |
| `showroom.content_repo` | `str` | -- | Git repository URL for Showroom content. |
| `showroom.content_ref` | `str` | `"main"` | Git branch or tag for content. Pin to a tag for the event release. |

Tab configuration and per-cluster attributes are managed in
`config/defaults.yaml` under the `showroom` key within Showroom runtime
parameters. The per-cluster `attributes` block is populated by automation
during cluster preparation and injected into the Showroom deployment:

```yaml
# Conceptual attributes populated per-cluster at deployment time
showroom_attributes:
  openshift_console_url: "https://console-openshift-console.apps.seat-01.example.com"
  mas_url: "https://maxinst.apps.seat-01.example.com"
  logging_url: "https://logging.apps.seat-01.example.com"
  seat_number: "01"
  student_username: "user01"
  student_password: "REDACTED"
```

---

### 2.8 `config/environments/development.yaml`

**Purpose**: Overrides for local development with a minimal single-cluster
setup.

**Location**: `mas-world-2026-automation/config/environments/development.yaml`

Key differences from defaults:

| Key | Value | Rationale |
|-----|-------|-----------|
| `fleet.attendee_cluster_count` | `1` | Single cluster for local testing. |
| `fleet.spare_cluster_count` | `0` | No spares needed. |
| `fleet.require_exact_cluster_counts` | `false` | Lenient validation. |
| `fleet.preparation.max_concurrent_clusters` | `1` | Sequential processing. |
| `student_credentials.allow_shared_password` | `true` | Convenience for development. Emits a security warning. |
| `secrets.provider` | `"env"` | Secrets loaded from environment variables. |
| `logging_config.log_level` | `"debug"` | Verbose output for troubleshooting. |

---

### 2.9 `config/environments/rehearsal.yaml`

**Purpose**: Overrides for a rehearsal run with a small representative fleet.

**Location**: `mas-world-2026-automation/config/environments/rehearsal.yaml`

Key differences from defaults:

| Key | Value | Rationale |
|-----|-------|-----------|
| `fleet.attendee_cluster_count` | `5` | Small representative fleet. |
| `fleet.spare_cluster_count` | `1` | One spare for failover testing. |
| `fleet.require_exact_cluster_counts` | `true` | Strict validation. |
| `fleet.preparation.max_concurrent_clusters` | `3` | Moderate parallelism. |
| `secrets.provider` | `"aws-sm"` | AWS Secrets Manager for realistic credential flow. |
| `secrets.config.aws_region` | `"us-east-2"` | Secrets Manager region. |
| `logging_config.log_level` | `"info"` | Standard verbosity. |

---

### 2.10 `config/environments/event.yaml`

**Purpose**: Production overrides for the live event with the full fleet.

**Location**: `mas-world-2026-automation/config/environments/event.yaml`

Key differences from defaults:

| Key | Value | Rationale |
|-----|-------|-----------|
| `fleet.attendee_cluster_count` | `50` | Full event fleet. |
| `fleet.spare_cluster_count` | `5` | Five spare clusters for failover. |
| `fleet.require_exact_cluster_counts` | `true` | Strict validation -- inventory must match. |
| `fleet.preparation.max_concurrent_clusters` | `5` | Conservative parallelism to avoid API throttling. |
| `student_credentials.allow_shared_password` | `false` | Enforced unique passwords. |
| `secrets.provider` | `"aws-sm"` | AWS Secrets Manager for production credential handling. |
| `secrets.config.aws_region` | `"us-east-2"` | Secrets Manager region. |
| `logging_config.log_level` | `"info"` | Standard verbosity. |
| `logging_config.structured` | `true` | Structured JSON logs for forwarding. |

---

## 3. Cluster-Specific Overrides

Individual clusters can override component configuration through the
`component_overrides` key in their `clusters.yaml` entry:

```yaml
clusters:
  - id: seat-17
    enabled: true
    purpose: attendee
    seat_number: 17
    connection:
      api_url: "https://api.seat-17.example.com:6443"
      admin_auth_method: kubeconfig
      admin_secret_ref: "secret://mas-world/clusters/seat-17/admin-kubeconfig"
    component_overrides:
      mas_edge:
        enabled: true
```

Override rules:

- Overrides apply only to the specified cluster.
- Keys within `component_overrides` map to top-level `components.*` keys.
- The override is deep-merged with the effective component configuration.
- Overrides are validated against the same Pydantic models as the base
  component configuration.
- Readiness checks respect per-cluster overrides (e.g., a cluster with
  `mas_edge.enabled: true` will have MAS Edge readiness checked).

---

## 4. Configuration Validation Rules

Validation runs before any cluster is modified. All checks must pass before
preparation begins.

| Check | Severity | Description |
|-------|----------|-------------|
| Duplicate cluster IDs | ERROR | Every `id` in `clusters.yaml` must be unique. |
| Duplicate seat numbers | ERROR | Seat numbers across all clusters must be unique (ignoring `null`). |
| Missing admin credential reference | ERROR | `connection.admin_secret_ref` must be a valid `secret://` path or `PLACEHOLDER`. |
| Missing student credential profile | ERROR | `credentials.student_credential_profile` must reference a defined profile. |
| More assignments than attendee clusters | ERROR | Active seat assignments cannot exceed enabled attendee clusters. |
| Cluster counts do not match inventory | ERROR / WARN | ERROR when `require_exact_cluster_counts` is `true`; WARN otherwise. |
| Cluster assigned to multiple seats | ERROR | A cluster ID can appear in at most one active assignment. |
| Seat assigned to multiple clusters | ERROR | A seat number can have at most one active assignment. |
| Reused usernames across clusters | ERROR | Generated usernames must be unique across the fleet. |
| Secret values embedded in configuration | ERROR | Raw secrets detected in any YAML file. |
| Invalid endpoint URLs | ERROR | URLs that do not match `https://` pattern. |
| Unsupported authentication method | ERROR | `admin_auth_method` must be one of `kubeconfig`, `token`, `username-password`, `external`. |
| Invalid component combinations | ERROR | Loki enabled without logging, or MAS Manage without MAS Core. |
| Attendee profile with cluster-admin | ERROR | Any non-facilitator profile with `restrictions.allow_cluster_admin: true`. |
| Missing spare capacity (event environment) | WARN | Fewer than expected spare clusters available. |
| Missing AWS account or region | ERROR | Required when AWS-dependent components (Loki S3) are enabled. |
| Missing database configuration | ERROR | Required when MAS is enabled. |
| Missing object storage configuration | ERROR | Required when Loki is enabled. |
| Invalid Showroom parameters | ERROR | Missing or invalid Showroom template, title, or content reference. |
| Shared passwords in event environment | ERROR | `allow_shared_password: true` in the `event` environment. |
| Password length below minimum | ERROR | Generated password length below 12 characters. |

---

## 5. CLI Configuration Commands

### Validate configuration

```bash
mas-world --env event config validate
```

Validate all configuration files for the specified environment. Exits with
code `0` on success, `1` if errors are found.

To validate a single cluster:

```bash
mas-world --env event config validate --cluster seat-01
```

### Render effective configuration

```bash
mas-world --env event config render
```

Display the fully merged configuration with secrets redacted. Useful for
verifying precedence and confirming what values are effective.

Options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--cluster` | `str` | -- | Render the effective configuration for a specific cluster, including its overrides. |
| `--format` | `yaml` or `json` | `yaml` | Output format. |

```bash
# Render as JSON for a specific cluster
mas-world --env rehearsal config render --cluster seat-01 --format json
```

### Show configuration differences

```bash
mas-world config diff --from development --to event
```

Display the differences between two environment configurations. Useful for
reviewing what changes between development and production.

Options:

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--from` | `str` | yes | Source environment name. |
| `--to` | `str` | yes | Target environment name. |
