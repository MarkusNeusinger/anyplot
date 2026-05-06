""" anyplot.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Created: 2026-05-06
"""

import os
import sys


# Priority: Add venv site-packages to front of sys.path before importing altair
venv_site_packages = "/home/runner/work/anyplot/anyplot/.venv/lib/python3.13/site-packages"
if venv_site_packages in sys.path:
    sys.path.remove(venv_site_packages)
sys.path.insert(0, venv_site_packages)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from altair import Chart, Color, Scale, X, Y  # noqa: E402


def main():
    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
    INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
    INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

    # Data
    np.random.seed(42)
    grid_size = 30
    x_vals = np.linspace(-5, 5, grid_size)
    y_vals = np.linspace(-5, 5, grid_size)
    X_grid, Y_grid = np.meshgrid(x_vals, y_vals)
    Z = np.sin(np.sqrt(X_grid**2 + Y_grid**2))

    # Convert 3D to 2D using isometric projection
    def isometric_projection(x, y, z, elevation=30, azimuth=45):
        """Project 3D coordinates to 2D using isometric projection."""
        el_rad = np.radians(elevation)
        az_rad = np.radians(azimuth)

        cos_el = np.cos(el_rad)
        sin_el = np.sin(el_rad)
        cos_az = np.cos(az_rad)
        sin_az = np.sin(az_rad)

        x_2d = x * cos_az - y * sin_az
        y_2d = (x * sin_az + y * cos_az) * sin_el + z * cos_el

        return x_2d, y_2d

    x_proj, y_proj = isometric_projection(X_grid, Y_grid, Z)

    # Create wireframe edges data
    lines_data = []
    for i in range(grid_size):
        for j in range(grid_size - 1):
            lines_data.append(
                {
                    "x_proj": x_proj[i, j],
                    "y_proj": y_proj[i, j],
                    "x_proj_next": x_proj[i, j + 1],
                    "y_proj_next": y_proj[i, j + 1],
                    "z": (Z[i, j] + Z[i, j + 1]) / 2,
                }
            )

    for i in range(grid_size - 1):
        for j in range(grid_size):
            lines_data.append(
                {
                    "x_proj": x_proj[i, j],
                    "y_proj": y_proj[i, j],
                    "x_proj_next": x_proj[i + 1, j],
                    "y_proj_next": y_proj[i + 1, j],
                    "z": (Z[i, j] + Z[i + 1, j]) / 2,
                }
            )

    df = pd.DataFrame(lines_data)

    # Plot
    chart = (
        Chart(df)
        .mark_line(size=2, opacity=0.8)
        .encode(
            x=X("x_proj:Q", axis=None),
            y=Y("y_proj:Q", axis=None),
            x2="x_proj_next:Q",
            y2="y_proj_next:Q",
            color=Color("z:Q", scale=Scale(scheme="viridis"), title="Height (Z)"),
        )
        .properties(width=1600, height=900, title="wireframe-3d-basic · altair · anyplot.ai")
        .configure_title(fontSize=28, color=INK, anchor="middle")
        .configure_legend(
            fillColor=ELEVATED_BG,
            strokeColor=INK_SOFT,
            labelColor=INK_SOFT,
            titleColor=INK,
            labelFontSize=16,
            titleFontSize=18,
        )
        .properties(background=PAGE_BG)
        .configure_view(fill=PAGE_BG, stroke=None)
    )

    chart.save(f"plot-{THEME}.png")
    chart.save(f"plot-{THEME}.html")


if __name__ == "__main__":
    main()
