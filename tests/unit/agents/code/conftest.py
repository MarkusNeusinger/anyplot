"""Shared fixtures for the code-handling tests: a catalogue-style source and the catalogue files."""

import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
CODE_LIBRARIES = ("matplotlib", "seaborn", "plotnine", "altair", "pygal", "letsplot", "plotly", "bokeh")
"""The libraries with a Python code profile (`normalise.SUPPORTED_LIBRARIES`), in the corpus order; plotly and bokeh
since PB-2a (2026-10-31)."""
CATALOGUE_FILES = [
    path
    for library in CODE_LIBRARIES
    for path in sorted(REPO_ROOT.glob(f"plots/*/implementations/python/{library}.py"))
]
R_CATALOGUE_FILES = sorted(REPO_ROOT.glob("plots/*/implementations/r/ggplot2.R"))
"""The ggplot2 catalogue files, which the R profile (`agents/anyplot/code/profiles/r/`) reads."""
JULIA_CATALOGUE_FILES = sorted(REPO_ROOT.glob("plots/*/implementations/julia/makie.jl"))
"""The Makie catalogue files, which the Julia profile (`agents/anyplot/code/profiles/julia/`) reads."""
JS_CATALOGUE_FILES = sorted(REPO_ROOT.glob("plots/*/implementations/javascript/*.*"))
"""The Chart.js, D3, ECharts, Highcharts (`.js`) and MUI X (`.tsx`) catalogue files, which the JavaScript profile
(`agents/anyplot/code/profiles/javascript/`) reads."""


def js_library(path: Path) -> str:
    """The library of a JavaScript catalogue file: its stem (`chartjs`, `muix`)."""
    return path.stem


def source(text: str) -> str:
    """Dedent a triple-quoted snippet and drop its leading newline."""
    return textwrap.dedent(text).lstrip("\n")


# A catalogue file in miniature: header, sys.path guard, theme block, palette, synthetic
# data, a literal limit, the catalogue title and a tight savefig at a 16:9 figure.
CATALOGUE = source('''
    """ anyplot.ai
    scatter-demo: Demo Scatter
    Library: matplotlib 3.11.2 | Python 3.13.13
    Quality: 90/100 | Updated: 2026-10-01
    """

    import os
    import sys


    # This file is named matplotlib.py; drop its directory from sys.path.
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

    import matplotlib.pyplot as plt
    import numpy as np


    # Theme tokens
    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
    IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

    np.random.seed(42)
    x = np.random.uniform(0, 10, 50)
    y = 2 * x + np.random.normal(0, 1, 50)

    fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
    ax.scatter(x, y, color=IMPRINT[0])
    ax.set_ylim(0, 25)
    ax.set_title("scatter-demo · python · matplotlib · anyplot.ai", color=INK)
    plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
''')

# The same file after normalisation: header, guard and title gone, dpi 200, no bbox_inches.
CATALOGUE_NORMALISED = source("""
    import os


    import matplotlib.pyplot as plt
    import numpy as np


    # Theme tokens
    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
    IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

    np.random.seed(42)
    x = np.random.uniform(0, 10, 50)
    y = 2 * x + np.random.normal(0, 1, 50)

    fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
    ax.scatter(x, y, color=IMPRINT[0])
    ax.set_ylim(0, 25)
    ax.set_title("", color=INK)
    plt.savefig(f"plot-{THEME}.png", dpi=200, facecolor=PAGE_BG)
""")

# A ggplot2 catalogue file in miniature: roxygen header, theme block, palette, column
# constants, the Data and Plot markers, synthetic data, the title and a 4800x2700 save.
R_CATALOGUE = source("""
    #' anyplot.ai
    #' scatter-demo: Demo Scatter
    #' Library: ggplot2 4.0.3 | R 4.6.1
    #' Quality: 90/100 | Updated: 2026-10-29

    library(ggplot2)
    library(ragg)

    # Theme tokens
    THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
    PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
    INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
    ALPHA    <- if (THEME == "light") 0.4 else 0.6
    IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                         "#AE3030", "#2ABCCD", "#954477", "#99B314")

    # Columns: set these to your table's column names
    SPEND   <- "Spend (k USD)"    # role: x
    REVENUE <- "Revenue (k USD)"  # role: y

    # Data: replace this block with your own table
    set.seed(42)
    df <- tibble::tibble(!!SPEND := runif(50, 5, 150), !!REVENUE := rnorm(50, 300, 40))

    # Plot: reads only df and the constants above
    p <- ggplot(df, aes(x = .data[[SPEND]], y = .data[[REVENUE]])) +
      geom_point(color = IMPRINT_PALETTE[1], alpha = ALPHA) +
      labs(title = "scatter-demo · r · ggplot2 · anyplot.ai", x = SPEND, y = REVENUE) +
      theme_minimal(base_size = 8) +
      theme(plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG))

    # Save
    ggsave(
      filename = sprintf("plot-%s.png", THEME),
      plot     = p,
      device   = ragg::agg_png,
      width    = 16,
      height   = 9,
      units    = "in",
      dpi      = 300
    )
""")

# The same file after normalisation: header and title gone, dpi 200.
R_CATALOGUE_NORMALISED = source("""
    library(ggplot2)
    library(ragg)

    # Theme tokens
    THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
    PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
    INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
    ALPHA    <- if (THEME == "light") 0.4 else 0.6
    IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                         "#AE3030", "#2ABCCD", "#954477", "#99B314")

    # Columns: set these to your table's column names
    SPEND   <- "Spend (k USD)"    # role: x
    REVENUE <- "Revenue (k USD)"  # role: y

    # Data: replace this block with your own table
    set.seed(42)
    df <- tibble::tibble(!!SPEND := runif(50, 5, 150), !!REVENUE := rnorm(50, 300, 40))

    # Plot: reads only df and the constants above
    p <- ggplot(df, aes(x = .data[[SPEND]], y = .data[[REVENUE]])) +
      geom_point(color = IMPRINT_PALETTE[1], alpha = ALPHA) +
      labs(title = "", x = SPEND, y = REVENUE) +
      theme_minimal(base_size = 8) +
      theme(plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG))

    # Save
    ggsave(
      filename = sprintf("plot-%s.png", THEME),
      plot     = p,
      device   = ragg::agg_png,
      width    = 16,
      height   = 9,
      units    = "in",
      dpi      = 200
    )
""")

# A Makie catalogue file in miniature: header, theme block (const and plain), palette, column
# constants, the Data and Plot markers, synthetic data, the title, `resolution =` and the save.
JULIA_CATALOGUE = source("""
    # anyplot.ai
    # scatter-demo: Demo Scatter
    # Library: makie 0.24.16 | Julia 1.13.2
    # Quality: 90/100 | Updated: 2026-10-29

    using CairoMakie
    using Colors
    using Random

    # Theme tokens
    const THEME    = get(ENV, "ANYPLOT_THEME", "light")
    const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
    INK            = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
    const ALPHA    = THEME == "light" ? 0.4 : 0.6
    const IMPRINT_PALETTE = [
        colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
        colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
    ]

    # Columns: set these to your table's column names
    const SPEND   = "Spend (k USD)"    # role: x
    const REVENUE = "Revenue (k USD)"  # role: y

    # Data: replace this block with your own table
    Random.seed!(42)
    spend = 5 .+ 145 .* rand(50)
    revenue = 300 .+ 40 .* randn(50)

    # Plot: reads only the data above
    fig = Figure(resolution = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)
    ax = Axis(fig[1, 1]; title = "scatter-demo · julia · makie · anyplot.ai", xlabel = SPEND, ylabel = REVENUE)
    scatter!(ax, spend, revenue; color = (IMPRINT_PALETTE[1], ALPHA))

    # Save
    save("plot-$(THEME).png", fig; px_per_unit = 2)
""")

# The same file after normalisation: header and title gone, `resolution` renamed to `size`.
JULIA_CATALOGUE_NORMALISED = source("""
    using CairoMakie
    using Colors
    using Random

    # Theme tokens
    const THEME    = get(ENV, "ANYPLOT_THEME", "light")
    const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
    INK            = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
    const ALPHA    = THEME == "light" ? 0.4 : 0.6
    const IMPRINT_PALETTE = [
        colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
        colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
    ]

    # Columns: set these to your table's column names
    const SPEND   = "Spend (k USD)"    # role: x
    const REVENUE = "Revenue (k USD)"  # role: y

    # Data: replace this block with your own table
    Random.seed!(42)
    spend = 5 .+ 145 .* rand(50)
    revenue = 300 .+ 40 .* randn(50)

    # Plot: reads only the data above
    fig = Figure(size = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)
    ax = Axis(fig[1, 1]; title = "", xlabel = SPEND, ylabel = REVENUE)
    scatter!(ax, spend, revenue; color = (IMPRINT_PALETTE[1], ALPHA))

    # Save
    save("plot-$(THEME).png", fig; px_per_unit = 2)
""")

# The miniature adapted: the sample replaced by the placeholder, the columns read from df.
JULIA_WORKING = source("""
    using CairoMakie
    using Colors
    using DataFrames

    # Theme tokens
    const THEME    = get(ENV, "ANYPLOT_THEME", "light")
    const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
    INK            = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
    const ALPHA    = THEME == "light" ? 0.4 : 0.6
    const IMPRINT_PALETTE = [
        colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
        colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
    ]

    # Columns: set these to your table's column names
    const SPEND   = "Ausgaben (k €)"   # role: x
    const REVENUE = "Umsatz \\$ (k)"   # role: y

    # Data: replace this block with your own table
    df = load_user_data()

    # Plot: reads only df and the constants above
    fig = Figure(size = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)
    ax = Axis(fig[1, 1]; title = "Umsatz nach Ausgaben", xlabel = SPEND, ylabel = REVENUE)
    scatter!(ax, df[!, SPEND], df[!, REVENUE]; color = (IMPRINT_PALETTE[1], ALPHA))

    # Save
    save("plot-$(THEME).png", fig; px_per_unit = 2)
""")

# What the Julia adapter prompt tells the adapter to write (`agents/anyplot/prompts/adapter_julia.md` and its highlights
# slot), in one working form: the column constants read as `df[!, ...]`, `dropmissing`, the number formatter with both
# marks, categories as integer positions, a span on a time axis as numeric offsets. `JULIA_PROMPT_IDIOM_SNIPPETS` stand
# verbatim in the prompt and in the form (the policy test holds the form against both validator profiles, the image
# test renders it from a `data.csv` with missing cells).
JULIA_PROMPT_IDIOM_SNIPPETS = (
    "dropmissing(df, [X, Y])",
    r'fmt(v; digits = 2) = (v < 0 ? "-" : "") * replace(@sprintf("%.*f", digits, abs(v)), '
    r'r"(?<=\d)(?=(?:\d{3})+(?:\.|$))" => THOUSANDS, "." => DECIMAL)',
    "unique(df[!, GROUP])",
    "[findfirst(==(g), groups) for g in df[!, GROUP]]",
    "colors = IMPRINT_PALETTE[1:length(groups)]",
    "groupby(df, GROUP; sort = false)",
    "peak, idx = findmax(skipmissing(df[!, Y]))",
    '"r = " * fmt(cor(df[!, X], df[!, Y]))',
    "days = Dates.value.(df[!, DAY] .- first(df[!, DAY]))",
    'xticks = (days[1:step:end], Dates.format.(df[!, DAY][1:step:end], "yyyy-mm-dd"))',
    "ytickformat = values -> fmt.(values)",
    "fmt(peak; digits = 0)",
    'ytickformat = values -> [fmt(v / 1e6; digits = 1) * " Mio." for v in values]',
    "xticks = (1:length(groups), groups)",
    'const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"',
)
JULIA_PROMPT_IDIOMS = source(r"""
    using CairoMakie
    using Colors
    using DataFrames
    using Dates
    using Printf
    using Statistics

    # Theme tokens
    const THEME = get(ENV, "ANYPLOT_THEME", "light")
    const PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
    const INK = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
    const IMPRINT_PALETTE = [colorant"#009E73", colorant"#C475FD", colorant"#4467A3"]
    const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"
    const DECIMAL = ","
    const THOUSANDS = "."

    # Columns: set these to your table's column names
    const DAY = "Tag"               # role: x
    const X = "Ausgaben (k €)"      # role: size
    const Y = "Umsatz \$ (k)"       # role: y
    const GROUP = "Region"          # role: group

    # Data: replace this block with your own table
    df = load_user_data()

    # Plot: reads only df and the constants above
    df = dropmissing(df, [X, Y])
    df = dropmissing(df, [DAY, GROUP])
    fmt(v; digits = 2) = (v < 0 ? "-" : "") * replace(@sprintf("%.*f", digits, abs(v)), r"(?<=\d)(?=(?:\d{3})+(?:\.|$))" => THOUSANDS, "." => DECIMAL)
    groups = unique(df[!, GROUP])
    group = [findfirst(==(g), groups) for g in df[!, GROUP]]
    colors = IMPRINT_PALETTE[1:length(groups)]
    totals = combine(groupby(df, GROUP; sort = false), Y => sum => Y)
    peak, idx = findmax(skipmissing(df[!, Y]))
    note = "r = " * fmt(cor(df[!, X], df[!, Y]))
    days = Dates.value.(df[!, DAY] .- first(df[!, DAY]))
    step = max(1, length(days) ÷ 6)
    fig = Figure(size = (1600, 900), backgroundcolor = PAGE_BG)
    ax = Axis(
        fig[1, 1];
        title = "Umsatz nach Tag",
        xlabel = DAY,
        ylabel = Y,
        xticks = (days[1:step:end], Dates.format.(df[!, DAY][1:step:end], "yyyy-mm-dd")),
        ytickformat = values -> fmt.(values),
    )
    lines!(ax, days, df[!, Y]; color = IMPRINT_PALETTE[group])
    vspan!(ax, days[1], days[2]; color = (INK_MUTED, 0.2))
    text!(ax, days[idx], peak; text = fmt(peak; digits = 0), color = INK)
    text!(ax, days[1], peak; text = note, color = INK)
    ax2 = Axis(
        fig[1, 2];
        xticks = (1:length(groups), groups),
        ytickformat = values -> [fmt(v / 1e6; digits = 1) * " Mio." for v in values],
    )
    barplot!(ax2, 1:length(groups), totals[!, Y]; color = colors)
    ax3 = Axis(fig[2, 1]; xlabel = DAY, ylabel = Y)
    scatter!(ax3, df[!, DAY], df[!, Y]; color = IMPRINT_PALETTE[1])
    Legend(fig[1, 3], [PolyElement(color = colors[i]) for i in eachindex(groups)], groups, GROUP)

    # Save
    save("plot-$(THEME).png", fig; px_per_unit = 2)
""")

# A Chart.js catalogue file in miniature: header, a square directive, token lines (one per global, a theme test),
# column constants, the Data and Plot markers, synthetic data, a `#` in a string and the title.
JS_CATALOGUE = source("""
    // anyplot.ai
    // scatter-demo: Demo Scatter
    // Library: chartjs 4.4.7 | JavaScript 22.23.0
    // Quality: 90/100 | Updated: 2026-10-30

    //# anyplot-orientation: square

    const t = window.ANYPLOT_TOKENS;
    const { width, height } = window.ANYPLOT_SIZE;
    const isDark = window.ANYPLOT_THEME === "dark";
    const MUTED = isDark ? "#A8A79F" : "#6B6A63";

    // Columns: set these to your data's column names
    const SPEND = "Spend (k USD)";  // role: x
    const REVENUE = "Revenue (k USD)";  // role: y

    // Data: replace this block with your own records, one object per row
    const data = Array.from({ length: 50 }, (_, i) => ({ [SPEND]: 5 + i * 3, [REVENUE]: 300 + Math.random() * 40 }));

    // Plot: reads only data and the constants above
    const canvas = document.createElement("canvas");
    document.getElementById("container").appendChild(canvas);
    new Chart(canvas, {
      type: "scatter",
      data: { datasets: [{ data: data.map((d) => ({ x: d[SPEND], y: d[REVENUE] })), backgroundColor: t.palette[0] }] },
      options: {
        animation: false,
        plugins: { title: { display: true, text: "scatter-demo · javascript · chartjs · anyplot.ai", color: t.ink } },
        scales: {
          x: { title: { display: true, text: SPEND }, grid: { color: "#00000022" } },
          y: { title: { display: true, text: REVENUE }, ticks: { color: MUTED } },
        },
      },
    });
""")

# The same file after normalisation: header and title gone, the directive on the first line.
JS_CATALOGUE_NORMALISED = source("""
    //# anyplot-orientation: square

    const t = window.ANYPLOT_TOKENS;
    const { width, height } = window.ANYPLOT_SIZE;
    const isDark = window.ANYPLOT_THEME === "dark";
    const MUTED = isDark ? "#A8A79F" : "#6B6A63";

    // Columns: set these to your data's column names
    const SPEND = "Spend (k USD)";  // role: x
    const REVENUE = "Revenue (k USD)";  // role: y

    // Data: replace this block with your own records, one object per row
    const data = Array.from({ length: 50 }, (_, i) => ({ [SPEND]: 5 + i * 3, [REVENUE]: 300 + Math.random() * 40 }));

    // Plot: reads only data and the constants above
    const canvas = document.createElement("canvas");
    document.getElementById("container").appendChild(canvas);
    new Chart(canvas, {
      type: "scatter",
      data: { datasets: [{ data: data.map((d) => ({ x: d[SPEND], y: d[REVENUE] })), backgroundColor: t.palette[0] }] },
      options: {
        animation: false,
        plugins: { title: { display: true, text: "", color: t.ink } },
        scales: {
          x: { title: { display: true, text: SPEND }, grid: { color: "#00000022" } },
          y: { title: { display: true, text: REVENUE }, ticks: { color: MUTED } },
        },
      },
    });
""")

# The miniature adapted: the sample replaced by the placeholder, the columns renamed.
JS_WORKING = (
    JS_CATALOGUE_NORMALISED.replace(
        "const data = Array.from({ length: 50 }, (_, i) => ({ [SPEND]: 5 + i * 3, [REVENUE]: 300 + Math.random() * 40 }));",
        "const data = loadUserData();",
    )
    .replace('"Spend (k USD)"', '"Ausgaben (k €)"')
    .replace('text: "", color', 'text: "Umsatz nach Ausgaben", color')
)

# A MUI X module in miniature, after normalisation: imports, token lines, constants, markers, and the component.
MUIX_WORKING = source("""
    //# anyplot-orientation: landscape
    import { ScatterChart } from "@mui/x-charts/ScatterChart";
    import Typography from "@mui/material/Typography";

    const t = window.ANYPLOT_TOKENS;
    const { width, height } = window.ANYPLOT_SIZE;

    // Columns: set these to your data's column names
    const X: string = "Ausgaben (k €)";  // role: x
    const Y = "Umsatz";  // role: y

    // Data: replace this block with your own records, one object per row
    const data = loadUserData();

    // Plot: reads only data and the constants above
    const points = data.map((d: Record<string, number>, id: number) => ({ id, x: d[X], y: d[Y] }));

    export default function Chart() {
      return (
        <div>
          <Typography sx={{ color: t.ink }}>Umsatz nach Ausgaben</Typography>
          <ScatterChart
            width={width}
            height={height - 40}
            series={[{ data: points, color: t.palette[0] }]}
            xAxis={[{ label: X }]}
            yAxis={[{ label: Y }]}
            skipAnimation
          />
        </div>
      );
    }
""")

# What the JavaScript prompts (`agents/anyplot/prompts/adapter_javascript.md` and its highlights slot) tell the adapter
# to write, as one working form per library: the column constants with an escaped quote and backslash, `null` dropped
# before a statistic, the plot language's marks through `fmt` on every value axis, the time axes kept in UTC, and the
# palette read from `t.palette`. `JS_PROMPT_IDIOM_SNIPPETS` stand verbatim in the prompt and in every library's form,
# `JS_LIBRARY_IDIOM_SNIPPETS` in the prompt and in their library's form (the policy test holds each form against both
# validator profiles, the image test renders it from a table with missing cells).
JS_PROMPT_IDIOM_SNIPPETS = (
    "const data = loadUserData();",
    "[...new Set(data.map((d) => d[GROUP]))]",
    "[...data].sort(",
    "data.filter((d) => d[Y] != null)",
    "const fmt = (v, digits = 2) => { const r = Number(v.toFixed(digits)); "
    'const [whole, frac] = Math.abs(r).toFixed(digits).split("."); '
    'return (r < 0 ? "-" : "") + whole.replace(/\\B(?=(\\d{3})+(?!\\d))/g, THOUSANDS) + (frac ? DECIMAL + frac : ""); };',
    '"r = " + fmt(r, 2)',
    'const INK_MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";',
    "const peak = data.filter((d) => d[Y] != null).reduce((best, d) => (best === null || d[Y] > best[Y] ? d : best), null)",
    "fmt(peak[Y], 0)",
    "const dated = data.filter((d) => d[DAY] != null);",
    "t.palette[i]",
)
JS_LIBRARY_IDIOM_SNIPPETS: dict[str, tuple[str, ...]] = {
    "chartjs": (
        "ticks: { callback: (v) => fmt(v, 1) }",
        '(v) => fmt(v / 1e6, 1) + " Mio."',
        'd[DAY].slice(0, 10).split("-").reverse().join(".")',
        "d[DAY].slice(11, 16)",
        "new Date(d[DAY]).getTime()",
        "new Date(v).toISOString().slice(0, 10)",
        "responsive: true",
        "maintainAspectRatio: false",
    ),
    "d3": (
        ".tickFormat((v) => fmt(v, 1))",
        "d3.scaleUtc()",
        'd3.utcFormat("%d.%m.%Y")',
        "d3.line().defined((d) => d[Y] != null)",
        "d3.scaleOrdinal().domain(groups).range(t.palette)",
        "window.ANYPLOT_SIZE",
    ),
    "echarts": (
        "axisLabel: { formatter: (v) => fmt(v, 1) }",
        "useUTC: true",
        "[new Date(d[DAY]).getTime(), d[Y]]",
        "color: t.palette",
        'echarts.init(document.getElementById("container"))',
    ),
    "highcharts": (
        "labels: { formatter() { return fmt(this.value, 1); } }",
        'labels: { format: "{value:%d.%m.%Y}" }',
        "[new Date(d[DAY]).getTime(), d[Y]]",
        "colors: t.palette",
    ),
    "muix": (
        "export default function",
        "@mui/x-charts/LineChart",
        "@mui/x-charts/hooks",
        "@mui/material/Typography",
        "skipAnimation",
        "width={width}",
        "useXScale()",
        "useYScale()",
        "useDrawingArea()",
        "colors={t.palette}",
        'colorMap: { type: "ordinal", values: groups, colors: groups.map((g, i) => t.palette[i]) }',
        "valueFormatter: (v) => fmt(v, 1)",
        'valueFormatter: (v) => (v == null ? "" : fmt(v, 1))',
        '(v) => fmt(v / 1e6, 1) + " Mio."',
        'scaleType: "utc"',
        "data: dated.map((d) => new Date(d[DAY]))",
        'valueFormatter: (v) => v.toISOString().slice(0, 10).split("-").reverse().join(".")',
        "tickMinStep: 24 * 60 * 60 * 1000",
    ),
}
_JS_IDIOM_HEAD = source(r"""
    //# anyplot-orientation: landscape
    const t = window.ANYPLOT_TOKENS;
    const { width, height } = window.ANYPLOT_SIZE;
    const INK_MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

    // Columns: set these to your data's column names
    const DAY = "Tag \"lokal\"";  // role: x
    const X = "Ausgaben (k €)";  // role: size
    const Y = "Umsatz\\Netto";  // role: y
    const GROUP = "Region";  // role: group

    // Data: replace this block with your own records, one object per row
    const data = loadUserData();

    // Plot: reads only data and the constants above
    const DECIMAL = ",";
    const THOUSANDS = ".";
    const fmt = (v, digits = 2) => { const r = Number(v.toFixed(digits)); const [whole, frac] = Math.abs(r).toFixed(digits).split("."); return (r < 0 ? "-" : "") + whole.replace(/\B(?=(\d{3})+(?!\d))/g, THOUSANDS) + (frac ? DECIMAL + frac : ""); };
    const groups = [...new Set(data.map((d) => d[GROUP]))];
    const colors = groups.map((g, i) => t.palette[i]);
    const dated = data.filter((d) => d[DAY] != null);
    const pairs = data.filter((d) => d[X] != null && d[Y] != null);
    const ranked = [...data].sort((a, b) => (b[X] ?? 0) - (a[X] ?? 0));
    const mean = (values) => values.reduce((sum, v) => sum + v, 0) / values.length;
    const mx = mean(pairs.map((d) => d[X]));
    const my = mean(pairs.map((d) => d[Y]));
    const spread = (key, m) => Math.sqrt(pairs.reduce((sum, d) => sum + (d[key] - m) ** 2, 0));
    const r = pairs.reduce((sum, d) => sum + (d[X] - mx) * (d[Y] - my), 0) / (spread(X, mx) * spread(Y, my));
    const note = "r = " + fmt(r, 2);
    const peak = data.filter((d) => d[Y] != null).reduce((best, d) => (best === null || d[Y] > best[Y] ? d : best), null);
    const title = "Umsatz bis " + fmt(peak[Y], 0) + ", " + note + ", zuerst " + ranked[0][GROUP];
""")
JS_PROMPT_IDIOMS: dict[str, str] = {
    "chartjs": _JS_IDIOM_HEAD
    + source(r"""
        const upper = document.createElement("div");
        const lower = document.createElement("div");
        upper.style.height = "50%";
        lower.style.height = "50%";
        const container = document.getElementById("container");
        container.appendChild(upper);
        container.appendChild(lower);
        const first = document.createElement("canvas");
        const second = document.createElement("canvas");
        upper.appendChild(first);
        lower.appendChild(second);
        new Chart(first, {
          type: "line",
          data: {
            labels: dated.map((d) => d[DAY].slice(0, 10).split("-").reverse().join(".") + " " + d[DAY].slice(11, 16)),
            datasets: groups.map((g, i) => ({
              label: g,
              data: dated.map((d) => (d[GROUP] === g ? d[Y] : null)),
              borderColor: t.palette[i],
              backgroundColor: colors[i],
            })),
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: { title: { display: true, text: title, color: t.ink } },
            scales: { y: { ticks: { callback: (v) => fmt(v, 1) } } },
          },
        });
        new Chart(second, {
          type: "scatter",
          data: {
            datasets: [{ label: Y, data: dated.map((d) => ({ x: new Date(d[DAY]).getTime(), y: d[Y] })), backgroundColor: INK_MUTED }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
              x: { type: "linear", ticks: { callback: (v) => new Date(v).toISOString().slice(0, 10) } },
              y: { ticks: { callback: (v) => fmt(v / 1e6, 1) + " Mio." } },
            },
          },
        });
    """),
    "d3": _JS_IDIOM_HEAD
    + source(r"""
        const margin = { top: 70, right: 40, bottom: 60, left: 110 };
        const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
        const x = d3.scaleUtc().domain(d3.extent(dated, (d) => new Date(d[DAY]))).range([margin.left, width - margin.right]);
        const y = d3.scaleLinear().domain(d3.extent(pairs, (d) => d[Y])).nice().range([height - margin.bottom, margin.top]);
        const color = d3.scaleOrdinal().domain(groups).range(t.palette);
        svg.append("g").attr("transform", `translate(0,${height - margin.bottom})`)
          .call(d3.axisBottom(x).ticks(6).tickFormat(d3.utcFormat("%d.%m.%Y")));
        svg.append("g").attr("transform", `translate(${margin.left},0)`).call(d3.axisLeft(y).tickFormat((v) => fmt(v, 1)));
        for (const g of groups) {
          svg.append("path")
            .datum(dated.filter((d) => d[GROUP] === g))
            .attr("fill", "none")
            .attr("stroke", color(g))
            .attr("stroke-width", 3)
            .attr("d", d3.line().defined((d) => d[Y] != null).x((d) => x(new Date(d[DAY]))).y((d) => y(d[Y])));
        }
        svg.append("text").attr("x", width / 2).attr("y", 36).attr("text-anchor", "middle").attr("fill", t.ink).text(title);
    """),
    "echarts": _JS_IDIOM_HEAD
    + source(r"""
        const chart = echarts.init(document.getElementById("container"));
        chart.setOption({
          animation: false,
          useUTC: true,
          color: t.palette,
          title: { text: title, left: "center", textStyle: { color: t.ink } },
          xAxis: { type: "time", axisLabel: { color: t.inkSoft } },
          yAxis: { type: "value", axisLabel: { formatter: (v) => fmt(v, 1) } },
          series: groups.map((g) => ({
            type: "line",
            name: g,
            data: dated.filter((d) => d[GROUP] === g).map((d) => [new Date(d[DAY]).getTime(), d[Y]]),
          })),
        });
    """),
    "highcharts": _JS_IDIOM_HEAD
    + source(r"""
        Highcharts.chart("container", {
          chart: { backgroundColor: t.pageBg, animation: false },
          credits: { enabled: false },
          colors: t.palette,
          title: { text: title, style: { color: t.ink } },
          xAxis: { type: "datetime", labels: { format: "{value:%d.%m.%Y}" } },
          yAxis: { title: { text: Y }, labels: { formatter() { return fmt(this.value, 1); } } },
          plotOptions: { series: { animation: false } },
          series: groups.map((g) => ({
            type: "line",
            name: g,
            data: dated.filter((d) => d[GROUP] === g).map((d) => [new Date(d[DAY]).getTime(), d[Y]]),
          })),
        });
    """),
    # MUI X's form is a TSX module: the imports below the directive, the shared head, then a component that draws the
    # dated values on a UTC axis with a gap for each `null`, an overlay at data positions through the chart's scales,
    # and the per-group totals as bars coloured by their category.
    "muix": _JS_IDIOM_HEAD.replace(
        "//# anyplot-orientation: landscape\n",
        source("""
            //# anyplot-orientation: landscape
            import { LineChart } from "@mui/x-charts/LineChart";
            import { BarChart } from "@mui/x-charts/BarChart";
            import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";
            import Typography from "@mui/material/Typography";
        """),
        1,
    )
    + source(r"""
        const totals = groups.map((g) => data.filter((d) => d[GROUP] === g && d[Y] != null).reduce((sum, d) => sum + d[Y], 0));

        function Marks() {
          const x = useXScale();
          const y = useYScale();
          const { left, width: plotWidth } = useDrawingArea();
          const at = peak[DAY] == null ? null : x(new Date(peak[DAY]));
          return (
            <g>
              <line x1={left} x2={left + plotWidth} y1={y(my)} y2={y(my)} stroke={INK_MUTED} strokeDasharray="6 4" />
              {at == null ? null : <circle cx={at} cy={y(peak[Y])} r={8} fill="none" stroke={t.ink} />}
            </g>
          );
        }

        export default function Chart() {
          return (
            <div>
              <Typography sx={{ color: t.ink, fontSize: 22, textAlign: "center" }}>{title}</Typography>
              <LineChart
                width={width}
                height={(height - 40) / 2}
                colors={t.palette}
                skipAnimation
                xAxis={[{
                  scaleType: "utc",
                  data: dated.map((d) => new Date(d[DAY])),
                  valueFormatter: (v) => v.toISOString().slice(0, 10).split("-").reverse().join("."),
                  tickMinStep: 24 * 60 * 60 * 1000,
                  height: 40,
                }]}
                yAxis={[{ valueFormatter: (v) => fmt(v, 1), width: 120 }]}
                series={[{ label: Y, data: dated.map((d) => d[Y]), showMark: true, valueFormatter: (v) => (v == null ? "" : fmt(v, 1)) }]}
              >
                <Marks />
              </LineChart>
              <BarChart
                width={width}
                height={(height - 40) / 2}
                skipAnimation
                hideLegend
                xAxis={[{
                  scaleType: "band",
                  data: groups,
                  label: GROUP,
                  height: 60,
                  colorMap: { type: "ordinal", values: groups, colors: groups.map((g, i) => t.palette[i]) },
                }]}
                yAxis={[{ valueFormatter: (v) => fmt(v / 1e6, 1) + " Mio.", width: 120 }]}
                series={[{ label: Y, data: totals, valueFormatter: (v) => (v == null ? "" : fmt(v, 1)) }]}
              />
            </div>
          );
        }
    """),
}

# What plotly's and bokeh's own sections of the adapter instruction (`agents/anyplot/prompts/adapter_plotly.md`,
# `adapter_bokeh.md`, PB-2a) tell the adapter to write, as one working form per library: the column constants with a
# quote and a backslash, the rows a mark needs dropped before a statistic, the timestamps in UTC, the plot language's
# marks (plotly's `separators`, bokeh's fixed ticks with Python-written labels) and the pinned figure save. Each
# snippet of `FIGURE_PROMPT_IDIOM_SNIPPETS` stands verbatim in its library's section and its form; the policy test
# holds each form against both validator profiles, the image test renders it from a table with missing cells.
FIGURE_PROMPT_IDIOM_SNIPPETS: dict[str, tuple[str, ...]] = {
    "plotly": (
        'fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")',
        "paper_bgcolor=PAGE_BG, plot_bgcolor=PAGE_BG",
        'font={"family": "Helvetica, Arial, sans-serif", "color": INK}',
        "df.dropna(subset=[X, Y])",
        'days = dated[DAY].dt.tz_convert("UTC").dt.tz_localize(None) if dated[DAY].dt.tz is not None else dated[DAY]',
        'tickformat="%d.%m.%Y"',
        "separators=DECIMAL + THOUSANDS",
        'tickformat=",.0f"',
        'f"{v:,.0f}".replace(",", "_").replace(".", DECIMAL).replace("_", THOUSANDS)',
        'render_mode="svg"',
    ),
    "bokeh": (
        'with open(f"plot-{THEME}.json", "w", encoding="utf-8") as figure_file:',
        "json.dump(json_item(p), figure_file)",
        "p = row(p, side)",
        "df.dropna(subset=[X, Y])",
        '[Y].astype("float64")',
        'DatetimeTickFormatter(days="%d.%m.%Y", months="%m.%Y", years="%Y")',
        "step = 10 ** math.floor(math.log10((high - low) / 5))",
        "step *= next(factor for factor in (1, 2, 2.5, 5, 10) if factor * step >= (high - low) / 5)",
        "ticks = [step * index for index in range(math.floor(low / step), math.ceil(high / step) + 1)]",
        "p.yaxis.ticker = FixedTicker(ticks=ticks)",
        'p.yaxis.major_label_overrides = {tick: f"{tick:,.0f}".replace(",", "_").replace(".", DECIMAL).replace("_", '
        "THOUSANDS) for tick in ticks}",
    ),
}
FIGURE_PROMPT_IDIOMS: dict[str, str] = {
    "plotly": source("""
        import os

        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        THEME = os.getenv("ANYPLOT_THEME", "light")
        PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
        INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
        INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
        GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
        IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

        DAY = 'Tag "lokal"'  # role: x
        X = DAY
        Y = "Umsatz\\\\Netto"  # role: y
        COUNT = "Anzahl"  # role: value
        GROUP = "Region"  # role: group
        DECIMAL, THOUSANDS = ",", "."

        df = load_user_data()

        dated = df.dropna(subset=[X, Y]).sort_values(DAY)
        days = dated[DAY].dt.tz_convert("UTC").dt.tz_localize(None) if dated[DAY].dt.tz is not None else dated[DAY]
        peak = dated[Y].idxmax()
        v = dated.loc[peak, Y]
        label = f"{v:,.0f}".replace(",", "_").replace(".", DECIMAL).replace("_", THOUSANDS)
        totals = df.dropna(subset=[GROUP, COUNT]).groupby(GROUP, sort=False)[COUNT].sum().astype("float64")
        spread = px.scatter(dated, x=X, y=Y, render_mode="svg")

        fig = make_subplots(rows=1, cols=2, column_widths=[0.62, 0.38], horizontal_spacing=0.1)
        fig.add_trace(go.Scatter(x=days, y=dated[Y], mode="lines+markers", line={"color": IMPRINT[0]}), row=1, col=1)
        fig.add_trace(spread.data[0].update(marker={"color": IMPRINT[0], "size": 4}, x=days), row=1, col=1)
        fig.add_annotation(x=days.loc[peak], y=v, text=label, font={"color": INK}, arrowcolor=INK_SOFT, row=1, col=1)
        fig.add_trace(go.Bar(x=list(totals.index), y=totals.to_numpy(), marker_color=IMPRINT[: len(totals)]), row=1, col=2)
        fig.update_xaxes(tickformat="%d.%m.%Y", row=1, col=1)
        fig.update_xaxes(gridcolor=GRID, tickfont={"color": INK_SOFT})
        fig.update_yaxes(tickformat=",.0f", gridcolor=GRID, tickfont={"color": INK_SOFT}, zeroline=False)
        fig.update_layout(
            title={"text": "Umsatz und Anzahl", "font": {"size": 16, "color": INK}, "x": 0.5},
            separators=DECIMAL + THOUSANDS,
            paper_bgcolor=PAGE_BG, plot_bgcolor=PAGE_BG,
            font={"family": "Helvetica, Arial, sans-serif", "color": INK},
            showlegend=False,
        )

        fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")
    """),
    "bokeh": source("""
        import json
        import math
        import os

        from bokeh.embed import json_item
        from bokeh.layouts import row
        from bokeh.models import ColumnDataSource, DatetimeTickFormatter, FixedTicker, Label
        from bokeh.plotting import figure

        THEME = os.getenv("ANYPLOT_THEME", "light")
        PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
        INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
        INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
        IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

        DAY = 'Tag "lokal"'  # role: x
        X = DAY
        Y = "Umsatz\\\\Netto"  # role: y
        COUNT = "Anzahl"  # role: value
        GROUP = "Region"  # role: group
        DECIMAL, THOUSANDS = ",", "."

        df = load_user_data()

        dated = df.dropna(subset=[X, Y]).sort_values(DAY)
        line = ColumnDataSource(data={"x": dated[DAY], "y": dated[Y].astype("float64")})
        peak = dated[Y].idxmax()
        v = dated.loc[peak, Y]
        label = f"{v:,.0f}".replace(",", "_").replace(".", DECIMAL).replace("_", THOUSANDS)
        totals = df.dropna(subset=[GROUP, COUNT]).groupby(GROUP, sort=False)[COUNT].sum().astype("float64")
        groups = [str(group) for group in totals.index]

        p = figure(width=2000, height=1800, x_axis_type="datetime", title="Umsatz", toolbar_location=None)
        p.line(x="x", y="y", source=line, line_color=IMPRINT[0], line_width=4)
        p.scatter(x="x", y="y", source=line, size=14, color=IMPRINT[0])
        p.add_layout(Label(x=dated.loc[peak, DAY], y=v, text=label, text_color=INK, text_align="right", y_offset=12))
        p.xaxis.formatter = DatetimeTickFormatter(days="%d.%m.%Y", months="%m.%Y", years="%Y")
        low, high = float(dated[Y].min()), float(dated[Y].max())
        step = 10 ** math.floor(math.log10((high - low) / 5))
        step *= next(factor for factor in (1, 2, 2.5, 5, 10) if factor * step >= (high - low) / 5)
        ticks = [step * index for index in range(math.floor(low / step), math.ceil(high / step) + 1)]
        p.yaxis.ticker = FixedTicker(ticks=ticks)
        p.yaxis.major_label_overrides = {tick: f"{tick:,.0f}".replace(",", "_").replace(".", DECIMAL).replace("_", THOUSANDS) for tick in ticks}

        side = figure(width=1200, height=1800, x_range=groups, title="Anzahl", toolbar_location=None)
        side.vbar(x=groups, top=totals.to_numpy(), width=0.7, color=IMPRINT[: len(groups)])
        side.y_range.start = 0
        for plot in (p, side):
            plot.background_fill_color = PAGE_BG
            plot.border_fill_color = PAGE_BG
            plot.outline_line_color = None
            plot.title.text_color = INK
            for axis in (plot.xaxis, plot.yaxis):
                axis.major_label_text_color = INK_SOFT
                axis.axis_line_color = INK_SOFT
            plot.grid.grid_line_color = INK
            plot.grid.grid_line_alpha = 0.1
        p = row(p, side)

        with open(f"plot-{THEME}.json", "w", encoding="utf-8") as figure_file:
            json.dump(json_item(p), figure_file)
    """),
}
