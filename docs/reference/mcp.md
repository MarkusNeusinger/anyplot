# MCP server

## Overview

The anyplot MCP (Model Context Protocol) server enables AI assistants and tools to access anyplot programmatically. It provides a standardized interface for searching specifications, fetching implementation code, and integrating anyplot into AI-powered development workflows.

**Endpoint**: `https://api.anyplot.ai/mcp/`

---

## Quick start

### Claude Desktop configuration

Add to your Claude Desktop config file:

**macOS/Linux**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "anyplot": {
      "url": "https://api.anyplot.ai/mcp/"
    }
  }
}
```

### Claude Code (CLI)

Add to `.claude/config.json`:

```json
{
  "mcp": {
    "anyplot": {
      "url": "https://api.anyplot.ai/mcp/"
    }
  }
}
```

---

## MCP tools

### list_specs

List all plot specifications with summary information.

**Parameters**:
- `limit` (optional, default: 100) - Number of specs to return. The catalogue holds more than 100 specs, so pass a larger value or page with `offset`
- `offset` (optional, default: 0) - Pagination offset

**Returns** a JSON array of spec summaries (no wrapper object):
```json
[
  {
    "id": "scatter-basic",
    "title": "Basic Scatter Plot",
    "description": "Simple scatter plot showing relationship between two variables",
    "tags": {
      "plot_type": ["scatter", "point"],
      "data_type": ["numeric", "continuous"],
      "domain": ["statistics", "general"],
      "features": ["basic", "2d"]
    },
    "library_count": 15,
    "website_url": "https://anyplot.ai/scatter-basic"
  }
]
```

`library_count` counts the implementations whose code is available.

**Example Usage**:
```
User: "List available plot types"
Claude: [calls list_specs(limit=400)]
```

---

### search_specs_by_tags

Search specifications using tag filters.

**Parameters** (every filter is a list of values):
- Spec-level: `plot_type` (scatter, bar, line, heatmap, ...), `data_type` (numeric, categorical, timeseries, ...), `domain` (statistics, finance, science, ...), `features` (basic, 3d, interactive, animated, ...)
- Impl-level: `library` (one of the 15 library ids), `dependencies` (scipy, sklearn, ...), `techniques` (colorbar, annotations, ...), `patterns` (data-generation, explicit-figure, ...), `dataprep` (normalization, aggregation, ...), `styling` (publication-ready, minimal, ...)
- `limit` (optional, default: 100) - Maximum results

**Filter Logic**:
- Multiple values within a category: **OR** (any match)
- Multiple categories: **AND** (all must match)
- A spec-level value only matches the category it is passed in: `plot_type=["finance"]` does not match a spec whose *domain* is finance
- Impl-level filters require at least one implementation that satisfies all of them

**Example**: `plot_type=["scatter"] AND library=["matplotlib", "seaborn"]`
Returns: Scatter plots that have implementations in matplotlib OR seaborn

**Returns** the same JSON array of spec summaries as `list_specs`.

**Example Usage**:
```
User: "Show me interactive 3D plots"
Claude: [calls search_specs_by_tags(features=["3d", "interactive"])]

User: "Find matplotlib scatter plots"
Claude: [calls search_specs_by_tags(plot_type=["scatter"], library=["matplotlib"])]
```

---

### get_spec_detail

Get complete specification including its implementations.

**Parameters**:
- `spec_id` (required) - The specification ID (e.g., 'scatter-basic')
- `libraries` (optional) - Library ids to include. Without it the response carries every implementation with its code, about 0.5 MB for a spec with 15 implementations, so pass the libraries you need

**Returns**:
```json
{
  "id": "scatter-basic",
  "title": "Basic Scatter Plot",
  "description": "Simple scatter plot...",
  "applications": ["Data exploration", "Correlation analysis"],
  "data": ["Two numeric variables"],
  "notes": ["Use alpha for overlapping points"],
  "tags": {
    "plot_type": ["scatter"],
    "data_type": ["numeric"],
    "domain": ["statistics"],
    "features": ["basic", "2d"]
  },
  "issue": 42,
  "suggested": "contributor",
  "created": "2025-01-10T08:00:00Z",
  "updated": "2025-01-15T10:30:00Z",
  "website_url": "https://anyplot.ai/scatter-basic",
  "implementations": [
    {
      "spec_id": "scatter-basic",
      "library_id": "matplotlib",
      "library_name": "Matplotlib",
      "language": "python",
      "code": "import matplotlib.pyplot as plt\n...",
      "quality_score": 95,
      "preview_url_light": "https://storage.googleapis.com/anyplot-images/plots/scatter-basic/python/matplotlib/plot-light.png",
      "preview_url_dark": "https://storage.googleapis.com/anyplot-images/plots/scatter-basic/python/matplotlib/plot-dark.png",
      "preview_html_light": null,
      "preview_html_dark": null,
      "library_version": "3.10.0",
      "python_version": "3.13",
      "language_version": "3.13",
      "generated_at": "2026-06-25T10:30:00Z",
      "generated_by": "claude-opus-4-7",
      "review_strengths": ["..."],
      "review_weaknesses": ["..."],
      "review_verdict": "APPROVED",
      "impl_tags": {"patterns": ["data-generation"]},
      "website_url": "https://anyplot.ai/scatter-basic/python/matplotlib"
    }
  ]
}
```

`code` has its `# noqa` comments stripped. The review checklist and image description are pipeline internals and are not returned.

**Raises**: `ValueError` if spec_id doesn't exist

**Example Usage**:
```
User: "Show me the scatter-basic spec with all implementations"
Claude: [calls get_spec_detail("scatter-basic")]
```

---

### get_implementation

Get implementation code for a specific specification and library.

**Parameters**:
- `spec_id` (required) - The specification ID
- `library` (required) - One of the 15 library ids: altair, bokeh, chartjs, d3, echarts, ggplot2, highcharts, letsplot, makie, matplotlib, muix, plotly, plotnine, pygal, seaborn. The language is resolved from the library

**Returns** one implementation object with the same fields as the entries of `get_spec_detail`:
```json
{
  "spec_id": "scatter-basic",
  "library_id": "matplotlib",
  "library_name": "Matplotlib",
  "language": "python",
  "code": "\"\"\"...\"\"\"\nimport matplotlib.pyplot as plt\n...",
  "quality_score": 95,
  "preview_url_light": "https://storage.googleapis.com/anyplot-images/plots/scatter-basic/python/matplotlib/plot-light.png",
  "preview_url_dark": "https://storage.googleapis.com/anyplot-images/plots/scatter-basic/python/matplotlib/plot-dark.png",
  "library_version": "3.10.0",
  "python_version": "3.13",
  "website_url": "https://anyplot.ai/scatter-basic/python/matplotlib"
}
```

**Raises**: `ValueError` if spec_id, library or implementation doesn't exist

**Example Usage**:
```
User: "Get matplotlib code for scatter-basic"
Claude: [calls get_implementation("scatter-basic", "matplotlib")]
Claude: "Here's the matplotlib implementation:"
[displays code]
```

---

### list_libraries

List all supported plotting libraries.

**Parameters**: None

**Returns** a JSON array with the same fields as the REST endpoint `GET /libraries`:
```json
[
  {
    "id": "matplotlib",
    "name": "Matplotlib",
    "language": "python",
    "framework": "none",
    "version": "3.10.0",
    "documentation_url": "https://matplotlib.org/",
    "description": "The classic standard, maximum flexibility"
  }
]
```

`language` is one of python, r, julia and javascript; `framework` is `react` for MUI X Charts and `none` otherwise.

**Example Usage**:
```
User: "What plotting libraries does anyplot support?"
Claude: [calls list_libraries()]
```

---

### get_tag_values

Get all available values for a specific tag category, with how often each occurs.

**Parameters**:
- `category` (required) - One of:
  - `plot_type` - Types of plots (scatter, bar, line, etc.)
  - `data_type` - Data types (numeric, categorical, etc.)
  - `domain` - Application domains (statistics, finance, etc.)
  - `features` - Plot features (basic, 3d, interactive, etc.)
  - `dependencies` - External dependencies
  - `techniques` - Implementation techniques
  - `patterns` - Code patterns
  - `dataprep` - Data preparation techniques
  - `styling` - Styling approaches

**Returns** a JSON array of `{value, count}`, most frequent first and ties alphabetical. For spec-level categories the count is the number of specs carrying the value; for impl-level categories it is the number of implementations with code that carry it:
```json
[
  {"value": "bar", "count": 45},
  {"value": "scatter", "count": 38},
  {"value": "line", "count": 32}
]
```

**Raises**: `ValueError` for an unknown category

**Example Usage**:
```
User: "What plot types are available?"
Claude: [calls get_tag_values("plot_type")]
```

---

## Tag reference

### Spec-level tags (4 categories)

Describe **WHAT** is visualized (same for all libraries):

| Category | Examples |
|----------|----------|
| `plot_type` | scatter, bar, line, heatmap, histogram, box, violin, pie, area, network |
| `data_type` | numeric, categorical, temporal, spatial, hierarchical, graph |
| `domain` | statistics, finance, science, ml, geospatial, time-series |
| `features` | basic, 3d, interactive, animated, multi, grouped, stacked |

### Impl-level tags (5 categories)

Describe **HOW** code implements it (per-library):

| Category | Examples |
|----------|----------|
| `dependencies` | scipy, sklearn, networkx, geopandas (external packages) |
| `techniques` | colorbar, annotations, subplots, grid, custom-axis |
| `patterns` | data-generation, api-call, file-io, optimization |
| `dataprep` | normalization, aggregation, transformation, filtering |
| `styling` | publication-ready, minimal, colorful, theme |

### Other filters

| Filter | Examples |
|--------|----------|
| `library` | altair, bokeh, chartjs, d3, echarts, ggplot2, highcharts, letsplot, makie, matplotlib, muix, plotly, plotnine, pygal, seaborn |
| `spec` | Specific spec ID (e.g., "scatter-basic") |

---

## Common usage patterns

### Pattern 1: browse by type

```
User: "Show me all heatmap examples"
Claude: [calls search_specs_by_tags(plot_type=["heatmap"])]
```

### Pattern 2: library-specific search

```
User: "Find plotly scatter plots"
Claude: [calls search_specs_by_tags(plot_type=["scatter"], library=["plotly"])]
```

### Pattern 3: feature-based discovery

```
User: "I need an interactive 3D plot"
Claude: [calls search_specs_by_tags(features=["3d", "interactive"])]
```

### Pattern 4: domain-specific search

```
User: "Show me finance-related visualizations"
Claude: [calls search_specs_by_tags(domain=["finance"])]
```

### Pattern 5: get code for multiple libraries

```
User: "Compare matplotlib and seaborn implementations of scatter-basic"
Claude: [calls get_implementation("scatter-basic", "matplotlib")]
Claude: [calls get_implementation("scatter-basic", "seaborn")]
```

---

## MCP vs REST API

| Feature | MCP Server | REST API |
|---------|------------|----------|
| **Purpose** | AI assistant integration | Web frontend data |
| **Protocol** | Streamable HTTP | HTTP/JSON |
| **Endpoint** | `/mcp` | `/specs`, `/plots`, etc. |
| **Response Format** | MCP protocol | JSON |
| **Authentication** | None (public) | None (public) |
| **Use Cases** | Claude, AI tools | anyplot.ai frontend |

**Key Difference**: MCP provides a **tool-based interface** optimized for AI assistants, while REST provides **data endpoints** optimized for web applications.

---

## Error handling

### Standard errors

| Error | Cause | Example |
|-------|-------|---------|
| `ValueError` | Invalid spec_id or library | `"Specification 'xyz' not found"` |
| `ValidationError` | Invalid parameters | `"Invalid library: 'foo'"` |

### Example error response

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Specification 'scatter-xyz' not found"
  }
}
```

---

## Rate limiting

The MCP server uses the same rate limiting as the REST API:

- **Public access**: Standard Cloudflare protection
- **No authentication required**
- **Fair use policy**: Intended for individual developers and AI assistants

---

## Technical details

### Architecture

The MCP server is integrated into the existing FastAPI backend:

```
api.anyplot.ai
│
├── /specs          (REST API for web app)
├── /plots          (REST API for web app)
│
└── /mcp            (MCP Server for AI assistants)
    └── Uses: SpecRepository → PostgreSQL
```

### Benefits of integration

- Zero additional infrastructure costs
- Direct database access (no network hop)
- Shared connection pooling
- Single deployment pipeline

### Transport

- **Protocol**: Streamable HTTP (Server-Sent Events)
- **Format**: JSON-RPC 2.0
- **Session Management**: Stateless (no session ID required)

---

## Testing your integration

### 1. MCP Inspector (browser)

Test MCP tools directly in your browser:

```bash
npx @anthropic-ai/mcp-inspector https://api.anyplot.ai/mcp/
```

### 2. Claude Desktop

1. Add config (see Quick Start)
2. Restart Claude Desktop
3. Open chat and type: "Use anyplot to show me scatter plots"
4. Claude will automatically use MCP tools

### 3. Custom client

```python
from mcp.client import Client

async with Client("https://api.anyplot.ai/mcp/") as client:
    tools = await client.list_tools()
    print(tools)

    result = await client.call_tool("list_specs", {"limit": 10})
    print(result)
```

---

## Troubleshooting

### "MCP server not responding"

1. Check endpoint is accessible: `curl https://api.anyplot.ai/mcp/`
2. Verify config file location and syntax
3. Restart Claude Desktop

### "Tool not found"

1. Verify tool name matches exactly (case-sensitive)
2. Check MCP server version supports the tool
3. Test with MCP Inspector

### "Invalid spec_id"

1. Use `list_specs` to see available specs
2. Check spec ID format: lowercase, hyphens only (e.g., "scatter-basic")
3. Verify spec exists: `search_specs_by_tags()`

---

## Related documentation

- **[API Reference](api.md)** - REST API endpoints (complementary to MCP)
- **[Database Schema](database.md)** - Understanding data models
- **[Tagging System](tagging-system.md)** - Tag taxonomy and usage
- **[Vision](../concepts/vision.md)** - MCP server as part of product vision

---

## Feedback and support

- **Issues**: [GitHub Issues](https://github.com/MarkusNeusinger/anyplot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MarkusNeusinger/anyplot/discussions)
- **Feature Requests**: Create an issue with label `enhancement`

---

## Version history

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | TBD | Initial MCP server implementation |
