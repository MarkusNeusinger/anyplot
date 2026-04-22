""" pyplots.ai
pie-basic: Basic Pie Chart
Library: plotly 6.5.2 | Python 3.14.0
Quality: 91/100 | Created: 2025-12-23
"""

import plotly.graph_objects as go


# Data - Market share of cloud providers (2024)
categories = ["AWS", "Azure", "Google Cloud", "Alibaba", "IBM", "Others"]
values = [31, 24, 11, 4, 3, 27]

# Colors - Python Blue first, cohesive palette avoiding adjacent red-green
colors = ["#306998", "#FFD43B", "#4ECDC4", "#C5A3FF", "#E07B54", "#8FBDD3"]

# Create donut chart (pie with hole) for modern aesthetic
fig = go.Figure(
    data=[
        go.Pie(
            labels=categories,
            values=values,
            textinfo="percent+label",
            textposition="outside",
            textfont={"size": 20, "color": "#2D3436"},
            hovertemplate="%{label}<br>%{value}% market share<br>(%{percent})<extra></extra>",
            marker={"colors": colors, "line": {"color": "white", "width": 3}},
            pull=[0.06, 0, 0, 0, 0, 0],
            sort=False,
            hole=0.35,
            direction="clockwise",
            rotation=90,
            domain={"x": [0.05, 0.75], "y": [0.0, 0.95]},
        )
    ]
)

# Center annotation inside the donut hole
fig.add_annotation(
    text="<b>Cloud<br>Market<br>2024</b>",
    x=0.40,
    y=0.475,
    xref="paper",
    yref="paper",
    showarrow=False,
    font={"size": 22, "color": "#306998", "family": "Arial Black, sans-serif"},
    xanchor="center",
    yanchor="middle",
)

# Callout annotation for AWS leadership - positioned in bottom-right near AWS slice
fig.add_annotation(
    text="<b>AWS</b> leads with <b>31%</b> market share",
    x=0.82,
    y=0.18,
    xref="paper",
    yref="paper",
    showarrow=True,
    ax=20,
    ay=50,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=2,
    arrowcolor="#306998",
    font={"size": 16, "color": "#2D3436", "family": "Arial, sans-serif"},
    bordercolor="#306998",
    borderwidth=2,
    borderpad=8,
    bgcolor="rgba(48, 105, 152, 0.08)",
)

# Layout
fig.update_layout(
    title={
        "text": "pie-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2D3436", "family": "Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    legend={
        "font": {"size": 18, "color": "#2D3436"},
        "orientation": "v",
        "yanchor": "middle",
        "y": 0.5,
        "xanchor": "left",
        "x": 0.82,
        "bgcolor": "rgba(255,255,255,0.8)",
        "bordercolor": "#E0E0E0",
        "borderwidth": 1,
    },
    template="plotly_white",
    margin={"t": 80, "b": 50, "l": 40, "r": 60},
    paper_bgcolor="#FAFAFA",
    plot_bgcolor="#FAFAFA",
    uniformtext={"minsize": 16, "mode": "hide"},
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html")
