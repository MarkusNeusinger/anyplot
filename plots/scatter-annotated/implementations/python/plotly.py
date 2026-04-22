""" pyplots.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Top tech companies by market cap and revenue (12 companies for cleaner annotations)
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

# Add scatter points
fig.add_trace(
    go.Scatter(
        x=market_cap,
        y=revenue,
        mode="markers+text",
        marker=dict(size=20, color="#306998", opacity=0.7, line=dict(width=2, color="white")),
        text=companies,
        textposition="top center",
        textfont=dict(size=14, color="#333333"),
        hovertemplate="<b>%{text}</b><br>Market Cap: $%{x}B<br>Revenue: $%{y}B<extra></extra>",
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

# Remove default text labels and add custom annotations with arrows
fig.update_traces(mode="markers", textposition=None, text=None)

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
            arrowcolor="#306998",
            ax=ax,
            ay=ay,
            font=dict(size=18, color="#333333"),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#306998",
            borderwidth=1,
            borderpad=4,
        )
    )

# Update layout
fig.update_layout(
    title=dict(
        text="scatter-annotated · plotly · pyplots.ai", font=dict(size=32, color="#333333"), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Market Cap (Billion USD)", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        showline=True,
        linewidth=2,
        linecolor="#333333",
        range=[-100, 3100],
    ),
    yaxis=dict(
        title=dict(text="Annual Revenue (Billion USD)", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        showline=True,
        linewidth=2,
        linecolor="#333333",
        range=[-30, 580],
    ),
    template="plotly_white",
    annotations=annotations,
    margin=dict(l=100, r=80, t=100, b=100),
    showlegend=False,
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs=True)
