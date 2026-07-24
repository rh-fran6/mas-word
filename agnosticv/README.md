# MAS World 2026 -- AgnosticV Catalog

AgnosticV catalog definitions for the MAS World 2026 workshop environment.

## Status

`MANUAL_FALLBACK_SKILL_UNAVAILABLE` -- The `/agnosticv:catalog-builder` skill
was evaluated but could not be executed against this project because the
existing-cluster integration model is not natively supported by the skill's
scaffold output. The catalog was built manually following RHDP AgnosticV
conventions and the canonical schema documentation.

## Architecture

This catalog does **not** provision OpenShift clusters. Clusters are
provisioned externally and registered with RHDP before this catalog is
applied. The catalog defines **post-provisioning workloads** that configure
each cluster for the workshop.

```text
Externally provisioned OCP cluster
        |
        v
RHDP order references this catalog item
        |
        v
AgnosticD executes mas-world-post-provision workload
        |
        v
Cluster is configured, Showroom deployed, seat assigned
        |
        v
agnosticd_user_info.data returned to RHDP
        |
        v
Attendee receives access information
```

## Directory layout

```text
catalog/           Catalog item definitions (main, dev, rehearsal variants)
vars/              Variable files (common defaults, environment overrides)
workloads/         Workload references (post-provision, Showroom, teardown)
access-data/       Access data templates (user_info, access cards)
schemas/           Variable schema definitions
docs/              Integration model and workflow documentation
```

## Usage

### Validate the catalog

```bash
# Using the AgnosticV validator (if available)
agnosticv validate catalog/

# Using the project CLI
mas-world config validate --catalog mas-world-2026-agnosticv/
```

### Development deployment

```bash
# Single-cluster development test
agnosticv deploy catalog/mas-world-2026-dev.yml \
  --vars vars/common.yml \
  --vars vars/development.yml
```

### Event deployment

```bash
# Full fleet deployment -- requires event.yml variables
agnosticv deploy catalog/mas-world-2026-workshop.yml \
  --vars vars/common.yml \
  --vars vars/event.yml
```

## Variable precedence

```text
vars/common.yml           Base defaults
vars/<environment>.yml     Environment-specific overrides
catalog/<variant>.yml      Catalog-item-level overrides
per-cluster overrides      Cluster-specific values from inventory
command-line overrides     Runtime overrides
```

## Sensitive values

No credentials, entitlement keys, passwords, tokens, or kubeconfigs are
stored in this directory. All sensitive values use `secret://` references
that are resolved at runtime by the configured secret provider.

## Related repositories

| Repository | Purpose |
|---|---|
| `mas-world-2026-automation` | Ansible roles and fleet orchestration |
| `mas-world-2026-showroom` | Attendee workshop content |
| `mas-world-2026-acm` | ACM policies and fleet management |
| `mas-world-2026-operations` | Runbooks and operational tooling |
| `mas-world-2026-public-content` | Sanitized attendee reference material |
