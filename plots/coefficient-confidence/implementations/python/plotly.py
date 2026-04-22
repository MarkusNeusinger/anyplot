""" pyplots.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: plotly 6.5.1 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import numpy as np
import plotly.graph_objects as go


# Data: Housing price regression coefficients
np.random.seed(42)

variables = [
    "Square Footage",
    "Bedrooms",
    "Bathrooms",
    "Garage Spaces",
    "Lot Size (acres)",
    "Age (years)",
    "Distance to City Center",
    "School Rating",
    "Crime Rate Index",
    "Property Tax Rate",
    "Has Pool",
    "Has Basement",
]

# Generate realistic regression coefficients with varying significance
coefficients = np.array([0.45, 0.12, 0.18, 0.08, 0.22, -0.15, -0.28, 0.32, -0.19, -0.05, 0.14, 0.09])
standard_errors = np.array([0.08, 0.09, 0.06, 0.05, 0.07, 0.04, 0.10, 0.08, 0.11, 0.06, 0.05, 0.07])

# 95% confidence intervals
ci_lower = coefficients - 1.96 * standard_errors
ci_upper = coefficients + 1.96 * standard_errors

# Determine significance (CI does not cross zero)
significant = (ci_lower > 0) | (ci_upper < 0)

# Sort by coefficient magnitude for better visualization
sort_idx = np.argsort(coefficients)
variables = [variables[i] for i in sort_idx]
coefficients = coefficients[sort_idx]
ci_lower = ci_lower[sort_idx]
ci_upper = ci_upper[sort_idx]
significant = significant[sort_idx]

# Colors based on significance
colors = ["#306998" if sig else "#999999" for sig in significant]
marker_symbols = ["circle" if sig else "circle-open" for sig in significant]

# Create figure
fig = go.Figure()

# Add error bars (confidence intervals)
for i in range(len(variables)):
    # Error bar line
    fig.add_trace(
        go.Scatter(
            x=[ci_lower[i], ci_upper[i]],
            y=[variables[i], variables[i]],
            mode="lines",
            line=dict(color=colors[i], width=4),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # End caps for error bars
    fig.add_trace(
        go.Scatter(
            x=[ci_lower[i], ci_upper[i]],
            y=[variables[i], variables[i]],
            mode="markers",
            marker=dict(symbol="line-ns", size=16, color=colors[i], line=dict(width=3)),
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Add coefficient points
fig.add_trace(
    go.Scatter(
        x=coefficients[significant],
        y=[variables[i] for i in range(len(variables)) if significant[i]],
        mode="markers",
        marker=dict(size=18, color="#306998", line=dict(width=2, color="white")),
        name="Significant (p < 0.05)",
        hovertemplate="%{y}<br>Coefficient: %{x:.3f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=coefficients[~significant],
        y=[variables[i] for i in range(len(variables)) if not significant[i]],
        mode="markers",
        marker=dict(size=18, color="#999999", symbol="circle-open", line=dict(width=3, color="#999999")),
        name="Not Significant",
        hovertemplate="%{y}<br>Coefficient: %{x:.3f}<extra></extra>",
    )
)

# Add vertical reference line at zero
fig.add_vline(
    x=0,
    line=dict(color="#333333", width=2, dash="dash"),
    annotation_text="Null",
    annotation_position="top",
    annotation_font=dict(size=16, color="#333333"),
)

# Layout
fig.update_layout(
    title=dict(text="coefficient-confidence · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Coefficient Estimate (Standardized)", font=dict(size=22)),
        tickfont=dict(size=18),
        zeroline=False,
        gridcolor="rgba(0,0,0,0.1)",
        range=[-0.6, 0.7],
    ),
    yaxis=dict(
        title=dict(text="Predictor Variable", font=dict(size=22)), tickfont=dict(size=18), gridcolor="rgba(0,0,0,0.1)"
    ),
    template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=18)),
    margin=dict(l=200, r=80, t=120, b=80),
    plot_bgcolor="white",
)

# Save as PNG (4800x2700)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
