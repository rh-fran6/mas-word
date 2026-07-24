# Production Logging Guidance

This document covers production considerations for OpenShift Logging with
LokiStack. The workshop environment uses minimal sizing for cost and speed.
Production deployments require significantly different configuration.

> **Conference sizing is NOT production sizing.** The workshop uses
> `1x.extra-small` with 3-day retention. This section describes what a
> production deployment looks like.

## LokiStack sizing

| Size | Daily ingestion | Use case | Replicas |
|---|---|---|---|
| `1x.extra-small` | ~100 GB/day | Demo, dev, workshop | Minimal, no HA |
| `1x.small` | ~100 GB/day | Small clusters | HA distributor, ingester, querier |
| `1x.medium` | ~500 GB/day | Production | Full HA across all components |

For production:
- Use `1x.medium` or larger.
- Ensure at least 3 ingester replicas for data durability.
- Set resource requests and limits appropriate for your log volume.

## Retention policies

Workshop: 3 days. Production considerations:

- **Application logs**: 30--90 days depending on compliance requirements.
- **Infrastructure logs**: 30--90 days.
- **Audit logs**: 90--365 days (often required by compliance frameworks).
- Configure per-tenant retention in the LokiStack `limits` section.
- Implement S3 lifecycle policies as a safety net.

```yaml
# Example production retention
spec:
  limits:
    global:
      retention:
        days: 30
    tenants:
      application:
        retention:
          days: 30
      infrastructure:
        retention:
          days: 60
      audit:
        retention:
          days: 365
```

## High availability

- Deploy LokiStack with `1x.medium` or larger for HA.
- Use pod anti-affinity to spread ingesters across nodes/zones.
- Monitor ingester WAL (write-ahead log) disk usage.
- Ensure the query frontend has sufficient replicas for concurrent users.

## S3 bucket configuration

### Encryption
- Enable SSE-S3 or SSE-KMS encryption on the bucket.
- Use AWS KMS for key management in regulated environments.

### Access control
- Block all public access on the bucket.
- Use a dedicated IAM principal (user or role) per cluster.
- Scope IAM policies to the specific bucket and prefix.
- Prefer IAM Roles for Service Accounts (IRSA) or Pod Identity over
  static access keys.

### Example IAM policy (minimum required)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR_BUCKET_NAME",
        "arn:aws:s3:::YOUR_BUCKET_NAME/*"
      ]
    }
  ]
}
```

### Lifecycle policy
- Transition old objects to S3 Glacier or Infrequent Access after
  retention period.
- Delete objects after the maximum required retention.
- This acts as a safety net beyond Loki's internal compaction.

## SIEM integration

Production environments typically forward logs to a SIEM in addition to
(or instead of) Loki:

### Splunk
- Use the ClusterLogForwarder `splunk` output type.
- Configure the Splunk HEC (HTTP Event Collector) endpoint and token.
- Separate indexes for application, infrastructure, and audit logs.

### Amazon CloudWatch
- Use the ClusterLogForwarder `cloudwatch` output type.
- Configure log group name templates.
- Use IAM roles scoped to CloudWatch Logs actions.

### General forwarding
- The ClusterLogForwarder supports multiple simultaneous outputs.
- You can forward to both Loki (for interactive queries) and a SIEM
  (for long-term retention and alerting).

```yaml
# Example: dual output to Loki and Splunk
spec:
  outputs:
    - name: loki
      type: lokiStack
      lokiStack:
        target:
          name: logging-loki
          namespace: openshift-logging
    - name: splunk
      type: splunk
      splunk:
        url: "YOUR_SPLUNK_HEC_URL"
        secretName: splunk-hec-secret
  pipelines:
    - name: all-to-loki
      inputRefs: [application, infrastructure, audit]
      outputRefs: [loki]
    - name: all-to-splunk
      inputRefs: [application, infrastructure, audit]
      outputRefs: [splunk]
```

## Monitoring and alerting

- Monitor Loki ingestion rate (`loki_distributor_bytes_received_total`).
- Alert on ingester WAL size approaching disk limits.
- Alert on query latency exceeding thresholds.
- Monitor S3 request costs and error rates.
- Monitor Vector collector health on each node.
- Set up alerts for log pipeline gaps (no logs received for N minutes).

## Capacity planning

Estimate daily log volume:
- Count the number of pods and their average log output.
- Multiply by retention period for total storage.
- Add 20--30% overhead for indexes and temporary storage.
- Plan for growth as workloads scale.

Rule of thumb: 1 GB/day of logs requires approximately 0.5--1 GB of S3
storage after compression over a 30-day retention period.
