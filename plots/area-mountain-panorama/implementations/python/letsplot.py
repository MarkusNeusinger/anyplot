"""anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-04-25
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
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "#D6D3C7" if THEME == "light" else "#3A3A34"
BRAND = "#009E73"

# Data — Wallis (Valais, Switzerland) panorama anchored on the Matterhorn
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

# Skyline — sum-of-Gaussians around peaks plus minor inter-peak ridges + organic noise
np.random.seed(42)
n_samples = 1600
angle = np.linspace(0, 290, n_samples)
base_elev = 3000.0

skyline = np.full_like(angle, base_elev)
for _, p in peaks_df.iterrows():
    bell = base_elev + (p["elev"] - base_elev) * np.exp(-((angle - p["angle"]) ** 2) / (2 * 7.0**2))
    skyline = np.maximum(skyline, bell)

minor_offsets = [9, 33, 56, 73, 88, 108, 138, 162, 198, 224, 258, 280]
for off in minor_offsets:
    h = 3450 + np.random.uniform(-180, 200)
    bell = base_elev + (h - base_elev) * np.exp(-((angle - off) ** 2) / (2 * 4.0**2))
    skyline = np.maximum(skyline, bell)

skyline = skyline + np.cumsum(np.random.randn(n_samples)) * 0.6
skyline_df = pd.DataFrame({"angle": angle, "elev": skyline})

# Stagger labels into three rows — name labels are wide, so use a generous gap
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
peaks_df["elev_y"] = peaks_df["label_y"] - 140
peaks_df["elev_text"] = peaks_df["elev"].astype(str) + " m"

# Highlight the anchor summit (Matterhorn) typographically
anchor_mask = peaks_df["name"] == "Matterhorn"
anchor_df = peaks_df[anchor_mask]
other_df = peaks_df[~anchor_mask]

# Compass bearing ticks — vantage point ~Gornergrat sweeping WSW → ENE
compass_breaks = [22, 90, 160, 230, 280]
compass_labels = ["WSW", "W", "NW", "N", "NE"]

plot = (
    ggplot()
    # Mountain silhouette
    + geom_area(data=skyline_df, mapping=aes(x="angle", y="elev"), fill=BRAND, color=BRAND, size=0.6, alpha=1.0)
    # Leader lines from each summit up to its label
    + geom_segment(
        data=peaks_df, mapping=aes(x="angle", y="elev", xend="angle", yend="label_y"), color=INK_SOFT, size=0.4
    )
    # Peak names — non-anchor
    + geom_text(
        data=other_df, mapping=aes(x="angle", y="label_y", label="name"), size=7, color=INK, fontface="bold", vjust=0.0
    )
    # Peak names — Matterhorn anchor (slightly larger for visual emphasis)
    + geom_text(
        data=anchor_df, mapping=aes(x="angle", y="label_y", label="name"), size=9, color=INK, fontface="bold", vjust=0.0
    )
    # Elevation under each name
    + geom_text(data=peaks_df, mapping=aes(x="angle", y="elev_y", label="elev_text"), size=6, color=INK_SOFT, vjust=0.0)
    + scale_x_continuous(name="Bearing", breaks=compass_breaks, labels=compass_labels, limits=[0, 290], expand=[0, 0])
    + scale_y_continuous(name="Elevation (m)", breaks=[3000, 3500, 4000, 4500], limits=[2800, 6000], expand=[0, 0])
    + labs(
        title="Wallis Panorama from Gornergrat · area-mountain-panorama · letsplot · anyplot.ai",
        subtitle="Skyline of the Pennine Alps with 16 labeled 4000-m summits",
    )
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_y=element_line(color=RULE, size=0.3),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        axis_line_y=element_blank(),
        axis_ticks_x=element_line(color=INK_SOFT),
        axis_ticks_y=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        plot_subtitle=element_text(size=16, color=INK_MUTED),
        plot_margin=[40, 40, 20, 20],
    )
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
