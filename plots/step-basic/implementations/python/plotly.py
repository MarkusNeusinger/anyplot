""" anyplot.ai
step-basic: Basic Step Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 89/100 | Created: 2026-04-30
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Monthly cumulative sales showing discrete jumps
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
x = list(range(len(months)))

monthly_sales = np.random.randint(15000, 45000, size=12)
cumulative_sales = np.cumsum(monthly_sales)

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=x,
        y=cumulative_sales,
        mode="lines+markers",
        line={"shape": "hv", "color": BRAND, "width": 4},
        marker={"size": 14, "color": BRAND, "line": {"color": PAGE_BG, "width": 2}},
        name="Cumulative Sales",
    )
)

# Style
fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "Monthly Cumulative Sales · step-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Month", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickmode": "array",
        "tickvals": x,
        "ticktext": months,
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Cumulative Sales ($)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    showlegend=False,
    margin={"l": 100, "r": 50, "t": 100, "b": 80},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
