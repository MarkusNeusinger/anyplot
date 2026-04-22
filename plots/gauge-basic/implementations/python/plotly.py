""" pyplots.ai
gauge-basic: Basic Gauge Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import plotly.graph_objects as go


# Data - Sales performance against quarterly target
value = 72  # Current sales achievement percentage
min_value = 0
max_value = 100
thresholds = [30, 70]  # Red/Yellow/Green zones

# Create gauge chart
fig = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=value,
        title={
            "text": "Sales Target Achievement<br><span style='font-size:24px'>gauge-basic · plotly · pyplots.ai</span>",
            "font": {"size": 32},
        },
        number={"font": {"size": 72}, "suffix": "%"},
        gauge={
            "axis": {
                "range": [min_value, max_value],
                "tickwidth": 3,
                "tickcolor": "#306998",
                "tickfont": {"size": 22},
                "ticksuffix": "%",
                "dtick": 10,
            },
            "bar": {"color": "#306998", "thickness": 0.25},
            "bgcolor": "white",
            "borderwidth": 3,
            "bordercolor": "#306998",
            "steps": [
                {"range": [min_value, thresholds[0]], "color": "#FF6B6B"},
                {"range": [thresholds[0], thresholds[1]], "color": "#FFD43B"},
                {"range": [thresholds[1], max_value], "color": "#4CAF50"},
            ],
            "threshold": {"line": {"color": "#306998", "width": 8}, "thickness": 0.85, "value": value},
        },
        domain={"x": [0.05, 0.95], "y": [0.1, 0.95]},
    )
)

# Layout for 4800x2700 px
fig.update_layout(
    font={"family": "Arial", "size": 22},
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin={"l": 80, "r": 80, "t": 120, "b": 60},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
