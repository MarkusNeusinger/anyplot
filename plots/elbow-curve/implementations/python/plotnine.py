""" anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-10
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
    geom_line,
    geom_point,
    geom_vline,
    ggplot,
    labs,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]
BRAND = IMPRINT[0]  # #009E73 - first series always
ACCENT = IMPRINT[1]  # #C475FD - accent for annotation line

# Data - Simulate realistic K-means inertia values
np.random.seed(42)

k_values = list(range(1, 11))

# Simulate inertia values that show clear elbow at k=4
base_inertias = [1000, 500, 280, 150, 120, 100, 85, 75, 68, 62]
noise = np.random.uniform(-5, 5, len(k_values))
inertias = [max(10, base + n) for base, n in zip(base_inertias, noise, strict=True)]

# Create DataFrame for plotting
df = pd.DataFrame({"k": k_values, "inertia": inertias})

# Optimal k (elbow point)
optimal_k = 4

# Plot
plot = (
    ggplot(df, aes(x="k", y="inertia"))
    + geom_line(color=BRAND, size=2, alpha=0.9)
    + geom_point(color=BRAND, size=5, alpha=1.0)
    + geom_vline(xintercept=optimal_k, linetype="dashed", color=ACCENT, size=1.5, alpha=0.8)
    + annotate(
        "text",
        x=optimal_k + 0.5,
        y=inertias[optimal_k - 1] + 80,
        label=f"Optimal k = {optimal_k}",
        size=14,
        color=ACCENT,
        ha="left",
        fontweight="bold",
    )
    + labs(
        title="elbow-curve · plotnine · anyplot.ai",
        x="Number of Clusters (k)",
        y="Inertia (Within-Cluster Sum of Squares)",
    )
    + scale_x_continuous(breaks=list(range(1, 11)))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        plot_title=element_text(size=24, color=INK, weight="bold"),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
