"""anyplot.ai
ridgeline-basic: Basic Ridgeline Plot
Library: plotnine 0.15.3 | Python 3.13.13
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_ribbon,
    geom_text,
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
ACCENT = "#009E73"  # Okabe-Ito green for focal annotation

# Data - Monthly temperature distributions for a temperate climate
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

# Peak label data: placed at July's baseline level (y=jul_idx) to the right
# of where the Jul ridge tapers off — clearly within July's y-band on the axis
jul_idx = months.index("Jul")
peak_df = pd.DataFrame([{"x": 34.5, "y": float(jul_idx) + 0.5, "label": "Peak: Jul ≈ 25°C"}])

# Plot
plot = (
    ggplot(ridge_df, aes(x="x", ymin="ymin", ymax="ymax", fill="month_idx", group="group"))
    + geom_ribbon(alpha=0.85, color=INK_SOFT, size=0.5)
    + scale_fill_cmap(cmap_name="cividis")
    # geom_text from a separate dataframe anchored to July's y-band (showcases multi-layer grammar)
    + geom_text(
        data=peak_df,
        mapping=aes(x="x", y="y", label="label"),
        inherit_aes=False,
        color=ACCENT,
        size=10,
        fontweight="bold",
        ha="right",
        va="center",
    )
    # Diagonal leader segment from label anchor to July's density peak at (25, jul_idx+ridge_scale)
    + annotate(
        "segment", x=25.5, xend=33.5, y=jul_idx + ridge_scale - 0.3, yend=float(jul_idx) + 0.5, color=ACCENT, size=0.9
    )
    + scale_y_continuous(breaks=list(range(12)), labels=months, limits=(-0.5, 14))
    + labs(
        x="Temperature (°C)",
        y="Month",
        title="ridgeline-basic · plotnine · anyplot.ai",
        subtitle="Monthly temperature distributions — Northern Hemisphere temperate climate",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_blank(),
        text=element_text(size=14, color=INK_SOFT),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        plot_subtitle=element_text(size=16, color=INK_SOFT),
        plot_margin=0.03,
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.10),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
