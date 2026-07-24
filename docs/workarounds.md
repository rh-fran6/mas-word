# Workarounds

Known workarounds for current limitations and edge cases.

> **Last updated:** 2026-07-20

---

## WA-001: Partial Fleet Failure Recovery

**Problem:** Some clusters fail to provision while others succeed (e.g., one AWS account has insufficient quota).

**Workaround:** Fix the underlying issue (quota, credentials, subnet), then re-run `make provision`. The `rosa create cluster` command is idempotent — it skips already-existing clusters and only creates the missing ones.

---

## WA-002: Async Job Timeout on Slow Accounts

**Problem:** `rosa create cluster` CLI invocation times out (default 300s) before returning the job ID, even though the cluster is being created in the background.

**Workaround:** Increase timeout values in `group_vars/all/rosa_defaults.yml`:
```yaml
rosa_create_async_timeout: 600   # 10 minutes
rosa_create_async_retries: 120   # More retries for polling
```

---

## WA-003: MachinePool Already Exists Error

**Problem:** Re-running `make provision` on an already-provisioned fleet causes `rosa create machinepool` to fail with "machinepool already exists."

**Workaround:** This is cosmetic — the machinepool was already created on the first run. The error doesn't affect cluster functionality. For cleaner runs, add `failed_when: false` to the machinepool task or check for existing machinepools before creating.

---

## WA-004: Destroy Fails for Already-Deleted Clusters

**Problem:** Running `make destroy` when some clusters have already been manually deleted causes `rosa describe cluster` to return errors.

**Workaround:** The destroy playbook handles this gracefully — clusters not found by `rosa describe` are skipped (they're excluded from `cluster_id_map`). No action needed.

---

## WA-005: Credential Template Generation for Non-Default Topology

**Problem:** The `generate-credentials-template.sh` script requires manually passing counts if your topology differs from defaults.

**Workaround:** Pass explicit arguments:
```bash
./scripts/generate-credentials-template.sh myprefix 1 2 20
# Generates template for 1 facilitator, 2 hubs, 20 seats
```

---

## WA-006: Ansible Verbose Mode Leaks Credentials

**Problem:** Running with `-vvv` may expose interpolated credential values despite `no_log: true`.

**Workaround:** Never use verbose mode (`-v`, `-vv`, `-vvv`) in environments where logs may be captured or shared. For debugging, use `make status` or `rosa describe cluster` directly instead of verbose playbook runs.

---

## WA-007: Partial `make setup-infra` Failure Recovery

**Problem:** `make setup-infra` partially fails due to API throttling or a transient network error, leaving some infrastructure resources created and others not.

**Workaround:** Simply re-run `make setup-infra`. All infrastructure tasks are idempotent — each task checks whether the resource already exists (by tag) before attempting to create it. Already-created resources will be discovered and skipped.

---

## WA-008: Lost or Corrupted `infra_state.yml`

**Problem:** `infra_state.yml` is accidentally deleted or corrupted, causing subsequent playbook runs to lose track of previously created infrastructure.

**Workaround:** Re-run `make setup-infra`. The role discovers existing resources by their tags (`Name` and `Project` tags) and regenerates the state file. No infrastructure is duplicated because creation is guarded by existence checks.


---

## Phase 2: MAS World Application Layer
