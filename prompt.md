# Claude Code Master Implementation Prompt

# MAS World 2026 — Configurable Multi-Cluster Maximo Workshop Environment

You are acting as the principal platform architect, senior OpenShift automation engineer, IBM Maximo Application Suite engineer, Red Hat Advanced Cluster Management engineer, security engineer, site reliability engineer, and technical documentation lead for an event-grade hands-on workshop.

Your task is to design and implement the complete post-provisioning environment for **MAS World on August 17, 2026**.

Do not merely create a design proposal or scaffolding. Implement the repositories, automation, configuration schemas, Ansible roles, manifests, policies, Showroom content, validation framework, tests, operational tooling, and documentation required to prepare and operate the environment end to end.

---

# 1. Event context

## Event details

* Event: MAS World
* Date: August 17, 2026
* Event timezone: America/Chicago
* Maximum planned attendance: 50
* Delivery type: conference workshop
* Default environment model: one dedicated OpenShift cluster per attendee
* Clusters are already provisioned before this project begins
* Attendees access their environments through Red Hat Showroom
* Attendees use browser-based terminals, OpenShift consoles, Maximo, and task tabs

The implementation must not hard-code 50 clusters. It must support development, rehearsal, and event fleets of different sizes through configuration only.

## Delivery team

* Ernie Steagall, ONEOK:

  * Primary presenter
  * Shares screen
  * Drives the live demonstrations
* Francis Anyaegbu, Red Hat:

  * Owns the OpenShift lab environment and Showroom content
  * Supports attendees
* Myles Vivian, Cohesive:

  * Owns and supports observability content
  * Supports attendees

## Session pattern

Each section follows this format:

1. A one-to-two-minute introductory slide explaining what is being done and why.
2. Presenter demonstration where appropriate.
3. A bounded attendee exercise.
4. Automated validation.
5. A supported solve or recovery path.

The planned lab segments are:

1. Navigation and Search — 10 minutes
2. Advanced Cluster Management — 10 minutes
3. Updates — 20 minutes
4. Observability and Logging — part of a 40-minute segment
5. Identity Provider Integration — part of a 40-minute segment

---

# 2. Existing infrastructure assumptions

Assume the following may already exist:

* A configurable number of attendee OpenShift clusters
* A configurable number of spare clusters
* One or more facilitator clusters
* One ACM hub cluster
* AWS accounts and networking
* DNS and ingress for each cluster
* Administrative credential references for every cluster
* AWS credentials or workload identity usable by automation
* IBM entitlement and MAS licensing information
* A Git hosting organization
* A container registry
* A CI/CD service

Do not provision OpenShift clusters.

Build all automation so that it can configure any supplied compatible OpenShift cluster.

Do not assume all clusters are identical. Detect and validate their actual state.

---

# 3. Primary outcome

Create an idempotent, secure, observable, restartable automation system that can take a newly provisioned compatible OpenShift cluster and transform it into a fully prepared MAS World attendee environment.

The target lifecycle must be:

```text
Existing OpenShift cluster
        ↓
Configuration validation
        ↓
Compatibility and capacity preflight
        ↓
Administrative credentials retrieved securely
        ↓
Cluster registered with ACM
        ↓
Event labels and ManagedClusterSet assigned
        ↓
Maximo Application Suite prerequisites installed
        ↓
MAS Core and Maximo Manage installed and configured
        ↓
Logging Operator and Loki installed
        ↓
AWS S3 object storage configured
        ↓
ClusterLogForwarder configured
        ↓
Identity components and prepared examples configured
        ↓
MAS Edge configured where required
        ↓
Student accounts and RBAC configured
        ↓
Sample data and exercises staged
        ↓
Showroom installed and parameterized
        ↓
Readiness and end-to-end tests executed
        ↓
Cluster marked READY, WARNING, or FAILED
        ↓
Environment added to seat assignment inventory
```

An environment must never be assigned to an attendee unless all mandatory readiness tests pass.

---

# 4. Mandatory working principles

# Mandatory RHDP Skills Marketplace usage

The RHDP Skills Marketplace skills installed in this Claude Code environment must be used where applicable. Do not merely read their documentation and manually reproduce their expected output.

Before implementation:

1. Detect and list all installed RHDP Skills Marketplace skills.
2. Confirm which versions or source revisions are installed.
3. Record the result in:

   * `docs/rhdp-skills-inventory.md`
4. Identify which skills apply to:

   * Showroom lab creation
   * Showroom verification
   * AgnosticV catalog creation
   * AgnosticV validation
   * AgnosticD workload development
   * Runtime automation
   * Architecture or diagram generation
5. Use the installed skills as the primary workflow wherever they support the required task.
6. Use manual implementation only for capabilities that the installed skills do not provide.
7. Document every material deviation from generated skill output.

## Required skill workflows

At minimum, evaluate and use the following skills if they are installed and applicable:

```text
/showroom:create-lab
/showroom:verify-content
/agnosticv:catalog-builder
/agnosticv:validator
```

Also inspect the installed marketplace for skills related to:

```text
AgnosticD workloads
Showroom scaffolding
Showroom runtime automation
Solve and Validate playbooks
OpenShift lab verification
Architecture diagrams
Catalog questions
Catalog schema validation
End-to-end workshop testing
```

Do not assume these exact names exist. Discover the installed skill names and use the closest supported equivalents.

## Showroom creation

Use the installed Showroom lab-creation skill to create or validate:

* The Showroom project scaffold
* `site.yml`
* `ui-config.yml`
* Navigation
* Module structure
* `Know → Do → Check` content
* Browser terminal integration
* OpenShift console tabs
* Maximo tabs
* Runtime automation directories
* Solve and Validate workflows
* Conclusion page
* Project-local skill rules

The workshop is participant-led and hands-on. Do not use a presenter-only demo skill as the main content-generation workflow.

Use the participant lab skill, conceptually equivalent to:

```text
/showroom:create-lab
```

Presenter-led sections, such as the ACM fleet demonstration, may include presenter guidance inside the broader hands-on lab.

## Showroom verification

Use the installed Showroom verification skill after:

* Initial scaffold generation
* Completion of each module
* Runtime automation implementation
* Final content freeze

Use the workflow conceptually equivalent to:

```text
/showroom:verify-content
```

Treat verification findings as tracked defects.

Record findings and remediation in:

```text
docs/showroom-verification-report.md
```

The final event release must not contain unresolved critical Showroom verification findings.

## AgnosticV catalog creation

Use the installed AgnosticV catalog-building skill to generate or validate the RHDP catalog configuration.

Use the workflow conceptually equivalent to:

```text
/agnosticv:catalog-builder
```

The generated catalog must support:

* Existing or externally provisioned OpenShift clusters
* Configurable attendee cluster count
* Configurable spare and facilitator clusters
* Post-provision AgnosticD workloads
* Showroom deployment
* Per-cluster variables
* Student credentials
* `agnosticd_user_info.data`
* Attendee access information
* Development, rehearsal, and event configurations

Do not assume the catalog builder provisions the OpenShift clusters. The clusters already exist. The catalog and workloads must integrate with the supported RHDP model for existing or pooled clusters.

Where the catalog builder does not natively support the required existing-cluster workflow, document:

1. The unsupported gap
2. The RHDP-supported integration pattern selected
3. The required platform-team work
4. Any external cluster-pool registration process
5. The boundary between AgnosticV and external fleet provisioning

## AgnosticV validation

Run the installed AgnosticV validator against every generated catalog configuration.

Use the workflow conceptually equivalent to:

```text
/agnosticv:validator
```

Validate at least:

```text
development configuration
rehearsal configuration
event configuration
all catalog includes
all required schemas
all workload references
all credential references
all generated access-data keys
all pinned image and content versions
```

Record validation results in:

```text
docs/agnosticv-validation-report.md
```

The event release must have no unresolved critical catalog-validation failures.

## AgnosticD workload integration

The installed skills may generate workload references or guidance, but they do not necessarily implement the Maximo, logging, identity, or ACM installation logic.

Create supported, idempotent AgnosticD workloads or equivalent approved Ansible automation for:

```text
cluster preflight
ACM registration
MAS prerequisites
MAS Core
Maximo Manage
database configuration
OpenShift Logging
LokiStack
ClusterLogForwarder
S3 integration
identity configuration
student accounts
MAS Edge where required
Showroom
readiness validation
repair
reset
teardown
```

When a marketplace skill provides an AgnosticD workload template, ruleset, or validator, use it rather than inventing the structure.

## Project-local skill rules

Create project-specific rules where supported:

```text
showroom/docs/SKILL-COMMON-RULES.md
showroom/prompts/
```

The local rules must enforce:

* No sensitive values in public content
* No cluster-specific hard-coded values
* Commands are safe to rerun
* Every hands-on task has expected output
* Every critical task has validation
* Every risky task has solve or reset automation
* HCP OAuth limitations are clearly identified
* Presenter-only tasks are clearly separated from attendee tasks
* Demo sizing is clearly separated from production sizing
* Attendees never receive ACM administration or cluster-admin
* No live exercise depends on long-running operator installation
* No attendee exercise damages MAS
* Public YAML uses placeholders for secrets

Project-local rules should extend or override marketplace defaults only where necessary.

## Skill execution evidence

For every marketplace skill used, record:

```text
skill name
purpose
date executed
input files
generated or modified files
validation result
manual changes made afterward
reason for each manual change
```

Store this in:

```text
docs/rhdp-skills-execution-log.md
```

Do not claim that an installed skill was used unless there is execution evidence.

## Skill-first implementation order

Use this sequence:

```text
1. Discover installed skills.
2. Read project-local and marketplace skill instructions.
3. Run the relevant Showroom scaffold or create-lab skill.
4. Review and commit generated Showroom structure.
5. Implement AgnosticD workloads and runtime automation.
6. Run Showroom verification.
7. Run the AgnosticV catalog builder.
8. Adapt the catalog to the approved existing-cluster integration model.
9. Run the AgnosticV validator.
10. Run end-to-end tests.
11. Rerun Showroom and AgnosticV validation after all corrections.
12. Produce final skill execution and validation reports.
```

## Graceful fallback

If a required skill is not installed, unavailable, or fails:

1. Record the issue in `docs/blockers.md`.
2. Capture the exact skill name and failure.
3. Read the corresponding marketplace documentation and canonical templates.
4. Implement the supported structure manually.
5. Clearly mark the result as:

   * `MANUAL_FALLBACK_SKILL_UNAVAILABLE`
6. Run all available validators afterward.

Do not silently bypass a marketplace skill.


## 4.1 Verify before coding

Before selecting versions or writing production manifests:

1. Read the RHDP Skills Marketplace developer guide and relevant skill documentation.
2. Read the current Showroom template and its canonical end-to-end branch.
3. Read the current AgnosticV schema and catalog examples.
4. Read current AgnosticD workload conventions.
5. Read IBM’s current documentation for:

   * Installing MAS into an existing OpenShift cluster
   * Supported OpenShift versions
   * Supported MAS versions
   * IBM Certificate Manager requirements
   * MongoDB requirements
   * Maximo Manage database requirements
   * Storage requirements
   * Entitlement and licensing requirements
   * Administrative permission modes
   * MAS CLI and supported installation methods
6. Read current Red Hat documentation for:

   * OpenShift Logging
   * Loki Operator
   * LokiStack
   * ClusterLogForwarder
   * Advanced Cluster Management
   * Governance policies
   * ACM Search
   * Placement
   * PlacementBinding
   * ManagedClusterSet
   * OpenShift GitOps
7. Produce a compatibility matrix before implementation.

Do not copy deprecated examples.

Do not use `latest`, floating branches, unpinned operator channels, or unversioned container images in the event release.

## 4.2 No invented APIs or schemas

Never invent:

* Showroom configuration fields
* AgnosticV variables
* MAS custom resources
* ACM policy fields
* Logging API versions
* LokiStack fields
* Operator channels
* Kubernetes resources
* IBM installation parameters

Every field must be traceable to current official documentation or a currently supported project example.

## 4.3 Idempotency

Every operation must be safe to rerun.

The automation must:

* Detect existing resources
* Reconcile intended configuration
* Avoid destructive replacement unless explicitly requested
* Wait for dependencies
* Retry transient operations
* Report permanent failures clearly
* Support resuming from a failed stage
* Record the last completed stage
* Preserve diagnostics
* Avoid leaving clusters in partially assigned states

## 4.4 Least privilege

Use cluster-admin only for operations that genuinely require it.

Create separate credentials and service accounts for:

* Fleet bootstrap
* ACM import
* Post-provision configuration
* Showroom runtime validation
* Attendee terminal access
* Presenter access
* Support staff access
* CI validation

Do not expose cluster-admin credentials to attendees or Showroom.

---

# 5. Required repository architecture

Create a clean multi-repository design or a monorepo with equivalent independently deployable directories.

The preferred logical repositories are:

```text
mas-world-2026-automation/
mas-world-2026-showroom/
mas-world-2026-public-content/
mas-world-2026-acm/
mas-world-2026-agnosticv/
mas-world-2026-operations/
```

Document why the final repository model was selected.

## 5.1 `mas-world-2026-automation`

Contains the primary cluster configuration automation.

Suggested structure:

```text
mas-world-2026-automation/
├── ansible.cfg
├── galaxy.yml
├── requirements.yml
├── pyproject.toml
├── Makefile
├── Taskfile.yml
├── config/
│   ├── defaults.yaml
│   ├── event.yaml
│   ├── clusters.yaml
│   ├── credentials.yaml
│   ├── components.yaml
│   ├── aws.yaml
│   ├── showroom.yaml
│   └── environments/
│       ├── development.yaml
│       ├── rehearsal.yaml
│       └── event.yaml
├── inventory/
├── schemas/
├── playbooks/
│   ├── prepare-fleet.yml
│   ├── prepare-cluster.yml
│   ├── validate-fleet.yml
│   ├── validate-cluster.yml
│   ├── repair-cluster.yml
│   ├── reset-exercises.yml
│   ├── rotate-credentials.yml
│   └── decommission-workshop.yml
├── roles/
│   ├── config_validation/
│   ├── cluster_preflight/
│   ├── event_metadata/
│   ├── acm_registration/
│   ├── mas_prerequisites/
│   ├── mas_core/
│   ├── maximo_manage/
│   ├── logging_operator/
│   ├── loki_stack/
│   ├── log_forwarding/
│   ├── identity_demo/
│   ├── mas_edge/
│   ├── student_accounts/
│   ├── sample_workloads/
│   ├── showroom/
│   ├── event_readiness/
│   └── environment_report/
├── plugins/
├── cli/
├── scripts/
├── tests/
├── molecule/
└── docs/
```

If the RHDP delivery model requires an Ansible collection, package these roles as a valid collection and provide the corresponding AgnosticD workload role.

## 5.2 `mas-world-2026-showroom`

Contains the attendee workshop.

Suggested structure:

```text
mas-world-2026-showroom/
├── content/
│   └── modules/
│       └── ROOT/
│           ├── nav.adoc
│           ├── pages/
│           │   ├── index.adoc
│           │   ├── access-readiness.adoc
│           │   ├── navigation-search.adoc
│           │   ├── acm-fleet-management.adoc
│           │   ├── updates.adoc
│           │   ├── observability.adoc
│           │   ├── identity.adoc
│           │   ├── production-architecture.adoc
│           │   ├── troubleshooting.adoc
│           │   └── conclusion.adoc
│           └── partials/
├── runtime-automation/
│   ├── readiness/
│   ├── navigation/
│   ├── acm/
│   ├── updates/
│   ├── observability/
│   └── identity/
├── site.yml
├── ui-config.yml
├── tests/
└── docs/
```

Use the current RHDP Showroom conventions and template.

## 5.3 `mas-world-2026-public-content`

Contains only safe, non-sensitive attendee reference material.

Suggested structure:

```text
mas-world-2026-public-content/
├── README.md
├── operators/
├── logging/
├── identity/
├── mas-edge/
├── architecture/
├── troubleshooting/
└── production-guidance/
```

All examples must be reusable after the event.

Use placeholders for secrets.

Never include:

* AWS access keys
* S3 credentials
* IBM entitlement keys
* MAS license secrets
* Internal URLs
* Kubeconfigs
* Tokens
* Attendee passwords
* Private certificate keys
* Private Git repositories
* Internal registry credentials

## 5.4 `mas-world-2026-acm`

Contains:

* ManagedClusterSets
* Managed-cluster labels
* Placements
* PlacementBindings
* Governance policies
* GitOps resources
* Presenter demonstration assets
* Fleet readiness reports

## 5.5 `mas-world-2026-operations`

Contains:

* Seat assignment tooling
* Fleet status dashboard
* Event runbook
* Repair procedures
* Spare-cluster reassignment procedure
* Escalation matrix
* Pre-event checklist
* Day-of-event checklist
* Post-event teardown
* Cost and resource reporting
* Incident templates

---

# 6. Configurability requirements

All environment-specific values must be supplied through validated configuration.

No cluster count, username, password, cluster URL, AWS account, region, namespace, component version, or seat assignment may be hard-coded in application logic, playbooks, manifests, templates, or Showroom content.

## 6.1 Configuration files

Create a schema-validated configuration model:

```text
config/
├── defaults.yaml
├── event.yaml
├── clusters.yaml
├── credentials.yaml
├── components.yaml
├── aws.yaml
├── showroom.yaml
└── environments/
    ├── development.yaml
    ├── rehearsal.yaml
    └── event.yaml
```

Configuration files may contain non-sensitive metadata and secret references only.

Actual secrets must remain in a configured secret provider.

## 6.2 Layered configuration

Support this precedence:

```text
defaults
   ↓
environment configuration
   ↓
event configuration
   ↓
cluster-specific override
   ↓
command-line override
```

Precedence must be deterministic and documented.

Implement:

```bash
validate-config
render-effective-config
show-config-differences
```

`render-effective-config` must redact all secrets.

---

# 7. Event and fleet configuration

Support this conceptual configuration:

```yaml
event:
  id: mas-world-2026
  name: MAS World 2026
  date: "2026-08-17"
  timezone: America/Chicago

fleet:
  attendee_cluster_count: 50
  spare_cluster_count: 5
  facilitator_cluster_count: 1

  require_exact_cluster_counts: true

  preparation:
    max_concurrent_clusters: 5
    per_cluster_timeout_minutes: 240
    retry_count: 3

  assignment:
    first_seat_number: 1
    seat_number_padding: 2
    automatically_assign_spares: false
```

The inventory is authoritative.

The configured counts must be validated against the enabled clusters in inventory.

The implementation must support different fleet sizes without code changes.

Examples:

```yaml
# Development
fleet:
  attendee_cluster_count: 1
  spare_cluster_count: 0
  facilitator_cluster_count: 1
```

```yaml
# Rehearsal
fleet:
  attendee_cluster_count: 5
  spare_cluster_count: 1
  facilitator_cluster_count: 1
```

```yaml
# Event
fleet:
  attendee_cluster_count: 50
  spare_cluster_count: 5
  facilitator_cluster_count: 1
```

---

# 8. Cluster inventory

Each cluster must be represented independently.

Support a structure equivalent to:

```yaml
clusters:
  - id: seat-01
    enabled: true
    purpose: attendee
    seat_number: 1

    connection:
      api_url: https://api.example-cluster.example.com:6443
      admin_auth_method: kubeconfig
      admin_secret_ref: secret://mas-world/clusters/seat-01/admin-kubeconfig

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

Support these cluster administrative authentication methods:

* Kubeconfig secret reference
* Service-account token secret reference
* OpenShift username/password secret reference where required
* External command or credential-provider integration
* Short-lived token generation where supported

Administrative credentials must be configurable independently for every cluster.

Do not assume one cluster-admin credential works for all clusters.

---

# 9. Secret-provider abstraction

Implement a provider abstraction supporting at least:

1. Environment variables for local development
2. Kubernetes Secrets for in-cluster execution
3. AWS Secrets Manager
4. Optional HashiCorp Vault support

Support secret references such as:

```text
secret://mas-world/clusters/seat-01/admin-kubeconfig
secret://mas-world/students/seat-01
secret://mas-world/ibm/entitlement
secret://mas-world/aws/s3/seat-01
```

Requirements:

* Retrieve secrets only at runtime
* Cache secrets in memory only where possible
* Never print secret values
* Redact known secret patterns
* Avoid writing kubeconfigs to disk
* Remove temporary credentials after use
* Never package credentials in CI artifacts
* Never include credentials in support bundles
* Never store secrets in Git

Where temporary kubeconfig files are unavoidable:

* Use mode `0600`
* Store them in an isolated temporary directory
* Delete them after each cluster operation
* Never log their contents
* Never reuse the same temporary path across concurrent operations

---

# 10. Student credential profiles

Make student-account behavior configurable through reusable profiles.

Support a structure equivalent to:

```yaml
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
      secret_ref_template: "secret://mas-world/facilitators/{{ username }}"

    access:
      cluster_roles:
        - cluster-admin
```

Support these student-password modes:

* Generated password
* Existing secret reference
* External identity-provider account
* Disabled local password where SSO is used
* Deterministic password from an approved secret seed only if explicitly enabled

Generated passwords must use a cryptographically secure generator.

Shared attendee passwords must be disabled by default:

```yaml
student_credentials:
  allow_shared_password: false
```

If shared credentials are enabled for development or rehearsal, emit a prominent security warning.

## 10.1 Student account lifecycle

Implement:

```bash
create-student-accounts
rotate-student-credentials
disable-student-accounts
delete-student-accounts
validate-student-access
export-attendee-access-cards
```

For every student account, validate:

* Authentication succeeds
* Assigned OpenShift console is accessible
* Assigned namespace is accessible
* Assigned Showroom is accessible
* Maximo is accessible where required
* Other attendee namespaces are not accessible
* ACM administration is not accessible
* The account is not cluster-admin
* Protected secrets cannot be retrieved
* Cluster-scoped operators cannot be modified unless explicitly required

---

# 11. Seat assignment model

Seat assignment must be stored independently from cluster preparation.

Support:

```yaml
assignments:
  - seat_number: 1
    cluster_id: seat-01
    credential_profile: attendee-default
    student_username: user01
    status: assigned
```

Implement:

```bash
assign-seat --seat 12 --cluster seat-12
replace-seat --seat 12 --cluster spare-02
unassign-seat --seat 12
show-seat --seat 12
export-seat-map
```

When replacing a cluster:

1. Disable or invalidate the old student credential where appropriate.
2. Create or activate the credential on the replacement cluster.
3. Update Showroom and Maximo endpoint data.
4. Update the assignment inventory.
5. Regenerate the attendee access card.
6. Mark the failed cluster as quarantined.
7. Validate the replacement.
8. Complete the assignment only after validation succeeds.

The reassignment operation must be transactional.

A failed reassignment must not leave the seat pointing to an unvalidated cluster.

---

# 12. Component configuration

Make every major component independently configurable.

Support a structure equivalent to:

```yaml
components:
  mas:
    enabled: true
    version: "<PINNED_VERSION>"
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
    deployment_mode: shared

  mas_edge:
    enabled: false

  showroom:
    enabled: true

  acm_registration:
    enabled: true
```

Disabling a component must not require code changes.

Readiness checks must mark disabled components as `NOT_APPLICABLE`, not `FAIL`.

Support cluster-specific overrides:

```yaml
cluster_overrides:
  seat-17:
    components:
      mas_edge:
        enabled: true
```

---

# 13. Configuration schema and validation

Provide JSON Schema, Pydantic models, or an equivalent strongly typed validation system.

Validation must detect:

* Duplicate cluster IDs
* Duplicate seat numbers
* Missing administrative credential references
* Missing student credential profiles
* More assignments than attendee clusters
* Counts that do not match inventory
* A cluster assigned to multiple seats
* A seat assigned to multiple clusters
* Reused usernames where uniqueness is required
* Secret values accidentally embedded directly in configuration
* Invalid endpoint URLs
* Unsupported authentication methods
* Invalid component combinations
* Attendee accounts assigned cluster-admin
* Missing spare capacity when policy requires it
* Missing AWS account or region details
* Unsupported MAS or OpenShift version combinations
* Missing database configuration
* Missing object storage configuration
* Invalid Showroom parameters

Configuration validation must complete before any cluster is modified.

---

# 14. Fleet orchestration requirements

Implement a maintainable CLI or equivalent interface supporting:

```bash
prepare-fleet --inventory config/clusters.yaml
prepare-cluster --cluster seat-01
validate-fleet
validate-cluster --cluster seat-01
repair-cluster --cluster seat-01
reset-exercise --cluster seat-01 --module observability
generate-seat-report
assign-seat --seat 12 --cluster seat-12
replace-seat --seat 12 --cluster spare-02
rotate-student-credentials
disable-student-accounts
```

Requirements:

* Parallel cluster processing
* Configurable maximum concurrency
* Per-cluster timeout
* Retry with exponential backoff
* Structured JSON logs
* Human-readable console output
* Per-cluster log files
* Aggregated summary
* Failure isolation
* Resume capability
* Dry-run mode where technically possible
* Targeting by cluster, purpose, seat, account, region, and status
* Secret-safe logging
* Exit codes suitable for CI/CD
* Machine-readable result files

Use conservative default concurrency to avoid saturating:

* AWS APIs
* IBM registries
* container registries
* OpenShift APIs
* Git hosting
* DNS
* ACM hub
* object storage

---

# 15. Cluster preflight

Before installation, verify and record:

* OpenShift version
* Kubernetes version
* Cluster platform
* Cluster ID
* API reachability
* Authentication validity
* Cluster-admin capability where required
* Worker count
* Worker architecture
* Schedulable CPU
* Schedulable memory
* Existing resource requests and limits
* StorageClasses
* Default StorageClass
* Dynamic provisioning
* VolumeBindingMode
* Ingress health
* DNS resolution
* Image registry access
* Internet or proxy configuration
* OperatorHub access
* IBM registry access
* AWS API and S3 access
* Existing operators and versions
* Existing MAS resources
* Existing logging resources
* Existing identity configuration
* Conflicting CRDs
* Certificate readiness
* Time synchronization
* Node pressure
* Degraded ClusterOperators
* Pending CSRs
* Required OpenShift features
* Available persistent storage capacity
* Existing namespaces that could conflict
* Cluster-wide network policy conditions

Generate a preflight report in JSON and Markdown.

Classify findings as:

* `PASS`
* `WARNING`
* `FAIL`
* `NOT_APPLICABLE`

Do not continue when a mandatory requirement fails.

---

# 16. Maximo Application Suite installation

Implement MAS installation using a currently supported IBM installation path.

Prefer official IBM automation, CLI, operators, and custom resources over handwritten unsupported flows.

The implementation must:

1. Select and pin a supported MAS version.
2. Select and pin compatible OpenShift and operator versions.
3. Install all required prerequisites.
4. Configure IBM entitlement securely.
5. Configure licensing securely.
6. Install MAS Core.
7. Install and activate Maximo Manage.
8. Configure the Manage database.
9. Configure persistent storage.
10. Configure routes and certificates.
11. Wait for required custom resources to become Ready.
12. Collect MAS URL and readiness data.
13. Load only sample data required for the workshop.
14. Confirm the environment survives automation reruns.
15. Implement a documented upgrade strategy.
16. Produce detailed installation diagnostics.
17. Support partial repair without reinstalling the entire suite.

Do not place IBM entitlement keys in Git.

## 16.1 Database architecture

The database architecture must be explicitly selected.

Evaluate:

* Dedicated database per cluster
* Shared database service with isolated databases
* Managed database service
* Database installed inside each cluster

Document:

* Security isolation
* Capacity
* Availability
* Cost
* Lifecycle
* Backup
* Recovery
* Cleanup
* Connection limits
* Failure blast radius
* Credential model
* Per-seat isolation

Do not assume a database model silently.

Create an architecture decision record.

## 16.2 Administrative permission mode

Determine the correct MAS administrative permission mode for the selected release.

Document:

* Permissions required at installation time
* Permissions retained at runtime
* Whether application lifecycle can be managed from MAS
* Namespace preparation requirements
* Functionality reduced by restrictive modes

Use the least-privilege mode that still supports the workshop.

---

# 17. OpenShift Logging and Loki

Install and configure currently supported versions of:

* Red Hat OpenShift Logging Operator
* Loki Operator
* LokiStack
* Supported log collector
* ClusterLogForwarder

Configure collection for:

* Application logs
* Infrastructure logs
* Audit logs

Use AWS S3 or another supported S3-compatible backend as the Loki object store.

## 17.1 S3 isolation

Implement one of these models after documenting the decision.

Preferred:

```text
One bucket per attendee cluster
```

Example:

```text
mas-world-2026-seat-01-loki-<unique-suffix>
```

Alternative:

```text
One shared bucket with isolated prefixes and strict IAM policies
```

If the shared model is selected, prove through automated negative tests that one cluster cannot access another cluster’s objects.

## 17.2 Credentials and storage lifecycle

Automate:

* Bucket creation or validation
* Encryption
* Public-access block
* Lifecycle policy
* Minimal IAM principal or approved workload identity
* Kubernetes object-storage secret
* Credential rotation
* Post-event revocation
* Post-event cleanup

Do not create credentials manually on event day.

If static IAM access keys are unavoidable:

* Generate and inject them automatically
* Store them in an approved secret provider
* Restrict them to the required bucket or prefix
* Revoke them after the event

## 17.3 Logging exercise

Create a deterministic sample workload that:

1. Emits uniquely identifiable log messages.
2. Includes a run ID and seat ID.
3. Terminates or is deleted.
4. Is recreated.
5. Allows the attendee to query historical logs from Loki.
6. Does not modify or delete a MAS production workload.

Provide:

* Preparation automation
* Attendee commands
* Expected outputs
* Validation
* Solve
* Reset
* Troubleshooting
* Cleanup

Clearly distinguish:

* Conference demonstration architecture
* Production logging architecture
* Short-term retention in Loki
* Long-term retention or SIEM integration
* Splunk or another SIEM
* CloudWatch as an optional architecture
* Supported production sizing

---

# 18. ACM hub and fleet management

Register all attendee, spare, and facilitator clusters with the ACM hub.

Create:

* ManagedClusterSet for the event
* Managed-cluster labels
* Placement resources
* PlacementBindings
* Governance policies
* Presenter-safe views
* Optional GitOps integration
* Fleet readiness reporting

Use labels such as:

```yaml
event: mas-world-2026
workload: maximo
environment: workshop
seat: "01"
purpose: attendee
logging: enabled
idp: preconfigured
readiness: ready
```

Ensure labels are applied consistently and validated.

## 18.1 ACM demonstration

Implement a safe, deterministic 10-minute presenter-led ACM demonstration.

The story is:

> How does the platform team consistently manage and verify a configurable fleet of Maximo OpenShift environments from one management plane?

The demo must show:

1. Fleet inventory
2. Cluster labels
3. Search across managed clusters
4. A workshop baseline governance policy
5. Exactly one deliberately noncompliant facilitator cluster
6. A harmless drift condition
7. Policy remediation
8. Return to full compliance
9. Transition into the logging lab

Create a policy hierarchy conceptually equivalent to:

```text
policy-mas-world-baseline
├── verify-mas-namespace
├── verify-logging-operator
├── verify-lokistack
├── verify-cluster-log-forwarder
├── verify-mas-edge
└── enforce-event-marker
```

Keep critical checks in `inform` mode unless enforcement is proven safe.

For live remediation, use a harmless resource such as a dedicated event ConfigMap.

Do not deliberately break:

* MAS
* Loki storage
* OAuth
* Ingress
* ACM connectivity
* Attendee clusters
* Certificates

Pre-stage drift only on a facilitator-owned cluster.

## 18.2 Attendee ACM access

Attendees must not receive ACM administrative access.

Default model:

* Presenter has scoped administrative access.
* Francis and Myles have support access.
* Attendees watch the central ACM demonstration.
* Attendees verify a safe propagated marker or policy result on their own cluster.

If read-only ACM access is considered, perform and document a security review first.

---

# 19. Identity and Keycloak

The workshop must explain:

* Keycloak as an identity provider
* OIDC concepts
* IDP-side configuration
* OpenShift-side configuration
* LDAP group synchronization
* MAS identity implications
* ingress-secret rotation where applicable
* ROSA HCP OAuth limitations where relevant

Separate the module into:

## DO

* Inspect safe preconfigured resources
* Inspect a sanitized Keycloak client
* Test authentication
* Inspect LDAP group-sync configuration
* Run a bounded group-sync demonstration where supported
* Validate resulting group membership

## OBSERVE

* OAuth server integration
* Secret references
* Identity mappings
* MAS behavior
* Certificate and route configuration

## DISCUSS

* Hosted-control-plane restrictions
* Production IDP topology
* External enterprise identity providers
* High availability
* Certificate lifecycle
* Secret rotation
* Break-glass access

Do not expose Keycloak administrative credentials to attendees.

Decide explicitly whether Keycloak is:

* Per attendee cluster
* Shared
* Hosted on the ACM hub
* Hosted externally

Create an architecture decision record covering:

* Isolation
* Resource use
* Failure domain
* Attendee safety
* Realism
* Scalability
* Credentials
* Network access

---

# 20. MAS updates exercise

Do not make session success depend on a full, lengthy MAS update completing during the allocated 20 minutes.

Create a deterministic update demonstration using one supported pattern:

1. A pre-staged MAS component update
2. A controlled operator or operand update
3. A small configuration update demonstrating lifecycle behavior
4. A presenter-led full update view with a smaller attendee exercise
5. Inspection of a previously completed update and its status history

The selected approach must:

* Be supported
* Complete predictably
* Have a recovery plan
* Avoid irreversible changes
* Include preflight validation
* Include post-update validation
* Distinguish demonstration behavior from production change management

Document production considerations:

* Backup
* Maintenance window
* Compatibility review
* Capacity headroom
* Rollback
* Database protection
* Change approval
* Monitoring
* Post-update verification

---

# 21. MAS Edge

Implement only the MAS Edge scope required for the workshop.

Before implementation:

* Confirm exact product name and supported version.
* Confirm prerequisites.
* Confirm whether it is installed per attendee cluster.
* Confirm resource requirements.
* Confirm licensing implications.
* Confirm networking and certificates.
* Confirm whether attendees interact with it directly.

Do not deploy an unnecessary heavy component merely because it appeared in preliminary notes.

If attendees do not interact directly with it, preconfigure it and expose only inspection and validation steps.

---

# 22. Showroom implementation

Use the current RHDP Showroom template and skills guidance.

The workshop structure must follow:

```text
Know → Do → Check
```

Every module must contain:

* Objective
* Why the task matters
* Estimated time
* Prerequisites
* Exact attendee actions
* Copy-paste-safe commands
* Explanation of commands
* Expected outputs
* Validation
* Solve path
* Reset path where feasible
* Production considerations
* Troubleshooting
* Transition to the next module

## 22.1 Tabs

Configure tabs using the actual supported Showroom schema.

Conceptually include:

* Workshop instructions
* Browser terminal
* Attendee OpenShift console
* Maximo UI
* Public Git repository
* Logging interface
* Optional supporting interfaces

Do not hard-code cluster-specific URLs.

Populate tabs through environment-specific data returned by automation.

## 22.2 Runtime automation

Create module-level runtime automation:

```text
runtime-automation/
├── readiness/
│   └── validate.yml
├── navigation/
│   ├── prepare.yml
│   ├── validate.yml
│   └── solve.yml
├── acm/
│   └── validate.yml
├── updates/
│   ├── prepare.yml
│   ├── validate.yml
│   ├── solve.yml
│   └── reset.yml
├── observability/
│   ├── prepare.yml
│   ├── validate.yml
│   ├── solve.yml
│   └── reset.yml
└── identity/
    ├── prepare.yml
    ├── validate.yml
    ├── solve.yml
    └── reset.yml
```

Runtime automation must operate with minimal permissions.

Validation output must be attendee-friendly and must not reveal sensitive data.

## 22.3 Readiness page

The first page must provide a one-click or one-command readiness check.

Expected categories:

```text
OpenShift API              PASS
OpenShift Console          PASS
Maximo Application Suite   PASS
Maximo Manage              PASS
Database                   PASS
Logging Operator           PASS
LokiStack                  PASS
S3 Object Storage          PASS
ClusterLogForwarder        PASS
Identity Integration       PASS
MAS Edge                   PASS or NOT_APPLICABLE
Showroom Runtime           PASS
Student Authentication     PASS
Student RBAC               PASS
```

---

# 23. Access cards and attendee materials

Generate an attendee-facing access card containing only:

* Seat number
* Showroom URL
* OpenShift console URL
* Maximo URL
* Student username
* Student password or secure one-time retrieval mechanism
* Basic support instructions

Do not expose:

* Cluster-admin credentials
* ACM credentials
* AWS credentials
* IBM credentials
* Other attendee assignments
* Secret-provider paths
* Internal operational metadata

Generate:

* Individual access cards
* Internal facilitator seat inventory
* Printable fallback assignment sheet
* CSV export
* JSON export
* QR codes where appropriate
* Regenerated materials after reassignment

---

# 24. Security requirements

Implement and document:

* Secret-provider abstraction
* Secret redaction
* Kubernetes RBAC
* ACM RBAC
* Attendee isolation
* Network boundaries
* S3 isolation
* Encryption in transit
* Encryption at rest
* Certificate management
* Image provenance
* Pinned images
* Vulnerability scanning
* Source secret scanning
* Dependency scanning
* Audit logging
* Break-glass access
* Credential rotation
* Post-event credential revocation
* Cleanup verification

Block commits containing probable credentials.

Use pre-commit hooks and CI secret scanners.

Do not include sensitive values in:

* Ansible output
* CLI output
* CI logs
* Showroom validation
* support bundles
* generated Markdown
* screenshots
* Git history
* test fixtures

---

# 25. Observability for the preparation platform

The environment-preparation system itself must be observable.

Collect metrics for:

* Cluster preparation duration
* Stage duration
* Success and failure counts
* API request failures
* Retry count
* MAS installation duration
* Operator readiness duration
* Loki readiness duration
* Showroom readiness
* Fleet compliance
* Seat availability
* Spare-cluster availability
* Credential-rotation success
* Student-login validation
* S3 validation
* Assignment and reassignment operations

Generate a fleet dashboard or equivalent report showing:

```text
Total clusters
Ready
Preparing
Warning
Failed
Assigned
Unassigned
Spare
Quarantined
Last validated
```

Use structured events suitable for forwarding to a monitoring platform.

---

# 26. Testing strategy

Implement multiple test layers.

## 26.1 Static tests

* YAML linting
* Ansible linting
* Python linting
* Python type checking
* shell linting
* JSON Schema validation
* Kubernetes schema validation
* documentation link validation
* secret scanning
* container scanning
* policy validation
* Showroom build validation

## 26.2 Unit tests

Test:

* Inventory parsing
* Configuration precedence
* Secret redaction
* Cluster selection
* State tracking
* Retry logic
* Report generation
* Seat assignment
* Spare replacement
* Validation result parsing
* Username generation
* Password generation
* Credential-profile resolution
* Component enablement
* Disabled-component handling
* Transaction rollback

## 26.3 Integration tests

On one development cluster, test:

* Fresh preparation
* Rerun with no changes
* Interrupted run and resume
* Repair of one missing resource
* Credential rotation
* Student-account creation
* Student-login validation
* Showroom variable generation
* Validation
* Module reset
* Cleanup
* ACM registration
* Loki historical log query
* Seat assignment
* Spare reassignment

## 26.4 Negative security tests

Prove that:

* One attendee cannot access another attendee namespace.
* One attendee cannot access another cluster.
* One attendee cannot access ACM administration.
* One attendee cannot retrieve cluster-admin credentials.
* One cluster cannot access another cluster’s S3 data.
* Secret values do not appear in logs.
* Disabled accounts cannot authenticate.
* Quarantined clusters cannot be assigned.

## 26.5 Concurrency tests

Test progressively:

1. One cluster
2. Three clusters
3. Five clusters
4. Ten clusters
5. Full planned concurrency

Record:

* API throttling
* Registry throttling
* Average duration
* Maximum duration
* Failure rate
* Required retries
* Bottlenecks
* Secret-provider load
* ACM hub load
* S3 API load

## 26.6 Full rehearsal

Perform at least one representative fleet rehearsal.

Test:

* Attendee login
* Showroom load
* Concurrent browser terminals
* Simultaneous log generation
* Simultaneous Loki queries
* ACM Search
* ACM policy propagation
* Update exercise
* Identity exercise
* Support workflows
* Spare reassignment
* Conference network assumptions
* Access-card distribution
* Credential rotation
* Event-day fleet validation

---

# 27. Readiness gates

A cluster is `READY` only if all mandatory enabled checks pass.

Example result:

```json
{
  "cluster_id": "seat-01",
  "overall_status": "READY",
  "validated_at": "2026-08-16T18:00:00Z",
  "checks": {
    "openshift": "PASS",
    "mas_core": "PASS",
    "maximo_manage": "PASS",
    "database": "PASS",
    "logging_operator": "PASS",
    "lokistack": "PASS",
    "cluster_log_forwarder": "PASS",
    "s3_write_read": "PASS",
    "historical_log_query": "PASS",
    "identity": "PASS",
    "showroom": "PASS",
    "runtime_automation": "PASS",
    "student_authentication": "PASS",
    "student_rbac": "PASS",
    "mas_edge": "NOT_APPLICABLE"
  }
}
```

A cluster with a mandatory failure must:

* Be marked `FAILED`
* Be excluded from assignment
* Generate a repair recommendation
* Preserve diagnostic information
* Avoid exposing secrets
* Be replaceable by a spare
* Be marked quarantined where appropriate

---

# 28. Operational runbooks

Create detailed runbooks for:

## Before the event

* Capacity confirmation
* Version freeze
* Image pre-pull
* Cluster preparation
* Fleet validation
* Student-account creation
* Credential rotation
* ACM drift staging
* Attendee assignment
* Spare confirmation
* Showroom smoke test
* Presentation rehearsal
* Support workstation setup
* Conference Wi-Fi test
* Backup access method

## Event morning

* Revalidate all clusters
* Replace failed clusters
* Confirm ACM compliance
* Re-stage safe drift
* Confirm S3 access
* Confirm Maximo routes
* Confirm Showroom
* Confirm presenter accounts
* Validate student logins
* Export final seat map
* Generate final access cards
* Freeze nonessential changes

## During the event

* Monitor fleet dashboard
* Assign or replace clusters
* Diagnose common attendee problems
* Reset exercises
* Restore safe ACM drift
* Rotate a compromised student credential
* Disable a lost or exposed account
* Escalate IBM or Red Hat platform issues
* Record incidents

## After the event

* Disable attendee credentials
* Revoke temporary cloud credentials
* Export required diagnostics
* Remove S3 content according to policy
* Unregister clusters from ACM where appropriate
* Uninstall event workloads or hand clusters to the external provisioner for deletion
* Verify cleanup
* Produce cost report
* Document lessons learned

---

# 29. Documentation deliverables

Create:

1. Executive architecture document
2. Product requirements document
3. Technical design document
4. Threat model
5. Compatibility matrix
6. Architecture decision records
7. Installation guide
8. Developer guide
9. Operator guide
10. Event runbook
11. Troubleshooting guide
12. Disaster and recovery procedure
13. Seat-assignment guide
14. Credential-management guide
15. Public attendee README
16. Production-versus-demo architecture guide
17. Teardown guide
18. Test report
19. Known limitations
20. Bill-of-materials document
21. Final acceptance report
22. Configuration reference
23. CLI reference
24. Security review
25. Fleet-sizing guide

Use Mermaid diagrams where appropriate.

Include at least:

* System context diagram
* Cluster preparation flow
* Repository and CI/CD flow
* Secret flow
* ACM topology
* Logging topology
* Identity topology
* Attendee access flow
* Seat assignment flow
* Spare replacement flow
* Configuration precedence flow
* Credential lifecycle flow

---

# 30. CI/CD requirements

Implement CI pipelines that:

* Validate pull requests
* Run static tests
* Run secret scanning
* Validate Kubernetes manifests
* Validate ACM policies
* Build and scan container images
* Render Showroom
* Validate links
* Run unit tests
* Run integration tests against development environments
* Produce versioned releases
* Generate checksums
* Generate software bill of materials
* Sign release artifacts where supported

Use separate environments:

```text
development
rehearsal
event
```

Require explicit approval before promotion to the event environment.

Pin the event release to immutable tags or commit SHAs.

Do not permit deployment when:

* Configuration validation fails
* Secrets are detected in source
* Compatibility validation fails
* Mandatory tests fail
* Release artifacts are unpinned

---

# 31. Public Git repository requirements

The public repository must provide reusable, sanitized examples.

Include:

* Logging Operator examples
* LokiStack example
* ClusterLogForwarder example
* Sample logging workload
* Query examples
* Keycloak/OIDC sanitized examples
* LDAP group-sync examples
* Production architecture guidance
* Sizing caveats
* Cleanup procedures
* Compatibility notes

Each YAML file must include:

* Purpose
* Required permissions
* Supported and tested versions
* Variables attendees must replace
* Security warnings
* Apply command
* Validation command
* Cleanup command

Do not imply that conference sizing is production sizing.

---

# 32. Explicit non-goals

Do not:

* Provision OpenShift clusters
* Hard-code 50 clusters
* Hard-code cluster-admin credentials
* Hard-code student usernames or passwords
* Assume one admin credential works for all clusters
* Give attendees cluster-admin
* Install MAS during the live attendee session
* Install Loki from scratch during the attendee session
* Run an uncontrolled full MAS update
* Allow attendees to mutate the ACM hub
* Commit credentials
* Depend on manually creating secrets on event day
* Use attendee clusters for destructive drift demonstrations
* Use unpinned versions
* Hide implementation gaps behind documentation
* Claim success without end-to-end validation
* Assign failed or unvalidated clusters
* Store passwords in public reports
* Expose secrets in logs or artifacts

---

# 33. Required implementation phases

## Phase 0 — Discovery

Produce:

* Repository assessment
* Version compatibility matrix
* Unanswered dependency list
* Architecture decisions
* Risk register
* Configuration model
* Secret-provider design
* Credential lifecycle design

Where information is unavailable, create clearly marked configuration placeholders and continue implementing everything that does not depend on the missing secret or entitlement.

Do not stop the entire project merely because credentials are absent.

## Phase 1 — Skeleton

Create all repositories or directories, coding standards, CI skeleton, schemas, configuration models, and documentation framework.

## Phase 2 — Single reference cluster

Fully prepare and validate one reference cluster.

This is the authoritative implementation.

## Phase 3 — Student identity and access

Create and validate one student account, RBAC model, access card, and credential lifecycle.

## Phase 4 — ACM hub

Register the reference cluster and create fleet metadata, policies, placements, and the presenter demonstration.

## Phase 5 — Showroom

Create all modules, runtime automation, validation, and reset workflows.

## Phase 6 — Small fleet rollout

Run against a development or rehearsal fleet using controlled concurrency.

## Phase 7 — Full rehearsal

Execute integration, security, load, recovery, and facilitator rehearsals.

## Phase 8 — Event release

Freeze versions, produce immutable release artifacts, validate all clusters, rotate credentials, generate the final seat inventory, and produce attendee access cards.

---

# 34. Acceptance criteria

The project is complete only when:

1. A supplied compatible OpenShift cluster can be prepared with one documented command.
2. The process is idempotent.
3. A failed run can resume.
4. Cluster count is configuration-driven.
5. Changing the attendee count from 50 to 5 requires configuration changes only.
6. Adding or removing a cluster requires inventory changes only.
7. Every cluster may use distinct administrative credentials.
8. Administrative credentials are retrieved only at runtime.
9. Student usernames are generated from configurable templates.
10. Student passwords are generated or retrieved according to configurable profiles.
11. Student RBAC is configurable without modifying playbook code.
12. Shared student passwords are disabled by default.
13. Seat assignments can change without rebuilding the fleet.
14. A spare can replace an attendee cluster with one documented command.
15. Reassignment is transactional.
16. Development, rehearsal, and event fleets use the same code with different configuration.
17. Component enablement and versions are configuration-driven.
18. Configuration validation completes before any cluster is modified.
19. All configured clusters are registered and labeled in ACM.
20. Fleet policies show expected compliance.
21. The safe ACM drift and remediation demonstration works reliably.
22. MAS Core is ready on every assignable cluster.
23. Maximo Manage is ready on every assignable cluster.
24. Database connectivity is validated.
25. Logging captures application, infrastructure, and audit logs.
26. Loki persists logs to supported object storage.
27. Historical logs remain queryable after a demo pod is deleted.
28. Identity exercises work within documented platform limitations.
29. Showroom is parameterized separately for every seat.
30. Attendees cannot access another attendee’s environment.
31. Attendees have no ACM administrative access.
32. Attendee accounts are not cluster-admin.
33. Every module has validation and solve automation.
34. Critical modules have reset automation.
35. Failed clusters are excluded from assignment.
36. A spare can replace a failed assigned environment.
37. All generated attendee materials contain only the credentials intended for that attendee.
38. Secret values do not appear in Git, logs, reports, CI artifacts, or support bundles.
39. CI passes all required tests.
40. A full rehearsal has been completed.
41. The event runbook has been reviewed by all three facilitators.
42. Teardown and credential revocation are tested.
43. The final release is pinned and reproducible.
44. Disabled components are reported as `NOT_APPLICABLE`.
45. Configuration changes do not require source-code modifications.
46. Negative access tests prove attendee isolation.
47. S3 isolation is tested.
48. Student credential rotation is tested.
49. Quarantined clusters cannot be assigned.
50. The final acceptance report maps evidence to every criterion.

---

# 35. Required final response from Claude Code

At the end of implementation, provide:

1. Executive summary
2. Repositories and files created
3. Architecture summary
4. Version compatibility matrix
5. Configuration model summary
6. Secret-provider implementation
7. Exact setup commands
8. Exact configuration-validation command
9. Exact fleet preparation command
10. Exact single-cluster preparation command
11. Exact fleet validation command
12. Exact student-account creation command
13. Exact credential-rotation command
14. Exact seat-assignment command
15. Exact spare-replacement command
16. Exact Showroom build and deployment command
17. Exact ACM demo preparation command
18. Exact exercise reset commands
19. Test results
20. Security findings
21. Known limitations
22. Missing secrets or external dependencies
23. Event-readiness status
24. Remaining manual actions
25. Links or paths to all documentation
26. A checklist mapped to every acceptance criterion

Do not report a feature as complete unless it exists and has been tested.

Use these status labels:

* `IMPLEMENTED_AND_TESTED`
* `IMPLEMENTED_NOT_TESTED`
* `SCAFFOLDED`
* `BLOCKED_EXTERNAL_DEPENDENCY`
* `NOT_IMPLEMENTED`

---

# 36. Initial execution instructions

Begin by:

1. Inspecting the current workspace.
2. Reading existing repositories and local instructions.
3. Reading the RHDP Skills Marketplace developer guide and current templates.
4. Reading the relevant IBM and Red Hat documentation.
5. Creating `docs/discovery-report.md`.
6. Creating `docs/compatibility-matrix.md`.
7. Creating `docs/risk-register.md`.
8. Creating `docs/architecture.md`.
9. Creating `docs/configuration-model.md`.
10. Creating `docs/credential-lifecycle.md`.
11. Creating `docs/implementation-plan.md`.
12. Creating the repository skeleton.
13. Implementing configuration validation.
14. Implementing secret-provider abstraction.
15. Implementing the single-reference-cluster path.
16. Implementing one student account and validating its isolation.
17. Implementing ACM registration and baseline policies.
18. Implementing Showroom.
19. Expanding to a small rehearsal fleet.
20. Running the full acceptance suite.

Do not begin a full fleet rollout until:

* Configuration validation passes
* The reference cluster passes all mandatory checks
* Student isolation tests pass
* Secret-redaction tests pass
* ACM policies are validated
* Showroom is functional
* The logging historical-query exercise works
* Seat assignment and spare replacement are tested

Make reasonable, documented assumptions where necessary.

Prefer working automation with visible placeholders over stopping because a non-secret design detail has not yet been supplied.

Never manufacture credentials, entitlement values, URLs, version compatibility, resource readiness, or test results.
