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

# Project operating contract

The complete authoritative project specification is in:

@prompt.md

Before executing every new user task:

1. Read `CLAUDE.md`.
2. Read `prompt.md`.
3. Read `.claude/inbox/current-task.json` when it exists.
4. Determine whether the new task changes the project specification.
5. If it changes the project, update `prompt.md` before implementation.
6. Append the instruction and disposition to `docs/change-log.md`.
7. Update `docs/decision-log.md`, `docs/workarounds.md`, and
   `docs/blockers.md` where applicable.
8. Run the specification synchronization command.
9. Begin implementation only after synchronization succeeds.
10. After implementation, update `docs/current-state.md` and
    `docs/implementation-status.md`.

A workaround must never be implemented silently. Before implementing a
material workaround:

1. Document the blocked requirement.
2. Document why it cannot be implemented.
3. Document alternatives considered.
4. Document the selected workaround and its implications.
5. Update `prompt.md`.
6. Update `docs/workarounds.md`.
7. Re-run specification synchronization.

Do not place raw credentials, passwords, tokens, kubeconfigs, entitlement
keys, AWS access keys, or private keys in any documentation.

## Execution order

Follow the phases defined in `prompt.md`.

Do not begin a full fleet rollout until all reference-cluster readiness,
security, identity, Showroom, ACM, and logging acceptance gates pass.