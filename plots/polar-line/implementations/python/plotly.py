""" pyplots.ai
polar-line: Polar Line Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Average hourly temperature pattern (two seasons)
np.random.seed(42)
hours = np.arange(0, 360, 15)  # 24 hours mapped to 360 degrees (15 deg = 1 hour)
hour_labels = [f"{h}:00" for h in range(24)]

# Summer pattern: warmer during day (12-18h), cooler at night
summer_base = 22 + 8 * np.sin(np.radians(hours - 90))  # Peak at 180 deg (noon)
summer_temp = summer_base + np.random.normal(0, 0.5, len(hours))

# Winter pattern: colder overall, less variation
winter_base = 5 + 5 * np.sin(np.radians(hours - 90))  # Peak at 180 deg (noon)
winter_temp = winter_base + np.random.normal(0, 0.3, len(hours))

# Close the loop by appending the first value
hours_closed = np.append(hours, hours[0])
summer_closed = np.append(summer_temp, summer_temp[0])
winter_closed = np.append(winter_temp, winter_temp[0])

# Create figure
fig = go.Figure()

# Summer line
fig.add_trace(
    go.Scatterpolar(
        r=summer_closed,
        theta=hours_closed,
        mode="lines+markers",
        name="Summer",
        line=dict(color="#FFD43B", width=4),
        marker=dict(size=10, color="#FFD43B"),
        hovertemplate="Hour: %{theta}°<br>Temp: %{r:.1f}°C<extra>Summer</extra>",
    )
)

# Winter line
fig.add_trace(
    go.Scatterpolar(
        r=winter_closed,
        theta=hours_closed,
        mode="lines+markers",
        name="Winter",
        line=dict(color="#306998", width=4),
        marker=dict(size=10, color="#306998"),
        hovertemplate="Hour: %{theta}°<br>Temp: %{r:.1f}°C<extra>Winter</extra>",
    )
)

# Layout
fig.update_layout(
    title=dict(
        text="Hourly Temperature Pattern · polar-line · plotly · pyplots.ai",
        font=dict(size=28),
        x=0.5,
        xanchor="center",
    ),
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 35],
            tickfont=dict(size=18),
            title=dict(text="Temperature (°C)", font=dict(size=20)),
            gridcolor="rgba(0,0,0,0.2)",
            ticksuffix="°C",
        ),
        angularaxis=dict(
            tickfont=dict(size=16),
            direction="clockwise",
            rotation=90,  # Start from top (midnight)
            tickmode="array",
            tickvals=list(range(0, 360, 15)),
            ticktext=hour_labels,
            gridcolor="rgba(0,0,0,0.2)",
        ),
        bgcolor="rgba(255,255,255,0.9)",
    ),
    legend=dict(
        font=dict(size=20), x=1.05, y=0.5, bgcolor="rgba(255,255,255,0.8)", bordercolor="rgba(0,0,0,0.3)", borderwidth=1
    ),
    template="plotly_white",
    margin=dict(l=80, r=150, t=100, b=80),
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
