"""anyplot.ai
venn-basic: Venn Diagram
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per set in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: one 0/1 membership column per set, plus the exclusive count of the region
SOLAR = "Solar"  # role: set_labels
WIND = "Wind"  # role: extra
HYDRO = "Hydro"  # role: extra
SITES = "Sites"  # role: set_sizes
REGION = "Region"  # role: intersections
SET_COLUMNS = [SOLAR, WIND, HYDRO]

# Data: replace this block with your own table, for example df = pd.read_csv("regions.csv")
# One row per region of the diagram; the membership flags say which sets it lies in.
df = pd.DataFrame(
    {
        SET_COLUMNS[0]: [1, 0, 0, 1, 1, 0, 1],
        SET_COLUMNS[1]: [0, 1, 0, 1, 0, 1, 1],
        SET_COLUMNS[2]: [0, 0, 1, 0, 1, 1, 1],
        REGION: ["Solar", "Wind", "Hydro", "Solar+Wind", "Solar+Hydro", "Wind+Hydro", "All three"],
        SITES: [42, 36, 24, 18, 9, 12, 6],
    }
)

# Plot
members = df[SET_COLUMNS].fillna(0).to_numpy(dtype=float) > 0
counts = df[SITES].to_numpy(dtype=float)
n_sets = len(SET_COLUMNS)

# Inclusive set sizes and pairwise overlaps follow from the exclusive counts
set_sizes = np.array([np.nansum(counts[members[:, i]]) for i in range(n_sets)])
radii = np.sqrt(set_sizes / np.pi)


def lens_area(d, r1, r2):
    """Overlap area of two circles whose centers are d apart."""
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return np.pi * min(r1, r2) ** 2
    a1 = np.arccos((d**2 + r1**2 - r2**2) / (2 * d * r1))
    a2 = np.arccos((d**2 + r2**2 - r1**2) / (2 * d * r2))
    return r1**2 * a1 + r2**2 * a2 - 0.5 * np.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))


def distance_for_overlap(target, r1, r2):
    """Center distance at which two circles overlap by the target area (bisection)."""
    lo, hi = abs(r1 - r2), r1 + r2
    for _ in range(60):
        mid = (lo + hi) / 2
        if lens_area(mid, r1, r2) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def pair_size(i, j):
    return np.nansum(counts[members[:, i] & members[:, j]])


# Place circles so each pairwise overlap area matches its inclusive intersection size
d01 = distance_for_overlap(pair_size(0, 1), radii[0], radii[1])
d02 = distance_for_overlap(pair_size(0, 2), radii[0], radii[2])
d12 = distance_for_overlap(pair_size(1, 2), radii[1], radii[2])
cx_c = (d01**2 + d02**2 - d12**2) / (2 * d01)
cy_c = -np.sqrt(max(d02**2 - cx_c**2, 0.0))
centers = np.array([[0.0, 0.0], [d01, 0.0], [cx_c, cy_c]])
centers -= centers.mean(axis=0)

# Circle outlines
theta = np.linspace(0, 2 * np.pi, 200)
df_circles = pd.concat(
    [
        pd.DataFrame(
            {
                "x": centers[i, 0] + radii[i] * np.cos(theta),
                "y": centers[i, 1] + radii[i] * np.sin(theta),
                "set": SET_COLUMNS[i],
            }
        )
        for i in range(n_sets)
    ],
    ignore_index=True,
)

# Count labels sit at the most interior point of each region
extent = (centers + radii[:, None]).max() + 0.1, (centers - radii[:, None]).min() - 0.1
gx, gy = np.meshgrid(np.linspace(extent[1], extent[0], 500), np.linspace(extent[1], extent[0], 500))
dist = np.stack([np.hypot(gx - centers[i, 0], gy - centers[i, 1]) for i in range(n_sets)])
inside = dist < radii[:, None, None]
margin = np.abs(dist - radii[:, None, None]).min(axis=0)
label_rows = []
for row, flags in enumerate(members):
    in_region = np.all(inside == flags[:, None, None], axis=0)
    best = np.where(in_region, margin, -1).argmax()
    label_rows.append({"x": gx.flat[best], "y": gy.flat[best], "label": str(int(np.nan_to_num(counts[row])))})
df_counts = pd.DataFrame(label_rows)

# Set names sit just outside each circle, pointing away from the diagram center
directions = centers / np.linalg.norm(centers, axis=1, keepdims=True)
name_pos = centers + directions * (radii[:, None] + 0.3 * radii.max())
df_names = pd.DataFrame({"x": name_pos[:, 0], "y": name_pos[:, 1], "label": SET_COLUMNS})

pad = 0.35 * radii.max()
x_lim = [(centers[:, 0] - radii).min() - pad, (centers[:, 0] + radii).max() + pad]
y_lim = [(centers[:, 1] - radii).min() - pad, (centers[:, 1] + radii).max() + pad]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    plot_title=element_text(size=18, face="bold", hjust=0.5, color=INK),
    legend_position="none",
    plot_margin=[40, 20, 20, 20],
)

plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", fill="set"), data=df_circles, alpha=0.4, color=INK_SOFT, size=1.5)
    + geom_text(aes(x="x", y="y", label="label"), data=df_counts, size=7, fontface="bold", color=INK)
    + geom_text(aes(x="x", y="y", label="label"), data=df_names, size=8, fontface="bold", color=INK)
    + scale_fill_manual(values=dict(zip(SET_COLUMNS, IMPRINT_PALETTE, strict=False)))
    + coord_fixed(ratio=1, xlim=x_lim, ylim=y_lim)
    + labs(title="venn-basic · python · letsplot · anyplot.ai")
    + theme_void()
    + anyplot_theme
    + ggsize(600, 600)
)

# Save as PNG and HTML with theme suffix
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images subdirectory if needed
if os.path.exists(f"lets-plot-images/plot-{THEME}.png"):
    os.rename(f"lets-plot-images/plot-{THEME}.png", f"plot-{THEME}.png")
if os.path.exists(f"lets-plot-images/plot-{THEME}.html"):
    os.rename(f"lets-plot-images/plot-{THEME}.html", f"plot-{THEME}.html")
if os.path.exists("lets-plot-images") and not os.listdir("lets-plot-images"):
    os.rmdir("lets-plot-images")
