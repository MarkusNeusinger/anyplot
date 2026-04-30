""" anyplot.ai
rose-basic: Basic Rose Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-04-30
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - Monthly rainfall (mm) showing pronounced seasonal pattern
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [92, 74, 60, 45, 32, 18, 12, 22, 48, 75, 98, 105]

# Plot
fig = go.Figure()

fig.add_trace(
    go.Barpolar(
        r=rainfall,
        theta=months,
        width=0.9,
        marker={
            "color": rainfall,
            "colorscale": "viridis",
            "line": {"color": PAGE_BG, "width": 2},
            "cmin": 0,
            "cmax": max(rainfall),
        },
        hovertemplate="<b>%{theta}</b><br>Rainfall: %{r} mm<extra></extra>",
    )
)

fig.update_layout(
    title={
        "text": "rose-basic · plotly · anyplot.ai",
        "font": {"size": 48, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    polar={
        "bgcolor": PAGE_BG,
        "angularaxis": {
            "tickfont": {"size": 28, "color": INK_SOFT},
            "direction": "clockwise",
            "rotation": 90,
            "gridcolor": GRID,
            "linecolor": INK_SOFT,
        },
        "radialaxis": {
            "tickfont": {"size": 22, "color": INK_SOFT},
            "gridcolor": GRID,
            "linecolor": INK_SOFT,
            "ticksuffix": " mm",
            "angle": 45,
            "dtick": 25,
        },
    },
    showlegend=False,
    margin={"l": 100, "r": 100, "t": 150, "b": 100},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
