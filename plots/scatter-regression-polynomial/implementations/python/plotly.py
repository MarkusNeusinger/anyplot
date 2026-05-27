""" anyplot.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: plotly 6.7.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-07
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

# Okabe-Ito palette - first series is always #009E73
BRAND = "#009E73"
ACCENT = "#C475FD"

# Data - Temperature vs Energy Consumption (environmental/building efficiency)
np.random.seed(42)
# Simulate heating/cooling season data where energy consumption follows a U-shaped curve
# (more energy needed for both heating in winter and cooling in summer)
outdoor_temp = np.linspace(-10, 40, 100)
base_consumption = 30
energy_consumption = 0.12 * (outdoor_temp - 15) ** 2 + base_consumption + np.random.normal(0, 5, len(outdoor_temp))

# Polynomial regression (degree 2 - quadratic, capturing the U-shaped curve)
coeffs = np.polyfit(outdoor_temp, energy_consumption, 2)
poly = np.poly1d(coeffs)
x_fit = np.linspace(outdoor_temp.min(), outdoor_temp.max(), 200)
y_fit = poly(x_fit)

# Calculate R²
y_pred = poly(outdoor_temp)
ss_res = np.sum((energy_consumption - y_pred) ** 2)
ss_tot = np.sum((energy_consumption - np.mean(energy_consumption)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Format polynomial equation
a, b, c = coeffs
equation = f"y = {a:.4f}x² + {b:.2f}x + {c:.1f}"

# Create figure
fig = go.Figure()

# Scatter points with brand color
fig.add_trace(
    go.Scatter(
        x=outdoor_temp,
        y=energy_consumption,
        mode="markers",
        name="Measured Data",
        marker={"size": 18, "color": BRAND, "opacity": 0.65, "line": {"width": 1.5, "color": PAGE_BG}},
    )
)

# Polynomial regression curve
fig.add_trace(
    go.Scatter(x=x_fit, y=y_fit, mode="lines", name="Polynomial Fit (degree 2)", line={"color": ACCENT, "width": 4})
)

# Layout with theme-adaptive chrome
fig.update_layout(
    title={
        "text": "Building Energy Consumption · scatter-regression-polynomial · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Outdoor Temperature (°C)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Energy Consumption (kWh)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    legend={
        "font": {"size": 18, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 100, "r": 80, "t": 120, "b": 100},
    annotations=[
        {
            "x": 0.98,
            "y": 0.05,
            "xref": "paper",
            "yref": "paper",
            "text": f"R² = {r_squared:.4f}<br>{equation}",
            "showarrow": False,
            "font": {"size": 18, "color": INK},
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
            "borderpad": 10,
            "xanchor": "right",
            "yanchor": "bottom",
        }
    ],
)

# Save as PNG and HTML with theme-suffixed filenames
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
