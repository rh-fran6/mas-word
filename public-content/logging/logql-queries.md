# LogQL Query Reference

LogQL is the query language used by Loki. These examples work with OpenShift
Logging when LokiStack is configured as the log store. Run them from the
OpenShift web console under **Observe > Logs**, or via the Loki API.

## Log stream selectors

Loki organizes logs into streams by labels. On OpenShift, the common labels
are:

- `kubernetes_namespace_name` -- the namespace
- `kubernetes_pod_name` -- the pod name
- `kubernetes_container_name` -- the container name
- `log_type` -- `application`, `infrastructure`, or `audit`

---

## 1. All logs from a specific namespace

```logql
{kubernetes_namespace_name="my-namespace"}
```

Returns all log lines from pods in `my-namespace`.

## 2. Logs from a specific pod

```logql
{kubernetes_namespace_name="my-namespace", kubernetes_pod_name="log-generator"}
```

Narrows results to a single pod.

## 3. Filter by keyword

```logql
{kubernetes_namespace_name="my-namespace"} |= "error"
```

Returns lines containing the string `error` (case-sensitive).

## 4. Exclude a keyword

```logql
{kubernetes_namespace_name="my-namespace"} != "healthcheck"
```

Filters out lines containing `healthcheck`.

## 5. Regex filter

```logql
{kubernetes_namespace_name="my-namespace"} |~ "level=(warn|error)"
```

Matches lines where `level=` is either `warn` or `error`.

## 6. Filter by run ID (workshop exercise)

```logql
{kubernetes_namespace_name="my-namespace"} |= "run_id=run-001"
```

Finds all log lines from a specific test run, even after the generating
pod has been deleted (historical log query).

## 7. Log rate over time

```logql
rate({kubernetes_namespace_name="my-namespace"}[5m])
```

Shows the per-second rate of log lines over 5-minute windows. Useful for
spotting log volume spikes.

## 8. Count lines by level

```logql
sum by (level) (
  count_over_time(
    {kubernetes_namespace_name="my-namespace"} | pattern `<_> level=<level> <_>` [10m]
  )
)
```

Parses the `level` field from unstructured log lines and counts
occurrences grouped by level.

## 9. Infrastructure logs from a specific node

```logql
{log_type="infrastructure", kubernetes_host="ip-10-0-1-100.ec2.internal"}
```

Useful for debugging node-level issues. Replace the hostname with your
actual node name (`oc get nodes`).

## 10. Audit logs for a specific user

```logql
{log_type="audit"} | json | user_username="system:serviceaccount:my-namespace:my-sa"
```

Parses JSON-structured audit log entries and filters by the acting user.
Audit log queries can be expensive; use a narrow time range.

---

## Tips

- **Time range**: Always set a reasonable time range in the UI or API.
  Querying weeks of data is slow and expensive.
- **Label cardinality**: Use labels for initial stream selection, then
  filter with `|=`, `!=`, or `|~` for content matching. Do not create
  high-cardinality labels.
- **JSON parsing**: Use `| json` to parse structured JSON logs, then
  filter on extracted fields: `| json | status_code >= 500`.
- **Line format**: Use `| line_format` to reshape output:
  `| line_format "{{.timestamp}} {{.message}}"`.
- **Log type tenants**: OpenShift Logging uses tenants for `application`,
  `infrastructure`, and `audit`. Select the correct tenant in the
  console dropdown or use `log_type` in queries.
