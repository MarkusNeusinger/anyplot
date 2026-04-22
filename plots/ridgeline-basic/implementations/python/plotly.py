""" pyplots.ai
ridgeline-basic: Basic Ridgeline Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - Monthly temperature distributions for a city
np.random.seed(42)

months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# Generate realistic temperature distributions (Celsius) for each month
# Northern hemisphere pattern: cold winters, warm summers
base_temps = [-2, 0, 5, 12, 18, 23, 26, 25, 20, 13, 6, 1]
data = {}
for i, month in enumerate(months):
    # More variation in transition months
    std = 4 if i in [2, 3, 8, 9] else 3
    data[month] = np.random.normal(base_temps[i], std, 200)

# X range for density evaluation
x_range = np.linspace(-15, 40, 300)

# Color gradient from blue (cold) to warm colors and back
colors = [
    "#306998",  # January - Python Blue
    "#3d78a8",
    "#4a88b8",
    "#6fa8c8",
    "#94c8d8",
    "#FFD43B",  # June - Python Yellow
    "#ff9f43",
    "#ff7f50",
    "#ff6b6b",
    "#94c8d8",
    "#4a88b8",
    "#306998",  # December - Python Blue
]

# Create figure
fig = go.Figure()

# Scaling factor for ridge height and overlap
ridge_scale = 0.12
overlap = 0.5

# Add ridges from bottom to top (reversed so January is at top)
for i, month in enumerate(reversed(months)):
    idx = len(months) - 1 - i
    temps = data[month]

    # Compute KDE using Silverman's rule for bandwidth
    n = len(temps)
    std_dev = np.std(temps, ddof=1)
    iqr = np.percentile(temps, 75) - np.percentile(temps, 25)
    bandwidth = 0.9 * min(std_dev, iqr / 1.34) * n ** (-0.2)

    density = np.zeros_like(x_range)
    for xi in temps:
        density += np.exp(-0.5 * ((x_range - xi) / bandwidth) ** 2)
    density /= n * bandwidth * np.sqrt(2 * np.pi)

    # Normalize density for consistent visual height
    density = density / density.max() * ridge_scale

    # Y offset for stacking
    y_offset = i * (1 - overlap) * ridge_scale

    # Create fill area using baseline
    y_fill = density + y_offset

    # Add filled area trace
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([[x_range[0]], x_range, [x_range[-1]]]),
            y=np.concatenate([[y_offset], y_fill, [y_offset]]),
            fill="toself",
            fillcolor=colors[idx],
            line={"color": "rgba(0,0,0,0.4)", "width": 1.5},
            mode="lines",
            name=month,
            showlegend=False,
            hovertemplate=f"{month}<br>Temperature: %{{x:.1f}}°C<extra></extra>",
        )
    )

# Calculate y-tick positions for month labels
y_ticks = [(len(months) - 1 - i) * (1 - overlap) * ridge_scale + ridge_scale * 0.4 for i in range(len(months))]

# Layout
fig.update_layout(
    title={"text": "ridgeline-basic · plotly · pyplots.ai", "font": {"size": 48}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Temperature (°C)", "font": {"size": 36}},
        "tickfont": {"size": 28},
        "range": [-15, 40],
        "gridcolor": "rgba(0,0,0,0.1)",
        "showgrid": True,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "", "font": {"size": 36}},
        "tickfont": {"size": 28},
        "tickvals": y_ticks,
        "ticktext": list(reversed(months)),
        "showgrid": False,
        "zeroline": False,
        "range": [-0.02, max(y_ticks) + ridge_scale * 0.7],
    },
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 180, "r": 50, "t": 120, "b": 100},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
