"""anyplot.ai
burndown-sprint: Agile Sprint Burndown Chart
Library: plotly | Python 3.13
Quality: pending | Created: 2026-06-14
"""

import os
import sys


# Remove this script's directory from sys.path so 'plotly' resolves to the
# installed package and not this file (which shares the package name).
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p != _script_dir]

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
WEEKEND_FILL = "rgba(26,26,23,0.05)" if THEME == "light" else "rgba(240,239,232,0.05)"

# Imprint palette — first series always #009E73
BRAND = "#009E73"  # actual remaining-work line
SCOPE_COLOR = "#AE3030"  # scope change event (semantic red — risk/addition)

# Data: 10-working-day sprint (Jan 6–17 2025), initial scope 40 SP
# Scope addition of +8 on Jan 9 (working day 4) causes remaining to jump
sprint_dates = pd.date_range("2025-01-06", "2025-01-17", freq="D").strftime("%Y-%m-%d").tolist()
remaining = [40, 36, 30, 38, 30, 30, 30, 22, 14, 8, 3, 0]

# Ideal burndown: straight reference from (sprint start, 40) to (sprint end, 0)
ideal_dates = [sprint_dates[0], sprint_dates[-1]]
ideal_values = [40, 0]

# Title (46 chars — under 67-char baseline, no fontsize scaling needed)
title = "burndown-sprint · python · plotly · anyplot.ai"

# Figure
fig = go.Figure()

# Weekend shading (Jan 11 Sat – Jan 12 Sun)
fig.add_vrect(
    x0="2025-01-11",
    x1="2025-01-13",
    fillcolor=WEEKEND_FILL,
    layer="below",
    line_width=0,
    annotation_text="Weekend",
    annotation_position="top left",
    annotation_font={"size": 9, "color": INK_MUTED},
)

# Ideal burndown reference line (dashed, theme-adaptive muted)
fig.add_trace(
    go.Scatter(
        x=ideal_dates,
        y=ideal_values,
        mode="lines",
        name="Ideal burndown",
        line={"color": INK_SOFT, "width": 2, "dash": "dash"},
    )
)

# Actual remaining work (step series — horizontal-then-vertical)
fig.add_trace(
    go.Scatter(
        x=sprint_dates,
        y=remaining,
        mode="lines+markers",
        name="Remaining story points",
        line={"color": BRAND, "width": 3.5, "shape": "hv"},
        marker={"color": BRAND, "size": 8, "symbol": "circle"},
    )
)

# Scope change event on Jan 9 (working day 4, +8 SP added)
fig.add_vline(
    x="2025-01-09",
    line_width=1.5,
    line_dash="dot",
    line_color=SCOPE_COLOR,
    annotation_text="Scope +8 SP",
    annotation_position="top right",
    annotation_font={"size": 10, "color": SCOPE_COLOR},
    annotation_bgcolor=ELEVATED_BG,
    annotation_bordercolor=SCOPE_COLOR,
    annotation_borderwidth=1,
)

# Layout
fig.update_layout(
    autosize=False,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0, "xanchor": "left", "xref": "paper"},
    xaxis={
        "title": {"text": "Sprint Day", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "tickformat": "%b %d",
        "showgrid": False,
        "showline": True,
        "mirror": False,
    },
    yaxis={
        "title": {"text": "Remaining Story Points", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": GRID,
        "rangemode": "tozero",
        "showgrid": True,
        "showline": True,
        "mirror": False,
    },
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"color": INK_SOFT, "size": 10},
        "x": 0.97,
        "y": 0.97,
        "xanchor": "right",
        "yanchor": "top",
    },
    font={"color": INK},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
