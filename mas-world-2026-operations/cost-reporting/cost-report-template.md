# MAS World 2026 -- Post-Event Cost Report

## Report Metadata

| Field | Value |
|-------|-------|
| Event | MAS World 2026 |
| Event Date | August 17, 2026 |
| Report Prepared By | [Name] |
| Report Date | [YYYY-MM-DD] |
| Reporting Period | [Start Date] to [End Date] |
| Currency | USD |

---

## 1. Executive Summary

[Provide a brief summary of total costs, cost per attendee, comparison to
budget, and key findings. Complete this section after filling in all
detail sections below.]

| Metric | Value |
|--------|-------|
| Total Infrastructure Cost | $PLACEHOLDER_TOTAL |
| Total Licensing Cost | $PLACEHOLDER_LICENSING |
| Grand Total | $PLACEHOLDER_GRAND_TOTAL |
| Actual Attendees | PLACEHOLDER_ATTENDEE_COUNT |
| Cost Per Attendee | $PLACEHOLDER_COST_PER_ATTENDEE |
| Budget Variance | $PLACEHOLDER_VARIANCE (PLACEHOLDER_PERCENT%) |
| Environment Active Duration | PLACEHOLDER_DAYS days |

---

## 2. AWS Costs Breakdown

### 2.1 EC2 / Compute Costs

Compute costs for all OpenShift cluster nodes across all clusters.

| Resource | Clusters | Instance Type | Count per Cluster | Hours | Unit Cost/hr | Subtotal |
|----------|----------|---------------|-------------------|-------|-------------|----------|
| Control plane nodes | 56 | PLACEHOLDER_INSTANCE_TYPE | 3 | PLACEHOLDER_HOURS | $PLACEHOLDER_RATE | $PLACEHOLDER_SUBTOTAL |
| Worker nodes | 56 | PLACEHOLDER_INSTANCE_TYPE | 3 | PLACEHOLDER_HOURS | $PLACEHOLDER_RATE | $PLACEHOLDER_SUBTOTAL |
| Infrastructure nodes | 56 | PLACEHOLDER_INSTANCE_TYPE | 2 | PLACEHOLDER_HOURS | $PLACEHOLDER_RATE | $PLACEHOLDER_SUBTOTAL |
| ACM hub nodes | 1 | PLACEHOLDER_INSTANCE_TYPE | 3 | PLACEHOLDER_HOURS | $PLACEHOLDER_RATE | $PLACEHOLDER_SUBTOTAL |
| **EC2 Total** | | | | | | **$PLACEHOLDER_EC2_TOTAL** |

Notes:

- Cluster breakdown: 50 attendee + 5 spare + 1 facilitator = 56 clusters,
  plus 1 ACM hub.
- Hours reflect total provisioned time from cluster creation through
  teardown, not just the event day.
- Include any additional nodes added during the preparation phase.

### 2.2 S3 Storage Costs

Object storage for Loki log data per cluster.

| Resource | Count | Storage (GB) | Requests | Storage Cost | Request Cost | Subtotal |
|----------|-------|-------------|----------|-------------|-------------|----------|
| Attendee Loki buckets | 50 | PLACEHOLDER_GB | PLACEHOLDER_REQUESTS | $PLACEHOLDER_STORAGE | $PLACEHOLDER_REQUESTS_COST | $PLACEHOLDER_SUBTOTAL |
| Spare Loki buckets | 5 | PLACEHOLDER_GB | PLACEHOLDER_REQUESTS | $PLACEHOLDER_STORAGE | $PLACEHOLDER_REQUESTS_COST | $PLACEHOLDER_SUBTOTAL |
| Facilitator Loki bucket | 1 | PLACEHOLDER_GB | PLACEHOLDER_REQUESTS | $PLACEHOLDER_STORAGE | $PLACEHOLDER_REQUESTS_COST | $PLACEHOLDER_SUBTOTAL |
| **S3 Total** | | | | | | **$PLACEHOLDER_S3_TOTAL** |

Notes:

- Storage includes application, infrastructure, and audit logs.
- Request costs cover PUT, GET, LIST, and DELETE operations.
- Lifecycle policies should expire data after the configured retention
  period.

### 2.3 Data Transfer Costs

| Resource | Direction | Volume (GB) | Unit Cost/GB | Subtotal |
|----------|-----------|-------------|-------------|----------|
| Cluster-to-S3 (same region) | Internal | PLACEHOLDER_GB | $0.00 | $0.00 |
| Cross-region transfer (if any) | Inter-region | PLACEHOLDER_GB | $PLACEHOLDER_RATE | $PLACEHOLDER_SUBTOTAL |
| Internet egress (attendee access) | Outbound | PLACEHOLDER_GB | $PLACEHOLDER_RATE | $PLACEHOLDER_SUBTOTAL |
| NAT Gateway processing | N/A | PLACEHOLDER_GB | $PLACEHOLDER_RATE | $PLACEHOLDER_SUBTOTAL |
| **Data Transfer Total** | | | | **$PLACEHOLDER_TRANSFER_TOTAL** |

### 2.4 IAM and Security Costs

| Resource | Count | Cost |
|----------|-------|------|
| IAM users/roles for S3 access | 56 | $0.00 (no charge) |
| KMS keys for S3 encryption | PLACEHOLDER_COUNT | $PLACEHOLDER_KMS_COST |
| KMS API requests | PLACEHOLDER_COUNT | $PLACEHOLDER_KMS_API_COST |
| Secrets Manager secrets | PLACEHOLDER_COUNT | $PLACEHOLDER_SECRETS_COST |
| **IAM/Security Total** | | **$PLACEHOLDER_IAM_TOTAL** |

### 2.5 Route 53 / DNS Costs

| Resource | Count | Cost |
|----------|-------|------|
| Hosted zones | PLACEHOLDER_COUNT | $PLACEHOLDER_ZONE_COST |
| DNS queries | PLACEHOLDER_COUNT | $PLACEHOLDER_QUERY_COST |
| **DNS Total** | | **$PLACEHOLDER_DNS_TOTAL** |

### 2.6 Other AWS Costs

| Resource | Description | Cost |
|----------|-------------|------|
| EBS volumes | Persistent storage for nodes and PVCs | $PLACEHOLDER_EBS_COST |
| Elastic Load Balancers | Ingress controllers per cluster | $PLACEHOLDER_ELB_COST |
| Elastic IPs | If allocated | $PLACEHOLDER_EIP_COST |
| CloudWatch (if used) | Metrics and log monitoring | $PLACEHOLDER_CW_COST |
| Support plan (proportional) | Allocated portion of support plan | $PLACEHOLDER_SUPPORT_COST |
| **Other AWS Total** | | **$PLACEHOLDER_OTHER_AWS_TOTAL** |

### AWS Grand Total

| Category | Cost |
|----------|------|
| EC2 / Compute | $PLACEHOLDER_EC2_TOTAL |
| S3 Storage | $PLACEHOLDER_S3_TOTAL |
| Data Transfer | $PLACEHOLDER_TRANSFER_TOTAL |
| IAM / Security | $PLACEHOLDER_IAM_TOTAL |
| DNS | $PLACEHOLDER_DNS_TOTAL |
| Other AWS | $PLACEHOLDER_OTHER_AWS_TOTAL |
| **AWS Grand Total** | **$PLACEHOLDER_AWS_GRAND_TOTAL** |

---

## 3. OpenShift Licensing Costs

| Resource | Count | License Model | Duration | Cost |
|----------|-------|---------------|----------|------|
| Attendee clusters | 50 | PLACEHOLDER_LICENSE_MODEL | PLACEHOLDER_DURATION | $PLACEHOLDER_OCP_ATTENDEE |
| Spare clusters | 5 | PLACEHOLDER_LICENSE_MODEL | PLACEHOLDER_DURATION | $PLACEHOLDER_OCP_SPARE |
| Facilitator cluster | 1 | PLACEHOLDER_LICENSE_MODEL | PLACEHOLDER_DURATION | $PLACEHOLDER_OCP_FACILITATOR |
| ACM hub cluster | 1 | PLACEHOLDER_LICENSE_MODEL | PLACEHOLDER_DURATION | $PLACEHOLDER_OCP_HUB |
| ACM hub license | 1 | PLACEHOLDER_LICENSE_MODEL | PLACEHOLDER_DURATION | $PLACEHOLDER_ACM_LICENSE |
| **OpenShift Total** | | | | **$PLACEHOLDER_OCP_TOTAL** |

Notes:

- Specify whether clusters use subscription, PAYG, or event/trial licensing.
- If using ROSA, note the ROSA service fee separately.
- ACM licensing may be bundled with OpenShift Platform Plus.

---

## 4. IBM MAS Licensing Costs

| Resource | Count | License Model | Duration | Cost |
|----------|-------|---------------|----------|------|
| MAS Core entitlements | PLACEHOLDER_COUNT | PLACEHOLDER_LICENSE_MODEL | PLACEHOLDER_DURATION | $PLACEHOLDER_MAS_CORE |
| Maximo Manage entitlements | PLACEHOLDER_COUNT | PLACEHOLDER_LICENSE_MODEL | PLACEHOLDER_DURATION | $PLACEHOLDER_MANAGE |
| AppConnect (if required) | PLACEHOLDER_COUNT | PLACEHOLDER_LICENSE_MODEL | PLACEHOLDER_DURATION | $PLACEHOLDER_APPCONNECT |
| MongoDB (if IBM-provided) | PLACEHOLDER_COUNT | PLACEHOLDER_LICENSE_MODEL | PLACEHOLDER_DURATION | $PLACEHOLDER_MONGODB |
| Other IBM components | PLACEHOLDER_COUNT | PLACEHOLDER_LICENSE_MODEL | PLACEHOLDER_DURATION | $PLACEHOLDER_OTHER_IBM |
| **IBM MAS Total** | | | | **$PLACEHOLDER_MAS_TOTAL** |

Notes:

- Specify whether licensing is per-cluster, per-user, per-AppPoint, or
  event/trial.
- Note any special event licensing arrangements.
- Include IBM entitlement key scope and expiration.

---

## 5. Other Infrastructure Costs

| Resource | Description | Cost |
|----------|-------------|------|
| Container registry | Image hosting and bandwidth | $PLACEHOLDER_REGISTRY |
| Git hosting | Repository hosting | $PLACEHOLDER_GIT |
| CI/CD pipeline | Build minutes and compute | $PLACEHOLDER_CICD |
| Domain registration (if new) | DNS domain for the event | $PLACEHOLDER_DOMAIN |
| TLS certificates (if purchased) | Wildcard or individual certs | $PLACEHOLDER_CERTS |
| Monitoring/alerting service | External monitoring if used | $PLACEHOLDER_MONITORING |
| Backup storage | Pre-event snapshots | $PLACEHOLDER_BACKUP |
| **Other Infrastructure Total** | | **$PLACEHOLDER_OTHER_INFRA_TOTAL** |

---

## 6. Cost Per Attendee

| Metric | Value |
|--------|-------|
| Total Event Cost (all categories) | $PLACEHOLDER_GRAND_TOTAL |
| Actual Attendees | PLACEHOLDER_ATTENDEE_COUNT |
| **Cost Per Attendee** | **$PLACEHOLDER_COST_PER_ATTENDEE** |

### Cost per attendee breakdown

| Category | Total Cost | Per Attendee |
|----------|-----------|-------------|
| AWS Infrastructure | $PLACEHOLDER_AWS_GRAND_TOTAL | $PLACEHOLDER_PER_ATTENDEE_AWS |
| OpenShift Licensing | $PLACEHOLDER_OCP_TOTAL | $PLACEHOLDER_PER_ATTENDEE_OCP |
| IBM MAS Licensing | $PLACEHOLDER_MAS_TOTAL | $PLACEHOLDER_PER_ATTENDEE_MAS |
| Other Infrastructure | $PLACEHOLDER_OTHER_INFRA_TOTAL | $PLACEHOLDER_PER_ATTENDEE_OTHER |
| **Total** | **$PLACEHOLDER_GRAND_TOTAL** | **$PLACEHOLDER_COST_PER_ATTENDEE** |

### Marginal cost analysis

| Metric | Value |
|--------|-------|
| Cost if 50 attendees (planned) | $PLACEHOLDER_PLANNED_TOTAL |
| Cost if 40 attendees | $PLACEHOLDER_40_TOTAL |
| Cost if 30 attendees | $PLACEHOLDER_30_TOTAL |
| Marginal cost per additional attendee | $PLACEHOLDER_MARGINAL |

Notes:

- Marginal cost is primarily the cost of one additional OpenShift cluster
  plus its S3 storage. Licensing may also scale per attendee.
- Spare and facilitator clusters are fixed overhead.

---

## 7. Budget Comparison

| Line Item | Budgeted | Actual | Variance | Variance % |
|-----------|----------|--------|----------|------------|
| AWS Compute | $PLACEHOLDER_BUDGET | $PLACEHOLDER_ACTUAL | $PLACEHOLDER_VAR | PLACEHOLDER_PCT% |
| AWS Storage | $PLACEHOLDER_BUDGET | $PLACEHOLDER_ACTUAL | $PLACEHOLDER_VAR | PLACEHOLDER_PCT% |
| AWS Data Transfer | $PLACEHOLDER_BUDGET | $PLACEHOLDER_ACTUAL | $PLACEHOLDER_VAR | PLACEHOLDER_PCT% |
| AWS Other | $PLACEHOLDER_BUDGET | $PLACEHOLDER_ACTUAL | $PLACEHOLDER_VAR | PLACEHOLDER_PCT% |
| OpenShift Licensing | $PLACEHOLDER_BUDGET | $PLACEHOLDER_ACTUAL | $PLACEHOLDER_VAR | PLACEHOLDER_PCT% |
| IBM MAS Licensing | $PLACEHOLDER_BUDGET | $PLACEHOLDER_ACTUAL | $PLACEHOLDER_VAR | PLACEHOLDER_PCT% |
| Other Infrastructure | $PLACEHOLDER_BUDGET | $PLACEHOLDER_ACTUAL | $PLACEHOLDER_VAR | PLACEHOLDER_PCT% |
| **Grand Total** | **$PLACEHOLDER_BUDGET_TOTAL** | **$PLACEHOLDER_ACTUAL_TOTAL** | **$PLACEHOLDER_TOTAL_VAR** | **PLACEHOLDER_TOTAL_PCT%** |

### Variance explanations

[For each line item with significant variance (>10%), explain the root
cause.]

- **[Line item]**: [Explanation of why actual differed from budget]
- **[Line item]**: [Explanation]

---

## 8. Cost Optimization Recommendations

### Immediate savings (applicable to future events)

| Recommendation | Estimated Savings | Effort |
|---------------|-------------------|--------|
| Use reserved or spot instances for worker nodes during preparation | $PLACEHOLDER_SAVINGS | Medium |
| Reduce spare cluster count if failure rate is low | $PLACEHOLDER_SAVINGS | Low |
| Use smaller instance types for preparation/rehearsal phases | $PLACEHOLDER_SAVINGS | Low |
| Consolidate S3 buckets with prefix isolation (evaluate security tradeoff) | $PLACEHOLDER_SAVINGS | Medium |
| Shorten environment active duration by automating faster provisioning | $PLACEHOLDER_SAVINGS | High |

### Structural optimizations (require architectural changes)

| Recommendation | Estimated Savings | Effort |
|---------------|-------------------|--------|
| Use shared MAS control plane with tenant isolation | $PLACEHOLDER_SAVINGS | High |
| Use managed database service instead of per-cluster databases | $PLACEHOLDER_SAVINGS | High |
| Evaluate MAS SaaS for workshop scenarios | $PLACEHOLDER_SAVINGS | High |
| Pool clusters across events using RHDP cluster pools | $PLACEHOLDER_SAVINGS | Medium |

### Licensing optimizations

| Recommendation | Estimated Savings | Effort |
|---------------|-------------------|--------|
| Negotiate event-specific licensing terms | $PLACEHOLDER_SAVINGS | Medium |
| Evaluate IBM Flex Points for MAS licensing | $PLACEHOLDER_SAVINGS | Low |
| Confirm ROSA licensing includes ACM entitlement | $PLACEHOLDER_SAVINGS | Low |

---

## 9. Data Retention Costs (Ongoing)

After the event, some resources continue to incur costs until explicitly
decommissioned.

| Resource | Retention Period | Monthly Cost | Total Until Deletion |
|----------|-----------------|-------------|---------------------|
| S3 Loki buckets (if retained) | PLACEHOLDER_DAYS days | $PLACEHOLDER_MONTHLY | $PLACEHOLDER_TOTAL |
| EBS snapshots (if retained) | PLACEHOLDER_DAYS days | $PLACEHOLDER_MONTHLY | $PLACEHOLDER_TOTAL |
| Secrets Manager secrets | Until revoked | $PLACEHOLDER_MONTHLY | $PLACEHOLDER_TOTAL |
| KMS keys | Until deleted | $PLACEHOLDER_MONTHLY | $PLACEHOLDER_TOTAL |
| DNS hosted zones | Until deleted | $PLACEHOLDER_MONTHLY | $PLACEHOLDER_TOTAL |
| **Ongoing Monthly Total** | | **$PLACEHOLDER_ONGOING_MONTHLY** | |

---

## 10. Teardown Cost Savings Timeline

This table shows the cumulative savings from tearing down resources after
the event.

| Action | Timing | Resources Freed | Monthly Savings |
|--------|--------|----------------|-----------------|
| Terminate attendee cluster nodes | Day 1 post-event | 50 clusters x N nodes | $PLACEHOLDER_MONTHLY |
| Terminate spare cluster nodes | Day 1 post-event | 5 clusters x N nodes | $PLACEHOLDER_MONTHLY |
| Delete S3 Loki data | Day PLACEHOLDER post-event | 56 S3 buckets | $PLACEHOLDER_MONTHLY |
| Revoke IAM credentials | Day 1 post-event | 56 IAM principals | $0 (security action) |
| Delete KMS keys (schedule) | Day 7 post-event | PLACEHOLDER_COUNT keys | $PLACEHOLDER_MONTHLY |
| Delete Secrets Manager secrets | Day 7 post-event | PLACEHOLDER_COUNT secrets | $PLACEHOLDER_MONTHLY |
| Delete DNS hosted zones | Day 30 post-event | PLACEHOLDER_COUNT zones | $PLACEHOLDER_MONTHLY |
| Terminate ACM hub | Day 7 post-event | 1 cluster | $PLACEHOLDER_MONTHLY |
| Terminate facilitator cluster | Day 7 post-event | 1 cluster | $PLACEHOLDER_MONTHLY |

### Teardown progress tracking

| Action | Scheduled Date | Completed Date | Completed By | Verified |
|--------|---------------|----------------|-------------|----------|
| Terminate attendee clusters | PLACEHOLDER_DATE | | | [ ] |
| Terminate spare clusters | PLACEHOLDER_DATE | | | [ ] |
| Delete S3 data | PLACEHOLDER_DATE | | | [ ] |
| Revoke IAM credentials | PLACEHOLDER_DATE | | | [ ] |
| Schedule KMS key deletion | PLACEHOLDER_DATE | | | [ ] |
| Delete secrets | PLACEHOLDER_DATE | | | [ ] |
| Delete DNS zones | PLACEHOLDER_DATE | | | [ ] |
| Terminate ACM hub | PLACEHOLDER_DATE | | | [ ] |
| Terminate facilitator | PLACEHOLDER_DATE | | | [ ] |
| Final AWS cost verification | PLACEHOLDER_DATE | | | [ ] |

---

## 11. Cost Data Sources

| Source | Description | Access |
|--------|-------------|--------|
| AWS Cost Explorer | Detailed AWS billing data | PLACEHOLDER_AWS_CONSOLE_URL |
| AWS Cost and Usage Report | Granular usage-level data | S3 export at PLACEHOLDER_CUR_BUCKET |
| IBM License Metric Tool | MAS license usage | PLACEHOLDER_ILMT_URL |
| Red Hat Subscription Manager | OpenShift entitlement | PLACEHOLDER_RHSM_URL |
| CI/CD billing dashboard | Pipeline compute costs | PLACEHOLDER_CICD_URL |

---

## 12. Approvals

| Role | Name | Approved | Date |
|------|------|----------|------|
| Lab Owner | Francis Anyaegbu | [ ] | |
| Presenter | Ernie Steagall | [ ] | |
| Observability Lead | Myles Vivian | [ ] | |
| Budget Owner | [Name] | [ ] | |
