""" pyplots.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - Simulating economic indicator over time with recession period
np.random.seed(42)
years = np.arange(2005, 2015)
# Economic indicator with dip during 2008-2009 recession
base_values = np.array([100, 105, 110, 95, 85, 90, 100, 108, 115, 120])
noise = np.random.randn(len(years)) * 3
values = base_values + noise

# Span regions to highlight
# Vertical span: 2008-2009 recession period
recession_start = 2007.5
recession_end = 2009.5

# Horizontal span: Growth target zone (105-115)
target_low = 105
target_high = 115

# Create figure
fig = go.Figure()

# Add horizontal span (target zone) first so it's behind everything
fig.add_hrect(
    y0=target_low,
    y1=target_high,
    fillcolor="#FFD43B",
    opacity=0.25,
    line_width=0,
    annotation_text="Target Zone",
    annotation_position="top left",
    annotation={"font": {"size": 20, "color": "#B8860B"}},
)

# Add vertical span (recession period)
fig.add_vrect(
    x0=recession_start,
    x1=recession_end,
    fillcolor="#306998",
    opacity=0.25,
    line_width=0,
    annotation_text="Recession",
    annotation_position="top left",
    annotation={"font": {"size": 20, "color": "#306998"}},
)

# Add the main data line
fig.add_trace(
    go.Scatter(
        x=years,
        y=values,
        mode="lines+markers",
        line={"color": "#306998", "width": 4},
        marker={"size": 14, "color": "#306998"},
        name="Economic Index",
    )
)

# Update layout for 4800x2700 px output
fig.update_layout(
    title={"text": "span-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Year", "font": {"size": 24}},
        "tickfont": {"size": 20},
        "dtick": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    yaxis={
        "title": {"text": "Economic Index", "font": {"size": 24}},
        "tickfont": {"size": 20},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    template="plotly_white",
    showlegend=True,
    legend={
        "font": {"size": 20},
        "x": 0.02,
        "y": 0.02,
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": "rgba(255,255,255,0.8)",
    },
    margin={"l": 100, "r": 100, "t": 120, "b": 100},
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
