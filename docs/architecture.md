# Architecture

## Overview

This project runs entirely on `localhost` — all `rosa` and `aws` CLI commands execute locally, targeting remote AWS accounts via per-cluster environment variables.

## Data Flow

```
group_vars/all/cluster_topology.yml    secrets/cluster-credentials.yml    group_vars/all/infra_state.yml
         (categories, counts, sizing)   (per-cluster AWS keys, region,     (auto-discovered subnet_ids
                        \                optionally subnet_ids)              from setup-infra.yml)
                         \                    |                              /
                          \                   |   credentials take         /
                           \                  |   precedence over        /
                            \                 |   infra_state           /
                             \                |                       /
                              plugins/filter/cluster_helpers.py
                               build_cluster_list() filter
                                        |
                               cluster_definitions[]
                              (flat list, one dict per cluster)
                                        |
                              loop + environment: per item
                                        |
                              rosa CLI commands with per-cluster AWS creds
```

The data merge works as follows:

1. `cluster-credentials.yml` provides AWS keys and, optionally, explicit `subnet_ids` per account
2. `infra_state.yml` provides auto-discovered `subnet_ids` produced by the infrastructure provisioning layer when subnets are not specified in credentials
3. `build_cluster_list()` merges both sources — credentials take precedence, so manually specified subnets are never overridden by auto-discovered ones
4. The merged data feeds into the cluster provisioning playbooks

## Infrastructure Provisioning Layer

Before clusters can be created, each AWS account needs networking infrastructure and ROSA account-level resources. The `setup-infra.yml` playbook automates this end-to-end.

### aws_infra Role

Creates the full networking stack in each AWS account:

- **VPC** with a configured CIDR block
- **Subnets**: 3 private and 3 public subnets, each placed in a separate Availability Zone for high availability
- **Internet Gateway** attached to the VPC
- **NAT Gateway** in a public subnet so private subnets can reach the internet
- **Route tables** with correct associations (public subnets route through the IGW; private subnets route through the NAT GW)

All resources are created per AWS account, so each account gets its own isolated networking stack.

### rosa_account_setup Role

Prepares each AWS account for ROSA HCP cluster creation:

- Runs `rosa init` to bootstrap the account (validates quotas, creates the ROSA-linked role if needed)
- Runs `rosa create account-roles --hosted-cp` to create the IAM roles required by ROSA HCP clusters

### Orchestration

`setup-infra.yml` orchestrates both roles across every account defined in `secrets/cluster-credentials.yml`:

1. Iterates over all accounts in the credentials file
2. Runs the `aws_infra` role to create networking resources
3. Runs the `rosa_account_setup` role to prepare ROSA prerequisites
4. Persists discovered infrastructure state (VPC IDs, subnet IDs, etc.) to `group_vars/all/infra_state.yml`

The persisted `infra_state.yml` is then consumed by `build_cluster_list()` during cluster provisioning, supplying subnet IDs for accounts that do not have them specified explicitly in credentials.

### Teardown

The `destroy-infra.yml` playbook tears down all infrastructure created by `setup-infra.yml`. It removes resources in dependency order (clusters first if still present, then NAT gateways, internet gateways, subnets, route tables, and finally VPCs) to avoid AWS deletion errors from dangling references.

## Key Mechanisms

### Per-Cluster AWS Credential Isolation

Each `shell` task sets `environment:` from the current loop item:

```yaml
environment:
  AWS_ACCESS_KEY_ID: "{{ item.aws_access_key_id }}"
  AWS_SECRET_ACCESS_KEY: "{{ item.aws_secret_access_key }}"
  AWS_DEFAULT_REGION: "{{ item.aws_region }}"
```

This ensures each iteration of a loop talks to the correct AWS account.

### Parallel Cluster Creation

1. `create.yml` fires all `rosa create cluster` commands with `async/poll:0` — all launch near-simultaneously
2. A separate `async_status` task with `until` waits for each CLI invocation to return
3. `wait_ready.yml` polls `rosa describe cluster` per-cluster until state is `ready`

The async pattern means all clusters start provisioning at roughly the same time, even though Ansible processes loop iterations sequentially for the polling phase.

### Naming Convention

- Pattern: `{cluster_prefix}-{category}-{index}`
- Seats are zero-padded: `seat-01`, `seat-02`, ..., `seat-99`
- Other categories use plain integers: `facilitator-1`, `hub-1`
- Zero-padding ensures consistent sorting for fleets up to 99 seats

### Role Structure

- **rosa_preflight**: Validates CLI tools, ROSA login, AWS credentials, topology
- **rosa_cluster**: Dispatches by `rosa_action` variable to specific task files (create, wait_ready, machinepool, verify, status, destroy, destroy_cleanup)

### Custom Filter Plugin

`build_cluster_list()` merges topology + credentials into a flat list. It:
- Sorts categories alphabetically for deterministic ordering
- Validates every generated cluster name has matching credentials
- Raises a clear error on missing credentials (fails before any cluster creation)


---

## Phase 2: MAS World Application Layer


**Status**: DRAFT — Phase 0
**Date**: 2026-07-19

---

## 1. System Context

```mermaid
graph TB
    subgraph "Event Infrastructure"
        ACM[ACM Hub Cluster]
        subgraph "Attendee Fleet"
            C1[Seat-01 Cluster]
            C2[Seat-02 Cluster]
            CN[Seat-NN Cluster]
        end
        subgraph "Spare Fleet"
            S1[Spare-01]
            S2[Spare-05]
        end
        FC[Facilitator Cluster]
    end

    subgraph "AWS"
        S3[S3 Buckets<br/>Per-Cluster Loki Storage]
        SM[Secrets Manager]
        IAM[IAM Policies]
    end

    subgraph "IBM"
        IBM_REG[IBM Registry<br/>cp.icr.io]
        IBM_ENT[Entitlement]
    end

    subgraph "Automation Platform"
        CLI[Fleet CLI]
        ANSIBLE[Ansible Playbooks]
        CI[CI/CD Pipeline]
        CONFIG[Configuration<br/>Schemas]
    end

    subgraph "Attendee Access"
        SHOW[Showroom]
        TERM[Browser Terminal]
        CONSOLE[OCP Console]
        MAXIMO[Maximo UI]
    end

    CLI --> ANSIBLE
    ANSIBLE --> C1
    ANSIBLE --> C2
    ANSIBLE --> CN
    ANSIBLE --> S1
    ANSIBLE --> FC
    ANSIBLE --> ACM

    C1 --> S3
    C2 --> S3
    CN --> S3

    C1 --> IBM_REG
    ACM --> C1
    ACM --> C2
    ACM --> CN
    ACM --> S1
    ACM --> FC

    CLI --> SM
    CLI --> CONFIG

    SHOW --> C1
    TERM --> C1
    CONSOLE --> C1
    MAXIMO --> C1
```

---

## 2. Cluster Preparation Flow

```mermaid
flowchart TD
    START[Existing OpenShift Cluster] --> VALIDATE_CONFIG[Configuration Validation]
    VALIDATE_CONFIG --> PREFLIGHT[Compatibility & Capacity Preflight]
    PREFLIGHT --> CREDS[Retrieve Admin Credentials]
    CREDS --> ACM_REG[Register with ACM Hub]
    ACM_REG --> LABELS[Apply Event Labels & ManagedClusterSet]
    LABELS --> MAS_PRE[Install MAS Prerequisites]
    MAS_PRE --> MAS_CORE[Install MAS Core]
    MAS_CORE --> MAS_MANAGE[Install & Configure Maximo Manage]
    MAS_MANAGE --> LOGGING[Install Logging Operator & Loki]
    LOGGING --> S3_SETUP[Configure S3 Object Storage]
    S3_SETUP --> CLF[Configure ClusterLogForwarder]
    CLF --> IDENTITY[Configure Identity Components]
    IDENTITY --> MAS_EDGE{MAS Edge<br/>Enabled?}
    MAS_EDGE -->|Yes| EDGE[Configure MAS Edge]
    MAS_EDGE -->|No| SKIP_EDGE[Skip]
    EDGE --> STUDENT
    SKIP_EDGE --> STUDENT[Create Student Accounts & RBAC]
    STUDENT --> SAMPLE[Stage Sample Data & Exercises]
    SAMPLE --> SHOWROOM_INSTALL[Install & Parameterize Showroom]
    SHOWROOM_INSTALL --> READINESS[Run Readiness Tests]
    READINESS --> STATUS{All Mandatory<br/>Checks Pass?}
    STATUS -->|Yes| READY[Mark READY]
    STATUS -->|No| FAILED[Mark FAILED<br/>Generate Repair Recommendation]
    READY --> ASSIGN[Add to Seat Assignment Inventory]
    FAILED --> QUARANTINE[Quarantine Cluster]
```

---

## 3. Repository Architecture

```text
maximo-world/                          # Monorepo root
│
├── docs/                              # Cross-cutting documentation
│   ├── discovery-report.md
│   ├── compatibility-matrix.md
│   ├── architecture.md                # This document
│   ├── configuration-model.md
│   ├── credential-lifecycle.md
│   ├── risk-register.md
│   ├── implementation-plan.md
│   ├── threat-model.md
│   ├── adr/                           # Architecture Decision Records
│   └── ...
│
├──          # Primary automation
│   ├── ansible.cfg
│   ├── galaxy.yml                     # Ansible collection metadata
│   ├── requirements.yml               # Ansible Galaxy dependencies
│   ├── pyproject.toml                 # Python project (CLI, plugins, tests)
│   ├── Makefile
│   ├── config/                        # Configuration hierarchy
│   ├── inventory/                     # Dynamic inventory
│   ├── schemas/                       # JSON Schema for config validation
│   ├── playbooks/                     # Ansible playbooks
│   ├── roles/                         # Ansible roles (17 roles)
│   ├── plugins/                       # Ansible plugins (filters, lookups)
│   ├── cli/                           # Python CLI (mas-world command)
│   ├── scripts/                       # Shell utilities
│   ├── tests/                         # Unit, integration, security tests
│   └── molecule/                      # Ansible Molecule test scenarios
│
├── showroom/           # Attendee workshop content
│   ├── content/modules/ROOT/          # Antora content
│   │   ├── nav.adoc
│   │   ├── pages/                     # Workshop pages (9 pages)
│   │   └── partials/                  # Reusable content fragments
│   ├── runtime-automation/            # Validate/solve/reset per module
│   ├── site.yml                       # Antora site configuration
│   └── ui-config.yml                  # Showroom UI configuration
│
├── public-content/     # Sanitized reusable examples
│   ├── operators/
│   ├── logging/
│   ├── identity/
│   └── ...
│
├── acm/               # ACM hub configuration
│   ├── managedclustersets/
│   ├── policies/
│   ├── placements/
│   └── demo-assets/
│
├── agnosticv/          # AgnosticV catalog
│
└── operations/         # Operational tooling
    ├── seat-assignment/
    ├── fleet-dashboard/
    ├── runbooks/
    └── ...
```

---

## 4. Automation Architecture

### 4.1 Ansible Collection Structure

The automation is packaged as an Ansible collection:
`masworld.automation`

```text
roles/
├── config_validation     # Validate configuration before execution
├── cluster_preflight     # Check cluster compatibility and capacity
├── event_metadata        # Apply labels and event markers
├── acm_registration      # Register cluster with ACM hub
├── mas_prerequisites     # Install MAS prerequisites (cert-manager, MongoDB, etc.)
├── mas_core              # Install MAS Core operator and Suite CR
├── maximo_manage          # Install and activate Maximo Manage
├── logging_operator      # Install Red Hat OpenShift Logging Operator
├── loki_stack            # Install Loki Operator and LokiStack
├── log_forwarding        # Configure ClusterLogForwarder
├── identity_demo         # Configure Keycloak and identity resources
├── mas_edge              # Configure MAS Edge (when enabled)
├── student_accounts      # Create student accounts, RBAC, htpasswd
├── sample_workloads      # Deploy exercise workloads and sample data
├── showroom              # Install and parameterize Showroom
├── event_readiness       # Run readiness checks
└── environment_report    # Generate cluster and fleet reports
```

### 4.2 Playbook Architecture

```text
playbooks/
├── prepare-fleet.yml         # Orchestrate full fleet preparation
├── prepare-cluster.yml       # Prepare a single cluster (all roles)
├── validate-fleet.yml        # Run readiness checks across fleet
├── validate-cluster.yml      # Run readiness checks on one cluster
├── repair-cluster.yml        # Repair specific failed components
├── reset-exercises.yml       # Reset exercise state for a module
├── rotate-credentials.yml    # Rotate student credentials
└── decommission-workshop.yml # Post-event teardown
```

### 4.3 CLI Architecture

```text
cli/
├── __init__.py
├── main.py                   # Click CLI entry point
├── commands/
│   ├── config.py             # validate-config, render-effective-config
│   ├── fleet.py              # prepare-fleet, validate-fleet
│   ├── cluster.py            # prepare-cluster, validate-cluster, repair-cluster
│   ├── students.py           # create/rotate/disable/delete student accounts
│   ├── seats.py              # assign/replace/unassign/show/export seats
│   ├── exercises.py          # reset-exercise
│   └── reports.py            # generate-seat-report, fleet-status
├── config/
│   ├── loader.py             # Configuration loading and merging
│   ├── schema.py             # Pydantic models
│   └── validator.py          # Configuration validation
├── secrets/
│   ├── provider.py           # SecretProvider ABC
│   ├── env_provider.py       # Environment variable provider
│   ├── k8s_provider.py       # Kubernetes Secrets provider
│   ├── aws_sm_provider.py    # AWS Secrets Manager provider
│   └── vault_provider.py     # HashiCorp Vault provider (optional)
├── inventory/
│   ├── manager.py            # Cluster inventory management
│   └── dynamic.py            # Ansible dynamic inventory script
├── orchestration/
│   ├── fleet.py              # Parallel fleet execution
│   ├── retry.py              # Retry with backoff
│   └── state.py              # State tracking and resume
└── reporting/
    ├── fleet_status.py       # Fleet dashboard data
    ├── seat_map.py           # Seat assignment report
    └── access_cards.py       # Access card generation
```

---

## 5. Secret Flow

```mermaid
sequenceDiagram
    participant CLI as Fleet CLI
    participant CFG as Config Layer
    participant SP as Secret Provider
    participant EXT as External Store<br/>(Env/K8s/AWS SM/Vault)
    participant K8s as Target Cluster

    CLI->>CFG: Load config with secret refs
    CFG-->>CLI: Config with secret://... references
    CLI->>SP: Resolve secret://mas-world/clusters/seat-01/admin-kubeconfig
    SP->>EXT: Fetch secret value
    EXT-->>SP: Raw secret data
    SP-->>CLI: Secret value (in memory)
    Note over CLI: Write kubeconfig to temp file (0600)
    CLI->>K8s: Authenticate using temp kubeconfig
    K8s-->>CLI: Authenticated session
    CLI->>K8s: Execute preparation roles
    Note over CLI: Delete temp kubeconfig
```

---

## 6. ACM Topology

```mermaid
graph TB
    subgraph "ACM Hub"
        HUB[Hub Cluster]
        MCS[ManagedClusterSet<br/>mas-world-2026]
        POLICY[Policy: mas-world-baseline]
        PLACE[Placement]
        PB[PlacementBinding]
        SEARCH[ACM Search]
    end

    subgraph "Managed Clusters"
        MC1[seat-01<br/>purpose: attendee<br/>readiness: ready]
        MC2[seat-02<br/>purpose: attendee<br/>readiness: ready]
        MCN[seat-NN<br/>purpose: attendee]
        MCS1[spare-01<br/>purpose: spare]
        MCF[facilitator-01<br/>purpose: facilitator<br/>drift: staged]
    end

    MCS --> MC1
    MCS --> MC2
    MCS --> MCN
    MCS --> MCS1
    MCS --> MCF
    POLICY --> PB
    PB --> PLACE
    PLACE --> MCS
    HUB --> SEARCH
    SEARCH --> MC1
    SEARCH --> MC2
    SEARCH --> MCN
```

---

## 7. Logging Topology

```mermaid
graph LR
    subgraph "Attendee Cluster"
        APP[Application Pods]
        INFRA[Infrastructure]
        AUDIT[Audit Events]
        VECTOR[Vector<br/>Log Collector]
        LOKI[LokiStack]
        CLF[ClusterLogForwarder]
    end

    subgraph "AWS"
        S3[S3 Bucket<br/>mas-world-2026-seat-NN-loki-xxx]
    end

    APP --> VECTOR
    INFRA --> VECTOR
    AUDIT --> VECTOR
    VECTOR --> CLF
    CLF --> LOKI
    LOKI --> S3
```

---

## 8. Identity Topology

```mermaid
graph TB
    subgraph "Attendee Cluster"
        OAUTH[OAuth Server]
        HTPASSWD[HTPasswd IDP<br/>Student accounts]
        KC[Keycloak<br/>Demo IDP]
        LDAP[LDAP<br/>Group Sync Demo]
        MAS_AUTH[MAS Auth]
    end

    STUDENT[Student] --> OAUTH
    OAUTH --> HTPASSWD
    OAUTH --> KC
    KC --> LDAP
    MAS_AUTH --> OAUTH

    style KC fill:#f9f,stroke:#333
    style LDAP fill:#f9f,stroke:#333
```

---

## 9. Attendee Access Flow

```mermaid
sequenceDiagram
    participant A as Attendee
    participant SR as Showroom
    participant T as Terminal
    participant OCP as OpenShift Console
    participant MAX as Maximo UI
    participant LOKI as Loki / Logging

    A->>SR: Open Showroom URL from access card
    SR-->>A: Workshop instructions + tabs
    A->>T: Open terminal tab
    T-->>A: Authenticated shell (student user)
    A->>OCP: Open console tab
    OCP-->>A: Login with student credentials
    A->>MAX: Open Maximo tab
    MAX-->>A: Maximo interface
    A->>SR: Click Validate button
    SR->>T: Run validation script
    T-->>SR: Validation results
    SR-->>A: PASS / FAIL with guidance
```

---

## 10. Seat Assignment Flow

```mermaid
flowchart TD
    ASSIGN[assign-seat --seat 12 --cluster seat-12]
    ASSIGN --> CHECK_CLUSTER{Cluster<br/>status?}
    CHECK_CLUSTER -->|READY| CHECK_SEAT{Seat<br/>available?}
    CHECK_CLUSTER -->|FAILED| REJECT1[Reject: cluster not ready]
    CHECK_CLUSTER -->|QUARANTINED| REJECT2[Reject: cluster quarantined]
    CHECK_SEAT -->|Yes| CREATE_CREDS[Create/activate credentials]
    CHECK_SEAT -->|No| REJECT3[Reject: seat already assigned]
    CREATE_CREDS --> UPDATE_SHOWROOM[Update Showroom parameters]
    UPDATE_SHOWROOM --> UPDATE_INV[Update assignment inventory]
    UPDATE_INV --> GEN_CARD[Generate access card]
    GEN_CARD --> VALIDATE[Validate student access]
    VALIDATE --> COMPLETE{Validation<br/>passed?}
    COMPLETE -->|Yes| DONE[Assignment complete]
    COMPLETE -->|No| ROLLBACK[Rollback assignment]
```

---

## 11. Spare Replacement Flow

```mermaid
flowchart TD
    REPLACE[replace-seat --seat 12 --cluster spare-02]
    REPLACE --> VALIDATE_SPARE{Spare cluster<br/>READY?}
    VALIDATE_SPARE -->|No| ABORT[Abort: spare not ready]
    VALIDATE_SPARE -->|Yes| DISABLE_OLD[Disable credentials on old cluster]
    DISABLE_OLD --> CREATE_NEW[Create credentials on spare]
    CREATE_NEW --> UPDATE_ENDPOINTS[Update Showroom & Maximo endpoints]
    UPDATE_ENDPOINTS --> UPDATE_ASSIGNMENT[Update assignment inventory]
    UPDATE_ASSIGNMENT --> REGEN_CARD[Regenerate access card]
    REGEN_CARD --> VALIDATE_NEW[Validate student access on spare]
    VALIDATE_NEW --> RESULT{Validation<br/>passed?}
    RESULT -->|Yes| QUARANTINE_OLD[Quarantine old cluster<br/>Complete assignment]
    RESULT -->|No| ROLLBACK[Rollback: restore original assignment]
```

---

## 12. Configuration Precedence Flow

```mermaid
flowchart LR
    D[defaults.yaml] --> E[environments/event.yaml]
    E --> EV[event.yaml]
    EV --> C[cluster-credentials.yml<br/>per-cluster identity]
    C --> CMD[Command-line<br/>arguments]
    CMD --> EFF[Effective<br/>Configuration]
    EFF --> VAL{Schema<br/>Validation}
    VAL -->|Pass| EXEC[Execute]
    VAL -->|Fail| STOP[Stop with errors]
```
