# MAS World 2026 -- Public Reference Material

This repository contains sanitized, reusable reference material from the
MAS World 2026 conference workshop. All examples use placeholder values and
are safe for public distribution.

> **Conference sizing is NOT production sizing.** Every example in this
> repository is configured for a small, short-lived workshop environment.
> Production deployments require significantly different sizing, high
> availability, backup, retention, and security configurations. See the
> `production-guidance/` directory for details.

## Contents

| Directory | Description |
|---|---|
| `operators/` | Example Operator Subscriptions for OpenShift Logging, Loki, and Cluster Observability |
| `logging/` | LokiStack, ClusterLogForwarder, sample log generator, and LogQL query examples |
| `identity/` | Keycloak OIDC client, OpenShift OAuth, LDAP group sync, and RBAC examples |
| `architecture/` | System context, logging topology, and identity topology diagrams (Mermaid) |
| `production-guidance/` | Production considerations for logging, identity, and MAS operations |
| `troubleshooting/` | Common workshop issues and diagnostic command reference |
| `mas-edge/` | MAS Edge (Visual Inspection Edge) overview and resource requirements |

## How to use these examples

1. Read the comments at the top of each YAML file for purpose, permissions,
   and tested versions.
2. Replace all `YOUR_*` and `<PLACEHOLDER>` values with your environment
   details.
3. Follow the apply, validation, and cleanup commands documented in each file.

## Security

These files contain **no secrets, credentials, or internal URLs**. All
sensitive values use clearly marked placeholders. Never commit real
credentials to a public repository.

## Compatibility

These examples were tested against:

- Red Hat OpenShift Container Platform 4.16 -- 4.21
- IBM Maximo Application Suite 9.x
- Red Hat OpenShift Logging 6.x
- Loki Operator 6.x

Verify compatibility with your specific versions before applying.

## License

These examples are provided as-is for educational and reference purposes.
