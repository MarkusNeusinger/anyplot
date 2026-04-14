# Documentation

Welcome to the anyplot documentation. Start here to find what you're looking for.

---

## Quick Links

| I want to... | Go to |
|--------------|-------|
| Understand the project | [Vision](concepts/vision.md) |
| Contribute plot ideas | [Contributing](contributing.md) |
| Set up local development | [Development Guide](development.md) |
| See how automation works | [Workflows](workflows/overview.md) |
| Look up API endpoints | [API Reference](reference/api.md) |
| Integrate anyplot into AI workflow | [MCP Server](reference/mcp.md) |
| Understand the database | [Database Schema](reference/database.md) |
| Explore repository structure | [Repository Structure](reference/repository.md) |

---

## Documentation Structure

```
docs/
├── index.md              # You are here
├── contributing.md       # How to contribute
├── development.md        # Local development setup
├── concepts/             # Philosophy and design
│   └── vision.md         # Product vision and mission
├── workflows/            # Process documentation
│   └── overview.md       # GitHub Actions automation
├── reference/            # Technical details
│   ├── api.md            # REST API endpoints
│   ├── mcp.md            # MCP server integration
│   ├── database.md       # PostgreSQL schema
│   ├── repository.md     # Directory structure
│   ├── tagging-system.md # Tag taxonomy reference
│   ├── plausible.md      # Analytics integration
│   └── seo.md            # SEO configuration
└── (reserved for future docs)
```

---

## Concepts

High-level understanding of why things work the way they do.

- **[Vision](concepts/vision.md)** - Product mission, the problem we solve, and how we're different

---

## Workflows

How the automation pipeline works.

- **[Overview](workflows/overview.md)** - Specification and implementation pipelines, label system

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

---

## Contributing

- **[Contributing Guide](contributing.md)** - How to propose plot ideas and improve specs
- **[Development Guide](development.md)** - Local setup, testing, code quality

---

## Other Resources

- **[README](../README.md)** - Project overview and quick start
- **[CLAUDE.md](../CLAUDE.md)** - AI assistant instructions (for Claude Code)
- **[copilot-instructions.md](../.github/copilot-instructions.md)** - AI assistant instructions (for GitHub Copilot)
- **[prompts/](../prompts/)** - AI agent prompts for code generation
