"""anyplot.ai
lollipop-grouped: Grouped Lollipop Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
REGION = "Region"  # role: category
PRODUCT_LINE = "Product line"  # role: series
REVENUE = "Quarterly revenue (million USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
df = pd.DataFrame(
    {
        REGION: ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"] * 3,
        PRODUCT_LINE: ["Electronics"] * 5 + ["Apparel"] * 5 + ["Home Goods"] * 5,
        REVENUE: [42.5, 38.2, 51.3, 18.7, 12.4, 28.3, 45.6, 32.1, 22.8, 8.9, 35.1, 29.8, 25.4, 15.2, 10.6],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=REGION, columns=PRODUCT_LINE, values=REVENUE, sort=False)
table = table.loc[table.sum(axis=1).sort_values(ascending=False).index]  # regions sorted by total revenue

x = np.arange(len(table.index))
n_series = len(table.columns)
step = 0.72 / n_series  # offset between neighbouring lollipops inside a group

fig = go.Figure()
for i, line in enumerate(table.columns):
    color = IMPRINT_PALETTE[i]
    values = table[line].to_numpy()
    xs = x + (i - (n_series - 1) / 2) * step

    # One trace for all stems of the series: segments from the zero baseline, separated by gaps
    stem_x = np.repeat(xs, 3).astype(object)
    stem_y = np.column_stack([np.zeros(len(values)), values, np.full(len(values), np.nan)]).ravel().astype(object)
    stem_x[2::3] = None
    stem_y[2::3] = None
    fig.add_trace(
        go.Scatter(
            x=stem_x,
            y=stem_y,
            mode="lines",
            line={"color": color, "width": 2},
            showlegend=False,
            hoverinfo="skip",
            connectgaps=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=values,
            mode="markers",
            marker={"size": 10, "color": color, "line": {"color": PAGE_BG, "width": 1}},
            name=str(line),
            customdata=table.index,
            hovertemplate="%{customdata}<br>" + str(line) + ": %{y:.1f}M<extra></extra>",
        )
    )

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={
        "text": "lollipop-grouped · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": REGION, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickvals": x,
        "ticktext": list(table.index),
        "showgrid": False,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": REVENUE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": INK_SOFT,
        "zerolinewidth": 1,
        "linecolor": INK_SOFT,
        "range": [0, np.nanmax(table.to_numpy()) * 1.1],
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "title": {"text": PRODUCT_LINE, "font": {"size": 10, "color": INK}},
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
    },
    margin={"l": 80, "r": 40, "t": 90, "b": 60},
    hovermode="closest",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
