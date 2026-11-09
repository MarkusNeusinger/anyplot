# Documentation

Welcome to the anyplot documentation. Start here to find what you're looking for.

---

## Quick links

| I want to... | Go to |
|--------------|-------|
| Understand the project | [Vision](concepts/vision.md) |
| Read the "Use with my data" agent design | [Agent network](concepts/agent-network.md) |
| Read how catalogue code adapts to other data | [Adaptable code](concepts/adaptable-code.md) |
| Read how anyplot is built with AI agents | [AI workflow](concepts/ai-workflow.md) |
| Read or set up the agent chat's usage telemetry | [Agent usage telemetry](reference/agent-telemetry.md) |
| Read or set up the machine-read telemetry | [Machine readers](reference/machine-readers.md) |
| Contribute plot ideas | [Contributing](contributing.md) |
| Set up local development | [Development Guide](development.md) |
| See how automation works | [Workflows](workflows/overview.md) |
| Report a broken plot | [Report Issues](workflows/report-issue.md) |
| Measure a review-rubric change | [Review Retest](workflows/review-retest.md) |
| Look up API endpoints | [API Reference](reference/api.md) |
| Integrate anyplot into AI workflow | [MCP Server](reference/mcp.md) |
| Understand the database | [Database Schema](reference/database.md) |
| Explore repository structure | [Repository Structure](reference/repository.md) |
| Style frontend or plots | [Style Guide](reference/style-guide.md) |
| Cap Vertex AI spend | [GCP Budget Guard](reference/gcp-budget-guard.md) |
| Investigate API latency | [Performance Reference](reference/performance.md) |

---

## Documentation structure

```
docs/
├── index.md              # You are here
├── contributing.md       # How to contribute
├── development.md        # Local development setup
├── concepts/             # Philosophy and design
│   ├── vision.md         # Product vision and mission
│   ├── library-expansion.md  # Roadmap for multi-language gallery expansion
│   ├── agent-network.md  # Design of the "Use with my data" agent network (ADK on Vertex AI)
│   ├── adaptable-code.md # Design for catalogue code that adapts to other data
│   └── ai-workflow.md    # How anyplot is built with AI agents: roles, the path of a change, rules
├── workflows/            # Process documentation
│   ├── overview.md       # GitHub Actions automation
│   ├── report-issue.md   # Reporting issues with specs or implementations
│   └── review-retest.md  # Measuring review-rubric changes on a frozen set
└── reference/            # Technical details
    ├── api.md            # REST API endpoints
    ├── mcp.md            # MCP server integration
    ├── database.md       # PostgreSQL schema
    ├── repository.md     # Directory structure
    ├── tagging-system.md # Tag taxonomy reference
    ├── plausible.md      # Analytics integration
    ├── seo.md            # SEO configuration
    ├── style-guide.md    # Brand, frontend, plot design system
    ├── gcp-budget-guard.md  # Function that disables Vertex AI when its budget is reached
    ├── agent-telemetry.md   # Content-free usage telemetry of the agent chat, BigQuery setup
    ├── machine-readers.md   # One content-free line per crawler, AI assistant or MCP read, BigQuery setup
    └── performance.md    # API latency measurements
```

---

## Concepts

High-level understanding of why things work the way they do.

- **[Vision](concepts/vision.md)** - Product mission, the problem we solve, and how we're different
- **[Library Expansion Roadmap](concepts/library-expansion.md)** - Multi-language gallery expansion plan and licensing policy
- **[Agent Network](concepts/agent-network.md)** - Design of the "Use with my data" agent network on Google ADK and Vertex AI (Claude Haiku 5.5 by default, Gemini 3.8 Flash as the second arm): agents, pipeline, guardrails, serving, roadmap (as of 2026-11-06, the chat has been public as an experimental page at `/agent` since 2026-11-02, for all 15 catalogue libraries, and one page for visitors and admins since 2026-11-06, with the admin's tools behind its admin menu; the runtime core, the model-regression harness with its committed Claude Haiku 5.5 baseline and the judge-only scope eval are built, the `anyplot-renderer` sandbox service and the `anyplot-agents` service run in Cloud Run behind their deploy triggers, quick feedback stores each reported case and triages it on `/debug`, and the `agents-eval.yml` workflow is not built)
- **[Adaptable Code](concepts/adaptable-code.md)** - Design for catalogue implementations that adapt to other data: one `# Data` block ending in a tidy `df`, column constants with role comments, a static checker and a perturbation smoke run, a regen gate route that merges conversions on render identity, and a rollout through a capped targeted pass over matplotlib and seaborn (revised 2026-10-23 after a second opinion; the checker PR is in progress)
- **[How anyplot is built with AI agents](concepts/ai-workflow.md)** - Who does what (the owner leads; Claude Code, Claude in GitHub Actions, Gemini, and Copilot write and review), what the owner brings, the path of a change to production, how corrections become rules, a worked example (#12557), and the limits

---

## Workflows

How the automation pipeline works.

- **[Overview](workflows/overview.md)** - Specification and implementation pipelines, label system
- **[Report Issues](workflows/report-issue.md)** - How plot spec/implementation issue reports are submitted, validated, and queued
- **[Review Retest](workflows/review-retest.md)** - Re-running the AI quality review on a frozen set to measure a rubric or model change, and monitoring the regen gate

---

## Reference

Technical details for development and integration.

- **[API](reference/api.md)** - REST endpoints, request/response formats
- **[MCP Server](reference/mcp.md)** - Model Context Protocol integration for AI assistants
- **[Database](reference/database.md)** - PostgreSQL schema and models
- **[Repository](reference/repository.md)** - Directory structure and file organization
- **[Tagging System](reference/tagging-system.md)** - Tag taxonomy (used by spec-create workflow)
- **[Plausible](reference/plausible.md)** - Analytics integration
- **[SEO](reference/seo.md)** - Search engine optimization setup
- **[Style Guide](reference/style-guide.md)** - Brand, frontend, and plot design system
- **[GCP Budget Guard](reference/gcp-budget-guard.md)** - Cloud Run function that disables the Vertex AI API when its Cloud Billing budget is reached: decision rules, logging, retries, permissions, limits (as of 2026-10-09, in the repository and not yet deployed)
- **[Agent usage telemetry](reference/agent-telemetry.md)** - The agent chat's content-free events, the log bucket, sink and BigQuery views, the `/debug` card, and the one-time setup (the log bucket, the sink, and the linked dataset are live, checked 2026-11-09)
- **[Machine readers](reference/machine-readers.md)** - One content-free line per request by a crawler, an AI assistant, or an MCP client, from the API and the site's nginx: when a line is written, its fields, the verified-bot header chain, the log bucket, sink and BigQuery views, the tile on `/stats` and the section on `/debug` that read them, and the one-time setup (as of 2026-11-09, the log bucket, sink, `_Default` exclusion, and BigQuery side are live; the Worker redeploy is pending)
- **[Performance](reference/performance.md)** - Backend API response-time measurements

---

## Contributing

- **[Contributing Guide](contributing.md)** - How to propose plot ideas and improve specs
- **[Development Guide](development.md)** - Local setup, testing, code quality

---

## Other resources

- **[README](../README.md)** - Project overview and quick start
- **[CLAUDE.md](../CLAUDE.md)** - AI assistant instructions (for Claude Code)
- **[copilot-instructions.md](../.github/copilot-instructions.md)** - AI assistant instructions (for GitHub Copilot)
- **[prompts/](../prompts/)** - AI agent prompts for code generation
