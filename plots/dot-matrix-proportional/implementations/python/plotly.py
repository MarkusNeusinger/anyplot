"""anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Created: 2026-05-08
"""

import math
import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CATEGORY = "Commute mode"  # role: category
COUNT = "Respondents"  # role: count
TOTAL = "Survey size"  # role: total

# Data: replace this block with your own table, for example df = pd.read_csv("survey.csv")
df = pd.DataFrame(
    {CATEGORY: ["Public Transit", "Car", "Cycling", "Work from Home"], COUNT: [42, 31, 15, 12], TOTAL: [100] * 4}
)

# Plot
total = int(df[TOTAL].iloc[0])
grid_cols = math.ceil(math.sqrt(total))
grid_rows = math.ceil(total / grid_cols)

# Fill left-to-right, top-to-bottom: dot i sits in column i % cols, row i // cols (row 0 at the top)
dot_index = 0
fig = go.Figure()
for i, (cat, count) in enumerate(zip(df[CATEGORY], df[COUNT], strict=True)):
    slots = range(dot_index, dot_index + int(count))
    dot_index += int(count)
    pct = count / total * 100
    fig.add_trace(
        go.Scatter(
            x=[k % grid_cols for k in slots],
            y=[grid_rows - 1 - k // grid_cols for k in slots],
            mode="markers",
            name=f"{cat}  ·  {count} ({pct:.0f}%)",
            marker={"color": IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)], "size": 22, "symbol": "circle"},
            hovertemplate=f"<b>{cat}</b><br>Count: {count}<br>Share: {pct:.0f}%<extra></extra>",
        )
    )

top = df.loc[df[COUNT].idxmax()]
title = "City Commute Survey · dot-matrix-proportional · python · plotly · anyplot.ai"

fig.update_layout(
    autosize=False,
    title={
        "text": title,
        "font": {"size": round(16 * min(1.0, 67 / len(title))), "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.975,
        "yanchor": "top",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={"visible": False, "range": [-0.7, grid_cols - 0.3], "fixedrange": True},
    yaxis={"visible": False, "range": [-0.7, grid_rows - 0.3], "scaleanchor": "x", "scaleratio": 1, "fixedrange": True},
    legend={
        "orientation": "h",
        "x": 0.5,
        "y": -0.04,
        "xanchor": "center",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"color": INK_SOFT, "size": 10},
        "tracegroupgap": 0,
    },
    annotations=[
        # Insight subtitle: draw attention to the largest category
        {
            "text": f"<b>{top[COUNT] / total:.0%}</b> · {top[CATEGORY]} is the largest group",
            "x": 0.5,
            "y": 1.0,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 11, "color": IMPRINT_PALETTE[0]},
            "xanchor": "center",
            "yanchor": "bottom",
        },
        # Scale context
        {
            "text": f"Each ● represents 1 respondent  ·  n = {total}",
            "x": 0.5,
            "y": -0.005,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 9, "color": INK_MUTED},
            "xanchor": "center",
            "yanchor": "bottom",
        },
    ],
    margin={"l": 40, "r": 40, "t": 85, "b": 100},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
