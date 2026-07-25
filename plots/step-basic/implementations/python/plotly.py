"""anyplot.ai
step-basic: Basic Step Plot
Library: plotly 6.9.0 | Python 3.13.14
Quality: 87/100 | Created: 2026-07-25
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"  # Imprint palette position 1

# Data - Monthly cumulative sales showing discrete jumps
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
x = list(range(len(months)))

monthly_sales = np.random.randint(15000, 45000, size=12)
cumulative_sales = np.cumsum(monthly_sales)
year_total = int(cumulative_sales[-1])

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=x,
        y=cumulative_sales,
        mode="lines+markers",
        line={"shape": "hv", "color": BRAND, "width": 3},
        marker={"size": 11, "color": BRAND, "line": {"color": PAGE_BG, "width": 2}},
        fill="tozeroy",
        fillcolor="rgba(0,158,115,0.12)",
        name="Cumulative Sales",
        customdata=months,
        hovertemplate="<b>%{customdata}</b><br>Cumulative: $%{y:,.0f}<extra></extra>",
    )
)

# Year-total reference line — focal point highlighting the running total
fig.add_hline(y=year_total, line_dash="dot", line_color=INK_SOFT, line_width=1.5, opacity=0.7)
fig.add_annotation(
    x=0,
    xref="paper",
    y=year_total,
    yref="y",
    xanchor="left",
    yanchor="bottom",
    yshift=12,
    text=f"Year total ${year_total:,.0f}",
    showarrow=False,
    font={"size": 11, "color": INK_SOFT},
)

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "step-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Month", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickmode": "array",
        "tickvals": x,
        "ticktext": months,
        "showgrid": False,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Cumulative Sales ($)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "rangemode": "tozero",
    },
    showlegend=False,
    margin={"l": 90, "r": 50, "t": 90, "b": 70},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
