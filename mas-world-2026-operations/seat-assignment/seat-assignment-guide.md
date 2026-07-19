# MAS World 2026 -- Seat Assignment Guide

## Overview

The seat assignment system maps attendees to OpenShift clusters. Each
attendee receives a unique seat number, which is bound to exactly one
cluster. The assignment is stored independently from cluster preparation,
allowing clusters to be replaced without rebuilding the fleet.

Cross-references:

- Fleet dashboard: `../fleet-dashboard/dashboard-guide.md`
- Incident templates: `../incident-templates/incident-report.md`
- Repair procedures: `../repair-procedures/`
- Event runbook: `../runbooks/`

---

## Seat Assignment Model

Each assignment record contains:

| Field | Description |
|-------|-------------|
| seat_number | Integer from 1 to the configured attendee count |
| cluster_id | The cluster bound to this seat (e.g., `seat-01`) |
| credential_profile | The student credential profile used (e.g., `attendee-default`) |
| student_username | Generated username (e.g., `user01`) |
| status | `assigned`, `unassigned`, or `reassigned` |

Key constraints:

- One seat maps to exactly one cluster.
- One cluster maps to at most one seat.
- A cluster must be in `READY` status before it can be assigned.
- A cluster in `FAILED` or `QUARANTINED` status cannot be assigned.
- Spare clusters are not assigned until needed.
- Reassignment is transactional: it either completes fully or rolls back.

---

## Pre-Event Bulk Assignment Workflow

Use this workflow the day before or morning of the event after all clusters
have been validated.

### Step 1: Validate the fleet

Confirm all attendee clusters are ready.

```bash
masworld fleet validate
```

Review the output. Every cluster intended for attendee assignment must show
`READY`. Refer to `../fleet-dashboard/dashboard-guide.md` for interpreting
statuses.

### Step 2: Validate configuration

```bash
masworld config validate
```

This checks for duplicate cluster IDs, duplicate seat numbers, missing
credential profiles, and count mismatches between configured fleet size
and available inventory.

### Step 3: Create student accounts

```bash
masworld student create --environment event
```

This creates student accounts on all attendee clusters using the configured
credential profiles. Passwords are generated, stored in the configured
secret provider, and never printed to the console.

### Step 4: Validate student access

```bash
masworld student validate
```

This confirms that every generated student account can authenticate,
access its assigned namespace, reach the OpenShift console, and is properly
restricted from other attendees' resources.

### Step 5: Assign all seats

```bash
masworld seat assign --all --environment event
```

This assigns seat numbers 1 through N to the configured attendee clusters
in inventory order. The command will refuse to proceed if:

- Any target cluster is not `READY`.
- The number of `READY` attendee clusters is less than the configured
  attendee count.
- Student accounts have not been created.

### Step 6: Verify assignments

```bash
masworld seat export-map --format table
```

Review the full seat map. Every seat should show `assigned` status with a
valid cluster and username.

### Step 7: Generate access cards

```bash
masworld student export-cards --format pdf --output ./access-cards/
```

This generates one access card per seat containing the seat number, Showroom
URL, OpenShift console URL, Maximo URL, student username, and student
password.

### Step 8: Generate facilitator materials

```bash
masworld seat export-map --format csv --output ./facilitator-seat-map.csv
masworld seat export-map --format json --output ./facilitator-seat-map.json
```

The CSV and JSON exports include all assignment data for facilitator
reference. These files contain student credentials and must not be shared
publicly or left unattended.

---

## Individual Seat Assignment

Assign a single seat to a specific cluster.

```bash
masworld seat assign --seat 12 --cluster seat-12
```

The command validates that:

- The cluster `seat-12` exists in inventory and is `READY`.
- The cluster is not already assigned to another seat.
- Seat 12 is not already assigned to another cluster.
- A student account exists on the target cluster.

If the student account does not yet exist, create it first:

```bash
masworld student create --seat 12
masworld student validate --seat 12
masworld seat assign --seat 12 --cluster seat-12
```

---

## Viewing Assignments

### View a single seat

```bash
masworld seat show --seat 12
```

Example output:

```
Seat 12:
  Cluster:          seat-12
  Status:           assigned
  Student Username:  user12
  Cluster Health:    READY
  Showroom URL:      PLACEHOLDER_SHOWROOM_URL_SEAT_12
  Console URL:       PLACEHOLDER_CONSOLE_URL_SEAT_12
  Maximo URL:        PLACEHOLDER_MAS_URL_SEAT_12
  Last Validated:    2026-08-17T08:15:00Z
```

### View the full seat map

```bash
masworld seat export-map --format table
```

Example output:

```
Seat  Cluster    Status      Username  Cluster Health  Last Validated
----  ---------  ----------  --------  --------------  ----------------------
01    seat-01    assigned    user01    READY           2026-08-17T08:15:00Z
02    seat-02    assigned    user02    READY           2026-08-17T08:15:00Z
03    seat-03    assigned    user03    READY           2026-08-17T08:15:00Z
...
50    seat-50    assigned    user50    READY           2026-08-17T08:15:00Z
S1    spare-01   unassigned  --        READY           2026-08-17T08:15:00Z
S2    spare-02   unassigned  --        READY           2026-08-17T08:15:00Z
S3    spare-03   unassigned  --        READY           2026-08-17T08:15:00Z
S4    spare-04   unassigned  --        READY           2026-08-17T08:15:00Z
S5    spare-05   unassigned  --        READY           2026-08-17T08:15:00Z
```

---

## Exporting Seat Maps

### Table format (human-readable, for terminal)

```bash
masworld seat export-map --format table
```

### CSV format (for spreadsheets)

```bash
masworld seat export-map --format csv --output ./seat-map.csv
```

### JSON format (for programmatic consumption)

```bash
masworld seat export-map --format json --output ./seat-map.json
```

### Filtered exports

Export only assigned seats:

```bash
masworld seat export-map --format table --status assigned
```

Export only unassigned or spare seats:

```bash
masworld seat export-map --format table --status unassigned
```

---

## Replacing a Failed Seat with a Spare

When a cluster fails during the event, replace it with a spare. This is
the most time-critical operation in this guide. Target completion: under
10 minutes.

### Step 1: Confirm the failure

```bash
masworld cluster validate --cluster seat-12
```

If the cluster shows `FAILED`, proceed with replacement.

### Step 2: Identify an available spare

```bash
masworld seat export-map --format table --status unassigned
```

Or check spare status directly:

```bash
masworld report fleet-status --purpose spare
```

Select a spare cluster that shows `READY`.

### Step 3: Execute the replacement

```bash
masworld seat replace --seat 12 --cluster spare-01
```

This command performs the following steps atomically:

1. Validates that `spare-01` is `READY`.
2. Creates or activates the student credential (`user12`) on `spare-01`.
3. Validates that `user12` can authenticate on `spare-01`.
4. Updates the seat assignment to point seat 12 to `spare-01`.
5. Updates Showroom endpoint data for seat 12.
6. Disables the `user12` credential on the failed `seat-12` cluster
   (if the cluster is reachable).
7. Marks `seat-12` as `QUARANTINED`.
8. Runs a post-replacement validation on `spare-01`.

If any step fails, the entire operation rolls back. The seat remains
pointed at the original cluster, and the spare is released.

### Step 4: Generate an updated access card

```bash
masworld student export-cards --seat 12 --format pdf
```

The new access card will contain the updated URLs for `spare-01`.

### Step 5: Provide the attendee with updated information

Hand the attendee the new access card. The student username (`user12`)
remains the same. The password may have been regenerated; check the
access card.

### Step 6: Verify the attendee can proceed

```bash
masworld student validate --seat 12
```

### Step 7: Record the incident

Document the replacement in an incident report. See
`../incident-templates/incident-report.md`.

---

## Unassigning a Seat

Remove a seat assignment without replacing it.

```bash
masworld seat unassign --seat 12
```

This command:

1. Removes the seat-to-cluster mapping.
2. Optionally disables the student credential on the cluster (if reachable).
3. Marks the seat as `unassigned`.

The cluster is not quarantined. It returns to the pool of available
clusters.

To also disable the student account:

```bash
masworld student disable --seat 12
masworld seat unassign --seat 12
```

---

## Access Card Generation

### Generate all access cards

```bash
masworld student export-cards --format pdf --output ./access-cards/
```

This creates one PDF per seat in the specified output directory.

### Generate a single access card

```bash
masworld student export-cards --seat 12 --format pdf
```

### Generate a printable batch

```bash
masworld student export-cards --format pdf --layout printable --output ./print-batch/
```

The `printable` layout arranges multiple cards per page for efficient
printing.

### Access card contents

Each access card contains:

| Field | Example |
|-------|---------|
| Seat Number | 12 |
| Showroom URL | PLACEHOLDER_SHOWROOM_URL_SEAT_12 |
| OpenShift Console URL | PLACEHOLDER_CONSOLE_URL_SEAT_12 |
| Maximo URL | PLACEHOLDER_MAS_URL_SEAT_12 |
| Username | user12 |
| Password | (generated, unique per seat) |
| Support Instructions | "Raise your hand for assistance" |

Access cards never contain:

- Cluster-admin credentials
- ACM credentials
- AWS credentials
- IBM entitlement keys
- Other attendees' credentials
- Internal operational URLs

---

## Handling Late Arrivals or Walk-ins

If an attendee arrives after initial assignment and seats are available:

### Step 1: Identify the next available seat

```bash
masworld seat export-map --format table --status unassigned
```

### Step 2: Check for an available cluster

If unassigned attendee clusters exist:

```bash
masworld seat assign --seat <next_available_seat> --cluster <available_cluster>
```

If only spares remain:

```bash
masworld seat assign --seat <next_available_seat> --cluster spare-NN
```

Assigning a spare to a new walk-in is acceptable when the spare has not
been needed for replacement.

### Step 3: Create student credentials if needed

```bash
masworld student create --seat <seat_number>
masworld student validate --seat <seat_number>
```

### Step 4: Generate the access card

```bash
masworld student export-cards --seat <seat_number> --format pdf
```

### Step 5: Hand the access card to the attendee

If the session has already started, point the attendee to the current
module in Showroom and assist them in catching up.

---

## Handling No-Shows (Reclaiming Seats)

If an attendee does not arrive and their seat is needed for a walk-in
or as an additional spare:

### Step 1: Confirm the attendee has not arrived

Wait until at least 15 minutes after the session start before reclaiming.
Check with the registration desk if possible.

### Step 2: Unassign the seat

```bash
masworld student disable --seat <seat_number>
masworld seat unassign --seat <seat_number>
```

### Step 3: Reassign if needed

The cluster is now available for reassignment to a walk-in or as a spare.

```bash
masworld seat assign --seat <new_seat_number> --cluster <cluster_id>
```

Or leave it unassigned as reserve capacity.

---

## Handling Attendee Requesting a Different Seat

If an attendee wants to move to a different seat (e.g., closer to a power
outlet, next to a colleague):

### Step 1: Check if the target seat is available

```bash
masworld seat show --seat <target_seat>
```

If the target seat is `unassigned`, proceed. If it is `assigned`, this
requires swapping two attendees, which is more complex (see below).

### Step 2: Unassign the current seat

```bash
masworld student disable --seat <current_seat>
masworld seat unassign --seat <current_seat>
```

### Step 3: Assign the new seat

```bash
masworld student create --seat <target_seat>
masworld seat assign --seat <target_seat> --cluster <target_cluster>
masworld student validate --seat <target_seat>
```

### Step 4: Generate a new access card

```bash
masworld student export-cards --seat <target_seat> --format pdf
```

### Swapping two attendees

If both seats are occupied:

1. Note both current assignments.
2. Unassign both seats.
3. Reassign each attendee to the other seat.
4. Generate new access cards for both.

```bash
masworld student disable --seat 5
masworld student disable --seat 18
masworld seat unassign --seat 5
masworld seat unassign --seat 18

masworld seat assign --seat 5 --cluster seat-18
masworld student create --seat 5
masworld student validate --seat 5

masworld seat assign --seat 18 --cluster seat-05
masworld student create --seat 18
masworld student validate --seat 18

masworld student export-cards --seat 5 --format pdf
masworld student export-cards --seat 18 --format pdf
```

Note: When swapping, the seat number changes but the cluster follows the
physical location. Each attendee gets new credentials for their new cluster.

---

## Emergency Reassignment During Session

If a cluster fails mid-session and the attendee must be moved immediately:

### Priority: minimize attendee downtime

1. Do not troubleshoot the failing cluster first. Replace immediately.
2. Use the spare replacement workflow (see "Replacing a Failed Seat with
   a Spare" above).
3. Troubleshoot the failed cluster after the attendee is back online.

```bash
masworld seat replace --seat <affected_seat> --cluster <spare_cluster>
masworld student export-cards --seat <affected_seat> --format pdf
```

Estimated time: 5-10 minutes.

If no spare clusters are available:

1. Check for unassigned attendee clusters from no-shows.
2. If none available, pair the attendee with a neighbor temporarily.
3. Record the incident and escalate.

---

## Full Workflow Example: Start to Finish

This example walks through the complete pre-event assignment workflow for
an event with 50 attendees, 5 spares, and 1 facilitator.

### Day before the event (August 16, 2026)

#### Validate configuration and fleet

```bash
masworld config validate
masworld fleet validate
```

Expected output: 50 attendee clusters `READY`, 5 spare clusters `READY`,
1 facilitator cluster `READY`.

#### Create student accounts

```bash
masworld student create --environment event
```

#### Validate student access

```bash
masworld student validate
```

Expected output: all 50 student accounts pass authentication, namespace
access, console access, and RBAC checks.

#### Assign all seats

```bash
masworld seat assign --all --environment event
```

#### Verify the seat map

```bash
masworld seat export-map --format table
```

#### Generate access cards

```bash
masworld student export-cards --format pdf --output ./access-cards/
masworld student export-cards --format pdf --layout printable --output ./print-batch/
```

#### Generate facilitator materials

```bash
masworld seat export-map --format csv --output ./facilitator-seat-map.csv
masworld seat export-map --format json --output ./facilitator-seat-map.json
masworld report seat-report --output ./seat-report.json
```

#### Print access cards

Print the cards from `./print-batch/` and organize them by seat number.

### Event morning (August 17, 2026)

#### Re-validate the fleet

```bash
masworld fleet validate
```

#### Rotate student credentials

```bash
masworld student rotate
```

#### Re-validate student access after rotation

```bash
masworld student validate
```

#### Regenerate access cards with new credentials

```bash
masworld student export-cards --format pdf --output ./access-cards/
masworld student export-cards --format pdf --layout printable --output ./print-batch/
```

#### Export final seat map

```bash
masworld seat export-map --format table
masworld seat export-map --format csv --output ./final-seat-map.csv
```

#### Confirm spare availability

```bash
masworld report fleet-status --purpose spare
```

Expected: 5 spare clusters, all `READY`.

### During the event

#### Monitor fleet health

```bash
masworld report fleet-status
```

Refer to `../fleet-dashboard/dashboard-guide.md` for continuous monitoring.

#### Handle a failure at seat 33

```bash
masworld cluster validate --cluster seat-33
# Output: FAILED

masworld seat replace --seat 33 --cluster spare-01
masworld student export-cards --seat 33 --format pdf
# Hand new access card to attendee at seat 33
```

#### Handle a walk-in (attendee 51)

```bash
masworld seat assign --seat 51 --cluster spare-02
masworld student create --seat 51
masworld student validate --seat 51
masworld student export-cards --seat 51 --format pdf
# Hand access card to walk-in attendee
```

### After the event

#### Disable all student accounts

```bash
masworld student disable --all
```

#### Export final seat map for records

```bash
masworld seat export-map --format json --output ./post-event-seat-map.json
```

#### Proceed with teardown

Refer to `../runbooks/` for the post-event teardown procedure.
