""" anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: plotnine 0.15.3 | Python 3.14.4
Quality: 85/100 | Created: 2026-04-25
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_ribbon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

# Peaks - Wallis (Valais) panorama from a Gornergrat-like vantage
peaks = (
    pd.DataFrame(
        {
            "name": [
                "Weisshorn",
                "Zinalrothorn",
                "Ober Gabelhorn",
                "Dent Blanche",
                "Matterhorn",
                "Liskamm",
                "Castor",
                "Pollux",
                "Breithorn",
                "Monte Rosa",
                "Strahlhorn",
                "Rimpfischhorn",
                "Allalinhorn",
                "Alphubel",
                "Täschhorn",
                "Dom",
            ],
            "angle_deg": [4, 12, 19, 26, 38, 60, 67, 72, 78, 90, 105, 113, 122, 130, 137, 144],
            "elevation_m": [
                4506,
                4221,
                4063,
                4358,
                4478,
                4527,
                4223,
                4092,
                4164,
                4634,
                4190,
                4199,
                4027,
                4206,
                4491,
                4545,
            ],
        }
    )
    .sort_values("angle_deg")
    .reset_index(drop=True)
)

# Skyline ridgeline - dense angular sampling, max-of-Gaussians per peak above a base
np.random.seed(42)
n_samples = 1600
angles = np.linspace(-3, 152, n_samples)
base_elev = 2950 + 90 * np.sin(angles / 14) + 55 * np.sin(angles / 4.5 + 0.7)
elevation = base_elev.copy()
for _, p in peaks.iterrows():
    sigma = 2.6
    contribution = (p["elevation_m"] - 2950) * np.exp(-((angles - p["angle_deg"]) ** 2) / (2 * sigma**2))
    elevation = np.maximum(elevation, 2950 + contribution)
elevation = elevation + np.random.normal(0, 12, n_samples)
elevation = pd.Series(elevation).rolling(window=5, center=True, min_periods=1).mean().values

skyline = pd.DataFrame({"angle_deg": angles, "elevation_m": elevation, "y_floor": 2500})

# Stagger labels onto two rows so clustered names don't collide
peaks["row"] = peaks.index % 2
peaks["label_y"] = np.where(peaks["row"] == 0, 4990, 5200)
peaks["leader_top"] = peaks["label_y"] - 80
peaks["label"] = peaks.apply(lambda r: f"{r['name']}\n{int(r['elevation_m']):,} m", axis=1)
peaks["is_anchor"] = peaks["name"] == "Matterhorn"

others = peaks[~peaks["is_anchor"]]
anchor = peaks[peaks["is_anchor"]]

plot = (
    ggplot()
    # Mountain silhouette - filled area below ridgeline
    + geom_ribbon(aes(x="angle_deg", ymin="y_floor", ymax="elevation_m"), data=skyline, fill=BRAND, alpha=1.0)
    # Leader lines from peak summits up to their labels
    + geom_segment(
        aes(x="angle_deg", xend="angle_deg", y="elevation_m", yend="leader_top"), data=others, color=INK_MUTED, size=0.4
    )
    + geom_segment(
        aes(x="angle_deg", xend="angle_deg", y="elevation_m", yend="leader_top"), data=anchor, color=INK, size=0.8
    )
    # Summit markers
    + geom_point(
        aes(x="angle_deg", y="elevation_m"), data=others, size=2.2, color=PAGE_BG, fill=BRAND, stroke=0.6, shape="o"
    )
    + geom_point(
        aes(x="angle_deg", y="elevation_m"), data=anchor, size=3.8, color=PAGE_BG, fill=BRAND, stroke=1.0, shape="o"
    )
    # Peak labels
    + geom_text(
        aes(x="angle_deg", y="label_y", label="label"), data=others, size=10, color=INK, ha="center", va="bottom"
    )
    + geom_text(
        aes(x="angle_deg", y="label_y", label="label"),
        data=anchor,
        size=12,
        color=INK,
        ha="center",
        va="bottom",
        fontweight="bold",
    )
    + scale_x_continuous(expand=(0.005, 0))
    + scale_y_continuous(
        breaks=[2500, 3000, 3500, 4000, 4500, 5000], labels=["2,500", "3,000", "3,500", "4,000", "4,500", "5,000"]
    )
    + coord_cartesian(xlim=(-2, 151), ylim=(2500, 5500))
    + labs(x="", y="Elevation (m)", title="Wallis from Gornergrat · area-mountain-panorama · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color=INK_SOFT),
        plot_title=element_text(size=22, color=INK, ha="left", margin={"b": 18}),
        axis_title_y=element_text(size=18, color=INK, margin={"r": 14}),
        axis_text_y=element_text(size=14, color=INK_SOFT),
        axis_text_x=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_margin=0.03,
    )
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
