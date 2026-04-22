""" pyplots.ai
windrose-basic: Wind Rose Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import numpy as np
import plotly.graph_objects as go


# Data - Simulated hourly wind measurements for one year
np.random.seed(42)
n_observations = 8760  # One year of hourly data

# Simulate wind direction with prevailing westerly and southwesterly winds
direction_weights = np.array([0.05, 0.05, 0.08, 0.10, 0.12, 0.20, 0.25, 0.15])  # N, NE, E, SE, S, SW, W, NW
directions_base = np.array([0, 45, 90, 135, 180, 225, 270, 315])
direction_idx = np.random.choice(8, size=n_observations, p=direction_weights)
directions = directions_base[direction_idx] + np.random.uniform(-20, 20, n_observations)
directions = directions % 360

# Simulate wind speeds with realistic distribution (Weibull-like)
speeds = np.random.weibull(2.0, n_observations) * 6  # Scale for realistic m/s values

# Define direction bins (8 sectors, 45 degrees each)
dir_bins = np.array([0, 45, 90, 135, 180, 225, 270, 315, 360])
dir_labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Define speed bins (m/s)
speed_bins = [0, 3, 6, 9, 12, np.inf]
speed_labels = ["0-3 m/s", "3-6 m/s", "6-9 m/s", "9-12 m/s", ">12 m/s"]
speed_colors = ["#306998", "#4A90D9", "#FFD43B", "#FF9F40", "#FF5252"]

# Bin the data
dir_indices = np.digitize(directions, dir_bins[:-1]) - 1
dir_indices = np.clip(dir_indices, 0, 7)
speed_indices = np.digitize(speeds, speed_bins[:-1]) - 1

# Calculate frequencies for each direction and speed combination
frequencies = np.zeros((8, 5))
for d in range(8):
    for s in range(5):
        frequencies[d, s] = np.sum((dir_indices == d) & (speed_indices == s))

# Convert to percentages
frequencies_pct = frequencies / n_observations * 100

# Create wind rose using barpolar
fig = go.Figure()

# Add traces for each speed bin (stacked from inside to outside)
for s in range(5):
    # Calculate the radial values for stacking
    r_values = frequencies_pct[:, s]

    fig.add_trace(
        go.Barpolar(
            r=r_values,
            theta=dir_labels,
            name=speed_labels[s],
            marker_color=speed_colors[s],
            marker_line_color="white",
            marker_line_width=1,
            opacity=0.9,
        )
    )

# Update layout for proper stacking and styling
fig.update_layout(
    title=dict(
        text="windrose-basic · plotly · pyplots.ai",
        font=dict(size=32, color="#333333"),
        x=0.5,
        xanchor="center",
        y=0.95,
    ),
    polar=dict(
        radialaxis=dict(visible=True, showticklabels=True, tickfont=dict(size=18), ticksuffix="%", angle=45, dtick=5),
        angularaxis=dict(
            tickfont=dict(size=22, color="#333333"),
            direction="clockwise",
            rotation=90,  # North at top
            categoryorder="array",
            categoryarray=["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
        ),
        bgcolor="rgba(255,255,255,0.9)",
    ),
    legend=dict(
        title=dict(text="Wind Speed", font=dict(size=20)),
        font=dict(size=18),
        x=1.05,
        y=0.5,
        xanchor="left",
        yanchor="middle",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="#cccccc",
        borderwidth=1,
    ),
    barmode="stack",
    template="plotly_white",
    margin=dict(l=80, r=180, t=120, b=80),
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
