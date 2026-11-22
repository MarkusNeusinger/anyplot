"""anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: plotly 6.7.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-18
"""

import os
import sys


# Work around naming conflict: drop the script directory from the import path
if sys.path and sys.path[0] == os.path.dirname(os.path.abspath(__file__)):
    sys.path.pop(0)
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per component in order (first series is always #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: category
PRODUCT = "Product"  # role: component
REVENUE = "Revenue ($ thousands)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
quarters = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025"]
revenue = {
    "Software": [180, 210, 195, 240, 260],
    "Hardware": [120, 95, 110, 130, 105],
    "Services": [85, 90, 105, 115, 125],
    "Maintenance": [45, 50, 52, 55, 60],
}
df = pd.DataFrame(
    {
        QUARTER: quarters * len(revenue),
        PRODUCT: [product for product in revenue for _ in quarters],
        REVENUE: [value for values in revenue.values() for value in values],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=QUARTER, columns=PRODUCT, values=REVENUE, sort=False, aggfunc="sum")
totals = table.sum(axis=1, skipna=True)
top = totals.max()

fig = go.Figure()
for i, product in enumerate(table.columns):
    fig.add_trace(
        go.Bar(
            name=product,
            x=table.index,
            y=table[product],
            marker_color=IMPRINT_PALETTE[i],
            text=[f"${v:,.0f}K" for v in table[product]],
            textposition="inside",
            insidetextanchor="middle",
            textfont={"size": 9, "color": "white"},
        )
    )

# Total label above every complete stack
for quarter, total in totals.items():
    fig.add_annotation(
        x=quarter,
        y=total,
        text=f"<b>${total:,.0f}K</b>",
        showarrow=False,
        font={"size": 11, "color": INK},
        yanchor="bottom",
        yshift=3,
    )

fig.update_layout(
    autosize=False,
    title={
        "text": "bar-stacked-labeled · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": QUARTER, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": REVENUE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [0, top * 1.12],
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    barmode="stack",
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "traceorder": "normal",
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"t": 100, "b": 60, "l": 80, "r": 40},
)

# Save as PNG and HTML (3200x1800)
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
