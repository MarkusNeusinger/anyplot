"""pyplots.ai
contour-density: Density Contour Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 88/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


# Data - simulating temperature and humidity measurements showing natural clusters
np.random.seed(42)

# Create three distinct clusters representing different climate conditions
n1 = 150
temp1 = np.random.normal(15, 4, n1)
humidity1 = np.random.normal(30, 8, n1)

n2 = 200
temp2 = np.random.normal(25, 5, n2)
humidity2 = np.random.normal(55, 10, n2)

n3 = 150
temp3 = np.random.normal(38, 4, n3)
humidity3 = np.random.normal(75, 8, n3)

# Combine data
temperature = np.concatenate([temp1, temp2, temp3])
humidity = np.concatenate([humidity1, humidity2, humidity3])

# Compute 2D KDE for density estimation
xy = np.vstack([temperature, humidity])
kde = gaussian_kde(xy)

# Create grid for density estimation
n_grid = 60
x_grid = np.linspace(temperature.min() - 5, temperature.max() + 5, n_grid)
y_grid = np.linspace(humidity.min() - 5, humidity.max() + 5, n_grid)
xx, yy = np.meshgrid(x_grid, y_grid)
positions = np.vstack([xx.ravel(), yy.ravel()])
z = kde(positions).reshape(xx.shape)

# Create filled contour visualization using binned density levels
n_levels = 10
z_min, z_max = z.min(), z.max()
levels = np.linspace(z_min, z_max, n_levels + 1)
z_binned = np.digitize(z, levels) - 1
z_binned = np.clip(z_binned, 0, n_levels - 1)

# Create grid cell data for filled contours
step_x = x_grid[1] - x_grid[0]
step_y = y_grid[1] - y_grid[0]

grid_data = pd.DataFrame({"x": xx.ravel(), "y": yy.ravel(), "density_level": z_binned.ravel()})

# Create filled contour chart using mark_rect with binning
x_domain = [float(temperature.min() - 6), float(temperature.max() + 6)]
y_domain = [float(humidity.min() - 6), float(humidity.max() + 6)]

filled_contours = (
    alt.Chart(grid_data)
    .mark_rect()
    .encode(
        x=alt.X(
            "x:Q",
            bin=alt.Bin(step=step_x),
            scale=alt.Scale(domain=x_domain),
            title="Temperature (°C)",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.3),
        ),
        y=alt.Y(
            "y:Q",
            bin=alt.Bin(step=step_y),
            scale=alt.Scale(domain=y_domain),
            title="Humidity (%)",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.3),
        ),
        color=alt.Color(
            "mean(density_level):Q",
            scale=alt.Scale(scheme="blues"),
            title="Density",
            legend=alt.Legend(titleFontSize=20, labelFontSize=16, gradientLength=400, gradientThickness=25),
        ),
    )
)

# Add contour line effect by layering darker outlines at level boundaries
contour_data = []
for i in range(n_grid - 1):
    for j in range(n_grid - 1):
        current = z_binned[i, j]
        # Check if adjacent cells have different levels (boundary)
        if i < n_grid - 1 and z_binned[i + 1, j] != current:
            contour_data.append({"x": x_grid[j], "y": (y_grid[i] + y_grid[i + 1]) / 2, "level": current})
        if j < n_grid - 1 and z_binned[i, j + 1] != current:
            contour_data.append({"x": (x_grid[j] + x_grid[j + 1]) / 2, "y": y_grid[i], "level": current})

if contour_data:
    contour_df = pd.DataFrame(contour_data)
    contour_points = (
        alt.Chart(contour_df)
        .mark_circle(size=8, opacity=0.6, color="#1a4d80")
        .encode(x=alt.X("x:Q", scale=alt.Scale(domain=x_domain)), y=alt.Y("y:Q", scale=alt.Scale(domain=y_domain)))
    )
    chart = alt.layer(filled_contours, contour_points)
else:
    chart = filled_contours

# Configure the chart with proper sizing
chart = chart.properties(
    width=1600, height=900, title=alt.Title(text="contour-density · altair · pyplots.ai", fontSize=28, anchor="middle")
).configure_view(strokeWidth=0)

# Save as PNG (1600 * 3 = 4800, 900 * 3 = 2700)
chart.save("plot.png", scale_factor=3.0)

# Save as interactive HTML
chart.save("plot.html")
