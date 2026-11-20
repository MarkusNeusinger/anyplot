"""anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
ACCENT = IMPRINT_PALETTE[1]  # elbow marker

# Columns: set these to your table's column names
K = "Number of clusters (k)"  # role: k_values
INERTIA = "Inertia (within-cluster sum of squares)"  # role: inertia

# Data: replace this block with your own table, for example df = pd.read_csv("kmeans_inertia.csv")
rng = np.random.default_rng(42)
base_inertias = np.array([1000, 500, 280, 150, 120, 100, 85, 75, 68, 62])
df = pd.DataFrame(
    {K: np.arange(1, len(base_inertias) + 1), INERTIA: base_inertias + rng.uniform(-5, 5, len(base_inertias))}
)

# Plot: reads only df and the constants above
# Elbow = the point farthest from the straight line joining the first and last point
x_norm = (df[K] - df[K].min()) / (df[K].max() - df[K].min())
y_norm = (df[INERTIA] - df[INERTIA].min()) / (df[INERTIA].max() - df[INERTIA].min())
elbow_idx = int(np.argmax(np.abs(x_norm + y_norm - 1)))
elbow_k = int(df[K].iloc[elbow_idx])
elbow_inertia = df[INERTIA].iloc[elbow_idx]
elbow_df = df.iloc[[elbow_idx]]

plot = (
    ggplot(df, aes(x=K, y=INERTIA))
    + geom_vline(xintercept=elbow_k, linetype="dashed", color=ACCENT, size=0.6, alpha=0.9)
    + geom_line(color=BRAND, size=1.2)
    + geom_point(color=BRAND, size=3.5)
    + geom_point(data=elbow_df, color=ACCENT, fill=ACCENT, size=5)
    + annotate(
        "text",
        x=elbow_k + 0.3,
        y=elbow_inertia + df[INERTIA].max() * 0.1,
        label=f"Elbow at k = {elbow_k}",
        size=11,
        color=INK,
        ha="left",
        fontweight="bold",
    )
    + labs(title="elbow-curve · python · plotnine · anyplot.ai")
    + scale_x_continuous(breaks=df[K].tolist())
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        plot_title=element_text(size=12, color=INK, weight="bold"),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
