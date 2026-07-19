# MAS World 2026 -- Incident Report Template

## Overview

This template is used to document incidents that occur during the MAS World
2026 workshop on August 17, 2026. Every incident that affects attendee
experience, blocks a session segment, or requires facilitator intervention
must be recorded.

Cross-references:

- Repair procedures: `../repair-procedures/`
- Event runbook: `../runbooks/`
- Fleet dashboard: `../fleet-dashboard/dashboard-guide.md`
- Seat assignment guide: `../seat-assignment/seat-assignment-guide.md`

---

## Incident ID Format

Use the format `MW26-NNNN` where `NNNN` is a zero-padded auto-incrementing
number starting at `0001`.

Assign the next available number in sequence. Check the incident log directory
for the highest existing number before assigning.

---

## Severity Definitions

| Severity | Definition |
|----------|-----------|
| Critical | Multiple attendees blocked from continuing. Session cannot proceed for affected seats. Immediate facilitator response required. Examples: cluster API unreachable, MAS down, Showroom inaccessible for multiple seats. |
| High | One attendee fully blocked or multiple attendees degraded. Workaround may exist but is not obvious. Examples: single cluster failed, student authentication broken on one seat, Loki queries returning errors. |
| Medium | One attendee partially degraded. Workaround is available and documented. Examples: slow console response, one exercise validation failing but content is accessible, cosmetic Showroom issue. |
| Low | Minor issue with no attendee impact or impact limited to a single non-critical feature. Examples: log formatting inconsistency, non-blocking warning in terminal, minor typo in content. |

---

## Category Definitions

| Category | Scope |
|----------|-------|
| Infrastructure | OpenShift cluster, nodes, networking, storage, compute, certificates |
| Application | MAS Core, Maximo Manage, database, operators, Loki, logging |
| Access | Authentication, RBAC, student accounts, Keycloak, console access |
| Content | Showroom pages, exercise instructions, runtime automation, solve/validate |
| Network | DNS, ingress, routes, conference Wi-Fi, connectivity between services |

---

## Blank Incident Report Template

```
============================================================
INCIDENT REPORT
============================================================

Incident ID:    MW26-____
Date/Time:      YYYY-MM-DD HH:MM CDT (America/Chicago)
Reported By:    [Name] ([Role: Presenter | Lab Owner | Observability Lead | Attendee])
Status:         [Open | In Progress | Resolved | Escalated | Deferred]

------------------------------------------------------------
AFFECTED ENVIRONMENT
------------------------------------------------------------

Seat Number:    ____
Cluster ID:     ____
Cluster Purpose: [attendee | spare | facilitator]

------------------------------------------------------------
CLASSIFICATION
------------------------------------------------------------

Severity:       [Critical | High | Medium | Low]
Category:       [Infrastructure | Application | Access | Content | Network]

------------------------------------------------------------
DESCRIPTION
------------------------------------------------------------

[What happened? What was the attendee trying to do? What was the expected
behavior? What was the observed behavior?]

------------------------------------------------------------
IMPACT
------------------------------------------------------------

Attendees Affected:     [Number]
Session Segment:        [Navigation | ACM | Updates | Observability | Identity]
Session Blocked:        [Yes | No]
Workaround Available:   [Yes | No]
Workaround Description: [If yes, describe]

------------------------------------------------------------
DIAGNOSTIC COMMANDS AND OUTPUTS
------------------------------------------------------------

Command 1:
$ [command]
Output:
[output]

Command 2:
$ [command]
Output:
[output]

------------------------------------------------------------
ROOT CAUSE
------------------------------------------------------------

[Identified root cause or "Under investigation"]

------------------------------------------------------------
RESOLUTION STEPS TAKEN
------------------------------------------------------------

Step 1: [action taken]
Step 2: [action taken]
Step N: [action taken]

Resolution Confirmed By: [Name]
Resolution Confirmed At: YYYY-MM-DD HH:MM CDT

------------------------------------------------------------
TIMING
------------------------------------------------------------

Reported At:    YYYY-MM-DD HH:MM CDT
Acknowledged At: YYYY-MM-DD HH:MM CDT
Resolved At:    YYYY-MM-DD HH:MM CDT
Total Resolution Time: [minutes]

------------------------------------------------------------
FOLLOW-UP ACTIONS
------------------------------------------------------------

- [ ] [Action item 1]
- [ ] [Action item 2]

------------------------------------------------------------
LESSONS LEARNED
------------------------------------------------------------

[What could have prevented this? What should change for future events?]

============================================================
```

---

## Example Incidents

### Example 1: Critical -- Cluster API Unreachable

```
============================================================
INCIDENT REPORT
============================================================

Incident ID:    MW26-0001
Date/Time:      2026-08-17 09:42 CDT (America/Chicago)
Reported By:    Francis Anyaegbu (Lab Owner)
Status:         Resolved

------------------------------------------------------------
AFFECTED ENVIRONMENT
------------------------------------------------------------

Seat Number:    07
Cluster ID:     seat-07
Cluster Purpose: attendee

------------------------------------------------------------
CLASSIFICATION
------------------------------------------------------------

Severity:       Critical
Category:       Infrastructure

------------------------------------------------------------
DESCRIPTION
------------------------------------------------------------

Attendee at seat 07 reported that the OpenShift console was unreachable.
The browser showed a connection timeout. The attendee was attempting to
begin the Navigation and Search exercise. The Showroom terminal was also
unresponsive.

------------------------------------------------------------
IMPACT
------------------------------------------------------------

Attendees Affected:     1
Session Segment:        Navigation and Search
Session Blocked:        Yes
Workaround Available:   No
Workaround Description: N/A

------------------------------------------------------------
DIAGNOSTIC COMMANDS AND OUTPUTS
------------------------------------------------------------

Command 1:
$ masworld cluster validate --cluster seat-07
Output:
Cluster seat-07: FAILED
  openshift_api: FAIL - Connection timed out after 30s
  console: FAIL - PLACEHOLDER_CONSOLE_URL unreachable
  mas_core: SKIPPED
  student_auth: SKIPPED

Command 2:
$ masworld report fleet-status --cluster seat-07
Output:
seat-07  FAILED  Last validated: 2026-08-17T09:43:12Z
  API endpoint: PLACEHOLDER_API_URL
  Status: Unreachable
  Last successful check: 2026-08-17T08:15:00Z

Command 3:
$ masworld seat show --seat 7
Output:
Seat 07:
  Cluster: seat-07
  Status: ASSIGNED
  Student: user07
  Cluster Health: FAILED

------------------------------------------------------------
ROOT CAUSE
------------------------------------------------------------

AWS EC2 instance hosting the control plane became unresponsive. AWS Health
Dashboard showed a hardware issue affecting the underlying host in
PLACEHOLDER_AWS_REGION.

------------------------------------------------------------
RESOLUTION STEPS TAKEN
------------------------------------------------------------

Step 1: Confirmed cluster seat-07 was unreachable.
Step 2: Checked spare cluster availability with masworld report fleet-status --purpose spare.
Step 3: Identified spare-01 as available and READY.
Step 4: Executed seat replacement:
        $ masworld seat replace --seat 7 --cluster spare-01
Step 5: Verified replacement cluster readiness:
        $ masworld cluster validate --cluster spare-01
Step 6: Confirmed attendee could log in to spare-01 with new credentials.
Step 7: Provided attendee with updated access information.
Step 8: Marked seat-07 as quarantined:
        Automatic via seat replace command.

Resolution Confirmed By: Francis Anyaegbu
Resolution Confirmed At: 2026-08-17 09:51 CDT

------------------------------------------------------------
TIMING
------------------------------------------------------------

Reported At:    2026-08-17 09:42 CDT
Acknowledged At: 2026-08-17 09:42 CDT
Resolved At:    2026-08-17 09:51 CDT
Total Resolution Time: 9 minutes

------------------------------------------------------------
FOLLOW-UP ACTIONS
------------------------------------------------------------

- [ ] File AWS support case for seat-07 host failure
- [ ] Verify seat-07 data is recoverable after event
- [ ] Review whether additional spare clusters are needed
- [ ] Update post-event teardown plan to include quarantined seat-07

------------------------------------------------------------
LESSONS LEARNED
------------------------------------------------------------

The spare replacement workflow completed within the target 10-minute window.
Having pre-validated spare clusters was essential. Consider increasing spare
count from 5 to 7 for future events to account for infrastructure failures
that cannot be predicted by preflight checks.

============================================================
```

### Example 2: High -- Student Authentication Failure

```
============================================================
INCIDENT REPORT
============================================================

Incident ID:    MW26-0002
Date/Time:      2026-08-17 10:15 CDT (America/Chicago)
Reported By:    Myles Vivian (Observability Lead)
Status:         Resolved

------------------------------------------------------------
AFFECTED ENVIRONMENT
------------------------------------------------------------

Seat Number:    23
Cluster ID:     seat-23
Cluster Purpose: attendee

------------------------------------------------------------
CLASSIFICATION
------------------------------------------------------------

Severity:       High
Category:       Access

------------------------------------------------------------
DESCRIPTION
------------------------------------------------------------

Attendee at seat 23 could not log in to the OpenShift console. The login
page loaded correctly but authentication returned "Invalid credentials."
Other attendees on nearby seats were not affected. The attendee confirmed
they were using the credentials from their access card.

------------------------------------------------------------
IMPACT
------------------------------------------------------------

Attendees Affected:     1
Session Segment:        Navigation and Search
Session Blocked:        Yes
Workaround Available:   Yes
Workaround Description: Rotate the student credential and provide updated password.

------------------------------------------------------------
DIAGNOSTIC COMMANDS AND OUTPUTS
------------------------------------------------------------

Command 1:
$ masworld student validate --seat 23
Output:
Seat 23 (user23 on seat-23):
  authentication: FAIL - 401 Unauthorized
  console_access: SKIPPED
  namespace_access: SKIPPED
  mas_access: SKIPPED

Command 2:
$ masworld cluster validate --cluster seat-23 --check student_authentication
Output:
seat-23 student_authentication: FAIL
  user23: authentication failed
  htpasswd secret: present
  oauth pods: Running (2/2)

------------------------------------------------------------
ROOT CAUSE
------------------------------------------------------------

The htpasswd secret on seat-23 contained a stale password hash for user23.
The credential rotation during the morning pre-event check did not complete
successfully for this one cluster, but the batch operation reported overall
success because other clusters succeeded.

------------------------------------------------------------
RESOLUTION STEPS TAKEN
------------------------------------------------------------

Step 1: Rotated the student credential:
        $ masworld student rotate --seat 23
Step 2: Verified new credential worked:
        $ masworld student validate --seat 23
Step 3: Generated updated access card:
        $ masworld student export-cards --seat 23 --format pdf
Step 4: Provided attendee with updated password from the regenerated access card.

Resolution Confirmed By: Myles Vivian
Resolution Confirmed At: 2026-08-17 10:19 CDT

------------------------------------------------------------
TIMING
------------------------------------------------------------

Reported At:    2026-08-17 10:15 CDT
Acknowledged At: 2026-08-17 10:15 CDT
Resolved At:    2026-08-17 10:19 CDT
Total Resolution Time: 4 minutes

------------------------------------------------------------
FOLLOW-UP ACTIONS
------------------------------------------------------------

- [ ] Investigate why the morning credential rotation skipped seat-23
- [ ] Add per-cluster validation assertion after batch credential rotation
- [ ] Review batch operation error reporting to surface partial failures

------------------------------------------------------------
LESSONS LEARNED
------------------------------------------------------------

Batch operations that report aggregate success can mask per-cluster failures.
The morning pre-event validation should use masworld student validate (per
seat) rather than relying on the exit code of the batch rotation. Add a
mandatory post-rotation validation step to the event-morning checklist in
../runbooks/.

============================================================
```

### Example 3: Medium -- Loki Query Returning Empty Results

```
============================================================
INCIDENT REPORT
============================================================

Incident ID:    MW26-0003
Date/Time:      2026-08-17 11:05 CDT (America/Chicago)
Reported By:    Myles Vivian (Observability Lead)
Status:         Resolved

------------------------------------------------------------
AFFECTED ENVIRONMENT
------------------------------------------------------------

Seat Number:    31
Cluster ID:     seat-31
Cluster Purpose: attendee

------------------------------------------------------------
CLASSIFICATION
------------------------------------------------------------

Severity:       Medium
Category:       Application

------------------------------------------------------------
DESCRIPTION
------------------------------------------------------------

Attendee at seat 31 completed the logging exercise and generated the sample
log workload successfully. However, when querying Loki for historical logs
after deleting the sample pod, the query returned zero results. Other
attendees nearby confirmed their queries returned expected results.

------------------------------------------------------------
IMPACT
------------------------------------------------------------

Attendees Affected:     1
Session Segment:        Observability and Logging
Session Blocked:        No
Workaround Available:   Yes
Workaround Description: Reset the exercise and have the attendee re-run
                        the sample workload, then wait 60 seconds before
                        querying.

------------------------------------------------------------
DIAGNOSTIC COMMANDS AND OUTPUTS
------------------------------------------------------------

Command 1:
$ masworld cluster validate --cluster seat-31 --check lokistack
Output:
seat-31 lokistack: PASS
  LokiStack status: Ready
  S3 bucket: PLACEHOLDER_S3_BUCKET_SEAT_31
  S3 connectivity: OK
  Ingester pods: Running (2/2)
  Querier pods: Running (2/2)

Command 2:
$ masworld cluster validate --cluster seat-31 --check cluster_log_forwarder
Output:
seat-31 cluster_log_forwarder: PASS
  ClusterLogForwarder: Deployed
  Pipeline status: Ready
  Collector pods: Running (3/3)

Command 3:
$ masworld exercise reset --cluster seat-31 --module observability
Output:
Resetting observability exercise on seat-31...
  Removed previous sample workload: OK
  Re-deployed sample workload: OK
  Waiting for log ingestion (60s)...
  Verified log query returns results: OK
Reset complete.

------------------------------------------------------------
ROOT CAUSE
------------------------------------------------------------

The attendee deleted the sample pod and immediately queried Loki. The log
collector had not yet flushed the final batch to the ingester. The logs
were in the collector buffer at the time of the query. After the exercise
reset introduced a 60-second delay, the logs appeared correctly.

------------------------------------------------------------
RESOLUTION STEPS TAKEN
------------------------------------------------------------

Step 1: Verified LokiStack and ClusterLogForwarder were healthy.
Step 2: Reset the observability exercise:
        $ masworld exercise reset --cluster seat-31 --module observability
Step 3: Instructed attendee to wait 60 seconds after pod deletion before
        querying, as noted in the exercise instructions.

Resolution Confirmed By: Myles Vivian
Resolution Confirmed At: 2026-08-17 11:10 CDT

------------------------------------------------------------
TIMING
------------------------------------------------------------

Reported At:    2026-08-17 11:05 CDT
Acknowledged At: 2026-08-17 11:05 CDT
Resolved At:    2026-08-17 11:10 CDT
Total Resolution Time: 5 minutes

------------------------------------------------------------
FOLLOW-UP ACTIONS
------------------------------------------------------------

- [ ] Add a more prominent note in the Showroom observability module
      about the ingestion delay
- [ ] Consider adding a progress indicator or polling script for attendees

------------------------------------------------------------
LESSONS LEARNED
------------------------------------------------------------

The 60-second ingestion delay is expected behavior but was not sufficiently
emphasized in the exercise instructions. The Showroom content should include
a callout box explaining that log ingestion is not instantaneous and that
attendees should wait before querying. Consider adding an automated polling
script that checks for log availability before telling the attendee to
proceed.

============================================================
```

---

## Incident Log Maintenance

After the event, collect all incident reports and:

1. Copy each completed report to `incident-reports/MW26-NNNN.md`.
2. Create a summary table in `incident-reports/summary.md`.
3. Review all lessons learned for inclusion in the post-event retrospective.
4. Identify patterns across incidents for systemic improvements.
5. Update the repair procedures in `../repair-procedures/` based on findings.
6. Update the event runbook in `../runbooks/` with new diagnostic steps.
