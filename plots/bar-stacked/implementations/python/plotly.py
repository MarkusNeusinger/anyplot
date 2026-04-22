""" pyplots.ai
bar-stacked: Stacked Bar Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 97/100 | Created: 2025-12-26
"""

import plotly.graph_objects as go


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
        marker_color="#306998",
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
        marker_color="#FFD43B",
        text=hardware,
        textposition="inside",
        textfont={"size": 18, "color": "#333"},
    )
)

fig.add_trace(
    go.Bar(
        name="Services",
        x=quarters,
        y=services,
        marker_color="#4ECDC4",
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
        marker_color="#FF6B6B",
        text=support,
        textposition="inside",
        textfont={"size": 18, "color": "white"},
    )
)

# Add total annotations above each bar
for quarter, total in zip(quarters, totals, strict=True):
    fig.add_annotation(
        x=quarter,
        y=total + 10,
        text=f"${total}K",
        showarrow=False,
        font={"size": 20, "color": "#333", "weight": "bold"},
    )

# Update layout
fig.update_layout(
    title={"text": "bar-stacked · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={"title": {"text": "Quarter", "font": {"size": 24}}, "tickfont": {"size": 20}},
    yaxis={
        "title": {"text": "Revenue (Thousands USD)", "font": {"size": 24}},
        "tickfont": {"size": 20},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    barmode="stack",
    bargap=0.3,
    template="plotly_white",
    legend={
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 20},
        "traceorder": "normal",
    },
    margin={"l": 100, "r": 60, "t": 120, "b": 80},
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
