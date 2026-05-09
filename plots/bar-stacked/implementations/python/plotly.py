"""anyplot.ai
bar-stacked: Stacked Bar Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 97/100 | Updated: 2026-05-09
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

# Okabe-Ito palette (first series always #009E73)
COLORS = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Quarterly revenue by product category
quarters = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]

# Revenue in thousands USD for each product category
software = [120, 145, 160, 180]
hardware = [80, 75, 90, 95]
services = [45, 55, 65, 75]
support = [25, 30, 35, 40]

# Calculate totals for annotation
totals = [s + h + sv + sp for s, h, sv, sp in zip(software, hardware, services, support, strict=True)]

# Create figure
fig = go.Figure()

# Add stacked bars (bottom to top)
fig.add_trace(
    go.Bar(
        name="Software",
        x=quarters,
        y=software,
        marker_color=COLORS[0],
        text=software,
        textposition="inside",
        textfont={"size": 18, "color": "white"},
    )
)

fig.add_trace(
    go.Bar(
        name="Hardware",
        x=quarters,
        y=hardware,
        marker_color=COLORS[1],
        text=hardware,
        textposition="inside",
        textfont={"size": 18, "color": "white"},
    )
)

fig.add_trace(
    go.Bar(
        name="Services",
        x=quarters,
        y=services,
        marker_color=COLORS[2],
        text=services,
        textposition="inside",
        textfont={"size": 18, "color": "white"},
    )
)

fig.add_trace(
    go.Bar(
        name="Support",
        x=quarters,
        y=support,
        marker_color=COLORS[3],
        text=support,
        textposition="inside",
        textfont={"size": 18, "color": "white"},
    )
)

# Add total annotations above each bar
for quarter, total in zip(quarters, totals, strict=True):
    fig.add_annotation(
        x=quarter, y=total + 10, text=f"${total}K", showarrow=False, font={"size": 20, "color": INK, "weight": "bold"}
    )

# Update layout with theme-adaptive colors
fig.update_layout(
    title={
        "text": "bar-stacked · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Quarter", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Revenue (Thousands USD)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    barmode="stack",
    bargap=0.3,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "orientation": "v",
        "yanchor": "top",
        "y": 0.99,
        "xanchor": "right",
        "x": 0.99,
        "font": {"size": 18, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 100, "r": 60, "t": 100, "b": 80},
)

# Save as PNG (4800 x 2700 px)
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
