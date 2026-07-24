# Spare Cluster Replacement Procedure -- MAS World 2026

**Status**: DRAFT
**Date**: 2026-07-19
**Audience**: Facilitators (Francis Anyaegbu, Ernie Steagall, Myles Vivian)
**Cross-references**:
- Cluster repair: `mas-world-2026-operations/repair-procedures/cluster-repair.md`
- Event runbook: `mas-world-2026-operations/runbooks/`
- Credential lifecycle: `docs/credential-lifecycle.md`
- Architecture: `docs/architecture.md`
- Configuration model: `docs/configuration-model.md`
- Seat assignment flow: `docs/architecture.md` (Section 11)
- Spare replacement flow: `docs/architecture.md` (Section 12)

---

## Overview

Spare replacement swaps a failed attendee cluster for a pre-validated spare
cluster. The operation is transactional: if any step fails, the system rolls
back to the original assignment rather than leaving the seat in an
inconsistent state.

**Estimated total time**: 3-5 minutes under normal conditions.

**Who can execute**: Francis Anyaegbu (lab owner), or any facilitator with
access to the `masworld` CLI and the configured secret provider.

---

## Pre-Replacement Checklist

Before initiating a replacement, confirm all of the following:

1. **The failure warrants replacement.** Review repair vs replace decision
   criteria in `cluster-repair.md`. Replacement consumes a finite spare
   resource.

2. **A spare cluster is available.**

   ```bash
   masworld report fleet-status
   ```

   Verify the output shows at least one spare cluster with status `READY`.
   Note the spare cluster ID (e.g., `spare-01`).

3. **The spare cluster has been validated recently.**

   ```bash
   masworld cluster validate --cluster <SPARE_CLUSTER_ID>
   ```

   All mandatory checks must show `PASS`. Do not use a spare that has not
   passed validation. If the spare fails validation, select a different spare
   or repair it first.

4. **You have identified the affected seat.**

   ```bash
   masworld seat show --seat <SEAT_NUMBER>
   ```

   Confirm the seat number, current cluster ID, and attendee username.

5. **You have access to the secret provider.** The replacement process
   retrieves and stores credentials. Verify secret provider connectivity:

   ```bash
   masworld config validate --env <ENVIRONMENT>
   ```

6. **During a live session only**: Notify the attendee that their environment
   is being replaced. Give them an estimated wait time of 3-5 minutes. Ask
   them to stop working temporarily to avoid data loss on the failed cluster.

---

## Replacement Procedure

### Step 1: Execute the Replacement Command

```bash
masworld seat replace --seat <SEAT_NUMBER> --cluster <SPARE_CLUSTER_ID>
```

Example:

```bash
masworld seat replace --seat 12 --cluster spare-02
```

This single command performs the full transactional replacement sequence
described below. Each sub-step is logged to the per-cluster log directory
and to structured JSON output.

### What Happens Automatically

The `masworld seat replace` command executes the following steps in order.
If any step fails, the command rolls back all completed steps and restores
the original assignment.

```text
Step 1/9: Validate spare cluster readiness
          - Runs masworld cluster validate --cluster <SPARE_CLUSTER_ID>
          - Aborts if any mandatory check fails

Step 2/9: Disable credentials on the failed cluster
          - Removes the student from htpasswd on the old cluster
          - Removes RoleBindings for the student on the old cluster
          - If the old cluster API is unreachable, this step is skipped
            (credentials are orphaned but the cluster will be quarantined)

Step 3/9: Create student credentials on the spare cluster
          - Generates or retrieves the student password from the secret
            provider (password is re-used if rotate_on_replace is false,
            regenerated if true)
          - Adds the student to htpasswd on the spare cluster
          - Creates the student namespace
          - Creates RoleBindings

Step 4/9: Update Showroom and endpoint data
          - Updates the Showroom ConfigMap on the spare cluster with:
            - New OpenShift console URL
            - New Maximo URL
            - New logging URL
            - Seat number and student username
          - Restarts Showroom pods to pick up new configuration

Step 5/9: Update the seat assignment inventory
          - Changes the cluster mapping for the seat from the old cluster
            to the spare cluster
          - Records the replacement timestamp and reason

Step 6/9: Regenerate access card
          - Generates a new access card for the seat with updated URLs
          - Stores the card for retrieval or printing

Step 7/9: Validate student access on the spare cluster
          - Tests student login via oc login
          - Tests OpenShift console access
          - Tests Maximo URL accessibility
          - Tests Showroom URL accessibility
          - Tests student namespace access
          - Tests student RBAC (positive and negative)

Step 8/9: Quarantine the failed cluster
          - Marks the old cluster status as QUARANTINED
          - Applies quarantine label in ACM
          - Removes the old cluster from assignable inventory
          - Preserves diagnostic data on the old cluster for later analysis

Step 9/9: Finalize
          - Marks the replacement as complete
          - Updates fleet status report
          - Logs the completed replacement with timestamp
```

### What Requires Manual Intervention

Under normal conditions, the entire replacement is automated. Manual
intervention is required only in these situations:

| Situation | Manual action required |
|-----------|----------------------|
| Spare cluster fails validation during replacement | Select a different spare or repair the spare first |
| Secret provider unreachable | Verify network and credentials for the secret provider |
| New access card needs physical delivery | Print and hand-deliver the updated access card to the attendee |
| Attendee has work in progress on the failed cluster | Inform the attendee that work on the old cluster is lost |
| Password was regenerated on replacement | Verbally give the attendee their new password or deliver the new access card |

---

## Validation After Replacement

After the automated replacement completes, run an independent validation:

```bash
masworld cluster validate --cluster <SPARE_CLUSTER_ID>
```

Expected output -- all checks must show `PASS`:

```text
openshift:               PASS
mas_core:                PASS
maximo_manage:           PASS
database:                PASS
logging_operator:        PASS
lokistack:               PASS
cluster_log_forwarder:   PASS
s3_write_read:           PASS
historical_log_query:    PASS
identity:                PASS
showroom:                PASS
runtime_automation:      PASS
student_authentication:  PASS
student_rbac:            PASS
mas_edge:                NOT_APPLICABLE (or PASS if enabled)
```

Additionally, verify the seat assignment is correct:

```bash
masworld seat show --seat <SEAT_NUMBER>
```

Expected output should show:

```text
Seat:     <SEAT_NUMBER>
Cluster:  <SPARE_CLUSTER_ID>
Username: user<SEAT_NUMBER>
Status:   assigned
```

Verify the attendee can log in and access their environment. Ask them to
confirm:

1. Showroom loads and shows correct content.
2. Terminal tab connects.
3. OpenShift console is accessible with their credentials.
4. Maximo UI loads.

---

## Updating Access Cards

If the replacement changed any URLs (which it always does, since the cluster
changed):

### Automated Access Card Regeneration

The `masworld seat replace` command automatically regenerates the access card
at step 6. To retrieve or regenerate it manually:

```bash
masworld student export-cards --seat <SEAT_NUMBER>
```

### Delivering the Updated Access Card

**During a live session**:

1. Retrieve the regenerated access card.
2. If the password did not change: Show the attendee the new URLs. The
   username and password remain the same.
3. If the password was regenerated: Deliver the new access card to the
   attendee. Do not read out the password aloud in the room.
4. If access cards were printed: Print a replacement card and hand it to the
   attendee. Collect and destroy the old card.

**Pre-event**:

1. Regenerate the full set of access cards after all replacements:

   ```bash
   masworld student export-cards
   ```

2. Verify no access card references the quarantined cluster.

---

## Communicating with the Affected Attendee

### During a Live Session

Use this communication sequence:

1. **Immediate notification** (when failure is detected):
   "We have detected an issue with your lab environment. We are switching you
   to a backup environment. This should take about 3-5 minutes. You can pause
   your current exercise and we will let you know when the new environment is
   ready."

2. **During replacement** (if the attendee asks):
   "The replacement is in progress. Your new environment is being set up with
   all the same capabilities. Your login credentials [will remain the same /
   will be updated -- check which applies]."

3. **After replacement** (when validation passes):
   "Your new environment is ready. [Hand over new access card or point to
   updated URLs.] You can continue from where you left off in the workshop.
   Any work you did on the previous environment will not carry over, but you
   can redo the steps from the current module."

4. **If the attendee is significantly behind due to the disruption**:
   Offer to run the solve automation for completed modules so they can catch
   up:

   ```bash
   masworld exercise reset --cluster <SPARE_CLUSTER_ID> --module <MODULE_NAME>
   ```

   This resets and optionally solves the exercise so the attendee can move
   forward.

### Pre-Event

No attendee communication is needed. Update the seat assignment inventory
and access cards.

---

## Quarantining the Failed Cluster

After a successful replacement, the failed cluster is automatically
quarantined. Quarantine means:

1. **Status set to QUARANTINED** in the cluster inventory.
2. **ACM label updated**: `readiness: quarantined` applied to the
   ManagedCluster resource on the ACM hub.
3. **Excluded from assignment**: The `masworld seat assign` command will
   reject any attempt to assign a seat to a quarantined cluster.
4. **Student credentials disabled** (if the old cluster API was reachable).
5. **Diagnostic data preserved**: Logs, events, and pod states are captured
   before quarantine for post-event analysis.

### Verifying Quarantine

```bash
masworld seat show --cluster <FAILED_CLUSTER_ID>
```

Expected output:

```text
Cluster:  <FAILED_CLUSTER_ID>
Status:   quarantined
Purpose:  attendee (quarantined)
Seat:     (unassigned)
```

Verify the quarantine label in ACM:

```bash
oc get managedcluster <FAILED_CLUSTER_ID> \
  -o jsonpath='{.metadata.labels.readiness}' \
  --kubeconfig PLACEHOLDER_HUB_KUBECONFIG
```

Expected: `quarantined`

### Post-Event Quarantined Cluster Handling

After the event, quarantined clusters should be:

1. Investigated for root cause (see diagnostic data captured during
   quarantine).
2. Repaired if reusable, or decommissioned if not.
3. Removed from ACM registration if decommissioned.
4. S3 buckets cleaned up per retention policy.
5. IAM credentials revoked.

---

## Post-Replacement Verification Checklist

Run through this checklist after every replacement to confirm nothing was
missed:

```text
[ ] masworld cluster validate --cluster <SPARE> shows all PASS
[ ] masworld seat show --seat <N> shows correct cluster mapping
[ ] Access card has been regenerated
[ ] Access card shows correct URLs for the spare cluster
[ ] Access card does NOT reference the failed cluster
[ ] Attendee can log in to OpenShift console
[ ] Attendee can access Maximo
[ ] Attendee can access Showroom
[ ] Showroom terminal tab works
[ ] Showroom displays correct seat-specific variables
[ ] Failed cluster status is QUARANTINED
[ ] Failed cluster is excluded from seat assignment
[ ] Fleet status report shows updated spare count
[ ] If last spare was used: facilitators are notified
```

---

## Edge Cases

### Replacement During an Active Session

**Scenario**: An attendee is actively working through a module when their
cluster fails.

**Key considerations**:

- Any in-progress work on the failed cluster is lost. The attendee must redo
  steps from the beginning of their current module on the spare cluster.
- Exercises from previous modules are already in a "solved" state on the
  spare only if the spare was pre-staged with solved states. Typically,
  spares are prepared identically to attendee clusters (at the base state
  before any exercises), so previous modules will appear unsolved.
- To help the attendee catch up, run the solve automation for all modules
  they have already completed:

  ```bash
  masworld exercise reset --cluster <SPARE_CLUSTER_ID> --module navigation --solve
  masworld exercise reset --cluster <SPARE_CLUSTER_ID> --module updates --solve
  # Repeat for each completed module
  ```

- Coordinate with the presenter (Ernie Steagall). If the session is between
  modules, the replacement is minimally disruptive. If the session is mid-
  exercise, the attendee will need individual support to catch up.
- Assign a facilitator (Francis or Myles) to help the affected attendee
  while the other continues supporting the rest of the room.

### Multiple Simultaneous Failures

**Scenario**: Two or more clusters fail at approximately the same time.

**Key considerations**:

- Run replacements sequentially, not in parallel, to avoid race conditions
  on the secret provider and ACM hub:

  ```bash
  masworld seat replace --seat 12 --cluster spare-01
  masworld seat replace --seat 23 --cluster spare-02
  ```

- After each replacement, verify before proceeding to the next:

  ```bash
  masworld cluster validate --cluster spare-01
  masworld cluster validate --cluster spare-02
  ```

- Check remaining spare capacity after each replacement:

  ```bash
  masworld report fleet-status
  ```

- If the number of failures exceeds the number of available spares, triage
  by impact:
  1. Replace clusters for attendees who are actively blocked first.
  2. Attempt rapid repair (see `cluster-repair.md`) on remaining failed
     clusters to restore them as either primary or spare capacity.
  3. If repair fails and no spares remain, consider pairing two attendees
     on one environment (last resort -- see "No Spares Remaining" below).

- Investigate whether the simultaneous failures share a common root cause
  (e.g., AWS region issue, DNS failure, shared infrastructure component).
  If systemic, further failures are likely. Notify all facilitators.

### Last Spare Used

**Scenario**: After a replacement, no spare clusters remain.

**Immediate actions**:

1. Notify all facilitators verbally and via the fleet dashboard:

   ```bash
   masworld report fleet-status
   ```

   The output will show `Spare: 0`.

2. Attempt to repair any quarantined clusters to restore spare capacity:

   ```bash
   masworld cluster repair --cluster <QUARANTINED_CLUSTER_ID>
   masworld cluster validate --cluster <QUARANTINED_CLUSTER_ID>
   ```

   If the quarantined cluster passes validation, return it to spare status:

   ```bash
   # This requires manual inventory update since quarantined clusters
   # cannot be automatically reassigned. Update the cluster purpose:
   masworld cluster repair --cluster <QUARANTINED_CLUSTER_ID>
   masworld cluster validate --cluster <QUARANTINED_CLUSTER_ID>
   # After validation passes, update the inventory to mark as spare
   ```

3. If no spare can be recovered and another cluster fails, options are:
   - **Pair attendees**: Seat two attendees at one environment. Both view the
     same Showroom. One drives, one observes. Not ideal but functional.
   - **Facilitator cluster**: As an absolute last resort, reassign the
     facilitator cluster to an attendee. This removes the ACM drift
     demonstration capability. Only do this with Ernie Steagall's approval
     since it affects his presentation.
   - **Accept reduced capacity**: If the session is near its end, an attendee
     without a cluster for the final module may be acceptable.

4. Document the situation in the incident log for the post-event review.

### Replacement Fails Partway Through

**Scenario**: The `masworld seat replace` command fails at one of its steps.

**Automated rollback behavior**:

The replacement command is transactional. If any step after step 1 (spare
validation) fails, the command automatically:

1. Restores the original seat assignment in the inventory.
2. Re-enables credentials on the original cluster (if the original cluster
   API is reachable and credentials were disabled).
3. Removes any partially created credentials on the spare cluster.
4. Reports which step failed and why.

**If automated rollback also fails**:

This is a critical situation. The seat may be in an inconsistent state.

1. Check the current state:

   ```bash
   masworld seat show --seat <SEAT_NUMBER>
   ```

2. Check both clusters:

   ```bash
   masworld cluster validate --cluster <ORIGINAL_CLUSTER_ID>
   masworld cluster validate --cluster <SPARE_CLUSTER_ID>
   ```

3. Determine which cluster is in a better state and manually assign the
   seat to that cluster:

   ```bash
   # If the original cluster is still functional despite the failure
   # that triggered replacement, keep the original assignment:
   masworld seat assign --seat <SEAT_NUMBER> --cluster <ORIGINAL_CLUSTER_ID> --force

   # If the spare is in a better state, complete the assignment manually:
   masworld seat assign --seat <SEAT_NUMBER> --cluster <SPARE_CLUSTER_ID> --force
   ```

4. Validate whichever cluster the seat is assigned to:

   ```bash
   masworld cluster validate --cluster <ASSIGNED_CLUSTER_ID>
   ```

5. Regenerate the access card:

   ```bash
   masworld student export-cards --seat <SEAT_NUMBER>
   ```

6. Log the incident with full details for post-event review.

### Spare Cluster Has a Partially Degraded Component

**Scenario**: The spare cluster passes mandatory validation but has a warning
on a non-mandatory component (e.g., `mas_edge: WARN`).

**Decision**: If the degraded component is not needed for the modules the
attendee has remaining, proceed with the replacement. The attendee can
complete the workshop on the spare even if one optional component has a
warning.

```bash
# Check which components have warnings
masworld cluster validate --cluster <SPARE_CLUSTER_ID>
```

If the warning is on a mandatory component that the attendee needs, select
a different spare or repair the spare first.

### Attendee Requests Their Old Environment Back

**Scenario**: After replacement, the attendee prefers their original
environment (e.g., they had significant progress).

**Response**: The original cluster is quarantined and may not be in a usable
state. Reverting is not supported as a standard operation. If the original
cluster is actually still functional:

1. Validate the original cluster:

   ```bash
   masworld cluster validate --cluster <ORIGINAL_CLUSTER_ID>
   ```

2. If it passes all checks, it can theoretically be swapped back. However,
   this consumes time and risks further disruption. Recommend that the
   attendee continue on the spare and offer to run solve automation for
   completed modules.

3. Only consider reverting if the original cluster is fully healthy AND the
   attendee has significant progress that would take more than 10 minutes
   to recreate.

---

## Rollback if Replacement Fails

If the automated replacement command fails and you need to manually restore
the original state:

### Step 1: Check Current State

```bash
masworld seat show --seat <SEAT_NUMBER>
masworld cluster validate --cluster <ORIGINAL_CLUSTER_ID>
masworld cluster validate --cluster <SPARE_CLUSTER_ID>
```

### Step 2: Restore Original Assignment (if original cluster is usable)

```bash
# Re-enable student credentials on the original cluster
masworld student create --cluster <ORIGINAL_CLUSTER_ID> --seat <SEAT_NUMBER>

# Reassign the seat to the original cluster
masworld seat assign --seat <SEAT_NUMBER> --cluster <ORIGINAL_CLUSTER_ID> --force

# Validate
masworld cluster validate --cluster <ORIGINAL_CLUSTER_ID> \
  --checks student_authentication,student_rbac,showroom

# Regenerate access card
masworld student export-cards --seat <SEAT_NUMBER>
```

### Step 3: Clean Up Partial State on Spare

```bash
# Remove any partially created student credentials on spare
masworld student delete --cluster <SPARE_CLUSTER_ID> --seat <SEAT_NUMBER>

# Return spare to available pool (it should still be in spare status
# if the replacement did not complete)
masworld cluster validate --cluster <SPARE_CLUSTER_ID>
```

### Step 4: If Neither Cluster is Usable

If both the original and spare clusters are in a failed state:

1. Attempt repair on both:

   ```bash
   masworld cluster repair --cluster <ORIGINAL_CLUSTER_ID>
   masworld cluster repair --cluster <SPARE_CLUSTER_ID>
   ```

2. Validate both:

   ```bash
   masworld cluster validate --cluster <ORIGINAL_CLUSTER_ID>
   masworld cluster validate --cluster <SPARE_CLUSTER_ID>
   ```

3. Assign the seat to whichever cluster recovers first.

4. If neither recovers within the time thresholds defined in
   `cluster-repair.md`, use a different spare (if available) or escalate.

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `masworld seat replace --seat <N> --cluster <SPARE_ID>` | Full transactional replacement |
| `masworld seat show --seat <N>` | Show current seat assignment |
| `masworld seat show --cluster <ID>` | Show cluster assignment status |
| `masworld report fleet-status` | Show fleet health and spare count |
| `masworld cluster validate --cluster <ID>` | Validate all checks on a cluster |
| `masworld cluster repair --cluster <ID>` | Attempt automated repair |
| `masworld student create --cluster <ID> --seat <N>` | Create student credentials |
| `masworld student delete --cluster <ID> --seat <N>` | Remove student credentials |
| `masworld student export-cards --seat <N>` | Regenerate access card for one seat |
| `masworld student export-cards` | Regenerate all access cards |
| `masworld exercise reset --cluster <ID> --module <M> --solve` | Solve a module for catch-up |
| `masworld config validate --env <ENV>` | Validate configuration and secret provider |
| `masworld seat assign --seat <N> --cluster <ID> --force` | Force-assign (manual recovery only) |

---

## Timing Estimates

| Phase | Duration |
|-------|----------|
| Pre-replacement validation | 30-60 seconds |
| Disable credentials on failed cluster | 10-30 seconds (skipped if API unreachable) |
| Create credentials on spare | 30-60 seconds |
| Update Showroom configuration | 30-60 seconds |
| Update assignment inventory | <5 seconds |
| Regenerate access card | <5 seconds |
| Validate student access on spare | 30-60 seconds |
| Quarantine failed cluster | 10-30 seconds |
| **Total (normal conditions)** | **3-5 minutes** |
| **Total (with solve automation for catch-up)** | **5-10 minutes per module** |
| **Total (with manual intervention for partial failure)** | **10-20 minutes** |
