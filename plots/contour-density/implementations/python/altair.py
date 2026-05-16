"""anyplot.ai
contour-density: Density Contour Plot
Library: altair | Python 3.13
Quality: pending | Created: 2026-05-16
"""

import os
import sys
from pathlib import Path


script_dir = str(Path(__file__).parent)
while script_dir in sys.path:
    sys.path.remove(script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import gaussian_kde  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - climate measurements showing natural clusters
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
n_grid = 80
x_grid = np.linspace(temperature.min() - 5, temperature.max() + 5, n_grid)
y_grid = np.linspace(humidity.min() - 5, humidity.max() + 5, n_grid)
xx, yy = np.meshgrid(x_grid, y_grid)
positions = np.vstack([xx.ravel(), yy.ravel()])
z = kde(positions).reshape(xx.shape)

# Prepare grid data for heatmap
grid_data = pd.DataFrame({"x": xx.ravel(), "y": yy.ravel(), "density": z.ravel()})

# Create filled contour visualization using heatmap
x_domain = [float(temperature.min() - 6), float(temperature.max() + 6)]
y_domain = [float(humidity.min() - 6), float(humidity.max() + 6)]

chart = (
    alt.Chart(grid_data)
    .mark_rect()
    .encode(
        x=alt.X(
            "x:Q",
            bin=alt.Bin(step=(x_grid[1] - x_grid[0])),
            scale=alt.Scale(domain=x_domain),
            title="Temperature (°C)",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, grid=False, labelColor=INK_SOFT, titleColor=INK),
        ),
        y=alt.Y(
            "y:Q",
            bin=alt.Bin(step=(y_grid[1] - y_grid[0])),
            scale=alt.Scale(domain=y_domain),
            title="Humidity (%)",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, grid=False, labelColor=INK_SOFT, titleColor=INK),
        ),
        color=alt.Color(
            "mean(density):Q",
            scale=alt.Scale(scheme="viridis"),
            title="Density",
            legend=alt.Legend(
                titleFontSize=20,
                labelFontSize=16,
                gradientLength=400,
                gradientThickness=25,
                titleColor=INK,
                labelColor=INK_SOFT,
                fillColor=PAGE_BG,
                strokeColor=INK_SOFT,
            ),
        ),
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title(text="contour-density · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=None, strokeWidth=0)
    .configure_axis(domainColor=INK_SOFT, gridOpacity=0.0)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
