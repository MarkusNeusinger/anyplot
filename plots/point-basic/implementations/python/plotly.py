""" pyplots.ai
point-basic: Point Estimate Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Treatment effects for different interventions
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]

# Generate realistic point estimates with varying confidence intervals
estimates = [0.0, 2.3, 3.8, 1.5, 4.2, 2.9]
# CI widths vary by sample size/variance
ci_widths = [0.8, 1.2, 0.9, 1.5, 1.1, 1.3]
lower = [e - w for e, w in zip(estimates, ci_widths, strict=False)]
upper = [e + w for e, w in zip(estimates, ci_widths, strict=False)]

# Create figure
fig = go.Figure()

# Add error bars (horizontal orientation)
fig.add_trace(
    go.Scatter(
        x=estimates,
        y=categories,
        mode="markers",
        marker={"size": 18, "color": "#306998", "symbol": "circle"},
        error_x={
            "type": "data",
            "symmetric": False,
            "array": [u - e for e, u in zip(estimates, upper, strict=False)],
            "arrayminus": [e - low for e, low in zip(estimates, lower, strict=False)],
            "color": "#306998",
            "thickness": 3,
            "width": 10,
        },
        name="Estimate ± 95% CI",
        showlegend=True,
    )
)

# Add reference line at zero (null hypothesis)
fig.add_vline(
    x=0,
    line={"color": "#FFD43B", "width": 3, "dash": "dash"},
    annotation_text="Null",
    annotation_position="top",
    annotation_font={"size": 18, "color": "#FFD43B"},
)

# Layout
fig.update_layout(
    title={"text": "point-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Effect Size (units)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "zeroline": False,
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    yaxis={
        "title": {"text": "Treatment Group", "font": {"size": 24}},
        "tickfont": {"size": 20},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    template="plotly_white",
    legend={
        "font": {"size": 18},
        "x": 0.98,
        "y": 0.02,
        "xanchor": "right",
        "yanchor": "bottom",
        "bgcolor": "rgba(255,255,255,0.8)",
    },
    margin={"l": 150, "r": 80, "t": 100, "b": 80},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
