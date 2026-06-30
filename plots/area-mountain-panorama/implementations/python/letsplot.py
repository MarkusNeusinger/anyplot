"""anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-06-30
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_area,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1 — ridge outline

# Mountain silhouette fill — dark slate for evening/dusk photo feel
MOUNTAIN_FILL = "#2C3E50"
# Sky panel background — atmospheric context above the ridgeline
SKY_COLOR = "#B8D4E8" if THEME == "light" else "#0B1726"

# Data — Wallis (Valais) panorama from Gornergrat, WSW to NE
peak_records = [
    ("Matterhorn", 22, 4478),
    ("Dent Blanche", 46, 4358),
    ("Ober Gabelhorn", 64, 4063),
    ("Zinalrothorn", 80, 4221),
    ("Weisshorn", 96, 4506),
    ("Dom", 122, 4545),
    ("Täschhorn", 132, 4491),
    ("Alphubel", 144, 4206),
    ("Allalinhorn", 156, 4027),
    ("Rimpfischhorn", 170, 4199),
    ("Strahlhorn", 184, 4190),
    ("Monte Rosa", 212, 4634),
    ("Liskamm", 230, 4527),
    ("Castor", 244, 4223),
    ("Pollux", 252, 4092),
    ("Breithorn", 268, 4164),
]
peaks_df = pd.DataFrame(peak_records, columns=["name", "angle", "elev"])
peaks_df["elev_text"] = peaks_df["elev"].astype(str) + " m"

# Skyline — piecewise-linear tent functions (triangular peaks, NOT Gaussians)
np.random.seed(42)
n_samples = 1600
angle = np.linspace(0, 290, n_samples)
base_elev = 3000.0
skyline = np.full_like(angle, base_elev)

# Asymmetric flank widths (left_deg, right_deg) per peak — steep and angular
peak_widths = [
    (11, 14),  # Matterhorn — steep left flank (iconic pyramid)
    (16, 12),  # Dent Blanche
    (10, 8),  # Ober Gabelhorn — compact
    (12, 10),  # Zinalrothorn
    (14, 16),  # Weisshorn
    (12, 10),  # Dom
    (8, 6),  # Täschhorn — narrow and steep
    (10, 12),  # Alphubel
    (10, 8),  # Allalinhorn
    (9, 11),  # Rimpfischhorn
    (12, 10),  # Strahlhorn
    (16, 14),  # Monte Rosa — broad massif
    (10, 12),  # Liskamm
    (7, 7),  # Castor — symmetric
    (6, 8),  # Pollux
    (14, 10),  # Breithorn
]

for i, (_, p) in enumerate(peaks_df.iterrows()):
    lw, rw = peak_widths[i]
    left_rise = base_elev + (p["elev"] - base_elev) * np.maximum(0.0, 1.0 - (p["angle"] - angle) / lw)
    right_fall = base_elev + (p["elev"] - base_elev) * np.maximum(0.0, 1.0 - (angle - p["angle"]) / rw)
    tent = np.where(angle <= p["angle"], left_rise, right_fall)
    skyline = np.maximum(skyline, tent)

# Minor ridge bumps and rocky notches between major peaks
minor_peaks = [
    (9, 3440),
    (33, 3490),
    (56, 3520),
    (73, 3460),
    (88, 3540),
    (108, 3500),
    (138, 3470),
    (162, 3510),
    (198, 3490),
    (224, 3530),
    (258, 3450),
    (280, 3480),
]
for mp_angle, mp_elev in minor_peaks:
    w = np.random.uniform(3, 7)
    tent = base_elev + (mp_elev - base_elev) * np.maximum(0.0, 1.0 - np.abs(angle - mp_angle) / w)
    skyline = np.maximum(skyline, tent)

# Organic roughness — rocky jaggedness along ridges
roughness = np.cumsum(np.random.randn(n_samples)) * 0.5
roughness -= roughness.mean()
skyline += roughness
skyline = np.maximum(skyline, 2870.0)  # floor above y-axis lower limit

skyline_df = pd.DataFrame({"angle": angle, "elev": skyline})

# Stagger labels into three rows to avoid crowding for the 16 clustered peaks
label_rows = [5650, 5350, 5050]
min_dx = 26
placed = []
label_y_values = []
for _, p in peaks_df.iterrows():
    chosen = label_rows[-1]
    for ry in label_rows:
        conflict = any(abs(p["angle"] - pa) < min_dx and pr == ry for pa, pr in placed)
        if not conflict:
            chosen = ry
            break
    label_y_values.append(chosen)
    placed.append((p["angle"], chosen))

peaks_df["label_y"] = label_y_values
peaks_df["elev_y"] = peaks_df["label_y"] - 130
anchor_df = peaks_df[peaks_df["name"] == "Matterhorn"]
other_df = peaks_df[peaks_df["name"] != "Matterhorn"]

# Compass bearing labels for geographic orientation
compass_breaks = [22, 90, 160, 230, 280]
compass_labels = ["WSW", "W", "NW", "N", "NE"]

# Title scaled for length (formula: round(16 * 67 / n), floor=11)
TITLE = "Wallis Panorama from Gornergrat · area-mountain-panorama · python · letsplot · anyplot.ai"
title_size = max(11, round(16 * 67 / len(TITLE)))

plot = (
    ggplot()
    # Dark mountain silhouette with BRAND ridge outline — evening/dusk alpine feel
    + geom_area(data=skyline_df, mapping=aes(x="angle", y="elev"), fill=MOUNTAIN_FILL, color=BRAND, size=0.8, alpha=1.0)
    # Leader lines from each summit up to its label
    + geom_segment(
        data=peaks_df, mapping=aes(x="angle", y="elev", xend="angle", yend="label_y"), color=INK_SOFT, size=0.4
    )
    # Peak markers — hover tooltips are lets-plot's key interactive HTML differentiator
    + geom_point(
        data=peaks_df,
        mapping=aes(x="angle", y="elev"),
        color=BRAND,
        size=2.5,
        tooltips=layer_tooltips().line("@name").line("@elev_text"),
    )
    # Peak names — non-anchor summits
    + geom_text(
        data=other_df,
        mapping=aes(x="angle", y="label_y", label="name"),
        size=3.5,
        color=INK,
        fontface="bold",
        vjust=0.0,
    )
    # Matterhorn anchor — slightly larger for focal emphasis
    + geom_text(
        data=anchor_df,
        mapping=aes(x="angle", y="label_y", label="name"),
        size=4.5,
        color=INK,
        fontface="bold",
        vjust=0.0,
    )
    # Elevation sub-labels below each peak name
    + geom_text(
        data=peaks_df, mapping=aes(x="angle", y="elev_y", label="elev_text"), size=3.0, color=INK_SOFT, vjust=0.0
    )
    + scale_x_continuous(name="Bearing", breaks=compass_breaks, labels=compass_labels, limits=[0, 290], expand=[0, 0])
    + scale_y_continuous(name="Elevation (m)", breaks=[3000, 3500, 4000, 4500], limits=[2800, 6000], expand=[0, 0])
    + labs(title=TITLE, subtitle="Pennine Alps 4000-m summits · 16 labeled peaks from Gornergrat (3089 m)")
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=SKY_COLOR),
        panel_grid_major_y=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        axis_line_y=element_blank(),
        axis_ticks_x=element_line(color=INK_SOFT),
        axis_ticks_y=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=title_size, color=INK),
        plot_subtitle=element_text(size=10, color=INK_MUTED),
        plot_margin=[40, 40, 20, 20],
    )
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
