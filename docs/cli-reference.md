# CLI Reference -- MAS World 2026

**Status**: DRAFT -- Phase 1
**Date**: 2026-07-19

---

## Installation

The CLI is installed as a Python package:

```bash
pip install -e .
```

This registers the `mas-world` entry point. All commands are invoked as
subcommands of `mas-world`.

---

## Global Options

Every command inherits these options from the top-level group:

| Option | Type | Default | Environment Variable | Description |
|--------|------|---------|---------------------|-------------|
| `--env` | `development` / `rehearsal` / `event` | `development` | `MAS_WORLD_ENV` | Target environment. Selects the environment overlay file. |
| `--config-dir` | path | `config` | `MAS_WORLD_CONFIG_DIR` | Path to the configuration directory. Must exist. |
| `--verbose` / `-v` | flag | `false` | -- | Enable verbose output including Ansible command details. |

Environment variables use the `MAS_WORLD_` prefix (set via Click's
`auto_envvar_prefix`).

Example:

```bash
mas-world --env event --config-dir /path/to/config --verbose fleet validate
```

---

## Command Groups

```text
mas-world
  config     Configuration validation and inspection
  cluster    Single-cluster preparation, validation, and repair
  fleet      Fleet-level preparation and validation
  student    Student account lifecycle management
  seat       Seat assignment and management
  exercise   Exercise reset and management
  report     Fleet and seat reporting
```

---

## `config` -- Configuration Management

### `mas-world config validate`

Validate all configuration files against Pydantic schemas and cross-reference
rules.

**Usage**:

```bash
mas-world --env <environment> config validate [--cluster <id>]
```

**Options**:

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--cluster` | `str` | no | Validate only the specified cluster's configuration. |

**Behavior**:

1. Loads all configuration files with the specified environment overlay.
2. Parses the merged configuration through the Pydantic `MASWorldConfig`
   model.
3. Runs cross-reference validation (duplicate IDs, seat conflicts, profile
   references, security checks).
4. Reports each finding with severity (`ERROR` or `WARNING`) and the
   configuration path where the issue was found.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Configuration is valid. |
| `1` | One or more validation errors found. |

**Examples**:

```bash
# Validate event configuration
mas-world --env event config validate

# Validate a specific cluster
mas-world --env rehearsal config validate --cluster seat-03
```

---

### `mas-world config render`

Render the effective merged configuration with secrets redacted.

**Usage**:

```bash
mas-world --env <environment> config render [--cluster <id>] [--format yaml|json]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--cluster` | `str` | -- | Render the effective config for a specific cluster, including its component overrides. |
| `--format` | `yaml` / `json` | `yaml` | Output format. |

**Behavior**:

1. Loads and merges all configuration layers for the specified environment.
2. Applies cluster-specific overrides if `--cluster` is provided.
3. Replaces all `secret://` references and detected secret patterns with
   `REDACTED`.
4. Outputs the full effective configuration to stdout.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Configuration rendered successfully. |
| `1` | Failed to load configuration. |

**Examples**:

```bash
# Render event config as YAML
mas-world --env event config render

# Render a specific cluster's config as JSON
mas-world --env rehearsal config render --cluster seat-01 --format json
```

---

### `mas-world config diff`

Show configuration differences between two environments.

**Usage**:

```bash
mas-world config diff --from <environment> --to <environment>
```

**Options**:

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--from` | `str` | yes | Source environment name. |
| `--to` | `str` | yes | Target environment name. |

**Behavior**:

1. Loads the effective configuration for both environments.
2. Computes a deep diff of all keys.
3. Displays each changed key with its source and target values.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Diff completed (with or without differences). |
| `1` | Failed to load one or both configurations. |

**Examples**:

```bash
# Compare development to event
mas-world config diff --from development --to event

# Compare rehearsal to event
mas-world config diff --from rehearsal --to event
```

---

## `cluster` -- Single-Cluster Operations

### `mas-world cluster prepare`

Prepare a single cluster by running the full preparation playbook.

**Usage**:

```bash
mas-world --env <environment> cluster prepare <cluster_id> [--dry-run]
```

**Arguments**:

| Argument | Required | Description |
|----------|----------|-------------|
| `cluster_id` | yes | The cluster ID as defined in `secrets/cluster-credentials.yml`. |

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dry-run` | flag | `false` | Show the Ansible command that would be executed without running it. |

**Behavior**:

1. Validates the cluster exists in inventory and is enabled.
2. Constructs extra variables including `cluster_id`, `cluster_purpose`,
   `seat_number`, `config_dir`, and `env`.
3. Executes `playbooks/prepare-cluster.yml` via `ansible-playbook`.
4. In dry-run mode, prints the command without executing.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Cluster preparation completed successfully. |
| `1` | Preparation failed (Ansible returned nonzero, or cluster not found). |

**Examples**:

```bash
# Prepare a single cluster
mas-world --env development cluster prepare seat-01

# Dry-run to verify the command
mas-world --env event cluster prepare seat-15 --dry-run
```

---

### `mas-world cluster validate`

Run readiness checks against a single cluster and report results.

**Usage**:

```bash
mas-world --env <environment> cluster validate <cluster_id> [--format text|json|markdown]
```

**Arguments**:

| Argument | Required | Description |
|----------|----------|-------------|
| `cluster_id` | yes | The cluster ID to validate. |

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | `text` / `json` / `markdown` | `text` | Output format for the readiness report. |

**Behavior**:

1. Validates the cluster exists in inventory.
2. Executes `playbooks/validate-cluster.yml`.
3. Reads the generated readiness report from `reports/readiness-<cluster_id>.json`
   if available.
4. Displays check results in the requested format.

In `text` format, each check is color-coded: green for `PASS`, red for
`FAIL`, cyan for `NOT_APPLICABLE`, yellow for `WARNING`.

**Readiness checks** (per the report JSON):

```text
openshift, mas_core, maximo_manage, database, logging_operator,
lokistack, cluster_log_forwarder, s3_write_read, historical_log_query,
identity, showroom, runtime_automation, student_authentication,
student_rbac, mas_edge
```

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | All mandatory checks passed. |
| `1` | One or more mandatory checks failed. |

**Examples**:

```bash
# Validate and display text report
mas-world --env event cluster validate seat-01

# Validate and get JSON report
mas-world --env event cluster validate seat-01 --format json

# Validate with verbose Ansible output
mas-world --env event -v cluster validate seat-01
```

---

### `mas-world cluster repair`

Repair failed components on a single cluster.

**Usage**:

```bash
mas-world --env <environment> cluster repair <cluster_id> [--component <name>]
```

**Arguments**:

| Argument | Required | Description |
|----------|----------|-------------|
| `cluster_id` | yes | The cluster ID to repair. |

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--component` | `str` | `"all"` | Repair only the specified component. Omit to repair all failed components. |

**Behavior**:

1. Validates the cluster exists in inventory.
2. Executes `playbooks/repair-cluster.yml` with `repair_components` set to
   the specified component or `all`.
3. Reports success or failure.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Repair completed successfully. |
| `1` | Repair failed. |

**Examples**:

```bash
# Repair all failed components
mas-world --env event cluster repair seat-01

# Repair only the logging component
mas-world --env event cluster repair seat-01 --component logging
```

---

## `fleet` -- Fleet Operations

### `mas-world fleet prepare`

Prepare all enabled clusters in the fleet with configurable parallelism.

**Usage**:

```bash
mas-world --env <environment> fleet prepare [--max-concurrent <n>] [--dry-run]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--max-concurrent` | `int` | from config | Maximum number of clusters to prepare in parallel. Overrides `fleet.preparation.max_concurrent_clusters`. |
| `--dry-run` | flag | `false` | List the clusters that would be prepared without executing. |

**Behavior**:

1. Loads configuration and identifies all enabled clusters.
2. If `--dry-run`, lists the clusters and exits.
3. Uses a thread pool to prepare clusters in parallel up to the concurrency
   limit.
4. Prints progress as each cluster completes: status, duration, and a
   running counter.
5. Produces a summary of succeeded and failed clusters.
6. Each cluster is prepared by invoking `playbooks/prepare-cluster.yml` in
   a subprocess.
7. Hard timeout per cluster: 4 hours (14400 seconds).

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | All clusters prepared successfully. |
| `1` | One or more clusters failed. |

**Examples**:

```bash
# Prepare the full event fleet
mas-world --env event fleet prepare

# Prepare with limited concurrency
mas-world --env event fleet prepare --max-concurrent 3

# Dry-run to see what would happen
mas-world --env event fleet prepare --dry-run
```

---

### `mas-world fleet validate`

Run readiness checks across all enabled clusters in the fleet.

**Usage**:

```bash
mas-world --env <environment> fleet validate [--format text|json|markdown]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | `text` / `json` / `markdown` | `text` | Output format for the fleet validation report. |

**Behavior**:

1. Loads configuration and identifies all enabled clusters.
2. Executes `playbooks/validate-fleet.yml`.
3. Reads per-cluster readiness reports from `reports/readiness-<cluster_id>.json`.
4. Aggregates status counts across the fleet.
5. Outputs a fleet summary and per-cluster results.

In `json` format, produces a structured report:

```json
{
  "validated_at": "2026-08-16T18:00:00+00:00",
  "total_clusters": 56,
  "status_counts": {
    "PASS": 50,
    "READY": 5,
    "FAIL": 1
  },
  "clusters": [...]
}
```

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Fleet validation playbook succeeded. |
| `1` | Validation playbook failed. |

**Examples**:

```bash
# Validate the full fleet
mas-world --env event fleet validate

# Get a JSON report for CI
mas-world --env event fleet validate --format json

# Get a Markdown report for documentation
mas-world --env event fleet validate --format markdown
```

---

## `student` -- Student Account Management

### `mas-world student create`

Create student accounts on target clusters using the configured credential
profiles.

**Usage**:

```bash
mas-world --env <environment> student create [--cluster <id>] [--seat <n>]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--cluster` | `str` | -- | Target a specific cluster. |
| `--seat` | `int` | -- | Target a specific seat number. |

If neither `--cluster` nor `--seat` is provided, creates accounts on all
enabled clusters with assigned seat numbers.

**Behavior**:

1. Resolves the credential profile for each target cluster.
2. Generates a password using a cryptographically secure generator (when
   `mode: generated`). Passwords meet complexity requirements: at least one
   lowercase, one uppercase, and one digit.
3. Stores the generated password in the configured secret provider.
4. Runs the student-creation playbook for each cluster.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | All student accounts created. |
| `1` | One or more creations failed. |

**Examples**:

```bash
# Create all student accounts
mas-world --env event student create

# Create for a specific seat
mas-world --env event student create --seat 12
```

---

### `mas-world student rotate`

Rotate student credentials by generating new passwords and updating the
clusters.

**Usage**:

```bash
mas-world --env <environment> student rotate [--cluster <id>] [--seat <n>]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--cluster` | `str` | -- | Target a specific cluster. |
| `--seat` | `int` | -- | Target a specific seat. |

**Behavior**:

1. Generates a new password for each target student.
2. Stores the new password in the secret provider.
3. Executes `playbooks/rotate-credentials.yml` to update the htpasswd file
   on each cluster.
4. Skips accounts with non-generated password modes (`secret-ref`,
   `external-idp`, `disabled`).

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | All rotations succeeded. |
| `1` | One or more rotations failed. |

**Examples**:

```bash
# Rotate all student credentials before the event
mas-world --env event student rotate

# Rotate a single compromised credential
mas-world --env event student rotate --seat 7
```

---

### `mas-world student disable`

Disable student accounts on target clusters.

**Usage**:

```bash
mas-world --env <environment> student disable [--cluster <id>] [--seat <n>]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--cluster` | `str` | -- | Target a specific cluster. |
| `--seat` | `int` | -- | Target a specific seat. |

**Behavior**:

Runs the preparation playbook with `student_action=disable` to deactivate
student authentication on the target clusters. The accounts remain but
cannot log in.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | All accounts disabled. |
| `1` | One or more disable operations failed. |

**Examples**:

```bash
# Disable all student accounts after the event
mas-world --env event student disable

# Disable a specific seat's account
mas-world --env event student disable --seat 12
```

---

### `mas-world student delete`

Delete student accounts from target clusters.

**Usage**:

```bash
mas-world --env <environment> student delete [--cluster <id>] [--seat <n>]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--cluster` | `str` | -- | Target a specific cluster. |
| `--seat` | `int` | -- | Target a specific seat. |

**Behavior**:

Runs the preparation playbook with `student_action=delete` to remove student
accounts, htpasswd entries, namespace RBAC bindings, and related resources.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | All accounts deleted. |
| `1` | One or more deletions failed. |

**Examples**:

```bash
# Delete all student accounts during teardown
mas-world --env event student delete
```

---

### `mas-world student validate`

Validate that student accounts can authenticate and that RBAC restrictions
are enforced.

**Usage**:

```bash
mas-world --env <environment> student validate [--cluster <id>] [--seat <n>]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--cluster` | `str` | -- | Target a specific cluster. |
| `--seat` | `int` | -- | Target a specific seat. |

**Behavior**:

Executes `playbooks/validate-cluster.yml` with student context to verify:

- Authentication succeeds with stored credentials.
- Assigned namespace is accessible.
- OpenShift console is reachable.
- Other students' namespaces are not accessible.
- ACM administrative access is denied.
- The account does not have cluster-admin.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | All validations passed. |
| `1` | One or more validations failed. |

**Examples**:

```bash
# Validate all students
mas-world --env event student validate

# Validate a specific seat
mas-world --env event student validate --seat 5
```

---

### `mas-world student export-cards`

Generate attendee access cards containing credentials and endpoint URLs.

**Usage**:

```bash
mas-world --env <environment> student export-cards [--seat <n>] [--format html|json|pdf]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--seat` | `int` | -- | Generate a card for a specific seat only. |
| `--format` | `html` / `json` / `pdf` | `html` | Output format. PDF falls back to JSON with guidance to print HTML. |

**Behavior**:

1. Reads active assignments from `config/assignments.yaml`.
2. Retrieves student passwords from the configured secret provider.
3. Generates access cards with: seat number, username, password, Showroom
   URL, OpenShift console URL, Maximo URL, and support instructions.
4. Cards never include cluster-admin credentials, AWS credentials, IBM
   entitlement keys, or internal operational metadata.

The HTML output includes print-friendly CSS with page-break rules for
physical card distribution.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Cards generated. |
| `1` | No active assignments found or secret provider unavailable. |

**Examples**:

```bash
# Generate all access cards as HTML
mas-world --env event student export-cards --format html > access-cards.html

# Generate a single card as JSON
mas-world --env event student export-cards --seat 12 --format json
```

---

## `seat` -- Seat Assignment Management

### `mas-world seat assign`

Assign a seat number to a cluster. The cluster must be enabled and have
purpose `attendee` or `spare`.

**Usage**:

```bash
mas-world --env <environment> seat assign --seat <n> --cluster <id>
```

**Options**:

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--seat` | `int` | yes | Seat number to assign. |
| `--cluster` | `str` | yes | Cluster ID to assign to this seat. |

**Behavior**:

1. Validates the cluster exists, is enabled, and has an assignable purpose.
2. Checks the seat is not already assigned (use `replace` to change).
3. Checks the cluster is not already assigned to a different seat.
4. Resolves the student username from the credential profile template.
5. Appends the assignment to `config/assignments.yaml`.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Seat assigned. |
| `1` | Validation failed (seat already assigned, cluster not found, etc.). |

**Examples**:

```bash
# Assign seat 12 to cluster seat-12
mas-world --env event seat assign --seat 12 --cluster seat-12
```

---

### `mas-world seat replace`

Replace a seat's cluster with a different cluster. The operation is
transactional: the old cluster is quarantined and the new assignment is
created atomically.

**Usage**:

```bash
mas-world --env <environment> seat replace --seat <n> --cluster <id>
```

**Options**:

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--seat` | `int` | yes | Seat number whose cluster is being replaced. |
| `--cluster` | `str` | yes | Replacement cluster ID. |

**Behavior**:

1. Validates the replacement cluster exists and is enabled.
2. Finds the current active assignment for the seat.
3. Marks the current cluster's assignment as `quarantined`.
4. Creates a new `assigned` entry for the seat with the replacement cluster.
5. Preserves the original username and credential profile.
6. Saves both changes to `config/assignments.yaml` in a single write.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Replacement completed. |
| `1` | Seat has no active assignment, or replacement cluster is invalid. |

**Examples**:

```bash
# Replace seat 12's failed cluster with a spare
mas-world --env event seat replace --seat 12 --cluster spare-02
```

---

### `mas-world seat unassign`

Remove the active assignment for a seat. The assignment status changes from
`assigned` to `unassigned`.

**Usage**:

```bash
mas-world --env <environment> seat unassign --seat <n>
```

**Options**:

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--seat` | `int` | yes | Seat number to unassign. |

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Seat unassigned. |
| `1` | No active assignment found for the seat. |

**Examples**:

```bash
mas-world --env event seat unassign --seat 12
```

---

### `mas-world seat show`

Display details for a seat assignment, including current assignment, endpoint
URLs, and assignment history.

**Usage**:

```bash
mas-world --env <environment> seat show --seat <n>
```

**Options**:

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--seat` | `int` | yes | Seat number to display. |

**Behavior**:

Displays:

- Current assignment status, cluster ID, username, and credential profile.
- Endpoint URLs (console, Maximo, Showroom, logging) from the cluster
  inventory.
- Historical entries (quarantined or unassigned previous clusters).

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Seat found and displayed. |
| `1` | No assignment records for the seat. |

**Examples**:

```bash
mas-world --env event seat show --seat 12
```

---

### `mas-world seat export-map`

Export the full seat assignment map for all active assignments.

**Usage**:

```bash
mas-world --env <environment> seat export-map [--format json|csv|markdown]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | `json` / `csv` / `markdown` | `json` | Output format. |

**Behavior**:

Exports all assignments with status `assigned`, sorted by seat number.
Includes: seat number, cluster ID, student username, credential profile,
and status.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Export completed. |
| `1` | No assignments found. |

**Examples**:

```bash
# Export as CSV for spreadsheet import
mas-world --env event seat export-map --format csv > seats.csv

# Export as Markdown for documentation
mas-world --env event seat export-map --format markdown

# Export as JSON for automation
mas-world --env event seat export-map --format json > seats.json
```

---

## `exercise` -- Exercise Management

### `mas-world exercise reset`

Reset an exercise module to its initial state on a specific cluster.

**Usage**:

```bash
mas-world --env <environment> exercise reset <cluster_id> --module <name>
```

**Arguments**:

| Argument | Required | Description |
|----------|----------|-------------|
| `cluster_id` | yes | Cluster ID where the exercise should be reset. |

**Options**:

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--module` | one of: `navigation`, `acm`, `updates`, `observability`, `identity` | yes | The exercise module to reset. |

**Behavior**:

1. Validates the cluster exists and is enabled.
2. Searches for the reset playbook in two locations:
   - `showroom/runtime-automation/<module>/reset.yml` (preferred)
   - `playbooks/reset-exercises.yml` (fallback, with `module` variable)
3. Executes the playbook with cluster context.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Exercise reset completed. |
| `1` | Reset failed, cluster not found, or no reset playbook available. |

**Examples**:

```bash
# Reset the observability exercise on seat-01
mas-world --env event exercise reset seat-01 --module observability

# Reset the identity exercise
mas-world --env event exercise reset seat-01 --module identity
```

---

## `report` -- Reporting

### `mas-world report fleet-status`

Display a fleet status dashboard showing cluster inventory, assignment
status, and spare availability.

**Usage**:

```bash
mas-world --env <environment> report fleet-status [--format text|json|markdown]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | `text` / `json` / `markdown` | `text` | Output format. |

**Behavior**:

Aggregates data from the cluster inventory and assignment file to produce:

- Total, enabled, and disabled cluster counts.
- Clusters by purpose (attendee, spare, facilitator).
- Assignment status (assigned, unassigned, quarantined).
- Spare cluster availability.
- Expected fleet counts from configuration.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Report generated. |
| `1` | Failed to load configuration. |

**Examples**:

```bash
# Text dashboard for the terminal
mas-world --env event report fleet-status

# JSON for monitoring integration
mas-world --env event report fleet-status --format json

# Markdown for runbook
mas-world --env event report fleet-status --format markdown
```

Sample text output:

```text
Fleet Status Dashboard -- event
Generated: 2026-08-16T18:00:00+00:00
=============================================

  Cluster inventory:
    Total:      56
    Enabled:    56
    Disabled:   0

  By purpose:
    Attendee        50
    Facilitator      1
    Spare            5

  Assignment status:
    Assigned:     48
    Unassigned:    2
    Quarantined:   0

  Spare clusters:
    Total:      5
    Available:  5

  Expected counts (from config):
    Attendee:    50
    Spare:       5
    Facilitator: 1
```

---

### `mas-world report seat-report`

Generate a comprehensive seat assignment report with endpoint details.

**Usage**:

```bash
mas-world --env <environment> report seat-report [--format text|json|markdown]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | `text` / `json` / `markdown` | `text` | Output format. |

**Behavior**:

Produces a report covering:

- Active assignments sorted by seat number with cluster ID, username,
  profile, and status.
- Endpoint URLs (console, Maximo, Showroom) for each assigned cluster.
- Quarantined clusters listed separately.
- Unassigned seats.
- Generation timestamp and environment.

**Exit codes**:

| Code | Meaning |
|------|---------|
| `0` | Report generated. |
| `1` | Failed to load configuration. |

**Examples**:

```bash
# Generate text report
mas-world --env event report seat-report

# Generate JSON report for processing
mas-world --env event report seat-report --format json > seat-report.json
```

---

## Exit Code Summary

All commands follow a consistent exit code convention:

| Code | Meaning |
|------|---------|
| `0` | Success. |
| `1` | Failure (validation error, execution error, or no results found). |
| `127` | `ansible-playbook` not found on `PATH`. |

---

## Common Workflows

### Pre-event preparation

```bash
# 1. Validate configuration
mas-world --env event config validate

# 2. Review effective configuration
mas-world --env event config render

# 3. Prepare the full fleet
mas-world --env event fleet prepare

# 4. Validate all clusters
mas-world --env event fleet validate --format json

# 5. Create student accounts
mas-world --env event student create

# 6. Validate student access
mas-world --env event student validate

# 7. Assign seats
mas-world --env event seat assign --seat 1 --cluster seat-01
# ... repeat for all seats

# 8. Rotate credentials
mas-world --env event student rotate

# 9. Generate access cards
mas-world --env event student export-cards --format html > access-cards.html

# 10. Final fleet status
mas-world --env event report fleet-status
```

### Day-of-event operations

```bash
# Revalidate the fleet
mas-world --env event fleet validate

# Check fleet status
mas-world --env event report fleet-status

# Replace a failed cluster
mas-world --env event seat replace --seat 12 --cluster spare-01

# Reset an exercise for an attendee
mas-world --env event exercise reset seat-12 --module observability

# Rotate a compromised credential
mas-world --env event student rotate --seat 7

# Disable a lost account
mas-world --env event student disable --seat 7
```

### Post-event teardown

```bash
# Disable all student accounts
mas-world --env event student disable

# Export final reports
mas-world --env event report seat-report --format json > final-seat-report.json
mas-world --env event report fleet-status --format json > final-fleet-status.json

# Delete student accounts
mas-world --env event student delete
```
