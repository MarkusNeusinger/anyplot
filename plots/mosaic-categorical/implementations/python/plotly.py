""" anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: plotly 7.1.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-22
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GAP = 0.015  # gap between neighbouring columns, in share of the full width
LABEL_MIN_HEIGHT = 0.08  # tiles shorter than this share of their column stay unlabeled

# Columns: set these to your table's column names
PASSENGER_CLASS = "Passenger Class"  # role: category_1
SURVIVAL = "Survival"  # role: category_2
PASSENGERS = "Passengers"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("titanic.csv")
df = pd.DataFrame(
    {
        PASSENGER_CLASS: ["First", "First", "Second", "Second", "Third", "Third"],
        SURVIVAL: ["Survived", "Did Not Survive", "Survived", "Did Not Survive", "Survived", "Did Not Survive"],
        PASSENGERS: [203, 122, 118, 167, 178, 528],
    }
)

# Plot
# Contingency table in the data's own order; the first level of the second variable goes on top
table = df.pivot_table(index=SURVIVAL, columns=PASSENGER_CLASS, values=PASSENGERS, aggfunc="sum", sort=False)
table = table.astype(float).iloc[::-1]
colors = {level: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, level in enumerate(df[SURVIVAL].unique())}

col_totals = table.sum(axis=0)
total = col_totals.sum()
col_widths = col_totals / total

shapes = []
annotations = []
hover_xs, hover_ys, hover_texts, hover_colors = [], [], [], []

x_start = 0.0
for class_name in table.columns:
    width = col_widths[class_name] - GAP
    y_start = 0.0
    for level in table.index:
        count = table.loc[level, class_name]
        height = count / col_totals[class_name]

        shapes.append(
            {
                "type": "rect",
                "x0": x_start,
                "y0": y_start,
                "x1": x_start + width,
                "y1": y_start + height,
                "fillcolor": colors[level],
                "line": {"color": PAGE_BG, "width": 1},
                "layer": "below",
            }
        )

        if height > LABEL_MIN_HEIGHT:
            annotations.append(
                {
                    "x": x_start + width / 2,
                    "y": y_start + height / 2,
                    "text": f"<b>{count:.0f}</b>",
                    "showarrow": False,
                    "font": {"size": 11, "color": "#1A1A17"},
                    "xanchor": "center",
                    "yanchor": "middle",
                }
            )

        hover_xs.append(x_start + width / 2)
        hover_ys.append(y_start + height / 2)
        hover_texts.append(
            f"<b>{class_name} Class — {level}</b><br>"
            f"Count: {count:.0f}<br>"
            f"Within-class proportion: {height * 100:.1f}%<br>"
            f"Share of all passengers: {count / total * 100:.1f}%"
        )
        hover_colors.append(colors[level])

        y_start += height

    annotations.append(
        {
            "x": x_start + width / 2,
            "y": -0.015,
            "text": f"<b>{class_name}</b>",
            "showarrow": False,
            "font": {"size": 12, "color": INK},
            "xanchor": "center",
            "yanchor": "top",
        }
    )

    x_start += width + GAP

fig = go.Figure()

# Legend traces (markers shown only in the legend), in the data's level order
for level, color in colors.items():
    fig.add_trace(
        go.Scatter(x=[None], y=[None], mode="markers", marker={"size": 10, "color": color}, name=level, showlegend=True)
    )

# Per-cell invisible scatter for interactive hover tooltips
fig.add_trace(
    go.Scatter(
        x=hover_xs,
        y=hover_ys,
        mode="markers",
        marker={"size": 1, "color": hover_colors, "opacity": 0},
        hovertemplate="%{text}<extra></extra>",
        text=hover_texts,
        showlegend=False,
    )
)

fig.update_layout(
    autosize=False,
    title={
        "text": "mosaic-categorical · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    shapes=shapes,
    annotations=annotations,
    xaxis={
        "title": {"text": PASSENGER_CLASS, "font": {"size": 12, "color": INK}, "standoff": 22},
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "showline": False,
        "range": [-0.02, 1.0],
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Proportion within class", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "zeroline": False,
        "range": [-0.1, 1.02],
        "tickvals": [0, 0.2, 0.4, 0.6, 0.8, 1.0],
        "linecolor": INK_SOFT,
    },
    legend={
        "title": {"text": SURVIVAL, "font": {"size": 10, "color": INK}},
        "font": {"size": 10, "color": INK_SOFT},
        "x": 1.01,
        "y": 0.75,
        "xanchor": "left",
        "yanchor": "middle",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 70, "r": 100, "t": 60, "b": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
