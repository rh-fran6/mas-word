# Fleet Sizing Guide --- MAS World 2026

**Status**: DRAFT --- Phase 0
**Date**: 2026-07-19

---

## 1. Per-Cluster Resource Requirements

The following table lists estimated resource requirements for all components
installed on each attendee cluster. These are **workshop-grade estimates** for
planning purposes only.

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit | Storage | Notes |
|-----------|-------------|-----------|----------------|--------------|---------|-------|
| MAS Core operators | 2 | 4 | 4 Gi | 8 Gi | - | Operator pods (SLS operator, Suite operator, etc.) |
| Maximo Manage | 4 | 8 | 8 Gi | 16 Gi | 100 Gi RWX | Application server, ServerBundle pods |
| Db2 (in-cluster) | 4 | 8 | 8 Gi | 16 Gi | 100 Gi RWO | Database engine for Manage |
| MongoDB | 1 | 2 | 2 Gi | 4 Gi | 50 Gi RWO | MAS configuration store |
| IBM SLS | 0.5 | 1 | 1 Gi | 2 Gi | - | Suite License Service |
| cert-manager | 0.5 | 1 | 0.5 Gi | 1 Gi | - | Certificate management |
| OpenShift Logging Operator | 0.5 | 1 | 0.5 Gi | 1 Gi | - | Log collection configuration |
| Loki Operator | 0.5 | 1 | 0.5 Gi | 1 Gi | - | LokiStack management |
| LokiStack (1x.extra-small) | 2 | 4 | 4 Gi | 8 Gi | 50 Gi RWO + S3 | Log storage and query |
| Vector (collector) | 0.5 | 1 | 0.5 Gi | 1 Gi | - | Per-node DaemonSet (3 nodes) |
| COO | 0.5 | 1 | 0.5 Gi | 1 Gi | - | Cluster Observability Operator |
| Keycloak | 1 | 2 | 1 Gi | 2 Gi | - | Identity provider for workshop demo |
| OpenLDAP | 0.25 | 0.5 | 256 Mi | 512 Mi | 1 Gi | Directory service for group sync demo |
| Showroom | 0.5 | 1 | 0.5 Gi | 1 Gi | - | Workshop UI and browser terminal |
| **TOTAL (estimated)** | **~18** | **~36** | **~32 Gi** | **~64 Gi** | **~301 Gi** | |

> **NOTE**: These numbers are estimates derived from documentation and workshop
> experience. Actual resource consumption must be validated on a reference
> cluster during Phase 2. Vector collector resources are per node and shown as
> a single instance above; multiply by worker count for total.

---

## 2. Worker Node Sizing

### Minimum configuration

| Property | Value |
|----------|-------|
| Worker count | 3 |
| Instance type | m5.4xlarge (or equivalent) |
| vCPU per node | 16 |
| Memory per node | 64 GiB |
| Total vCPU | 48 |
| Total memory | 192 GiB |

### Rationale

With approximately 18 vCPU requested and 32 Gi memory requested by workshop
components, 3 x m5.4xlarge nodes provide:

- Sufficient capacity for all workshop components
- Headroom for OpenShift platform pods (~8-10 vCPU, ~16-20 Gi)
- Room for burst usage during exercises
- Tolerance for one node entering maintenance

### Storage classes

| Storage class | Type | Use case |
|---------------|------|----------|
| gp3-csi | EBS (RWO) | Db2, MongoDB, LokiStack WAL |
| efs-csi | EFS (RWX) | Maximo Manage application storage |

### Alternative instance types

| Instance type | vCPU | Memory | Notes |
|---------------|------|--------|-------|
| m5.4xlarge | 16 | 64 GiB | Recommended baseline |
| m5.2xlarge | 8 | 32 GiB | Insufficient for full MAS stack |
| m6i.4xlarge | 16 | 64 GiB | Newer generation, comparable |
| m5.8xlarge | 32 | 128 GiB | Allows 2-node cluster (reduced HA) |

---

## 3. S3 Storage Estimates

### Per-cluster storage

| Metric | Estimate |
|--------|----------|
| Log volume per cluster (workshop duration) | 1--5 GB |
| Retention period | 7 days (workshop active) |
| Lifecycle expiration | 30 days post-event |
| Bucket naming | `mas-world-2026-{cluster-id}-loki-{suffix}` |

### Fleet-wide storage

| Fleet | Clusters | Storage estimate | Notes |
|-------|----------|------------------|-------|
| Development | 2 | 2--10 GB | Minimal log volume |
| Rehearsal | 7 | 7--35 GB | Simulated attendee activity |
| Event | 56 | 56--280 GB | Full fleet with concurrent exercises |

### S3 cost estimate (us-east-2)

| Item | Unit cost | Event estimate |
|------|-----------|----------------|
| Storage (S3 Standard) | $0.023/GB/month | $1.30--6.50/month |
| PUT requests | $0.005/1000 | Negligible for workshop |
| GET requests | $0.0004/1000 | Negligible for workshop |
| Data transfer (same region) | Free | Loki to S3 in same region |

---

## 4. ACM Hub Capacity

### Hub cluster sizing

| Property | Value |
|----------|-------|
| Managed clusters | 56 (50 attendee + 5 spare + 1 facilitator) |
| Recommended worker count | 3 |
| Recommended instance type | m5.2xlarge (8 vCPU, 32 GiB each) |
| Total hub compute | 24 vCPU, 96 GiB |

### ACM resource overhead

| Function | Impact |
|----------|--------|
| Search indexing | Indexes resources across all 56 managed clusters |
| Policy propagation | Evaluates governance policies on every managed cluster |
| Governance status | Aggregates compliance status for fleet dashboard |
| Placement engine | Computes placement decisions for ManagedClusterSets |
| Agent connections | 56 concurrent klusterlet agent connections |

### ACM considerations

- Search queries during the presenter demo will hit all 56 clusters
  simultaneously.
- Policy evaluation runs on a configurable interval (default 10 seconds for
  `inform` mode).
- The hub must be prepared and validated before attendee clusters are
  registered.

---

## 5. AWS API Rate Limits and Concurrent Preparation

### Default concurrency

| Parameter | Default | Notes |
|-----------|---------|-------|
| `max_concurrent_clusters` | 5 | Conservative to avoid API throttling |
| `per_cluster_timeout_minutes` | 240 | MAS installation is the bottleneck |
| `retry_count` | 3 | Exponential backoff between retries |

### Rate limit considerations

| AWS service | Default limit | Concern | Mitigation |
|-------------|--------------|---------|------------|
| S3 bucket creation | 100 buckets per account | 56 buckets needed; within limit | Stagger creation |
| IAM user creation | 5000 users per account | 56 users needed; well within limit | None required |
| IAM API rate | 10 requests/second (sustained) | Concurrent IAM policy creation | Stagger with 1-second delay |
| EC2 API rate | Varies by action | Node scaling during prep | Limit concurrent cluster prep |
| Secrets Manager | 5000 requests/second | Secret retrieval during fleet prep | Within limits |

### External service rate limits

| Service | Concern | Mitigation |
|---------|---------|------------|
| IBM container registry | Pull rate limits on entitlement registry | Stagger image pulls; pre-pull during off-peak |
| Red Hat container registry | Authenticated pull limits | Use pull secret; stagger |
| OperatorHub | Operator catalog fetches | Pre-cache catalog sources |
| Git hosting | Clone/fetch during Showroom deployment | Cache repositories |

---

## 6. Fleet Composition

| Environment | Attendee clusters | Spare clusters | Facilitator clusters | Total clusters |
|-------------|-------------------|----------------|----------------------|----------------|
| Development | 1 | 0 | 1 | 2 |
| Rehearsal | 5 | 1 | 1 | 7 |
| Event | 50 | 5 | 1 | 56 |

### Spare cluster rationale

- 10% spare capacity provides coverage for hardware failure, software
  corruption, or attendee overflow.
- Spare clusters are fully prepared and validated but not assigned to a seat.
- Reassignment from spare to attendee is a single documented command.
- Spare clusters remain in the `unassigned` state until needed.

### Facilitator cluster purpose

- Hosts the pre-staged ACM drift condition for the governance demo.
- Used by Ernie for the live presenter demonstration.
- Carries the deliberately noncompliant policy for remediation.
- Not assigned to any attendee seat.

---

## 7. Preparation Time Estimates

### Per-cluster preparation breakdown

| Stage | Estimated duration | Notes |
|-------|-------------------|-------|
| Preflight validation | 2--5 minutes | API checks, capacity validation |
| ACM registration | 3--5 minutes | Import and label assignment |
| MAS prerequisites | 15--30 minutes | cert-manager, MongoDB, SLS, operators |
| MAS Core installation | 30--60 minutes | Operator install and Suite CR readiness |
| Maximo Manage activation | 60--120 minutes | Application deployment and database setup |
| Logging stack | 10--20 minutes | Logging Operator, Loki Operator, LokiStack |
| S3 bucket and IAM setup | 2--5 minutes | Bucket creation, IAM user, policy |
| ClusterLogForwarder | 2--5 minutes | Log forwarding configuration |
| Identity components | 5--10 minutes | Keycloak, OpenLDAP, OAuth configuration |
| Student accounts | 2--5 minutes | htpasswd, RBAC, namespace |
| Showroom deployment | 5--10 minutes | Workshop UI and runtime automation |
| Readiness validation | 5--10 minutes | End-to-end health checks |
| **Total per cluster** | **2--4 hours** | **MAS is the primary bottleneck** |

### Fleet preparation estimates

| Scenario | Concurrency | Total time estimate | Notes |
|----------|-------------|---------------------|-------|
| Sequential (1 at a time) | 1 | 112--224 hours | Not recommended |
| Low concurrency | 3 | 38--75 hours | Conservative |
| Default concurrency | 5 | 23--45 hours | Recommended |
| High concurrency | 10 | 12--23 hours | Risk of API throttling |

### Preparation timeline recommendation

| Milestone | Time before event |
|-----------|-------------------|
| Begin fleet preparation | T-72 hours minimum |
| Fleet preparation complete | T-24 hours |
| Final fleet validation | T-12 hours |
| Credential rotation | T-6 hours |
| Final readiness check | T-2 hours |
| Access card generation | T-1 hour |

> **RECOMMENDATION**: Begin fleet preparation at least 72 hours before the
> event (August 14, 2026 for the August 17 event). This provides buffer for
> failures, retries, and spare cluster preparation.

---

## 8. Workshop vs. Production Sizing

> **IMPORTANT**: The resource numbers in this document are sized for a
> single-day, single-user-per-cluster workshop environment. They are NOT
> suitable for production deployments.

| Dimension | Workshop sizing | Production considerations |
|-----------|----------------|--------------------------|
| MAS replicas | Single replica per component | Multiple replicas for HA |
| Database | Single Db2 instance (in-cluster) | External HA database service (e.g., RDS, Db2 Warehouse) |
| MongoDB | Single replica set | 3+ member replica set with dedicated storage |
| LokiStack size | `1x.extra-small` | `1x.medium` or larger based on log volume |
| Loki retention | 7 days | Months to years depending on compliance |
| S3 storage | 1--5 GB per cluster | Terabytes depending on log volume and retention |
| Worker nodes | 3 x m5.4xlarge | Sized per IBM and Red Hat capacity planning tools |
| Keycloak | Single pod, ephemeral | HA deployment with persistent storage and external DB |
| Certificates | Self-signed or Let's Encrypt | Enterprise CA-signed with automated renewal |
| Monitoring | Workshop readiness checks | Full Prometheus/Grafana stack with alerting |
| Backup | None (workshop is ephemeral) | Regular automated backups with tested restore |
| DR | Spare cluster reassignment | Multi-site or multi-region disaster recovery |
| Network policy | Default OpenShift isolation | Fine-grained NetworkPolicy per namespace |
| Log forwarding | S3 only | SIEM integration (Splunk, CloudWatch, ELK) |

Production environments should follow IBM's official MAS sizing guidance and
Red Hat's OpenShift capacity planning documentation. The workshop
configuration intentionally uses minimal resource allocations to reduce cost
and preparation time for a time-bounded event.
