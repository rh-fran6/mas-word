# RHDP Skills Marketplace Inventory

Discovered: 2026-07-15
Plugin source: `rhdp-marketplace` v2.14.0
Plugin cache: `~/.claude/plugins/cache/rhdp-marketplace/`

## Installed Plugins

| Plugin | Version | Skills | Agents | Status |
|--------|---------|--------|--------|--------|
| showroom | 2.14.0 | 4 | 9 | Installed |
| agnosticv | 2.14.0 | 2 | 8 | Installed |
| health | 2.14.0 | 1 | 0 | Installed |

---

## Skills Detail

### showroom:create-lab

- **Trigger**: `/showroom:create-lab`
- **Model**: claude-sonnet-4-6
- **Purpose**: Generates Red Hat Showroom workshop content (AsciiDoc modules, nav.adoc, site.yml, ui-config.yml). Supports interactive and headless (ph_payload) modes.
- **Architecture**: Orchestrator pattern. Delegates to `showroom:file-generator` (parallel, one per file) and `showroom:module-reviewer` (quality check).
- **Phases**: Parse arguments, detect mode (new/continue), planning form, Showroom scaffold setup (site.yml, ui-config.yml), spawn file generators in parallel, quality check via module-reviewer, nav.adoc merge, deliver.
- **Applicability to MAS World 2026**: **PRIMARY** — use this skill to generate all Showroom workshop content (index.adoc, overview, details, exercise modules). The skill creates properly structured AsciiDoc with `role="execute"` blocks, correct attribute references, and navigation entries.

### showroom:verify-content

- **Trigger**: `/showroom:verify-content`
- **Model**: claude-sonnet-4-6
- **Purpose**: Parallel quality review of workshop/demo content against Red Hat standards. Produces a consolidated findings table with severity levels (Critical, High, Warning, Info, Recommendation).
- **Architecture**: Orchestrator. Delegates to `showroom:scaffold-checker` (Haiku, root config files) and `showroom:module-reviewer` (Sonnet, one per .adoc file in parallel).
- **Checks**: B.1-B.7 cross-module structure, scaffold config (site.yml, ui-config.yml, antora.yml), per-module content quality, acronym first-use, undefined attributes, `role="execute"` usage.
- **Applicability to MAS World 2026**: **MANDATORY POST-CREATION** — run after `create-lab` generates content. Validates AsciiDoc structure, missing files, attribute consistency, and Red Hat style compliance.

### showroom:create-demo

- **Trigger**: `/showroom:create-demo`
- **Model**: claude-sonnet-4-6
- **Purpose**: Generates presenter-led demo content using Know/Show structure. Same architecture as create-lab but for demo (not hands-on workshop) content.
- **Applicability to MAS World 2026**: **NOT APPLICABLE** — MAS World is a hands-on workshop, not a presenter-led demo. Use `create-lab` instead.

### showroom:blog-generate

- **Trigger**: `/showroom:blog-generate`
- **Model**: claude-sonnet-4-6
- **Purpose**: Transforms completed Showroom lab/demo content into blog posts for Red Hat Developer, internal blogs, or marketing platforms.
- **Applicability to MAS World 2026**: **NOT APPLICABLE** — post-event deliverable at most. Not part of the automation workflow.

### agnosticv:catalog-builder

- **Trigger**: `/agnosticv:catalog-builder`
- **Model**: claude-sonnet-4-6
- **Purpose**: Creates or updates AgnosticV catalog configurations (common.yaml, dev.yaml, description.adoc, info-message-template.adoc) for RHDP deployments. Four modes: Full Catalog, Description Only, Info Message Template, Virtual CI.
- **Architecture**: Orchestrator (MODE 1). Batched planning form, shared_context JSON, parallel agents (`agnosticv:config-writer` + `agnosticv:description-writer`), workflow-reviewer, optional git commit.
- **Key features**: UUID generation/collision-check, infrastructure type routing (OCP/VMs/Sandbox API), event catalog support (Summit/RH One), workload variable verification, password pattern enforcement, collection version management.
- **Applicability to MAS World 2026**: **CONDITIONAL** — applicable only if this project needs to create an AgnosticV catalog entry for RHDP. The MAS World automation is a standalone post-provisioning system that runs on pre-provisioned clusters; it does not use the RHDP AgnosticV catalog pipeline for provisioning. However, if an RHDP catalog entry is needed for cluster provisioning or to integrate with RHDP's self-service portal, this skill would be used. **Currently: not in scope for Phase 0-2.**

### agnosticv:validator

- **Trigger**: `/agnosticv:validator`
- **Model**: claude-sonnet-4-6
- **Purpose**: Validates AgnosticV catalog configurations against best practices and deployment requirements. 27+ checks including UUID, YAML syntax, workload dependencies, category, infrastructure, collections, deployer, reporting labels, event-specific rules.
- **Architecture**: Orchestrator v2.0.0. Pre-flight (YAML parse, CI type classification, commitv detection, babylon schema, event context), then parallel subagents (`agnosticv:schema-checker`, `agnosticv:metadata-checker`, `agnosticv:workload-checker`, `agnosticv:ocp-infra-checker` or `agnosticv:sandbox-checker`).
- **Applicability to MAS World 2026**: **CONDITIONAL** — same conditions as `agnosticv:catalog-builder`. Only applicable if an AgnosticV catalog entry exists. **Currently: not in scope for Phase 0-2.**

### health:deployment-validator

- **Trigger**: `/health:deployment-validator`
- **Model**: claude-sonnet-4-6
- **Purpose**: Creates validation roles for RHDP deployments. Collaborative pattern: provides discovery commands for the developer to run on bastion, then generates Ansible validation role code based on output. Validates pods, routes, operators, custom resources, ConfigMaps, Secrets.
- **Applicability to MAS World 2026**: **APPLICABLE IN LATER PHASES** — can be used to create health-check Ansible roles for validating MAS deployment readiness (MAS pods, SLS, Db2, operator health) on each cluster. Relevant for Phase 3 (Ansible role implementation) but requires SSH access to a live cluster.

---

## Agents (not directly invocable as skills)

### Showroom Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| showroom:file-generator | Sonnet | Generates one AsciiDoc file per invocation |
| showroom:module-reviewer | Sonnet | Quality check on a single .adoc module |
| showroom:scaffold-checker | Haiku | Checks root config files (site.yml, ui-config.yml, antora.yml) |
| showroom:diagram-generator | — | Generates diagrams for content |
| showroom:doc-writer | — | General documentation writing |
| showroom:format-detector | — | Detects content format (workshop/demo) |
| showroom:score-aggregator | — | Aggregates review scores |
| showroom:zero-content-reviewer | — | Reviews zero-content scaffolds |
| showroom:zero-scaffold-checker | — | Checks zero-content scaffold structure |

### AgnosticV Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| agnosticv:config-writer | — | Generates common.yaml + dev.yaml |
| agnosticv:description-writer | — | Generates description.adoc + info-message-template.adoc |
| agnosticv:metadata-checker | — | Validates __meta__ section |
| agnosticv:schema-checker | — | Validates against babylon.yaml schema |
| agnosticv:workload-checker | — | Validates workload dependencies |
| agnosticv:ocp-infra-checker | — | OCP infrastructure validation |
| agnosticv:sandbox-checker | — | Sandbox API CI validation |
| agnosticv:workflow-reviewer | — | Cross-skill consistency check |

---

## Skill-First Implementation Order for MAS World 2026

Per prompt.md Section 4, skills must be attempted before manual implementation.

### Phase 0-1: Discovery and Skeleton
1. No skill invocations required — these phases involve research, Pydantic models, and Ansible scaffolding.

### Phase 2: Showroom Content
1. **`/showroom:create-lab`** — Generate workshop content (index, overview, details, exercise modules) for the MAS World workshop.
2. **`/showroom:verify-content`** — Validate all generated content against Red Hat standards.
3. If `create-lab` cannot produce MAS-specific content (e.g., requires live environment variables not available at generation time), document as `MANUAL_FALLBACK_SKILL_UNAVAILABLE` with reason.

### Phase 3: Ansible Roles (conditional)
4. **`/health:deployment-validator`** — If a live cluster is available, use this to generate health-check validation roles for MAS components.

### Phase 4+: AgnosticV Integration (conditional)
5. **`/agnosticv:catalog-builder`** — Only if an RHDP catalog entry is needed.
6. **`/agnosticv:validator`** — Only after catalog-builder creates files.

---

## Documentation References

| Document | Path |
|----------|------|
| Showroom Common Rules | `~/.claude/plugins/cache/rhdp-marketplace/showroom/2.14.0/docs/SKILL-COMMON-RULES.md` |
| AgnosticV Common Rules | `~/.claude/plugins/cache/rhdp-marketplace/agnosticv/2.14.0/docs/AGV-COMMON-RULES.md` |
| FTL Patterns | `~/.claude/plugins/cache/rhdp-marketplace/health/2.14.0/docs/FTL-PATTERNS.md` |
| OCP Catalog Questions | `~/.claude/plugins/cache/rhdp-marketplace/agnosticv/2.14.0/docs/ocp-catalog-questions.md` |
| OCP Validator Checks | `~/.claude/plugins/cache/rhdp-marketplace/agnosticv/2.14.0/docs/ocp-validator-checks.md` |
| Infrastructure Guide | `~/.claude/plugins/cache/rhdp-marketplace/agnosticv/2.14.0/docs/infrastructure-guide.md` |
