""" anyplot.ai
windrose-basic: Wind Rose Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-07
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

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
speed_colors = ["#4A90E2", "#4467A3", "#FFD43B", "#FF9F40", "#FF5252"]

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
        text="windrose-basic · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center", y=0.95
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    polar=dict(
        radialaxis=dict(
            visible=True,
            showticklabels=True,
            tickfont=dict(size=18, color=INK_SOFT),
            ticksuffix="%",
            angle=45,
            dtick=5,
            title=dict(text="Frequency (%)", font=dict(size=20, color=INK)),
            gridcolor=GRID,
        ),
        angularaxis=dict(
            tickfont=dict(size=22, color=INK),
            direction="clockwise",
            rotation=90,
            categoryorder="array",
            categoryarray=["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
        ),
        bgcolor=PAGE_BG,
    ),
    legend=dict(
        title=dict(text="Wind Speed", font=dict(size=20, color=INK)),
        font=dict(size=18, color=INK_SOFT),
        x=1.05,
        y=0.5,
        xanchor="left",
        yanchor="middle",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    barmode="stack",
    margin=dict(l=80, r=180, t=120, b=80),
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
