"""anyplot.ai
alluvial-basic: Basic Alluvial Diagram
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
YEAR = "Year"  # role: time_point
BROWSER = "Browser"  # role: category
SHARE = "Market share (%)"  # role: value
NEXT_YEAR = "Next year"  # role: extra
NEXT_BROWSER = "Browser in next period"  # role: extra
FLOW = "Users moving (%)"  # role: flow

# Data: replace this block with your own table, for example df = pd.read_csv("flows.csv")
# One row per band: the browser at a year, the browser the same users use at the next year, and the flow size.
flows = [
    # 2015 -> 2018: Chrome growth, Firefox decline
    ("2015", "Chrome", "Chrome", 420),
    ("2015", "Chrome", "Safari", 30),
    ("2015", "Firefox", "Firefox", 140),
    ("2015", "Firefox", "Chrome", 45),
    ("2015", "Firefox", "Safari", 15),
    ("2015", "Safari", "Safari", 180),
    ("2015", "Safari", "Chrome", 50),
    ("2015", "Edge", "Edge", 85),
    ("2015", "Edge", "Chrome", 35),
    # 2018 -> 2021: Chrome dominance, Firefox further decline
    ("2018", "Chrome", "Chrome", 460),
    ("2018", "Chrome", "Safari", 25),
    ("2018", "Chrome", "Edge", 15),
    ("2018", "Firefox", "Firefox", 105),
    ("2018", "Firefox", "Chrome", 40),
    ("2018", "Firefox", "Safari", 15),
    ("2018", "Safari", "Safari", 200),
    ("2018", "Safari", "Chrome", 45),
    ("2018", "Edge", "Edge", 95),
    ("2018", "Edge", "Chrome", 30),
    # 2021 -> 2024: Consolidation, Chrome dominance continues
    ("2021", "Chrome", "Chrome", 480),
    ("2021", "Chrome", "Edge", 20),
    ("2021", "Firefox", "Firefox", 95),
    ("2021", "Firefox", "Chrome", 20),
    ("2021", "Safari", "Safari", 215),
    ("2021", "Safari", "Chrome", 50),
    ("2021", "Edge", "Edge", 110),
    ("2021", "Edge", "Chrome", 25),
]
df = pd.DataFrame(flows, columns=[YEAR, BROWSER, NEXT_BROWSER, FLOW])
df[NEXT_YEAR] = df[YEAR].map(dict(zip(["2015", "2018", "2021"], ["2018", "2021", "2024"], strict=True)))
df[SHARE] = df.groupby([YEAR, BROWSER], sort=False)[FLOW].transform("sum")

# Plot: reads only df and the constants above
years = list(dict.fromkeys(list(df[YEAR]) + list(df[NEXT_YEAR])))
browsers = list(dict.fromkeys(list(df[BROWSER]) + list(df[NEXT_BROWSER])))
n_years, n_browsers = len(years), len(browsers)
color_of = {b: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, b in enumerate(browsers)}

# Node i of column t is browser b: index = t * n_browsers + b
node_labels = browsers * n_years
node_colors = [color_of[b] for b in node_labels]
x_positions = np.repeat(0.01 + np.arange(n_years) / (n_years - 1) * 0.98, n_browsers)
y_positions = np.tile(np.linspace(0.15, 0.92, n_browsers), n_years)

year_index = {y: t for t, y in enumerate(years)}
sources = [year_index[y] * n_browsers + browsers.index(b) for y, b in zip(df[YEAR], df[BROWSER], strict=True)]
targets = [
    (year_index[y] + 1) * n_browsers + browsers.index(b) for y, b in zip(df[YEAR], df[NEXT_BROWSER], strict=True)
]
link_colors = []
for b in df[BROWSER]:
    hex_color = color_of[b]
    r, g, bl = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    link_colors.append(f"rgba({r},{g},{bl},0.3)")

fig = go.Figure(
    data=[
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=18,
                thickness=20,
                line=dict(color=INK_SOFT, width=0.5),
                label=node_labels,
                color=node_colors,
                x=x_positions,
                y=y_positions,
                hovertemplate="<b>%{label}</b><extra></extra>",
            ),
            link=dict(
                source=sources,
                target=targets,
                value=list(df[FLOW]),
                color=link_colors,
                hovertemplate="<b>%{source.label}</b> → <b>%{target.label}</b><br>"
                + f"{FLOW}: <b>%{{value}}</b><extra></extra>",
            ),
        )
    ]
)

# Column headers
for t, year in enumerate(years):
    fig.add_annotation(
        x=t / (n_years - 1),
        y=1.02,
        yanchor="bottom",
        xref="paper",
        yref="paper",
        text=f"<b>{year}</b>",
        showarrow=False,
        font=dict(size=13, color=INK),
        xanchor="center",
    )

# Legend: one square marker per browser
for b in browsers:
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=10, color=color_of[b], symbol="square"),
            name=b,
            showlegend=True,
        )
    )

# Style
fig.update_layout(
    autosize=False,
    title=dict(
        text="Browser Market Share · alluvial-basic · python · plotly · anyplot.ai",
        font=dict(size=16, color=INK),
        x=0.5,
        xanchor="center",
        y=0.97,
    ),
    font=dict(size=11, color=INK),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=40, r=40, t=100, b=80),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.12,
        xanchor="center",
        x=0.5,
        font=dict(size=11, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
