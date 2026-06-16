""" anyplot.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_smooth,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

np.random.seed(42)
n_points = 100
temperature = np.random.uniform(0, 40, n_points)
optimal_temp = 20
energy = 50 + 0.15 * (temperature - optimal_temp) ** 2 + np.random.normal(0, 3, n_points)

df = pd.DataFrame({"temperature": temperature, "energy": energy})

coeffs = np.polyfit(temperature, energy, 2)
poly_func = np.poly1d(coeffs)
y_pred = poly_func(temperature)
ss_res = np.sum((energy - y_pred) ** 2)
ss_tot = np.sum((energy - np.mean(energy)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

a, b, c = coeffs
b_sign = "+" if b >= 0 else "-"
b_abs = abs(b)
equation_text = f"y = {a:.3f}x² {b_sign} {b_abs:.3f}x + {c:.2f}"
r_squared_text = f"R² = {r_squared:.3f}"
annotation_text = f"{equation_text}\n{r_squared_text}"

plot = (
    ggplot(df, aes(x="temperature", y="energy"))
    + geom_point(size=4, alpha=0.65, color=BRAND)
    + geom_smooth(
        method="lm", formula="y ~ I(x) + I(x**2)", se=True, color="#C475FD", fill="#AE3030", alpha=0.25, size=2
    )
    + annotate("text", x=38, y=115, label=annotation_text, ha="right", va="top", size=17, color=INK)
    + labs(
        title="scatter-regression-polynomial · plotnine · anyplot.ai",
        x="Temperature (°C)",
        y="Energy Consumption (kWh)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        text=element_text(size=14, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
    )
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
