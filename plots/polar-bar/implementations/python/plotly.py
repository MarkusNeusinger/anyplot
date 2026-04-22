""" pyplots.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data: Wind speed distribution by direction (8 compass points)
# Each direction has 3 speed ranges (stacked bars)
np.random.seed(42)

directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Wind speed frequencies by direction (simulating typical coastal wind patterns)
# Light breeze (0-10 km/h)
light = np.array([8, 5, 4, 3, 6, 12, 15, 10])
# Moderate breeze (10-20 km/h)
moderate = np.array([6, 4, 3, 2, 4, 10, 12, 8])
# Strong breeze (20+ km/h)
strong = np.array([3, 2, 1, 1, 2, 5, 6, 4])

# Create figure with polar subplot
fig = go.Figure()

# Add stacked bars for each wind speed category (base is cumulative)
fig.add_trace(
    go.Barpolar(
        r=light,
        theta=directions,
        name="Light (0-10 km/h)",
        marker=dict(color="#306998", line=dict(color="white", width=2)),
        opacity=0.9,
    )
)

fig.add_trace(
    go.Barpolar(
        r=moderate,
        theta=directions,
        name="Moderate (10-20 km/h)",
        marker=dict(color="#FFD43B", line=dict(color="white", width=2)),
        opacity=0.9,
    )
)

fig.add_trace(
    go.Barpolar(
        r=strong,
        theta=directions,
        name="Strong (20+ km/h)",
        marker=dict(color="#4ECDC4", line=dict(color="white", width=2)),
        opacity=0.9,
    )
)

# Update layout for polar chart
fig.update_layout(
    title=dict(text="polar-bar · plotly · pyplots.ai", font=dict(size=32, color="#333"), x=0.5, y=0.95),
    polar=dict(
        barmode="stack",
        radialaxis=dict(
            visible=True,
            range=[0, max(light + moderate + strong) + 3],
            tickfont=dict(size=18),
            tickangle=45,
            gridcolor="rgba(0,0,0,0.2)",
            linecolor="rgba(0,0,0,0.3)",
            title=dict(text="Frequency (%)", font=dict(size=18)),
        ),
        angularaxis=dict(
            tickfont=dict(size=22, color="#333"),
            direction="clockwise",
            rotation=90,  # N at top
            gridcolor="rgba(0,0,0,0.15)",
            linecolor="rgba(0,0,0,0.3)",
        ),
        bgcolor="rgba(255,255,255,0.95)",
    ),
    legend=dict(
        font=dict(size=20),
        x=0.85,
        y=0.95,
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="rgba(0,0,0,0.2)",
        borderwidth=1,
    ),
    template="plotly_white",
    margin=dict(l=80, r=180, t=120, b=80),
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
