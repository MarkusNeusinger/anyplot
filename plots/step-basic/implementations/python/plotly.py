""" pyplots.ai
step-basic: Basic Step Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-15
"""

import numpy as np
import plotly.graph_objects as go


# Data - Monthly cumulative sales showing discrete jumps
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
x = list(range(len(months)))

# Cumulative sales that increase in discrete steps
monthly_sales = np.random.randint(15000, 45000, size=12)
cumulative_sales = np.cumsum(monthly_sales)

# Create step plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=x,
        y=cumulative_sales,
        mode="lines+markers",
        line={"shape": "hv", "color": "#306998", "width": 4},  # 'hv' creates post-step style
        marker={"size": 14, "color": "#FFD43B", "line": {"color": "#306998", "width": 2}},
        name="Cumulative Sales",
    )
)

# Layout for 4800x2700 px
fig.update_layout(
    title={
        "text": "Monthly Cumulative Sales · step-basic · plotly · pyplots.ai",
        "font": {"size": 32},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Month", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "tickmode": "array",
        "tickvals": x,
        "ticktext": months,
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    yaxis={
        "title": {"text": "Cumulative Sales ($)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    template="plotly_white",
    showlegend=True,
    legend={"font": {"size": 18}, "x": 0.02, "y": 0.98, "bgcolor": "rgba(255,255,255,0.8)"},
    margin={"l": 100, "r": 50, "t": 100, "b": 80},
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html")
