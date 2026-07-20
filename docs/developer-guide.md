# Developer Guide — MAS World 2026

**Status**: DRAFT — Phase 1
**Date**: 2026-07-19

---

## 1. Repository Structure

This project is organized as a monorepo with six logical sub-projects:

```text
mas-world-2026/
├── CLAUDE.md                          # Project instructions
├── prompt.md                          # Master specification
├── .pre-commit-config.yaml            # Pre-commit hooks
├── .yamllint.yml                      # YAML linter config
├── .ansible-lint.yml                  # Ansible linter config
├── .gitleaks.toml                     # Secret scanning rules
├── .github/workflows/ci.yml          # CI pipeline (6 jobs)
├── docs/                             # Project documentation
│
├── mas-world-2026-automation/         # Ansible collection + Python CLI
│   ├── ansible.cfg
│   ├── galaxy.yml                     # Collection: masworld.automation
│   ├── pyproject.toml                 # Python project config
│   ├── Makefile                       # Build targets
│   ├── requirements.yml               # Ansible collection dependencies
│   ├── cli/                           # Python CLI (Click)
│   │   ├── main.py                    # Entry point (mas-world command)
│   │   ├── commands/                  # Command groups
│   │   ├── config/                    # Config loader, schema, validator
│   │   ├── secrets/                   # Secret provider abstraction
│   │   ├── inventory/
│   │   ├── orchestration/
│   │   └── reporting/
│   ├── config/                        # Configuration files
│   │   ├── defaults.yaml
│   │   ├── event.yaml
│   │   ├── clusters.yaml
│   │   ├── credentials.yaml
│   │   ├── components.yaml
│   │   ├── aws.yaml
│   │   ├── showroom.yaml
│   │   └── environments/
│   │       ├── development.yaml
│   │       ├── rehearsal.yaml
│   │       └── event.yaml
│   ├── playbooks/                     # Ansible playbooks
│   ├── roles/                         # 17 Ansible roles
│   ├── plugins/                       # Ansible plugins and filters
│   ├── tests/                         # Test suite
│   │   ├── conftest.py
│   │   └── unit/
│   ├── schemas/
│   ├── scripts/
│   └── molecule/
│
├── mas-world-2026-showroom/           # Antora/AsciiDoc workshop content
│   ├── site.yml
│   ├── ui-config.yml
│   ├── content/
│   │   └── modules/ROOT/
│   │       ├── nav.adoc
│   │       └── pages/                 # Workshop modules (01- through 99-)
│   └── runtime-automation/            # Per-module validate/solve/reset
│       ├── readiness/
│       ├── navigation/
│       ├── acm/
│       ├── updates/
│       ├── observability/
│       └── identity/
│
├── mas-world-2026-acm/                # ACM manifests and policies
│   ├── demo-assets/
│   ├── gitops/
│   ├── labels/
│   ├── managedclustersets/
│   ├── placements/
│   ├── policies/
│   └── reports/
│
├── mas-world-2026-agnosticv/          # RHDP catalog configuration
│   ├── catalog/
│   ├── vars/
│   ├── workloads/
│   ├── schemas/
│   ├── access-data/
│   └── docs/
│
├── mas-world-2026-public-content/     # Sanitized attendee examples
│   ├── architecture/
│   ├── identity/
│   ├── logging/
│   ├── mas-edge/
│   ├── operators/
│   ├── production-guidance/
│   └── troubleshooting/
│
└── mas-world-2026-operations/         # Operational tooling
    ├── checklists/
    ├── cost-reporting/
    ├── fleet-dashboard/
    ├── incident-templates/
    ├── repair-procedures/
    ├── runbooks/
    └── seat-assignment/
```

---

## 2. Development Environment Setup

### Prerequisites

See `docs/installation-guide.md` for basic prerequisites (Python, Ansible, OpenShift CLI). This section covers additional developer tooling.

**Required versions:**

- Python >= 3.11
- Ansible Core >= 2.17.0, < 2.18.0
- Node.js >= 20 (for Showroom/Antora builds)

### Initial setup

Clone the repository and install all dependencies:

```bash
# Create and activate a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install the CLI and all dev dependencies
pip install -e mas-world-2026-automation[dev]

# Install Ansible collection dependencies
ansible-galaxy collection install -r mas-world-2026-automation/requirements.yml

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Verify the CLI is available
mas-world --help
```

### IDE setup

**VS Code (recommended):**

Install these extensions:

- Python (ms-python.python)
- Ruff (charliermarsh.ruff)
- Ansible (redhat.ansible)
- YAML (redhat.vscode-yaml)
- AsciiDoc (asciidoctor.asciidoctor-vscode)
- ShellCheck (timonwong.shellcheck)

Suggested workspace settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "yaml.schemas": {
    "https://json.schemastore.org/ansible-playbook": "mas-world-2026-automation/playbooks/*.yml",
    "https://json.schemastore.org/ansible-role-2.9": "mas-world-2026-automation/roles/*/tasks/*.yml"
  },
  "ansible.python.interpreterPath": "${workspaceFolder}/.venv/bin/python"
}
```

**PyCharm:**

- Set the project interpreter to `.venv/bin/python`.
- Mark `mas-world-2026-automation` as a sources root.
- Enable the Ruff plugin for formatting and linting.

---

## 3. Branch Strategy

| Branch | Purpose | Protection |
|--------|---------|------------|
| `main` | Stable, release-ready code | Protected: PRs required, CI must pass |
| `feature/<name>` | New features and enhancements | Developer branches |
| `fix/<name>` | Bug fixes | Developer branches |
| `release/<version>` | Release candidates | Created from `main` when cutting a release |

**Rules:**

- All changes go through pull requests. Direct pushes to `main` are blocked.
- CI must pass before merging.
- Use descriptive branch names: `feature/logging-exercise-reset`, `fix/seat-assignment-rollback`.
- Keep PRs focused. Prefer small, reviewable changes over large omnibus PRs.
- Rebase feature branches on `main` before opening a PR to keep history clean.

---

## 4. Pre-commit Hooks

Pre-commit hooks run automatically on every `git commit`. They are defined in `.pre-commit-config.yaml` at the repository root.

**Installed hooks:**

| Hook | Source | Purpose |
|------|--------|---------|
| `trailing-whitespace` | pre-commit-hooks v5.0.0 | Remove trailing whitespace |
| `end-of-file-fixer` | pre-commit-hooks v5.0.0 | Ensure files end with a newline |
| `check-yaml` | pre-commit-hooks v5.0.0 | Validate YAML syntax (multi-doc allowed) |
| `check-json` | pre-commit-hooks v5.0.0 | Validate JSON syntax |
| `check-merge-conflict` | pre-commit-hooks v5.0.0 | Detect merge conflict markers |
| `check-added-large-files` | pre-commit-hooks v5.0.0 | Block files over 500 KB |
| `no-commit-to-branch` | pre-commit-hooks v5.0.0 | Block direct commits to `main`/`master` |
| `gitleaks` | gitleaks v8.21.2 | Scan for secrets and credentials |
| `yamllint` | yamllint v1.35.1 | Lint YAML files (config: `.yamllint.yml`) |
| `ansible-lint` | ansible-lint v24.12.2 | Lint playbooks and roles (config: `.ansible-lint.yml`) |
| `ruff` | ruff v0.8.6 | Python linting with auto-fix |
| `ruff-format` | ruff v0.8.6 | Python formatting |
| `shellcheck` | shellcheck v0.10.0.1 | Lint shell scripts |

**Setup and usage:**

```bash
# Install hooks (one-time, after cloning)
pre-commit install

# Run all hooks against staged files (happens automatically on commit)
pre-commit run

# Run all hooks against all files
pre-commit run --all-files

# Skip hooks in an emergency (strongly discouraged)
git commit --no-verify -m "emergency fix"
```

If a hook fails, fix the issue before committing. Do not habitually skip hooks.

---

## 5. Running Tests

### Unit tests

The test suite is under `mas-world-2026-automation/tests/unit/` and uses pytest. There are currently 39 test functions across three test modules:

- `test_config_loader.py` — configuration loading and precedence
- `test_config_validation.py` — schema validation and error detection
- `test_secret_provider.py` — secret provider abstraction and redaction

```bash
# Run all unit tests (from the automation directory)
cd mas-world-2026-automation
make test

# Or directly with pytest
pytest tests/unit/ -v

# Run a specific test file
pytest tests/unit/test_config_validation.py -v

# Run a specific test by name
pytest tests/unit/ -k "test_duplicate_cluster_id" -v

# Run with coverage
pytest tests/unit/ --cov=cli --cov-report=term-missing
```

### Linting

```bash
# Run all linters (from the automation directory)
cd mas-world-2026-automation
make lint
```

This runs:
1. `ansible-lint` on playbooks and roles
2. `yamllint` on YAML files across playbooks, roles, ACM manifests, and config
3. `ruff check` on Python code in `cli/`, `plugins/`, and `tests/`

To run linters individually:

```bash
# Ansible lint only
ansible-lint playbooks/ roles/

# YAML lint only
yamllint -c .yamllint.yml playbooks/ roles/ acm/ config/

# Python lint only
python -m ruff check cli/ plugins/ tests/

# Python format check
python -m ruff format --check cli/ plugins/ tests/

# Type checking
python -m mypy cli/ plugins/ --strict
```

### Configuration validation

```bash
# Validate configuration schemas via the CLI
mas-world --env development config validate

# Or via Make
cd mas-world-2026-automation
make validate ENVIRONMENT=development
```

### Showroom build validation

```bash
# Build the Antora site to check for AsciiDoc errors
cd mas-world-2026-showroom
npx @antora/cli@3.1 --fetch site.yml
```

---

## 6. Adding a New Ansible Role

Roles live in `mas-world-2026-automation/roles/`. Each role follows a standard directory structure.

### Scaffold a new role

```bash
cd mas-world-2026-automation/roles
mkdir -p my_new_role/{defaults,tasks,meta,templates}
```

Create the required files:

**`roles/my_new_role/meta/main.yml`**

```yaml
galaxy_info:
  role_name: my_new_role
  author: MAS World 2026 Team
  description: Brief description of what the role does
  license: Apache-2.0
  min_ansible_version: "2.17"
  platforms:
    - name: GenericLinux
      versions:
        - all
dependencies: []
```

**`roles/my_new_role/defaults/main.yml`**

```yaml
# All role variables with sensible defaults.
# Prefix variables with the role name to avoid collisions.
my_new_role_enabled: true
my_new_role_namespace: "masworld-system"
```

**`roles/my_new_role/tasks/main.yml`**

```yaml
- name: Skip role when disabled
  ansible.builtin.meta: end_play
  when: not my_new_role_enabled | default(true)

- name: Check current state
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Namespace
    name: "{{ my_new_role_namespace }}"
  register: _my_new_role_ns

- name: Create namespace when absent
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: Namespace
      metadata:
        name: "{{ my_new_role_namespace }}"
  when: _my_new_role_ns.resources | length == 0

- name: Wait for namespace to be active
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Namespace
    name: "{{ my_new_role_namespace }}"
  register: _my_new_role_ns_status
  until:
    - _my_new_role_ns_status.resources | length > 0
    - _my_new_role_ns_status.resources[0].status.phase == "Active"
  retries: 10
  delay: 5
```

### Idempotency patterns

Every role must be safe to run multiple times. Follow these patterns:

1. **Check before create.** Use `k8s_info` to check whether a resource exists before creating it. Apply only when the resource is absent or its spec has drifted.

2. **Wait for readiness.** After creating or modifying a resource, use `until` loops to wait for the resource to reach a ready state before proceeding.

3. **Use `state: present`.** Prefer `state: present` over deletion and re-creation. Let Kubernetes reconcile the desired state.

4. **Handle disabled components.** Check the `<role>_enabled` variable at the top of the role and exit early with `ansible.builtin.meta: end_play` when the component is disabled.

5. **Protect secrets.** Add `no_log: true` to any task that handles credentials, tokens, passwords, or secret references.

```yaml
- name: Create object storage secret
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: Secret
      metadata:
        name: loki-s3-credentials
        namespace: openshift-logging
      type: Opaque
      stringData:
        access_key_id: "{{ s3_access_key }}"
        access_key_secret: "{{ s3_secret_key }}"
  no_log: true
```

### Register the role with ansible-lint

If the role is not yet wired into playbooks, add it to the `mock_roles` list in `.ansible-lint.yml` so ansible-lint does not report it as missing.

### Add a molecule test scenario

```bash
mkdir -p molecule/my_new_role
```

Create `molecule/my_new_role/molecule.yml` and `converge.yml` following the existing molecule patterns.

---

## 7. Adding a CLI Command

The CLI uses [Click](https://click.palletsprojects.com/) and is structured into command groups under `mas-world-2026-automation/cli/commands/`.

### Existing command groups

| Group | File | Description |
|-------|------|-------------|
| `config` | `commands/config.py` | Configuration validation, rendering, diffing |
| `cluster` | `commands/cluster.py` | Single-cluster prepare, validate, repair |
| `fleet` | `commands/fleet.py` | Fleet-wide prepare, validate |
| `seat` | `commands/seats.py` | Seat assignment, replacement, export |
| `student` | `commands/students.py` | Student account lifecycle |
| `exercise` | `commands/exercises.py` | Exercise reset |
| `report` | `commands/reports.py` | Fleet and cluster reports |

### Adding a command to an existing group

Open the relevant file in `cli/commands/` and add a new Click command:

```python
@your_group.command("new-subcommand")
@click.option("--cluster", required=True, help="Target cluster ID.")
@click.pass_context
def new_subcommand(ctx: click.Context, cluster: str) -> None:
    """One-line description of the command."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]

    # Load configuration using the standard loader
    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    # Validate before modifying anything
    validator = ConfigValidator()
    errors = validator.validate(config, cluster_id=cluster)
    if errors:
        click.secho("Configuration validation failed.", fg="red", err=True)
        sys.exit(1)

    # Resolve secrets at runtime, never cache to disk
    # Use secret:// references from config, not hard-coded values

    # Perform the operation
    click.secho(f"Operation completed for cluster {cluster}.", fg="green")
```

### Adding a new command group

1. Create `cli/commands/my_group.py` with a `@click.group()` function.
2. Register it in `cli/main.py`:

```python
from cli.commands.my_group import my_group
cli.add_command(my_group, "my-group")
```

### Patterns to follow

- **Always load config through `ConfigLoader`.** Do not read YAML files directly.
- **Always validate before mutating.** Run `ConfigValidator.validate()` before modifying cluster state.
- **Resolve secrets through the provider abstraction.** Use `cli/secrets/provider.py`, never read secrets directly from files or environment variables.
- **Use `click.secho` for user output.** Use `fg="green"` for success, `fg="red"` for errors, `fg="yellow"` for warnings.
- **Exit with appropriate codes.** `sys.exit(0)` for success, `sys.exit(1)` for errors.
- **Never print secret values.** Redact credentials in all output.

### Add a unit test

Create or extend a test file in `tests/unit/`:

```python
"""Tests for the new subcommand."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from cli.main import cli


def test_new_subcommand_validates_config() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--env", "development", "my-group", "new-subcommand", "--cluster", "seat-01"])
    # Assert expected behavior
    assert result.exit_code == 0
```

---

## 8. Showroom Content Conventions

Workshop content lives in `mas-world-2026-showroom/` and uses the RHDP Showroom framework built on Antora with AsciiDoc.

### Module structure

Every workshop module follows the **Know, Do, Check** pattern:

1. **Know** — Explain the concept: what it is, why it matters, what the attendee will accomplish.
2. **Do** — Step-by-step hands-on instructions with copy-paste-safe commands.
3. **Check** — Validate the result. Provide expected output, validation commands, and a solve/reset path.

### File location

Module pages live in:

```text
mas-world-2026-showroom/content/modules/ROOT/pages/
```

Files are numbered for ordering: `01-access-readiness.adoc`, `02-navigation-search.adoc`, etc. Navigation is defined in `nav.adoc`.

### Writing guidelines

**Use Antora attributes for all environment-specific values.** Never hard-code cluster URLs, usernames, or namespace names:

```asciidoc
Navigate to the OpenShift console at {openshift_console_url}.

Log in with username `{student_username}` and password `{student_password}`.
```

**Mark executable commands with `role="execute"`.** This enables click-to-run in the browser terminal:

```asciidoc
[source,bash,role="execute"]
----
oc get pods -n openshift-logging
----
```

**Show expected output.** After every command, show what the attendee should see:

```asciidoc
.Expected output
[source,text]
----
NAME                           READY   STATUS    RESTARTS   AGE
collector-abcde                1/1     Running   0          2h
loki-ingester-0                1/1     Running   0          2h
----
```

**Include validation steps.** Each exercise must end with a way to verify success:

```asciidoc
== Check your work

Run the following command to verify the ClusterLogForwarder is active:

[source,bash,role="execute"]
----
oc get clusterlogforwarder instance -n openshift-logging -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
----

Expected result: `True`
```

### Runtime automation

Each module has automation scripts in `runtime-automation/<module>/`:

| File | Purpose |
|------|---------|
| `prepare.yml` | Pre-stage resources needed for the exercise |
| `validate.yml` | Check whether the attendee completed the exercise correctly |
| `solve.yml` | Automatically complete the exercise (for attendees who are stuck) |
| `reset.yml` | Reset the exercise to its initial state (for retry) |

Not every module needs all four files. At minimum, `validate.yml` is required for every module.

Runtime automation must:

- Run with minimal permissions (student-level RBAC, not cluster-admin).
- Produce attendee-friendly output (clear pass/fail messages, no stack traces).
- Never reveal secret values, admin credentials, or internal metadata in output.

---

## 9. Code Style

### Python

- **Formatter and linter:** Ruff (configured in `pyproject.toml`)
- **Line length:** 100 characters
- **Target version:** Python 3.11
- **Type hints:** Required on all function signatures. Mypy strict mode is enabled.
- **Lint rules:** E, F, I (isort), N (naming), W, UP (pyupgrade), S (bandit security), B (bugbear), A (builtins), C4 (comprehensions), SIM (simplify)
- **Imports:** Sorted by ruff/isort. Standard library first, then third-party, then local.

Example:

```python
def resolve_seat_username(seat_number: int, template: str) -> str:
    """Generate a username from the seat number and template."""
    padded = str(seat_number).zfill(2)
    return template.replace("{{ seat_number | pad(2) }}", padded)
```

### Ansible

- **Use fully qualified collection names (FQCN).** Write `kubernetes.core.k8s`, not `k8s`. Write `ansible.builtin.debug`, not `debug`.
- **Add `no_log: true`** on every task that handles secrets, credentials, tokens, or passwords.
- **Name every task.** Unnamed tasks are flagged by ansible-lint.
- **Prefix role variables** with the role name to prevent collisions.
- **Follow the production profile** as configured in `.ansible-lint.yml`.

### YAML

- **Indentation:** 2 spaces, consistent sequence indentation.
- **Line length:** 200 characters maximum (configured in `.yamllint.yml`).
- **No implicit or explicit octals** (e.g., write `"0644"` as a string, not `0644`).
- **Document start markers (`---`)** are not required (disabled in yamllint config).
- **Truthy values:** Only `true`, `false`, `yes`, `no` are allowed.

### Shell scripts

- All `.sh` files are validated by ShellCheck.
- Use `set -euo pipefail` at the top of every script.
- Quote all variable expansions.

---

## 10. Security Rules

These rules are mandatory. Violations will be caught by pre-commit hooks and CI.

### Never commit credentials

- No passwords, tokens, API keys, entitlement keys, private keys, or kubeconfigs in source.
- Use `secret://` references in configuration files. Example: `secret://mas-world/clusters/seat-01/admin-kubeconfig`.
- Use placeholder values in examples: `PLACEHOLDER`, `UNSET`, or Jinja2 template variables (`{{ variable }}`).
- The gitleaks hook (`.gitleaks.toml`) scans for AWS access keys, generic secret patterns, private key headers, and IBM entitlement key patterns.

### Protect secrets in Ansible

- Add `no_log: true` on any task that handles credential values.
- Never use `debug` to print secret variables.
- `ansible.cfg` sets `no_log = true` as the global default; do not override this to `false` in production tasks.

### Protect secrets in Python

- Resolve secrets through the provider abstraction (`cli/secrets/provider.py`).
- Never write secrets to disk, logs, or stdout.
- The `ConfigLoader.render_effective()` method has a `redact_secrets=True` parameter. Always use it for any user-facing output.

### Protect secrets in output

- CI logs must not contain secret values.
- Showroom validation output must not reveal admin credentials.
- Generated reports, access cards, and exports must contain only the credentials intended for the specific attendee.
- Support bundles and diagnostics must be scrubbed of secrets.

### Access control

- Attendee accounts must never be cluster-admin.
- Attendee accounts must not have ACM administrative access.
- Attendee accounts must not be able to access other attendees' namespaces.
- These constraints are enforced by RBAC configuration and verified by negative security tests.

---

## 11. CI Pipeline Overview

The CI pipeline is defined in `.github/workflows/ci.yml` and runs on pushes to `main` and on all pull requests. It consists of six jobs:

```text
                    ┌───────────────────┐
                    │  detect-changes   │
                    │ (path filtering)  │
                    └────────┬──────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                      │
       v                     v                      v
┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ lint-and-    │   │  validate-       │   │  validate-       │
│ validate     │   │  showroom        │   │  manifests       │
│              │   │ (if showroom     │   │ (PRs only,       │
│ yamllint     │   │  files changed)  │   │  kubeconform)    │
│ ansible-lint │   │  Antora build    │   └──────────────────┘
│ ruff check   │   │  nav.adoc check  │
│ ruff format  │   └──────────────────┘
│ shellcheck   │
│ YAML syntax  │
└──────────────┘

┌──────────────┐   ┌──────────────────┐
│ unit-tests   │   │ secret-scan      │
│              │   │ (PRs only,       │
│ pytest       │   │  gitleaks)       │
│ JUnit report │   └──────────────────┘
└──────────────┘

┌──────────────┐
│ docs-links   │
│ (if .md      │
│  files       │
│  changed)    │
└──────────────┘
```

| Job | Trigger | What it does |
|-----|---------|--------------|
| **lint-and-validate** | All pushes and PRs | yamllint, ansible-lint, ruff, shellcheck, YAML syntax check |
| **secret-scan** | PRs only | Gitleaks scan with `.gitleaks.toml` rules |
| **unit-tests** | All pushes and PRs | pytest against `tests/unit/`, uploads JUnit XML artifact |
| **validate-manifests** | PRs only | kubeconform validation of ACM YAML manifests |
| **validate-showroom** | PRs changing `mas-world-2026-showroom/` | Antora build, nav.adoc cross-reference check |
| **docs-links** | PRs changing `*.md` files | Checks for broken relative links in Markdown |

**CI must pass before any PR can be merged to `main`.**

To reproduce CI checks locally:

```bash
# Run the same linting CI does
cd mas-world-2026-automation
make lint

# Run unit tests
make test

# Build Showroom
cd ../mas-world-2026-showroom
npx @antora/cli@3.1 --fetch site.yml

# Run gitleaks
gitleaks detect --config .gitleaks.toml --source .
```

---

## 12. Making a Release

### Version strategy

- Use semantic versioning: `MAJOR.MINOR.PATCH`.
- The version is defined in two places:
  - `mas-world-2026-automation/pyproject.toml` (`version` field)
  - `mas-world-2026-automation/galaxy.yml` (`version` field)
- Both must be updated together.

### Release checklist

1. **Ensure `main` is green.** All CI jobs must pass.

2. **Update version numbers.**

   Edit `pyproject.toml` and `galaxy.yml` to reflect the new version.

3. **Pin all component versions.**

   Verify that `config/components.yaml` specifies exact, pinned versions for:
   - MAS Core and Maximo Manage
   - OpenShift Logging Operator
   - Loki Operator
   - All Ansible collection dependencies (`requirements.yml`)
   - Container images (use digest or immutable tag, never `latest`)

4. **Run the full validation suite.**

   ```bash
   # Lint
   make lint

   # Unit tests
   make test

   # Configuration validation for all environments
   mas-world --env development config validate
   mas-world --env rehearsal config validate
   mas-world --env event config validate

   # Showroom build
   cd mas-world-2026-showroom && npx @antora/cli@3.1 --fetch site.yml

   # Secret scan
   gitleaks detect --config .gitleaks.toml --source .
   ```

5. **Create the release commit and tag.**

   ```bash
   git add -A
   git commit -m "Release v0.2.0: pin versions for rehearsal"
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin main --tags
   ```

6. **Generate the bill of materials.**

   Record all pinned versions, collection dependencies, container image digests, and Ansible collection versions in `docs/bill-of-materials.md`.

7. **Event release gate.**

   The event release (`event` environment) requires:
   - All configuration validations pass.
   - All unit and integration tests pass.
   - Full rehearsal completed and documented.
   - All cluster readiness checks pass.
   - Student credentials rotated.
   - Immutable tags or commit SHAs for all deployable artifacts.
   - Explicit approval from all three facilitators.

### What must never be in a release

- Unpinned versions (`latest`, floating branches, open-ended operator channels)
- Embedded credentials, tokens, or entitlement keys
- Unresolved critical Showroom verification findings
- Unresolved critical AgnosticV validation failures
- Failing mandatory tests

---

## Appendix: Key File Reference

| File | Purpose |
|------|---------|
| `mas-world-2026-automation/pyproject.toml` | Python project metadata, dependencies, tool config |
| `mas-world-2026-automation/galaxy.yml` | Ansible collection metadata (namespace: `masworld`, name: `automation`) |
| `mas-world-2026-automation/ansible.cfg` | Ansible runtime configuration |
| `mas-world-2026-automation/Makefile` | Build targets: `lint`, `test`, `prepare-cluster`, `prepare-fleet`, `validate`, etc. |
| `mas-world-2026-automation/requirements.yml` | Ansible collection dependencies |
| `.pre-commit-config.yaml` | Pre-commit hook definitions |
| `.yamllint.yml` | YAML linter configuration |
| `.ansible-lint.yml` | Ansible linter configuration (production profile) |
| `.gitleaks.toml` | Secret scanning rules |
| `.github/workflows/ci.yml` | CI pipeline definition |
| `prompt.md` | Master project specification |
| `CLAUDE.md` | Project instructions and operating contract |
