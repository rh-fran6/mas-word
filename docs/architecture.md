# Architecture Document — MAS World 2026

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
├── mas-world-2026-automation/         # Primary automation
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
├── mas-world-2026-showroom/           # Attendee workshop content
│   ├── content/modules/ROOT/          # Antora content
│   │   ├── nav.adoc
│   │   ├── pages/                     # Workshop pages (9 pages)
│   │   └── partials/                  # Reusable content fragments
│   ├── runtime-automation/            # Validate/solve/reset per module
│   ├── site.yml                       # Antora site configuration
│   └── ui-config.yml                  # Showroom UI configuration
│
├── mas-world-2026-public-content/     # Sanitized reusable examples
│   ├── operators/
│   ├── logging/
│   ├── identity/
│   └── ...
│
├── mas-world-2026-acm/               # ACM hub configuration
│   ├── managedclustersets/
│   ├── policies/
│   ├── placements/
│   └── demo-assets/
│
├── mas-world-2026-agnosticv/          # AgnosticV catalog
│
└── mas-world-2026-operations/         # Operational tooling
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
    EV --> C[clusters.yaml<br/>per-cluster overrides]
    C --> CMD[Command-line<br/>arguments]
    CMD --> EFF[Effective<br/>Configuration]
    EFF --> VAL{Schema<br/>Validation}
    VAL -->|Pass| EXEC[Execute]
    VAL -->|Fail| STOP[Stop with errors]
```
