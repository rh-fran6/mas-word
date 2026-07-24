# Production Identity Guidance

This document covers production identity and access management
considerations for OpenShift and IBM Maximo Application Suite. The
workshop uses a simplified Keycloak deployment for demonstration purposes.

> **Workshop identity is NOT production identity.** The workshop deploys a
> single Keycloak instance with a demo LDAP directory. Production
> deployments require high availability, enterprise directory integration,
> certificate management, and compliance controls.

## Identity provider selection

| Provider | Protocol | Use case |
|---|---|---|
| Active Directory + ADFS | SAML 2.0 | Enterprise Windows environments |
| Azure AD / Entra ID | OIDC | Microsoft cloud-native organizations |
| Keycloak / RHSSO | OIDC | Self-managed, multi-protocol federation |
| Okta | OIDC / SAML | SaaS identity management |
| Ping Identity | OIDC / SAML | Enterprise federation |
| LDAP (direct) | LDAP bind | Simple environments without SSO requirements |

For OpenShift:
- Prefer OIDC over LDAP for the OAuth identity provider.
- Use LDAP group sync separately for group-based RBAC.
- Multiple identity providers can coexist on a single cluster.

## High-availability Keycloak

If self-managing Keycloak:

- Deploy at least 3 replicas across availability zones.
- Use an external database (PostgreSQL) with replication.
- Configure Infinispan distributed cache for session clustering.
- Place behind a load balancer with health checks.
- Use persistent storage for realm exports and themes.
- Monitor JVM heap, connection pool, and session count.
- Automate realm configuration via GitOps (realm export/import).

## Certificate management

### OAuth server certificates
- OpenShift OAuth uses the cluster ingress certificate by default.
- For custom domains, provide a certificate via the
  `spec.servingCerts` field on the OAuth CR or the ingress controller.
- Use certificates from a trusted CA (not self-signed) in production.

### Keycloak TLS
- Terminate TLS at the OpenShift Route (edge or reencrypt).
- If using passthrough, configure Keycloak's internal TLS.
- Automate certificate renewal (cert-manager or enterprise PKI).

### Certificate rotation
- Plan for certificate rotation without downtime.
- Test rotation in a non-production environment first.
- Document the rotation procedure and notify dependent teams.

## LDAP vs SAML vs OIDC

| Feature | LDAP (direct) | SAML 2.0 | OIDC |
|---|---|---|---|
| Protocol type | Bind/search | XML assertions | JSON/JWT tokens |
| SSO support | No | Yes | Yes |
| MFA support | Limited | Via IdP | Via IdP |
| OpenShift support | Yes | No (use OIDC) | Yes |
| MAS support | Via OpenShift | Via OpenShift | Via OpenShift |
| Group sync | oc adm groups sync | Manual mapping | Claims-based |
| Complexity | Low | Medium | Low-Medium |
| Recommended | Dev/simple | Legacy enterprise | Modern enterprise |

**Recommendation**: Use OIDC for OpenShift OAuth integration. Use LDAP
group sync for RBAC group management. This gives SSO and fine-grained
group-based access control.

## Break-glass access

Always maintain a local emergency access method:

1. **htpasswd identity provider**: Keep a separate htpasswd-backed
   identity provider with one or two emergency admin accounts.
2. Store the htpasswd file and credentials in a secure vault.
3. Document the break-glass procedure separately from the primary
   identity system.
4. Test break-glass access quarterly.
5. Audit break-glass usage and require incident reports.

```yaml
# Example: htpasswd provider for break-glass
spec:
  identityProviders:
    - name: emergency-access
      type: HTPasswd
      mappingMethod: claim
      htpasswd:
        fileData:
          name: htpasswd-emergency-secret
```

## Credential rotation

### Service account tokens
- Use bound service account tokens (automatic in OCP 4.x).
- Set appropriate token expiration.

### OAuth client secrets
- Rotate Keycloak client secrets at least annually.
- Coordinate rotation with the OpenShift OAuth configuration.
- Use a Secret in `openshift-config`, not inline values.

### LDAP bind credentials
- Rotate bind passwords according to enterprise policy.
- Update the LDAP sync configuration and Keycloak federation.
- Use service accounts with minimal LDAP permissions.

### User passwords
- Enforce password policies via the identity provider.
- For workshop attendees: rotate before each event, revoke after.
- Never share passwords across attendees in production.

## MAS identity integration

MAS integrates with OpenShift authentication:

- MAS uses OpenShift OAuth for user authentication.
- MAS maintains its own user and group database synchronized from
  OpenShift.
- Application-level roles (e.g., Maximo Manage roles) are managed
  within MAS.
- Ensure the OpenShift OAuth provider is stable before configuring MAS
  identity.
- Test MAS login after any OAuth configuration change.

## ROSA HCP considerations

ROSA with Hosted Control Planes (HCP) has a different OAuth model:

- The OAuth server runs in the hosted control plane, not on the cluster.
- Some OAuth customizations (custom login pages, certain provider
  types) may behave differently.
- Test identity provider configuration on HCP specifically.
- Consult Red Hat documentation for current HCP OAuth limitations.
