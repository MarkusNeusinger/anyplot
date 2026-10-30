"""Shared fixtures for the code-handling tests: a catalogue-style source and the catalogue files."""

import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
CODE_LIBRARIES = ("matplotlib", "seaborn", "plotnine", "altair", "pygal", "letsplot")
"""The libraries with a Python code profile (`normalise.SUPPORTED_LIBRARIES`), in the corpus order."""
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
