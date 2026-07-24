# RHDP Integration Model

## Status

`MANUAL_FALLBACK_SKILL_UNAVAILABLE` -- The `/agnosticv:catalog-builder` skill
was evaluated but could not be executed because the existing-cluster
integration model is not natively supported by the skill's scaffold output.
This catalog was built manually following RHDP AgnosticV conventions.

## Overview

This document describes how the MAS World 2026 AgnosticV catalog integrates
with the Red Hat Demo Platform (RHDP).

### Architecture

```text
                   +------------------+
                   |   RHDP Portal    |
                   | (Service Catalog)|
                   +--------+---------+
                            |
                            | 1. Order placed
                            v
                   +------------------+
                   |    AgnosticV     |
                   | (Catalog Engine) |
                   +--------+---------+
                            |
                            | 2. Resolves variables
                            |    from catalog + vars
                            v
                   +------------------+
                   |    AgnosticD     |
                   | (Workload Runner)|
                   +--------+---------+
                            |
                            | 3. Executes workload roles
                            |    against existing cluster
                            v
              +-----------------------------+
              |  Pre-provisioned OCP Cluster |
              |  (external to RHDP)          |
              +-----------------------------+
                            |
                            | 4. Returns agnosticd_user_info.data
                            v
                   +------------------+
                   |   RHDP Portal    |
                   | (Access Info)    |
                   +------------------+
```

## Integration points

### 1. Catalog item registration

The catalog items in `catalog/` are registered with RHDP. Each variant
(workshop, dev, rehearsal) is a separate orderable item in the service
catalog.

### 2. Variable resolution

When an order is placed, RHDP resolves variables in this order:

```text
vars/common.yml              Base defaults
vars/<environment>.yml        Environment overrides
catalog/<variant>.yml         Catalog-level overrides
per-order parameters          Values from the order form
```

### 3. Workload execution

AgnosticD executes the workload roles defined in `workloads/`. Each role
corresponds to an Ansible role in the `masworld.automation` collection
(`mas-world-2026-automation/roles/`).

### 4. Access data return

After successful execution, the `agnosticd_user_info.data` template
(`access-data/user-info-template.yml`) is populated with computed values
and returned to RHDP. The user sees their access information in the
service catalog.

### 5. Teardown

When the order is deprovisioned, AgnosticD executes the teardown workload
(`workloads/mas-world-teardown.yml`), which removes event-specific
resources and revokes credentials.

## Credential flow

```text
Order placed
    |
    v
AgnosticD resolves secret:// references
    |
    v
Secret provider (env / file / k8s / aws-sm / vault)
    |
    v
Credentials available in Ansible variables (memory only)
    |
    v
Roles use credentials for cluster configuration
    |
    v
Credentials discarded after execution
    |
    v
Student password stored in secret provider
    |
    v
agnosticd_user_info.data includes resolved student password
```

No credentials are stored in Git, logs, or CI artifacts.

## Environment mapping

| Environment | Catalog variant | Fleet size | Secret provider |
|---|---|---|---|
| Development | `mas-world-2026-dev.yml` | 1 attendee, 0 spare, 1 facilitator | `env` |
| Rehearsal | `mas-world-2026-rehearsal.yml` | 5 attendee, 1 spare, 1 facilitator | `aws-sm` |
| Event | `mas-world-2026-workshop.yml` | 50 attendee, 5 spare, 1 facilitator | `aws-sm` |

## RHDP platform team requirements

The following items require coordination with the RHDP platform team:

1. **Catalog registration** -- Register the catalog items with RHDP.
2. **Existing-cluster pool** -- Register pre-provisioned clusters with
   RHDP's cluster pool or equivalent mechanism.
3. **Secret provider access** -- Grant AgnosticD execution environments
   access to the configured secret provider.
4. **Network access** -- Ensure AgnosticD runners can reach cluster API
   endpoints, AWS APIs, IBM registries, and the ACM hub.
5. **Execution timeout** -- Confirm that the RHDP workload execution
   timeout supports the 240-minute per-cluster timeout.

## Collection dependency

The workload roles require the `masworld.automation` Ansible collection.
This collection must be available in the AgnosticD execution environment,
either by:

- Publishing to Automation Hub or Galaxy
- Including via `requirements.yml`
- Pre-installing in the execution environment image
