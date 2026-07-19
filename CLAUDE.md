# Project Instructions

## Master specification

The authoritative implementation specification is located at:

- `prompt.md`

Before beginning or continuing implementation:

1. Read `prompt.md` in full.
2. Treat its requirements and acceptance criteria as mandatory.
3. Read the current implementation status in:
   - `docs/implementation-status.md`
   - `docs/decision-log.md`
   - `docs/blockers.md`
4. Do not claim that a feature has been tested unless test evidence exists.
5. Never commit credentials, kubeconfigs, tokens, passwords, entitlement keys,
   license secrets, or private keys.
6. Use configuration and secret references rather than hard-coded
   environment-specific values.
7. Implement the reference-cluster workflow before any fleet rollout.
8. Update implementation status and evidence before ending each work session.

## Execution order

Follow the phases defined in `prompt.md`.

Do not begin a full fleet rollout until all reference-cluster readiness,
security, identity, Showroom, ACM, and logging acceptance gates pass.