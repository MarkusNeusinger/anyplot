""" pyplots.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Quarterly product sales with asymmetric confidence intervals (10th-90th percentile)
np.random.seed(42)

products = ["Product A", "Product B", "Product C", "Product D", "Product E", "Product F"]

# Central values (median sales in thousands)
sales_median = np.array([85, 62, 45, 78, 95, 55])

# Asymmetric errors (lower and upper bounds differ)
# Lower errors are smaller (closer to median), upper errors are larger (right-skewed distribution)
error_lower = np.array([12, 8, 15, 10, 18, 7])
error_upper = np.array([25, 18, 10, 22, 35, 20])

# Create figure
fig = go.Figure()

# Add scatter plot with asymmetric error bars
fig.add_trace(
    go.Scatter(
        x=products,
        y=sales_median,
        mode="markers",
        marker=dict(size=18, color="#306998", line=dict(width=2, color="white")),
        error_y=dict(
            type="data",
            symmetric=False,
            array=error_upper,
            arrayminus=error_lower,
            color="#306998",
            thickness=3,
            width=12,
        ),
        name="Median Sales (10th-90th percentile)",
        showlegend=True,
    )
)

# Update layout for 4800×2700 px output
fig.update_layout(
    title=dict(text="errorbar-asymmetric · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Product Category", font=dict(size=24)),
        tickfont=dict(size=20),
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Quarterly Sales (thousands USD)", font=dict(size=24)),
        tickfont=dict(size=20),
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
        range=[0, 150],
    ),
    template="plotly_white",
    legend=dict(
        font=dict(size=18),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1,
    ),
    margin=dict(l=100, r=80, t=120, b=100),
    plot_bgcolor="white",
)

# Add annotation explaining the error bars
fig.add_annotation(
    x=0.98,
    y=0.02,
    xref="paper",
    yref="paper",
    text="Error bars show 10th-90th percentile range",
    showarrow=False,
    font=dict(size=16, color="#666666"),
    align="right",
    xanchor="right",
    yanchor="bottom",
)

# Save as PNG (4800 × 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
