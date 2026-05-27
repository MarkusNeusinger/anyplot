""" anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
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
BRAND_ACCENT = "#C475FD"

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

# Identify key companies (top 3 by market cap) for visual emphasis
top_companies = sorted(zip(companies, market_cap), key=lambda x: x[1], reverse=True)[:3]
top_names = {name for name, _ in top_companies}

# Color data points: key companies get accent color, others get brand
marker_colors = [BRAND_ACCENT if company in top_names else BRAND for company in companies]

# Add scatter points with differentiated colors for emphasis
fig.add_trace(
    go.Scatter(
        x=market_cap,
        y=revenue,
        mode="markers",
        marker=dict(
            size=[25 if c in top_names else 20 for c in companies],
            color=marker_colors,
            opacity=0.8,
            line=dict(width=2.5, color="white" if THEME == "light" else PAGE_BG),
        ),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Market Cap: $%{x:.0f}B<br>"
            "Annual Revenue: $%{y:.0f}B<br>"
            "Efficiency: %{customdata:.2f}x"
            "<extra></extra>"
        ),
        text=companies,
        customdata=revenue / market_cap,
    )
)


# Smart label positioning with collision detection
def calculate_label_positions(companies, market_cap, revenue, x_range=(0, 3000), y_range=(0, 600)):
    """Calculate annotation positions with directional distribution."""
    positions = {}
    directions = [(100, -30), (100, 30), (-100, -30), (-100, 30), (0, 60), (0, -60)]

    for i, company in enumerate(companies):
        positions[company] = directions[i % len(directions)]

    return positions


position_adjustments = calculate_label_positions(companies, market_cap, revenue)

# Create annotations with enhanced styling
annotations = []

for company, cap, rev in zip(companies, market_cap, revenue):
    ax, ay = position_adjustments.get(company, (0, -40))
    is_key = company in top_names

    # Enhanced annotation styling with better visual hierarchy
    annotations.append(
        dict(
            x=cap,
            y=rev,
            text=f"<b>{company}</b>",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
            arrowwidth=2.5,
            arrowcolor=BRAND_ACCENT if is_key else BRAND,
            ax=ax,
            ay=ay,
            font=dict(size=19 if is_key else 18, color=INK, family="Arial, sans-serif"),
            bgcolor=ELEVATED_BG,
            bordercolor=BRAND_ACCENT if is_key else INK_SOFT,
            borderwidth=2 if is_key else 1.5,
            borderpad=5,
            opacity=0.95,
        )
    )

# Update layout with enhanced visual hierarchy and polish
fig.update_layout(
    title=dict(
        text="scatter-annotated · plotly · anyplot.ai",
        font=dict(size=28, color=INK, family="Arial, sans-serif"),
        x=0.5,
        xanchor="center",
        y=0.98,
        yanchor="top",
    ),
    xaxis=dict(
        title=dict(text="Market Cap (Billion USD)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        showline=True,
        linewidth=2.5,
        linecolor=INK_SOFT,
        range=[-100, 3100],
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Annual Revenue (Billion USD)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        showline=True,
        linewidth=2.5,
        linecolor=INK_SOFT,
        range=[-30, 580],
        zeroline=False,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    annotations=annotations,
    margin=dict(l=120, r=100, t=120, b=120),
    showlegend=False,
    hovermode="closest",
    font=dict(family="Arial, sans-serif", color=INK),
)

# Save with theme-suffixed filenames
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
