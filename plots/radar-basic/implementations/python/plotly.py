""" pyplots.ai
radar-basic: Basic Radar Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import plotly.graph_objects as go


# Data - Employee performance across competencies
categories = ["Communication", "Technical Skills", "Teamwork", "Problem Solving", "Leadership", "Creativity"]
values = [85, 92, 78, 88, 72, 80]

# Close the polygon by repeating the first value
categories_closed = categories + [categories[0]]
values_closed = values + [values[0]]

# Create figure
fig = go.Figure()

fig.add_trace(
    go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.25)",
        line={"color": "#306998", "width": 3},
        marker={"size": 12, "color": "#306998"},
        name="Performance Score",
    )
)

# Layout
fig.update_layout(
    title={"text": "radar-basic · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    polar={
        "radialaxis": {
            "visible": True,
            "range": [0, 100],
            "tickvals": [20, 40, 60, 80, 100],
            "tickfont": {"size": 16},
            "gridcolor": "rgba(0, 0, 0, 0.2)",
            "linecolor": "rgba(0, 0, 0, 0.3)",
        },
        "angularaxis": {"tickfont": {"size": 20}, "gridcolor": "rgba(0, 0, 0, 0.2)", "linecolor": "rgba(0, 0, 0, 0.3)"},
        "bgcolor": "white",
    },
    template="plotly_white",
    showlegend=True,
    legend={"font": {"size": 18}, "x": 0.95, "y": 0.95, "xanchor": "right"},
    margin={"l": 100, "r": 100, "t": 100, "b": 100},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
