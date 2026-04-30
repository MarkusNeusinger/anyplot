"""anyplot.ai
ridgeline-basic: Basic Ridgeline Plot
Library: plotnine | Python 3.13
Quality: 92/100 | Updated: 2026-04-30
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_ribbon,
    ggplot,
    labs,
    scale_fill_cmap,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Monthly temperature distributions
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

temp_params = {
    "Jan": (2, 4),
    "Feb": (4, 4),
    "Mar": (8, 5),
    "Apr": (13, 4),
    "May": (18, 4),
    "Jun": (22, 3),
    "Jul": (25, 3),
    "Aug": (24, 3),
    "Sep": (20, 4),
    "Oct": (14, 4),
    "Nov": (8, 4),
    "Dec": (4, 4),
}

# Generate raw samples for KDE
data = []
for month in months:
    mean, std = temp_params[month]
    values = np.random.normal(mean, std, 200)
    for v in values:
        data.append({"month": month, "temp": v})

df = pd.DataFrame(data)

# Compute KDE density curves for ridgeline layout
x_range = np.linspace(-10, 40, 300)
ridge_scale = 2.5

density_data = []
for i, month in enumerate(months):
    month_data = df[df["month"] == month]["temp"]
    kde = stats.gaussian_kde(month_data)
    density = kde(x_range)
    density_scaled = density / density.max() * ridge_scale

    for x, d in zip(x_range, density_scaled, strict=True):
        density_data.append(
            {"x": x, "ymin": float(i), "ymax": float(i) + d, "group": month, "month_idx": float(i) / 11.0}
        )

ridge_df = pd.DataFrame(density_data)
ridge_df["group"] = pd.Categorical(ridge_df["group"], categories=months, ordered=True)

# Plot
plot = (
    ggplot(ridge_df, aes(x="x", ymin="ymin", ymax="ymax", fill="month_idx", group="group"))
    + geom_ribbon(alpha=0.85, color=INK_SOFT, size=0.5)
    + scale_fill_cmap(cmap_name="cividis")
    + scale_y_continuous(breaks=list(range(12)), labels=months, limits=(-0.5, 14))
    + labs(x="Temperature (°C)", y="Month", title="ridgeline-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        text=element_text(size=14, color=INK_SOFT),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.10),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
