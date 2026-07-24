# Configuration Model — MAS World 2026

**Status**: DRAFT — Phase 0
**Date**: 2026-07-19

---

## 1. Configuration Precedence

```text
defaults.yaml                              ← Base defaults for all environments
   ↓
environments/<env>.yaml                    ← Environment-specific (dev / rehearsal / event)
   ↓
event.yaml                                 ← Event-specific overrides
   ↓
secrets/cluster-credentials.yml (per-cluster)  ← Cluster identity and credentials
   ↓
Command-line arguments                     ← Runtime overrides
```

Later layers override earlier layers. The merge is deep — nested keys are
merged, not replaced, unless the value is a scalar or list.

`render-effective-config` displays the fully merged configuration with
secrets redacted.

---

## 2. Configuration Files

### 2.1 `config/defaults.yaml`

Base defaults that apply to all environments unless overridden.

```yaml
event:
  id: mas-world-2026
  name: "MAS World 2026"
  date: "2026-08-17"
  timezone: America/Chicago

fleet:
  attendee_cluster_count: 1
  spare_cluster_count: 0
  facilitator_cluster_count: 1
  require_exact_cluster_counts: false
  preparation:
    max_concurrent_clusters: 1
    per_cluster_timeout_minutes: 240
    retry_count: 3
    retry_backoff_base_seconds: 30
  assignment:
    first_seat_number: 1
    seat_number_padding: 2
    automatically_assign_spares: false

components:
  mas:
    enabled: true
    # version: set in compatibility matrix
    install_core: true
    install_manage: true
  logging:
    enabled: true
    collect_application: true
    collect_infrastructure: true
    collect_audit: true
  loki:
    enabled: true
    object_storage_mode: bucket-per-cluster
  keycloak:
    enabled: true
    deployment_mode: per-cluster
  mas_edge:
    enabled: false
  showroom:
    enabled: true
  acm_registration:
    enabled: false

secrets:
  provider: env
  config: {}

student_credentials:
  allow_shared_password: false
  default_profile: attendee-default

student_credential_profiles:
  attendee-default:
    username_template: "user{{ seat_number | pad(2) }}"
    display_name_template: "MAS World Attendee {{ seat_number }}"
    authentication_provider: htpasswd
    password:
      mode: generated
      length: 18
      secret_ref_template: "secret://mas-world/students/seat-{{ seat_number | pad(2) }}"
      rotate_before_event: true
      expire_after_event: true
    access:
      cluster_role: basic-user
      additional_cluster_roles: []
      namespaces:
        - name_template: "student-{{ seat_number | pad(2) }}"
          role: admin
    restrictions:
      allow_cluster_admin: false
      allow_acm_access: false
      allow_other_student_namespaces: false
      allow_protected_secret_read: false

  facilitator:
    username_template: "facilitator{{ index }}"
    authentication_provider: htpasswd
    password:
      mode: generated
      length: 24
      secret_ref_template: "secret://mas-world/facilitators/{{ username }}"
    access:
      cluster_roles:
        - cluster-admin

logging:
  log_level: info
  structured: true
  per_cluster_log_dir: logs/clusters
  redact_secrets: true
```

### 2.2 `config/event.yaml`

Event-specific configuration.

```yaml
event:
  id: mas-world-2026
  name: "MAS World 2026"
  date: "2026-08-17"
  timezone: America/Chicago

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

### 2.3 `secrets/cluster-credentials.yml`

Per-cluster inventory and credentials. This is the single source of truth
for all per-cluster identity and credentials (AWS keys, account IDs,
purpose, seat_number, enabled, api_url, admin_password). The file is
encrypted with Ansible Vault.

The top-level key is `cluster_credentials`, a dictionary keyed by cluster
name matching the pattern `{cluster_prefix}-{category}-{index}`. Phase 2
fleet playbooks use the `to_cluster_list` filter to convert this
dictionary into an iterable list.

```yaml
cluster_credentials:
  lab-seat-01:
    aws_access_key_id: "AKIA..."
    aws_secret_access_key: "wJalr..."
    aws_region: us-east-2
    enabled: true
    purpose: attendee
    seat_number: 1
    api_url: "https://api.lab-seat-01.example.com:6443"
    admin_password: "REDACTED"

  # Additional clusters follow the same structure
```

Event-level defaults (admin_username, auth_method,
student_credential_profile) stay in `config/defaults.yaml`.

### 2.4 `config/credentials.yaml`

Credential references only — no actual secrets.

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

### 2.5 `config/components.yaml`

Component versions and configuration. Versions are populated from the
compatibility matrix.

```yaml
components:
  openshift:
    # version: target major.minor (latest stable patch resolved automatically)
    required_features: []

  mas:
    # version: set from compatibility matrix
    # channel: set from compatibility matrix
    catalog_source: ibm-operator-catalog
    install_core: true
    install_manage: true

  logging:
    # operator_version: set from compatibility matrix
    # channel: set from compatibility matrix
    collector: vector

  loki:
    # operator_version: set from compatibility matrix
    # channel: set from compatibility matrix
    size: 1x.extra-small
    storage:
      backend: s3
      bucket_prefix: "mas-world-2026"
      retention_days: 7

  acm:
    # version: set from compatibility matrix
    # hub_cluster_id: set in components.acm_registration.hub_cluster_id, referencing a cluster in inventory with purpose: hub

  keycloak:
    # version: set from compatibility matrix
    realm_name: mas-world
    deployment_mode: per-cluster
```

### 2.6 `config/aws.yaml`

AWS-specific configuration.

```yaml
aws:
  default_region: us-east-2
  s3:
    bucket_naming: "mas-world-2026-{cluster_id}-loki-{suffix}"
    encryption: AES256
    public_access_block: true
    lifecycle_rules:
      - id: expire-after-event
        expiration_days: 30
        enabled: true
    versioning: false
  iam:
    policy_prefix: "mas-world-2026"
    path: "/mas-world-2026/"
```

### 2.7 `config/showroom.yaml`

Showroom configuration.

```yaml
showroom:
  template: nookbag
  theme: summit
  title: "MAS World 2026 — Maximo on OpenShift Workshop"
  tabs:
    - type: instructions
      title: Workshop
    - type: terminal
      title: Terminal
    - type: console
      title: OpenShift Console
      url_attribute: openshift_console_url
    - type: url
      title: Maximo
      url_attribute: mas_url
    - type: url
      title: Git Repository
      url_attribute: public_git_url
    - type: url
      title: Logging
      url_attribute: logging_url
  attributes:
    # These are populated per-cluster by automation
    openshift_console_url: "PLACEHOLDER"
    mas_url: "PLACEHOLDER"
    logging_url: "PLACEHOLDER"
    public_git_url: "PLACEHOLDER"
    seat_number: "PLACEHOLDER"
    student_username: "PLACEHOLDER"
    student_password: "PLACEHOLDER"
```

### 2.8 `config/environments/development.yaml`

```yaml
fleet:
  attendee_cluster_count: 1
  spare_cluster_count: 0
  facilitator_cluster_count: 1
  require_exact_cluster_counts: false
  preparation:
    max_concurrent_clusters: 1

student_credentials:
  allow_shared_password: true

secrets:
  provider: env

logging:
  log_level: debug
```

### 2.9 `config/environments/rehearsal.yaml`

```yaml
fleet:
  attendee_cluster_count: 5
  spare_cluster_count: 1
  facilitator_cluster_count: 1
  require_exact_cluster_counts: true
  preparation:
    max_concurrent_clusters: 3

secrets:
  provider: aws-sm

logging:
  log_level: info
```

### 2.10 `config/environments/event.yaml`

```yaml
fleet:
  attendee_cluster_count: 50
  spare_cluster_count: 5
  facilitator_cluster_count: 1
  require_exact_cluster_counts: true
  preparation:
    max_concurrent_clusters: 5

student_credentials:
  allow_shared_password: false

secrets:
  provider: aws-sm

logging:
  log_level: info
  structured: true
```

---

## 3. Configuration Validation

Validation runs before any cluster modification. Checks include:

| Check | Severity |
|-------|----------|
| Duplicate cluster IDs | ERROR |
| Duplicate seat numbers | ERROR |
| Missing admin credential reference | ERROR |
| Missing student credential profile | ERROR |
| More assignments than attendee clusters | ERROR |
| Cluster counts don't match inventory | ERROR (if require_exact) / WARN |
| Cluster assigned to multiple seats | ERROR |
| Seat assigned to multiple clusters | ERROR |
| Reused usernames across clusters | ERROR |
| Secret values embedded in config | ERROR |
| Invalid endpoint URLs | ERROR |
| Unsupported auth method | ERROR |
| Invalid component combinations | ERROR |
| Attendee with cluster-admin | ERROR |
| Missing spare capacity (event env) | WARN |
| Missing AWS account/region | ERROR (if AWS components enabled) |
| Missing database configuration | ERROR (if MAS enabled) |
| Missing object storage configuration | ERROR (if Loki enabled) |
| Invalid Showroom parameters | ERROR (if Showroom enabled) |
| Shared passwords in event environment | ERROR |

---

## 4. CLI Configuration Commands

```bash
# Validate all configuration
mas-world validate-config --env event

# Render effective merged configuration (secrets redacted)
mas-world render-effective-config --env event

# Show differences between environments
mas-world show-config-differences --from development --to event

# Validate a single cluster's configuration
mas-world validate-config --env event --cluster seat-01
```
