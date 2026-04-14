# 🔌 MCP Server

## Overview

The anyplot MCP (Model Context Protocol) server enables AI assistants and tools to access anyplot programmatically. It provides a standardized interface for searching specifications, fetching implementation code, and integrating anyplot into AI-powered development workflows.

**Endpoint**: `https://api.anyplot.ai/mcp/`

---

## Quick Start

### Claude Desktop Configuration

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

## MCP Tools

### list_specs

List all plot specifications with summary information.

**Parameters**:
- `limit` (optional, default: 50, max: 100) - Number of specs to return
- `offset` (optional, default: 0) - Pagination offset

**Returns**:
```json
{
  "total": 253,
  "specs": [
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
      "library_count": 9
    }
  ]
}
```

**Example Usage**:
```
User: "List available plot types"
Claude: [calls list_specs(limit=20)]
```

---

### search_specs_by_tags

Search specifications using tag filters.

**Parameters**:
- `plot_type` (optional) - Filter by plot types (scatter, bar, line, heatmap, etc.)
- `data_type` (optional) - Filter by data types (numeric, categorical, temporal, etc.)
- `domain` (optional) - Filter by domain (statistics, finance, science, etc.)
- `features` (optional) - Filter by features (basic, 3d, interactive, animated, etc.)
- `library` (optional) - Filter by library (matplotlib, seaborn, plotly, etc.)
- `techniques` (optional) - Filter by implementation techniques (colorbar, annotations, etc.)
- `dependencies` (optional) - Filter by dependencies (scipy, sklearn, etc.)
- `limit` (optional, default: 50) - Maximum results

**Filter Logic**:
- Multiple values within a category: **OR** (any match)
- Multiple categories: **AND** (all must match)

**Example**: `plot_type=["scatter"] AND library=["matplotlib", "seaborn"]`
Returns: Scatter plots that have implementations in matplotlib OR seaborn

**Returns**:
```json
{
  "total": 15,
  "specs": [...]
}
```

**Example Usage**:
```
User: "Show me interactive 3D plots"
Claude: [calls search_specs_by_tags(features=["3d", "interactive"])]

User: "Find matplotlib scatter plots"
Claude: [calls search_specs_by_tags(plot_type=["scatter"], library=["matplotlib"])]
```

---

### get_spec_detail

Get complete specification including all implementations.

**Parameters**:
- `spec_id` (required) - The specification ID (e.g., 'scatter-basic')

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
  "implementations": [
    {
      "library": "matplotlib",
      "code": "import matplotlib.pyplot as plt\n...",
      "quality_score": 95,
      "preview_url": "https://storage.googleapis.com/...",
      "library_version": "3.10.0"
    }
  ]
}
```

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
- `library` (required) - One of: matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, highcharts, letsplot

**Returns**:
```json
{
  "spec_id": "scatter-basic",
  "library": "matplotlib",
  "code": "\"\"\"...\"\"\"\nimport matplotlib.pyplot as plt\n...",
  "quality_score": 95,
  "preview_url": "https://storage.googleapis.com/anyplot-images/plots/scatter-basic/matplotlib/plot.png",
  "preview_html": null,
  "library_version": "3.10.0",
  "python_version": "3.13"
}
```

**Raises**: `ValueError` if spec_id or implementation doesn't exist

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

**Returns**:
```json
{
  "libraries": [
    {
      "id": "matplotlib",
      "name": "Matplotlib",
      "version": "3.10.0",
      "description": "The classic standard, maximum flexibility",
      "documentation_url": "https://matplotlib.org/"
    }
  ]
}
```

**Example Usage**:
```
User: "What plotting libraries does anyplot support?"
Claude: [calls list_libraries()]
```

---

### get_tag_values

Get all available values for a specific tag category with counts.

**Parameters**:
- `category` (required) - One of:
  - `plot_type` - Types of plots (scatter, bar, line, etc.)
  - `data_type` - Data types (numeric, categorical, etc.)
  - `domain` - Application domains (statistics, finance, etc.)
  - `features` - Plot features (basic, 3d, interactive, etc.)
  - `techniques` - Implementation techniques
  - `dependencies` - External dependencies

**Returns**:
```json
{
  "category": "plot_type",
  "values": [
    {"value": "scatter", "count": 45},
    {"value": "bar", "count": 38},
    {"value": "line", "count": 32}
  ]
}
```

**Example Usage**:
```
User: "What plot types are available?"
Claude: [calls get_tag_values("plot_type")]
```

---

## Tag Reference

### Spec-Level Tags (4 categories)

Describe **WHAT** is visualized (same for all libraries):

| Category | Examples |
|----------|----------|
| `plot_type` | scatter, bar, line, heatmap, histogram, box, violin, pie, area, network |
| `data_type` | numeric, categorical, temporal, spatial, hierarchical, graph |
| `domain` | statistics, finance, science, ml, geospatial, time-series |
| `features` | basic, 3d, interactive, animated, multi, grouped, stacked |

### Impl-Level Tags (5 categories)

Describe **HOW** code implements it (per-library):

| Category | Examples |
|----------|----------|
| `dependencies` | scipy, sklearn, networkx, geopandas (external packages) |
| `techniques` | colorbar, annotations, subplots, grid, custom-axis |
| `patterns` | data-generation, api-call, file-io, optimization |
| `dataprep` | normalization, aggregation, transformation, filtering |
| `styling` | publication-ready, minimal, colorful, theme |

### Other Filters

| Filter | Examples |
|--------|----------|
| `library` | matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, highcharts, letsplot |
| `spec` | Specific spec ID (e.g., "scatter-basic") |

---

## Common Usage Patterns

### Pattern 1: Browse by Type

```
User: "Show me all heatmap examples"
Claude: [calls search_specs_by_tags(plot_type=["heatmap"])]
```

### Pattern 2: Library-Specific Search

```
User: "Find plotly scatter plots"
Claude: [calls search_specs_by_tags(plot_type=["scatter"], library=["plotly"])]
```

### Pattern 3: Feature-Based Discovery

```
User: "I need an interactive 3D plot"
Claude: [calls search_specs_by_tags(features=["3d", "interactive"])]
```

### Pattern 4: Domain-Specific Search

```
User: "Show me finance-related visualizations"
Claude: [calls search_specs_by_tags(domain=["finance"])]
```

### Pattern 5: Get Code for Multiple Libraries

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

## Error Handling

### Standard Errors

| Error | Cause | Example |
|-------|-------|---------|
| `ValueError` | Invalid spec_id or library | `"Specification 'xyz' not found"` |
| `ValidationError` | Invalid parameters | `"Invalid library: 'foo'"` |

### Example Error Response

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Specification 'scatter-xyz' not found"
  }
}
```

---

## Rate Limiting

The MCP server uses the same rate limiting as the REST API:

- **Public access**: Standard Cloudflare protection
- **No authentication required**
- **Fair use policy**: Intended for individual developers and AI assistants

---

## Technical Details

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

### Benefits of Integration

- Zero additional infrastructure costs
- Direct database access (no network hop)
- Shared connection pooling
- Single deployment pipeline

### Transport

- **Protocol**: Streamable HTTP (Server-Sent Events)
- **Format**: JSON-RPC 2.0
- **Session Management**: Stateless (no session ID required)

---

## Testing Your Integration

### 1. MCP Inspector (Browser)

Test MCP tools directly in your browser:

```bash
npx @anthropic-ai/mcp-inspector https://api.anyplot.ai/mcp/
```

### 2. Claude Desktop

1. Add config (see Quick Start)
2. Restart Claude Desktop
3. Open chat and type: "Use anyplot to show me scatter plots"
4. Claude will automatically use MCP tools

### 3. Custom Client

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

## Related Documentation

- **[API Reference](api.md)** - REST API endpoints (complementary to MCP)
- **[Database Schema](database.md)** - Understanding data models
- **[Tagging System](tagging-system.md)** - Tag taxonomy and usage
- **[Vision](../concepts/vision.md)** - MCP server as part of product vision

---

## Feedback & Support

- **Issues**: [GitHub Issues](https://github.com/MarkusNeusinger/anyplot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MarkusNeusinger/anyplot/discussions)
- **Feature Requests**: Create an issue with label `enhancement`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | TBD | Initial MCP server implementation |
