# Troubleshooting

## Cluster Stuck in "installing" State

Clusters typically take 15-30 minutes to reach "ready". If a cluster is stuck beyond 45 minutes:

```bash
# Check cluster status
rosa describe cluster --cluster=lab-seat-01

# Check installation logs
rosa logs install --cluster=lab-seat-01 --watch
```

Common causes:
- Insufficient EC2 quota in the AWS account
- Subnet misconfiguration (no NAT gateway, wrong route tables)
- AWS account not enrolled in ROSA

## AWS Credentials Expired

If credentials expire mid-provisioning:

1. Generate new credentials in the AWS account
2. Update `secrets/cluster-credentials.yml`
3. Re-run `make provision` — ROSA handles existing clusters gracefully

## Subnet Not Found

```
Error: The subnet ID 'subnet-xxx' does not exist
```

Verify the subnet exists in the correct region:

```bash
aws ec2 describe-subnets --subnet-ids subnet-xxx --region us-east-1
```

## EC2 Quota Exceeded

```
Error: You have requested more vCPU capacity than your current limit
```

Request a quota increase:

```bash
aws service-quotas request-service-quota-increase \
  --service-code ec2 \
  --quota-code L-1216C47A \
  --desired-value 100
```

## Async Job Timed Out

If cluster creation times out during the `rosa create cluster` command:

1. Increase `rosa_create_async_timeout` in `group_vars/all/rosa_defaults.yml`
2. Increase `rosa_create_async_retries` for longer polling

```yaml
rosa_create_async_timeout: 600   # 10 minutes for CLI to return
rosa_create_async_retries: 120   # More retries
```

## Partial Failure Recovery

If some clusters succeed and others fail:

1. Fix the underlying issue (credentials, quotas, etc.)
2. Re-run `make provision`

The `rosa create cluster` command is idempotent for existing clusters — it will skip already-created clusters and only create the missing ones.

## Preflight Check Failures

### "No credentials found for cluster 'xxx'"

The credential key in `secrets/cluster-credentials.yml` doesn't match the generated name.

Generated names follow: `{prefix}-{category}-{index}`
- Seats are zero-padded: `seat-01`, not `seat-1`
- Other categories use plain integers: `hub-1`, `facilitator-1`

### "rosa: command not found"

Install the ROSA CLI:

```bash
# macOS
brew install rosa-cli

# Linux
curl -sL https://mirror.openshift.com/pub/openshift-v4/clients/rosa/latest/rosa-linux.tar.gz | tar xz
sudo mv rosa /usr/local/bin/
```

### "aws sts get-caller-identity failed"

The AWS credentials are invalid. Verify:

```bash
AWS_ACCESS_KEY_ID=AKIA... AWS_SECRET_ACCESS_KEY=... aws sts get-caller-identity
```

## Destroying Clusters

### Destroy fails with "cluster not found"

If a cluster was already manually deleted, `make destroy` handles this gracefully — it skips clusters that no longer exist.

### IAM cleanup fails

Operator role and OIDC provider cleanup may fail if the cluster deletion is still in progress. Wait a few minutes and re-run:

```bash
make destroy-auto
```
