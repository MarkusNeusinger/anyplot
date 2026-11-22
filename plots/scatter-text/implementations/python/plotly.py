""" anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: plotly 7.1.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-22
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per paradigm in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
LANGUAGE = "Language"  # role: label
ABSTRACTION = "Level of Abstraction"  # role: x
TYPE_SAFETY = "Type Safety"  # role: y
PARADIGM = "Paradigm"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("languages.csv")
df = pd.DataFrame(
    {
        LANGUAGE: [
            "Python",
            "Haskell",
            "R",
            "Julia",
            "Lisp",
            "Prolog",
            "Java",
            "Ruby",
            "Perl",
            "PHP",
            "Lua",
            "JavaScript",
            "TypeScript",
            "Kotlin",
            "Swift",
            "C#",
            "Dart",
            "Go",
            "MATLAB",
            "Scala",
            "Clojure",
            "F#",
            "OCaml",
            "Elixir",
            "Erlang",
            "C++",
            "Rust",
            "Fortran",
            "COBOL",
            "Assembly",
        ],
        ABSTRACTION: [
            8.5,
            9.0,
            9.5,
            7.5,
            9.5,
            7.5,
            6.5,
            8.0,
            8.5,
            7.0,
            6.0,
            5.0,
            7.5,
            5.5,
            7.0,
            6.0,
            8.0,
            5.0,
            6.5,
            6.0,
            9.8,
            8.0,
            8.5,
            8.5,
            9.2,
            3.0,
            4.0,
            2.0,
            5.0,
            1.0,
        ],
        TYPE_SAFETY: [
            3.0,
            9.5,
            3.0,
            4.5,
            5.0,
            8.0,
            8.0,
            1.5,
            2.5,
            1.5,
            4.0,
            1.5,
            7.0,
            8.5,
            9.0,
            8.5,
            6.0,
            7.0,
            3.0,
            9.0,
            4.5,
            8.5,
            9.5,
            5.5,
            6.5,
            6.0,
            9.0,
            3.5,
            6.5,
            2.5,
        ],
        PARADIGM: [
            "Functional",
            "Functional",
            "Functional",
            "Functional",
            "Functional",
            "Functional",
            "OOP",
            "OOP",
            "OOP",
            "OOP",
            "OOP",
            "Multi-paradigm",
            "Multi-paradigm",
            "Modern OOP",
            "Modern OOP",
            "Modern OOP",
            "Modern OOP",
            "Systems",
            "Systems",
            "Typed functional",
            "Typed functional",
            "Typed functional",
            "Typed functional",
            "Scripting",
            "Scripting",
            "Legacy and low-level",
            "Legacy and low-level",
            "Legacy and low-level",
            "Legacy and low-level",
            "Legacy and low-level",
        ],
    }
)

# Plot: reads only df and the constants above
fig = go.Figure()
for i, (paradigm, rows) in enumerate(df.groupby(PARADIGM, sort=False)):
    hover = [
        f"<b>{name}</b><br>{ABSTRACTION}: {xv:.1f}<br>{TYPE_SAFETY}: {yv:.1f}"
        for name, xv, yv in zip(rows[LANGUAGE], rows[ABSTRACTION], rows[TYPE_SAFETY], strict=True)
    ]
    fig.add_trace(
        go.Scatter(
            x=rows[ABSTRACTION],
            y=rows[TYPE_SAFETY],
            mode="text",
            text=rows[LANGUAGE],
            textfont=dict(size=11, color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]),
            textposition="middle center",
            name=str(paradigm),
            hovertext=hover,
            hoverinfo="text",
        )
    )

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title=dict(
        text="scatter-text · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text=ABSTRACTION, font=dict(size=13, color=INK)),
        tickfont=dict(size=11, color=INK_SOFT),
        range=[0, df[ABSTRACTION].max() * 1.07],
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text=TYPE_SAFETY, font=dict(size=13, color=INK)),
        tickfont=dict(size=11, color=INK_SOFT),
        range=[0, df[TYPE_SAFETY].max() * 1.1],
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend=dict(
        title=dict(text=PARADIGM, font=dict(size=12, color=INK)),
        font=dict(size=11, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        x=1.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
    ),
    margin=dict(l=70, r=150, t=60, b=60),
    font=dict(family="Arial", color=INK),
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
