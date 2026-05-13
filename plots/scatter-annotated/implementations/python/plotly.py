"""anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: plotly 6.5.0 | Python 3.13.11
Quality: pending | Created: 2025-12-30
"""

import os

import numpy as np
from plotly import graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data - Top tech companies by market cap and revenue
np.random.seed(42)

companies = [
    "Apple",
    "Microsoft",
    "Alphabet",
    "Amazon",
    "Meta",
    "Tesla",
    "Nvidia",
    "Samsung",
    "TSMC",
    "Oracle",
    "Salesforce",
    "Netflix",
]

# Market cap (billions USD) - x axis
market_cap = np.array([2800, 2700, 1700, 1500, 900, 700, 1200, 350, 500, 300, 250, 250])

# Annual revenue (billions USD) - y axis
revenue = np.array([380, 210, 280, 520, 130, 95, 60, 230, 70, 50, 32, 33])

# Create figure
fig = go.Figure()

# Add scatter points with brand color
fig.add_trace(
    go.Scatter(
        x=market_cap,
        y=revenue,
        mode="markers",
        marker=dict(size=20, color=BRAND, opacity=0.7, line=dict(width=2, color=PAGE_BG)),
        hovertemplate="<b>%{text}</b><br>Market Cap: $%{x}B<br>Revenue: $%{y}B<extra></extra>",
        text=companies,
    )
)

# Manually adjust label positions to avoid overlap
annotations = []

# Position adjustments (ax, ay in pixels from point)
position_adjustments = {
    "Apple": (70, -45),
    "Microsoft": (-90, 45),
    "Alphabet": (80, 0),
    "Amazon": (0, -55),
    "Nvidia": (0, 55),
    "TSMC": (75, 20),
    "Meta": (70, -35),
    "Tesla": (-75, -25),
    "Samsung": (-80, 0),
    "Oracle": (75, -30),
    "Salesforce": (-90, 0),
    "Netflix": (80, 25),
}

# Create annotations with theme-adaptive colors
for company, cap, rev in zip(companies, market_cap, revenue):
    ax, ay = position_adjustments.get(company, (0, -40))

    annotations.append(
        dict(
            x=cap,
            y=rev,
            text=f"<b>{company}</b>",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor=BRAND,
            ax=ax,
            ay=ay,
            font=dict(size=18, color=INK),
            bgcolor=ELEVATED_BG,
            bordercolor=INK_SOFT,
            borderwidth=1,
            borderpad=4,
        )
    )

# Update layout with theme-adaptive colors
fig.update_layout(
    title=dict(text="scatter-annotated · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Market Cap (Billion USD)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        showline=True,
        linewidth=2,
        linecolor=INK_SOFT,
        range=[-100, 3100],
    ),
    yaxis=dict(
        title=dict(text="Annual Revenue (Billion USD)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        showline=True,
        linewidth=2,
        linecolor=INK_SOFT,
        range=[-30, 580],
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    annotations=annotations,
    margin=dict(l=100, r=80, t=100, b=100),
    showlegend=False,
)

# Save with theme-suffixed filenames
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
