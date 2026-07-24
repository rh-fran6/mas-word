# MAS Operations -- Production Guidance

This document covers production operational considerations for IBM Maximo
Application Suite on OpenShift. The workshop environment is simplified for
demonstration purposes.

> **Workshop operations are NOT production operations.** The workshop uses
> minimal sizing, abbreviated procedures, and demonstration data.
> Production MAS deployments require comprehensive planning across backup,
> updates, monitoring, and disaster recovery.

## Backup strategy

### What to back up

| Component | Method | Frequency |
|---|---|---|
| MAS configuration (CRs) | `oc get` exports, GitOps | After every change |
| Maximo Manage database | Database-native backup (pg_dump, db2 backup) | Daily + before updates |
| Persistent volumes | CSI snapshots or backup tool (OADP) | Daily |
| Certificates and secrets | Vault export or sealed-secret backup | After rotation |
| OpenShift cluster state | etcd backup | Daily + before updates |
| S3 log data | S3 cross-region replication | Continuous |

### Backup tools
- **OADP** (OpenShift API for Data Protection): Velero-based backup for
  Kubernetes resources and persistent volumes.
- **Database-native tools**: Use the database vendor's backup utilities
  for consistent database snapshots.
- **GitOps**: Store all declarative configuration in Git for versioned
  recovery.

### Backup validation
- Test restoration quarterly.
- Document recovery time objectives (RTO) and recovery point objectives
  (RPO).
- Maintain runbooks for each recovery scenario.

## Update planning

### Pre-update checklist

1. Review IBM release notes and compatibility matrix.
2. Verify OpenShift version compatibility with the target MAS version.
3. Check operator channel and update graph.
4. Back up the database and critical persistent volumes.
5. Back up MAS custom resources.
6. Verify cluster health (no degraded operators, sufficient capacity).
7. Notify stakeholders and schedule a maintenance window.
8. Prepare rollback procedure.
9. Test the update on a non-production environment first.

### Update sequence

```text
1. OpenShift platform update (if required)
2. Operator catalog update
3. MAS Core operator update
4. MAS application operator updates (Manage, etc.)
5. Post-update validation
6. Database migration verification
7. Functional testing
8. Performance baseline comparison
```

### Post-update validation

- Verify all MAS custom resources report Ready status.
- Test user login through all identity providers.
- Verify Maximo Manage functionality (create/view work orders).
- Check database connectivity and data integrity.
- Verify integrations (email, LDAP sync, external systems).
- Monitor error rates for 24--48 hours.

## Maintenance windows

- Schedule maintenance during low-usage periods.
- Communicate windows at least 1 week in advance.
- Duration: plan for 2--4 hours for MAS updates.
- Have rollback capability within the maintenance window.
- Maintain a war-room communication channel during updates.

## Monitoring

### Key metrics to monitor

| Metric | Source | Alert threshold |
|---|---|---|
| MAS pod health | Kubernetes | Any pod not Running for > 5 min |
| Database connections | Database metrics | > 80% pool utilization |
| API response time | Application metrics | p95 > 5 seconds |
| Storage utilization | PVC metrics | > 85% capacity |
| Certificate expiry | cert-manager / manual | < 30 days to expiry |
| Operator health | OLM | CSV not Succeeded |
| Node resources | Kubernetes | CPU/memory > 80% |

### Monitoring tools
- OpenShift built-in monitoring (Prometheus + Grafana).
- Cluster Observability Operator for extended dashboards.
- IBM Maximo health APIs for application-level monitoring.
- External monitoring (Datadog, Dynatrace, etc.) for unified views.

## Capacity planning

### Compute resources (per cluster)

| Component | CPU request | Memory request | Notes |
|---|---|---|---|
| MAS Core | 4--8 cores | 8--16 GB | Varies by configuration |
| Maximo Manage | 8--16 cores | 16--32 GB | Depends on user count |
| Database | 4--8 cores | 16--32 GB | Depends on data volume |
| Logging stack | 2--4 cores | 4--8 GB | Depends on log volume |
| Keycloak | 1--2 cores | 2--4 GB | Per replica |

These are estimates. Size based on actual workload testing.

### Storage

- Database: 100+ GB SSD (depends on data volume).
- Persistent volumes for MAS: 50+ GB.
- Loki WAL: 50+ GB fast storage per ingester.
- S3: depends on log volume and retention.

### Worker nodes
- Minimum 3 worker nodes for HA.
- 5+ workers recommended for production MAS workloads.
- Use dedicated nodes for database workloads where possible.

## Database management

### Connection management
- Configure connection pooling.
- Monitor active connections vs. pool size.
- Set appropriate connection timeouts.
- Close idle connections to prevent pool exhaustion.

### Performance
- Monitor slow queries.
- Maintain database statistics and indexes.
- Schedule maintenance tasks (vacuum, reindex) during off-hours.
- Monitor tablespace growth.

### Security
- Use dedicated database users per application component.
- Rotate database credentials on a regular schedule.
- Enable audit logging on the database.
- Encrypt data at rest and in transit.
- Restrict network access to the database.

## Disaster recovery

### Scenarios and responses

| Scenario | RTO target | Recovery method |
|---|---|---|
| Pod failure | Minutes | Kubernetes self-healing |
| Node failure | Minutes | Pod rescheduling + PV reattach |
| Database corruption | 1--4 hours | Restore from backup |
| Cluster failure | 4--8 hours | Rebuild cluster + restore |
| Region failure | 8--24 hours | Failover to DR region |

### DR planning
- Document the recovery procedure for each scenario.
- Test DR procedures at least annually.
- Maintain a secondary environment for critical workloads.
- Ensure backups are stored in a separate failure domain.
- Keep runbooks updated and accessible during an outage.

## Cost management

- Monitor cloud infrastructure costs (compute, storage, network).
- Use reserved instances or savings plans for steady-state workloads.
- Implement resource quotas and limit ranges.
- Review and right-size resource requests quarterly.
- Clean up unused persistent volumes and S3 data.
- Tag all cloud resources for cost allocation.
