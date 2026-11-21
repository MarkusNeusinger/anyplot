"""anyplot.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MOSAIC = "AAB;CCD;EFG"  # one letter per panel slot; a repeated letter spans those cells, "." leaves a gap
ROW_SHARE = [0.40, 0.33, 0.27]  # relative height of each mosaic row; the largest row holds the primary data

# Columns: set these to your table's column names
PANEL = "Panel"  # role: extra
TITLE = "Panel title"  # role: extra
KIND = "Chart kind"  # role: extra
SHADE = "Palette position"  # role: extra
X = "X value"  # role: x
Y = "Y value"  # role: y
X_LABEL = "X axis title"  # role: extra
Y_LABEL = "Y axis title"  # role: extra

# Data: replace this block with your own table, one row per mark, for example df = pd.read_csv("panels.csv")
rng = np.random.default_rng(42)
n_days = 120
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
revenue = 50000 + np.cumsum(rng.normal(0, 1000, n_days)) + np.arange(n_days) * 200
revenue = np.maximum(revenue, 30000)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
monthly_sales = [42000, 48000, 51000, 46000, 58000, 62000]
product_x = rng.normal(50, 15, 100)
product_y = product_x * 0.7 + rng.normal(20, 10, 100)
categories = ["Electronics", "Clothing", "Food", "Books", "Sports"]
cat_values = [35, 28, 22, 15, 18]
n_metric = 30
metrics = [rng.random(n_metric) * 20 + 80, rng.random(n_metric) * 15 + 60, rng.random(n_metric) * 25 + 45]

# (panel, title, chart kind, palette position or -1 for one color per bar, x, y, x title, y title)
panels = [
    ("A", "Revenue Trend (Overview)", "area", 0, list(dates), list(revenue), "Date", "Revenue ($)"),
    ("B", "Monthly Sales", "bar", 1, months, monthly_sales, "Month", "Sales ($)"),
    ("C", "Product Performance", "scatter", 0, list(product_x), list(product_y), "Feature X", "Feature Y"),
    ("D", "Category Distribution", "hbar", -1, categories, cat_values, "Units Sold", ""),
]
metric_info = [("E", "Efficiency", 0, "%"), ("F", "Quality Score", 1, "Score"), ("G", "Response Time", 2, "ms")]
for (letter, title, pos, unit), values in zip(metric_info, metrics, strict=True):
    panels.append((letter, title, "area", pos, list(range(n_metric)), list(values), "Days", unit))

df = pd.concat(
    [
        pd.DataFrame({PANEL: p, TITLE: t, KIND: k, SHADE: s, X: xs, Y: ys, X_LABEL: xl, Y_LABEL: yl})
        for p, t, k, s, xs, ys, xl, yl in panels
    ],
    ignore_index=True,
)

# Plot: reads only df and the constants above
rows_def = MOSAIC.split(";")
n_rows, n_cols = len(rows_def), len(rows_def[0])
groups = list(df.groupby(PANEL, sort=False))  # panels fill the mosaic slots in table order
specs = [[None] * n_cols for _ in range(n_rows)]
slots = []
for r, row in enumerate(rows_def):
    c = 0
    while c < n_cols:
        ch = row[c]
        span = 1
        while c + span < n_cols and row[c + span] == ch:
            span += 1
        if ch != ".":
            slots.append((ch, r + 1, c + 1, span))
        c += span
slots = slots[: len(groups)]
for _, r, c, span in slots:
    specs[r - 1][c - 1] = {"colspan": span}

fig = make_subplots(
    rows=n_rows,
    cols=n_cols,
    specs=specs,
    row_heights=[h / sum(ROW_SHARE[:n_rows]) for h in ROW_SHARE[:n_rows]],
    subplot_titles=[rows[TITLE].iloc[0] for _, rows in groups[: len(slots)]],
    vertical_spacing=0.13,
    horizontal_spacing=0.08,
)


def rgba(hex_color, alpha):
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


def area(xs, ys, color):
    return go.Scatter(
        x=xs, y=ys, mode="lines", line={"color": color, "width": 2.5}, fill="tozeroy", fillcolor=rgba(color, 0.22)
    )


def bar(xs, ys, color):
    return go.Bar(x=xs, y=ys, marker_color=color)


def scatter(xs, ys, color):
    marker = {"size": 7, "color": color, "opacity": 0.75, "line": {"width": 0.8, "color": PAGE_BG}}
    return go.Scatter(x=xs, y=ys, mode="markers", marker=marker)


def hbar(xs, ys, color):
    colors = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(len(xs))]
    return go.Bar(x=ys, y=xs, orientation="h", marker_color=colors)


BUILDERS = {"area": area, "bar": bar, "scatter": scatter, "hbar": hbar}
HORIZONTAL = {"hbar"}
ZERO_BASED = {"area", "bar"}

for (_, row, col, _), (_, rows) in zip(slots, groups, strict=False):
    kind = rows[KIND].iloc[0]
    position = int(rows[SHADE].iloc[0])
    color = IMPRINT_PALETTE[(position if position >= 0 else len(slots)) % len(IMPRINT_PALETTE)]
    fig.add_trace(BUILDERS.get(kind, area)(list(rows[X]), list(rows[Y]), color), row=row, col=col)
    fig.update_xaxes(title_text=rows[X_LABEL].iloc[0], row=row, col=col)
    fig.update_yaxes(title_text=rows[Y_LABEL].iloc[0], row=row, col=col)
    if kind in HORIZONTAL:
        fig.update_yaxes(autorange="reversed", row=row, col=col)
    if kind in ZERO_BASED:
        fig.update_yaxes(rangemode="tozero", row=row, col=col)

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={
        "text": "subplot-mosaic · python · plotly · anyplot.ai",
        "font": {"size": 17, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"l": 62, "r": 22, "t": 62, "b": 42},
)
axis_style = {
    "tickfont": {"size": 8, "color": INK_SOFT},
    "title_font": {"size": 9, "color": INK},
    "title_standoff": 3,
    "gridcolor": GRID,
    "linecolor": INK_SOFT,
    "zerolinecolor": INK_SOFT,
    "automargin": True,
}
fig.update_xaxes(**axis_style)
fig.update_yaxes(**axis_style)
fig.update_annotations(font={"size": 11, "color": INK})

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
