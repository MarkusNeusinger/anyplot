# anyplot vision

## Mission

**Making data visualization effortless: Find the right plot, see it with *your* data, get working code instantly.**

## The problem

Developers waste hours on visualization:

- **Library Lock-in**: Pick one library, then realize another was better
- **Discovery Hell**: Finding the right plot type across libraries is frustrating
- **Rigid Categories**: Hard to find specialized plots or discover similar alternatives
- **Generic Examples**: Tutorials show fake data, not yours
- **Outdated Code**: Examples break across library versions and ecosystem updates

## The solution

**anyplot is an AI-powered platform where specifications meet automation.**

### The human touch

While AI can generate plots instantly, **humans need inspiration and choice**. If you ask AI to "make a chart," you'll
get the same generic scatter plot every time.

anyplot is different: **AI curates and maintains, humans discover and choose.**

- Browse hundreds of specialized plot types you didn't know existed
- Compare visual styles side-by-side to find what resonates
- Discover creative approaches from the community
- Choose the exact variation that tells your story

**AI automates the boring parts. You bring the creativity.**

### How it works

1. **Spec Collection**: Comprehensive markdown specifications for every plot type
2. **AI Code Generation**: Automatically creates implementations for all major libraries
3. **Continuous Quality**: AI validates, tests, and improves examples constantly
4. **Smart Discovery**: Typo-tolerant search over tags and titles + dynamic tagging + a similarity map of the catalogue
5. **Your Data**: Paste your data on a plot page, and an agent adapts that plot's code to it (experimental)

### What makes it different

- **Library Agnostic**: Compare libraries side-by-side. 15 libraries across four languages as of 2026-11-02 — Python (matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, lets-plot), R (ggplot2), Julia (Makie.jl), and JavaScript (Chart.js, D3.js, ECharts, Highcharts, MUI X Charts); the architecture is designed to welcome more
- **Always Current**: AI agents keep examples updated and optimized
- **Multi-Dimensional Discovery**: Find plots by domain (finance, research), type (scatter, bar), or specific use case (
  ROC curve, Sankey diagram)
- **Multiple Styles**: Same plot, different visual styles—pick what you like
- **Community + AI**: Users submit specs, AI generates and maintains code
- **Global**: AI-native means any language, anywhere

## Key features

### Core (free)

- Browse all plot types with live examples
- Compare libraries side-by-side
- Copy production-ready code
- Search and filter by tags and titles
- AI-generated explanations
- **MCP Server**: Integrate anyplot into your AI workflow ([Docs](../reference/mcp.md), [Issue #4129](https://github.com/MarkusNeusinger/anyplot/issues/4129))
- **Use with my data** (experimental since 2026-11-02): Paste your data on a plot page, and the chat at `/agent` adapts that plot's code to it ([Design](agent-network.md))

### Premium (future)

- **Try with *your* data**: Upload CSV/Excel/JSON, see all plots with your actual data (beyond the free chat, which takes pasted text for one plot at a time)
- **Custom styles**: Generate plots matching your brand colors
- **API access**: Programmatic access to plot generation

## Why we'll win

1. **First to solve the real problem**: Your data, not examples
2. **Never outdated**: AI continuously updates and improves
3. **True discovery**: Similarity clustering reveals plots you didn't know existed
4. **Specification-driven**: Every plot is guaranteed to work as described
5. **Community scale**: Open source + AI automation = comprehensive coverage

---

*"Stop adapting examples to your data. Start visualizing your data directly."*

**anyplot - Where your data meets visualization.**
