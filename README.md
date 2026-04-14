<img src="app/public/logo.svg" alt="anyplot.ai" width="250">

**→ [anyplot.ai](https://anyplot.ai)**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/MarkusNeusinger/anyplot/actions/workflows/ci-tests.yml/badge.svg?branch=main)](https://github.com/MarkusNeusinger/anyplot/actions/workflows/ci-tests.yml)
[![Ruff](https://github.com/MarkusNeusinger/anyplot/actions/workflows/ci-lint.yml/badge.svg?branch=main)](https://github.com/MarkusNeusinger/anyplot/actions/workflows/ci-lint.yml)
[![codecov](https://codecov.io/github/MarkusNeusinger/anyplot/graph/badge.svg?token=4EGPSHH0H0)](https://codecov.io/github/MarkusNeusinger/anyplot)

> library-agnostic, ai-powered python plotting examples.

---

## What is anyplot?

**anyplot** is an AI-powered platform for Python data visualization that automatically discovers, generates, tests, and
maintains plotting examples. Browse hundreds of plots across all major Python libraries - matplotlib, seaborn, plotly,
bokeh, altair, plotnine, pygal, highcharts, and lets-plot.

**Community-driven, AI-maintained** - Propose plot ideas via GitHub Issues, AI generates the code, automated quality
checks ensure excellence. Zero manual coding required.

---

## Features

- **AI-generated code** - All implementations automatically generated and maintained by AI
- **Compare libraries** - View matplotlib, seaborn, plotly side-by-side for the same plot
- **Always current** - AI agents continuously update examples with latest library versions
- **Natural language search** - Find plots by asking "show correlation between variables"
- **AI quality review** - Claude evaluates every plot against quality standards (score ≥ 50 required)
- **Open source** - Community proposes ideas via Issues, AI generates the code

---

## Architecture

**Specification-first design**: Every plot starts as a Markdown spec (library-agnostic), then AI generates
implementations for all 9 supported libraries.

```
plots/scatter-basic/
├── specification.md     # Library-agnostic specification
├── specification.yaml   # Tags, created, issue, suggested
├── metadata/            # Per-library metadata (quality scores, preview URLs)
│   ├── matplotlib.yaml
│   └── ...
└── implementations/
    ├── matplotlib.py
    ├── seaborn.py
    ├── plotly.py
    └── ... (6 more)
```

**Issue-based workflow**: GitHub Issues as state machine for plot lifecycle. Status tracked via live-updating table (no sub-issues). Each library generates in parallel, creating PRs to a feature branch.

**AI quality review**: Claude evaluates generated plots. Score ≥ 90 → immediate merge. Score < 90 → repair loop (max 3 attempts). After 3 attempts: ≥ 50 → merge, < 50 → failed.

See [docs/reference/](docs/reference/) for details.

---

## Tech Stack

**Backend**: FastAPI • PostgreSQL • SQLAlchemy • Python 3.10+

**Frontend**: React 19 • Vite • TypeScript • MUI

**Plotting**: matplotlib • seaborn • plotly • bokeh • altair • plotnine • pygal • highcharts • lets-plot

**Infrastructure**: Google Cloud Run • Cloud SQL • Cloud Storage

**Automation**: GitHub Actions

**AI**: Claude (code generation + quality review)

---

## MCP Server

anyplot provides an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server for AI assistants to search plot specifications and fetch implementation code.

**Available Tools:**
- `list_specs` - List all plot specifications
- `search_specs_by_tags` - Search by plot type, domain, features, library
- `get_spec_detail` - Get full specification with all implementations
- `get_implementation` - Get code for a specific library
- `list_libraries` - List supported plotting libraries
- `get_tag_values` - Get available tag values by category

### Configuration

Add to your MCP client configuration (e.g., Claude Code `.mcp.json`):

**SSE Transport** (recommended, wider compatibility):
```json
{
  "mcpServers": {
    "anyplot": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://api.anyplot.ai/sse/"]
    }
  }
}
```

**Streamable HTTP Transport** (modern, bidirectional):
```json
{
  "mcpServers": {
    "anyplot": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://api.anyplot.ai/mcp/"]
    }
  }
}
```

---

## License Notes

Most plotting libraries are fully open source. Note these exceptions:

- **Highcharts**: Free for non-commercial use. Commercial use requires a license from [highcharts.com](https://www.highcharts.com/license)

---

## Project Structure

```
anyplot/
├── plots/              # Plot specs + metadata + implementations
├── prompts/            # AI agent prompts
├── api/                # FastAPI backend
├── app/                # React frontend
├── core/               # Shared business logic
├── automation/         # Workflow scripts (sync, labels)
├── tests/              # Test suite (unit, integration, e2e)
├── alembic/            # Database migrations
├── docs/               # Documentation
└── .github/workflows/  # GitHub Actions
```

**For details**, see [Repository Structure](docs/reference/repository.md)

---

## Documentation

- **[Vision](docs/concepts/vision.md)** - Product vision and mission
- **[Contributing](docs/contributing.md)** - How to add/improve specs and implementations
- **[Workflows](docs/workflows/overview.md)** - Automation flows and label system
- **[Reference](docs/reference/)** - API, database, repository structure

---

## Contributing

We welcome contributions! **All code is AI-generated** - you propose ideas, AI implements them.

**Three ways to contribute** (from [anyplot.ai](https://anyplot.ai) or GitHub):

| Action | When to Use | From anyplot.ai |
|--------|-------------|-----------------|
| **Suggest Spec** | Propose a new plot type | "suggest spec" link in catalog |
| **Report Spec Issue** | Problem with a specification | "report issue" link on spec page |
| **Report Impl Issue** | Problem with a library implementation | "report issue" link on impl page |

**How it works**:

1. You create Issue (or click link on anyplot.ai)
2. AI validates and processes your input
3. Maintainer reviews and approves
4. AI generates/fixes the code
5. Automated quality review ensures excellence

**Important**: Don't submit code directly! If a plot has quality issues, it means the spec needs improvement, not the code.

See [contributing.md](docs/contributing.md) for details.

---

## Development

See **[Development Guide](docs/development.md)** for local setup instructions.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Links

- **Website**: [anyplot.ai](https://anyplot.ai)
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/MarkusNeusinger/anyplot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MarkusNeusinger/anyplot/discussions)
- **Stats**: [Public Analytics](https://plausible.io/anyplot.ai)

---

<div align="center">

**Built by [Markus Neusinger](https://linkedin.com/in/markus-neusinger/)**

[⭐ Star us on GitHub](https://github.com/MarkusNeusinger/anyplot) • [💡 Request New Plot](https://github.com/MarkusNeusinger/anyplot/issues/new?template=request-new-plot.yml)

</div>
