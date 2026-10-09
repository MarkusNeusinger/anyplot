# Documentation

Welcome to the anyplot documentation. Start here to find what you're looking for.

---

## Quick links

| I want to... | Go to |
|--------------|-------|
| Understand the project | [Vision](concepts/vision.md) |
| Read the "Use with my data" agent design | [Agent network](concepts/agent-network.md) |
| Read how catalogue code adapts to other data | [Adaptable code](concepts/adaptable-code.md) |
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
│   ├── agent-network.md  # Design of the "Use with my data" agent network (ADK + Gemini)
│   └── adaptable-code.md # Design for catalogue code that adapts to other data
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
    └── performance.md    # API latency measurements
```

---

## Concepts

High-level understanding of why things work the way they do.

- **[Vision](concepts/vision.md)** - Product mission, the problem we solve, and how we're different
- **[Library Expansion Roadmap](concepts/library-expansion.md)** - Multi-language gallery expansion plan and licensing policy
- **[Agent Network](concepts/agent-network.md)** - Design of the "Use with my data" agent network on Google ADK and Gemini: agents, pipeline, guardrails, serving, roadmap (as of 2026-10-09, only the `agents/` package skeleton with settings and contracts is built)
- **[Adaptable Code](concepts/adaptable-code.md)** - Design for catalogue implementations that adapt to other data: one `# Data` block ending in a tidy `df`, column constants with role comments, a static checker and a perturbation smoke run, the regen gate's adapt route, and a rollout through the daily regeneration (as of 2026-10-09, design only)

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
