# MAS World 2026 -- Fleet Dashboard and Monitoring Guide

## Overview

The fleet dashboard provides real-time visibility into the health and
assignment status of all clusters in the MAS World 2026 environment. Use
it to monitor cluster readiness, detect failures, track seat assignments,
and respond to issues during the event.

Cross-references:

- Seat assignment guide: `../seat-assignment/seat-assignment-guide.md`
- Incident templates: `../incident-templates/incident-report.md`
- Repair procedures: `../repair-procedures/`
- Event runbook: `../runbooks/`

---

## Fleet Status Overview

The fleet status report shows every cluster in the inventory with its
current health and assignment status.

```bash
masworld report fleet-status
```

Example output:

```
MAS World 2026 -- Fleet Status Report
Generated: 2026-08-17T09:00:00Z (America/Chicago)

SUMMARY
-------
Total Clusters:    56
  Attendee:        50
  Spare:            5
  Facilitator:      1

Status Breakdown:
  READY:           54
  PREPARING:        0
  WARNING:          1
  FAILED:           1
  QUARANTINED:      0

Assignment Breakdown:
  Assigned:        50
  Unassigned:       5 (spare)
  Facilitator:      1

CLUSTER DETAIL
--------------
Cluster      Purpose      Status     Seat  Username  Last Validated
-----------  -----------  ---------  ----  --------  ----------------------
seat-01      attendee     READY      01    user01    2026-08-17T08:55:00Z
seat-02      attendee     READY      02    user02    2026-08-17T08:55:00Z
seat-03      attendee     READY      03    user03    2026-08-17T08:55:00Z
...
seat-17      attendee     WARNING    17    user17    2026-08-17T08:55:00Z
...
seat-42      attendee     FAILED     42    user42    2026-08-17T08:55:00Z
...
seat-50      attendee     READY      50    user50    2026-08-17T08:55:00Z
spare-01     spare        READY      --    --        2026-08-17T08:55:00Z
spare-02     spare        READY      --    --        2026-08-17T08:55:00Z
spare-03     spare        READY      --    --        2026-08-17T08:55:00Z
spare-04     spare        READY      --    --        2026-08-17T08:55:00Z
spare-05     spare        READY      --    --        2026-08-17T08:55:00Z
facilitator  facilitator  READY      --    --        2026-08-17T08:55:00Z
```

---

## Cluster Status Definitions

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| READY | All mandatory readiness checks pass. The cluster can be assigned to an attendee or is operating normally. | None. |
| PREPARING | The cluster is currently being configured by automation. Do not assign it. | Wait for preparation to complete. Monitor progress. |
| WARNING | One or more non-mandatory checks have failed. The cluster is functional but degraded. | Investigate the warning. Decide whether to repair before or during the event. |
| FAILED | One or more mandatory checks have failed. The cluster cannot be assigned. | Replace with a spare if assigned. Attempt repair if time permits. |
| QUARANTINED | The cluster was previously assigned and has been replaced. It is excluded from all assignment operations. | Do not reassign. Investigate after the event or when time permits. |

---

## Seat Status Definitions

| Status | Meaning |
|--------|---------|
| ASSIGNED | The seat is bound to a cluster and a student account is active. |
| UNASSIGNED | The seat number exists but is not bound to any cluster. |
| SPARE | The cluster is reserved as a replacement and is not bound to any seat. |

---

## Using Report Commands

### Full fleet status

```bash
masworld report fleet-status
```

Shows all clusters with status, assignment, and last validation time.

### Filter by cluster purpose

```bash
masworld report fleet-status --purpose attendee
masworld report fleet-status --purpose spare
masworld report fleet-status --purpose facilitator
```

### Filter by status

```bash
masworld report fleet-status --status READY
masworld report fleet-status --status FAILED
masworld report fleet-status --status WARNING
masworld report fleet-status --status QUARANTINED
```

### Single cluster detail

```bash
masworld cluster validate --cluster seat-17
```

Example output:

```
Cluster seat-17: WARNING
  Validated at: 2026-08-17T08:55:00Z

  Check                     Status   Detail
  ------------------------  -------  ----------------------------------------
  openshift_api             PASS     API responding, v4.16.x
  openshift_console         PASS     Console accessible
  mas_core                  PASS     MAS Core Ready
  maximo_manage             PASS     Manage Ready
  database                  PASS     DB connection OK
  logging_operator          PASS     Logging Operator running
  lokistack                 WARNING  Ingester pod restart count: 3
  cluster_log_forwarder     PASS     CLF pipeline Ready
  s3_write_read             PASS     S3 read/write OK
  historical_log_query      PASS     Historical query returned results
  identity                  PASS     Keycloak integration OK
  showroom                  PASS     Showroom accessible
  runtime_automation        PASS     All modules validated
  student_authentication    PASS     user17 authenticated
  student_rbac              PASS     RBAC checks passed
  mas_edge                  N/A      Component disabled

  Overall: WARNING (1 warning, 0 failures)
```

### Seat report

```bash
masworld report seat-report
```

Example output:

```
MAS World 2026 -- Seat Report
Generated: 2026-08-17T09:00:00Z

Seats Configured:    50
Seats Assigned:      50
Seats Unassigned:     0

Spares Available:     5
Spares Used:          0

Assignment Health:
  Healthy Seats:     49
  Warning Seats:      1 (seat 17)
  Failed Seats:       0

Seat  Cluster    Health    Username  Showroom  Console  Maximo
----  ---------  --------  --------  --------  -------  ------
01    seat-01    READY     user01    OK        OK       OK
02    seat-02    READY     user02    OK        OK       OK
...
17    seat-17    WARNING   user17    OK        OK       OK
...
50    seat-50    READY     user50    OK        OK       OK
```

### JSON output for programmatic use

```bash
masworld report fleet-status --format json --output ./fleet-status.json
masworld report seat-report --format json --output ./seat-report.json
```

---

## Key Metrics to Watch

### Before the event

| Metric | Target | Command |
|--------|--------|---------|
| Total READY clusters | >= attendee count + spare count | `masworld report fleet-status --status READY` |
| FAILED clusters | 0 | `masworld report fleet-status --status FAILED` |
| Student auth pass rate | 100% | `masworld student validate` |
| Available spares | >= configured spare count | `masworld report fleet-status --purpose spare` |

### During the event

| Metric | Target | Action if breached |
|--------|--------|--------------------|
| FAILED clusters | 0 | Replace with spare. See `../seat-assignment/seat-assignment-guide.md`. |
| WARNING clusters | Monitor trend | Investigate. If degrading, preemptively replace. |
| Available spares | >= 2 | Alert facilitators. Consider reclaiming no-show seats. |
| QUARANTINED clusters | Track count | No action during event unless spares depleted. |
| Student auth failures | 0 | Rotate credential for affected seat. |

---

## Setting Up Monitoring During the Event

### Continuous monitoring terminal

Dedicate one terminal on the support workstation to periodic fleet checks.

Run a status check every 5 minutes during the active session:

```bash
watch -n 300 masworld report fleet-status --format table
```

Or run manual checks at key moments:

```bash
# Before session start
masworld report fleet-status

# After each module transition
masworld report fleet-status --status FAILED
masworld report fleet-status --status WARNING

# After any reported issue
masworld cluster validate --cluster <cluster_id>
```

### Recommended check schedule

| Time | Action | Command |
|------|--------|---------|
| T-60 min | Full fleet validation | `masworld fleet validate` |
| T-30 min | Student access validation | `masworld student validate` |
| T-15 min | Fleet status snapshot | `masworld report fleet-status` |
| T-0 (session start) | Confirm all seats assigned | `masworld seat export-map --format table` |
| Every 10 min | Quick fleet status | `masworld report fleet-status --status FAILED` |
| After each module | Check for new failures | `masworld report fleet-status` |
| Post-session | Final fleet status | `masworld report fleet-status --format json --output ./post-event-status.json` |

---

## Alert Thresholds and Responses

### Critical alerts

| Condition | Response |
|-----------|----------|
| Any assigned cluster FAILED | Immediately replace with spare. See `../seat-assignment/seat-assignment-guide.md`. |
| More than 3 clusters FAILED simultaneously | Pause the session. Assess whether this is a systemic issue (shared infrastructure, AWS region, ACM hub). Escalate per `../runbooks/`. |
| All spares consumed | Alert all facilitators. Reclaim unassigned or no-show seats. Prepare to pair attendees if necessary. |
| ACM hub unreachable | The ACM demo segment cannot proceed. Skip to the next module or use pre-recorded fallback. |
| Student auth failure rate > 5% | Investigate whether credential rotation or identity infrastructure has a systemic issue. |

### Warning alerts

| Condition | Response |
|-----------|----------|
| Any cluster WARNING | Monitor for escalation to FAILED. Investigate root cause. |
| Spare count drops below 2 | Proactively attempt to repair QUARANTINED clusters to restore spare capacity. |
| Single cluster validation slow (> 60s) | May indicate network congestion or cluster degradation. Monitor. |
| Loki ingester pod restarts > 5 | May indicate storage or memory pressure. Check S3 connectivity and resource limits. |

---

## Quick Health Check Commands

Use these commands for rapid assessment during the event.

### Is everything OK?

```bash
masworld report fleet-status --status FAILED
```

If this returns no clusters, the fleet is healthy.

### How many spares do I have?

```bash
masworld report fleet-status --purpose spare --status READY
```

### Is a specific seat working?

```bash
masworld seat show --seat <number>
masworld cluster validate --cluster <cluster_id>
masworld student validate --seat <number>
```

### What failed on a cluster?

```bash
masworld cluster validate --cluster <cluster_id>
```

The output lists every check with its pass/fail status and detail.

### Can all students log in?

```bash
masworld student validate
```

### What is the Loki status across the fleet?

```bash
masworld cluster validate --cluster <cluster_id> --check lokistack
masworld cluster validate --cluster <cluster_id> --check cluster_log_forwarder
masworld cluster validate --cluster <cluster_id> --check s3_write_read
masworld cluster validate --cluster <cluster_id> --check historical_log_query
```

### What is the MAS status on a cluster?

```bash
masworld cluster validate --cluster <cluster_id> --check mas_core
masworld cluster validate --cluster <cluster_id> --check maximo_manage
masworld cluster validate --cluster <cluster_id> --check database
```

### Quick fleet summary (one line)

```bash
masworld report fleet-status --format summary
```

Example output:

```
Fleet: 54 READY, 1 WARNING, 1 FAILED, 0 QUARANTINED | Spares: 5 available | Seats: 50/50 assigned
```

---

## Troubleshooting Dashboard Issues

### Fleet status command hangs or times out

The command queries each cluster API. If one or more clusters are
unreachable, the command may take longer than expected.

Use per-cluster validation to isolate the slow cluster:

```bash
masworld cluster validate --cluster seat-01 --timeout 30
masworld cluster validate --cluster seat-02 --timeout 30
```

### Fleet status shows stale data

The `Last Validated` timestamp indicates when the cluster was last checked.
If the timestamp is old, re-run validation:

```bash
masworld fleet validate
```

Or validate a single cluster:

```bash
masworld cluster validate --cluster <cluster_id>
```

### Discrepancy between fleet status and seat map

If the fleet status shows a cluster as FAILED but the seat map still shows
it as assigned, the seat may need manual intervention:

```bash
masworld seat show --seat <number>
masworld cluster validate --cluster <cluster_id>
```

If the cluster is truly FAILED and assigned, replace it:

```bash
masworld seat replace --seat <number> --cluster <spare_cluster>
```

See `../seat-assignment/seat-assignment-guide.md` for the full replacement
workflow.
