""" pyplots.ai
polar-scatter: Polar Scatter Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go


# Data - synthetic wind measurements with prevailing directions
np.random.seed(42)
n_points = 120

# Create wind data with prevailing directions (NW and SE winds common)
# Cluster 1: Northwest winds (~315°)
n1 = 45
angles1 = np.random.normal(315, 25, n1)
speeds1 = np.random.gamma(3, 3, n1) + 5

# Cluster 2: Southeast winds (~135°)
n2 = 40
angles2 = np.random.normal(135, 30, n2)
speeds2 = np.random.gamma(2.5, 2.5, n2) + 3

# Cluster 3: Scattered winds from other directions
n3 = n_points - n1 - n2
angles3 = np.random.uniform(0, 360, n3)
speeds3 = np.random.gamma(2, 2, n3) + 2

# Combine all data
angles = np.concatenate([angles1, angles2, angles3])
angles = angles % 360  # Normalize to 0-360
speeds = np.concatenate([speeds1, speeds2, speeds3])

# Create time of day categories for color encoding
hours = np.random.choice([6, 9, 12, 15, 18], n_points)
time_labels = np.array(["Morning" if h <= 9 else "Afternoon" if h <= 15 else "Evening" for h in hours])

# Create figure
fig = go.Figure()

# Color mapping for time of day
colors = {"Morning": "#306998", "Afternoon": "#FFD43B", "Evening": "#E07B39"}

# Add traces for each time period
for period in ["Morning", "Afternoon", "Evening"]:
    mask = time_labels == period
    fig.add_trace(
        go.Scatterpolar(
            r=speeds[mask],
            theta=angles[mask],
            mode="markers",
            name=period,
            marker={"size": 14, "color": colors[period], "opacity": 0.75, "line": {"width": 1, "color": "white"}},
        )
    )

# Update layout for 4800x2700 px canvas
fig.update_layout(
    title={
        "text": "Wind Observations · polar-scatter · plotly · pyplots.ai",
        "font": {"size": 32},
        "x": 0.5,
        "xanchor": "center",
    },
    font={"size": 18},
    polar={
        "bgcolor": "white",
        "angularaxis": {
            "tickmode": "array",
            "tickvals": [0, 45, 90, 135, 180, 225, 270, 315],
            "ticktext": ["N (0°)", "NE", "E (90°)", "SE", "S (180°)", "SW", "W (270°)", "NW"],
            "tickfont": {"size": 18},
            "direction": "clockwise",
            "rotation": 90,  # North at top
            "gridcolor": "rgba(0,0,0,0.15)",
            "linecolor": "rgba(0,0,0,0.3)",
        },
        "radialaxis": {
            "title": {"text": "Wind Speed (m/s)", "font": {"size": 20}},
            "tickfont": {"size": 16},
            "gridcolor": "rgba(0,0,0,0.15)",
            "linecolor": "rgba(0,0,0,0.3)",
            "range": [0, max(speeds) * 1.1],
        },
    },
    legend={
        "title": {"text": "Time of Day", "font": {"size": 20}},
        "font": {"size": 18},
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "rgba(0,0,0,0.2)",
        "borderwidth": 1,
        "x": 1.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
    },
    template="plotly_white",
    margin={"l": 80, "r": 180, "t": 100, "b": 80},
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
