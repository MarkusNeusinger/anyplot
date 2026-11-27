"""anyplot.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"  # INK at 15 %

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # Imprint position 1 — cumulative line (first series)
ANYPLOT_AMBER = "#DDCC77"  # semantic anchor — caution, 90% threshold
MATTE_RED = IMPRINT_PALETTE[4]  # Imprint position 5 — alert, 95% threshold

# Constants
THRESHOLD_CAUTION = 90.0  # percent of variance
THRESHOLD_TARGET = 95.0

# Columns: set these to your table's column names
COMPONENT = "Principal component"  # role: n_components
CUMULATIVE = "Cumulative explained variance (%)"  # role: explained_variance_ratio
INDIVIDUAL = "Individual explained variance (%)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("pca_variance.csv")
# Image-pixel PCA: 8x8 handwritten digit images (64 pixel features), first 30 components
pixels = load_digits().data
pca = PCA(n_components=30).fit(pixels)
df = pd.DataFrame(
    {
        COMPONENT: np.arange(1, len(pca.explained_variance_ratio_) + 1),
        INDIVIDUAL: np.round(pca.explained_variance_ratio_ * 100, 2),
        CUMULATIVE: np.round(np.cumsum(pca.explained_variance_ratio_) * 100, 2),
    }
)

# Plot: reads only df and the constants above
components = df[COMPONENT].to_numpy()
cumulative = df[CUMULATIVE].to_numpy()
last = len(df) - 1

# First component counts that reach each threshold
crossed_caution = components[cumulative >= THRESHOLD_CAUTION]
crossed_target = components[cumulative >= THRESHOLD_TARGET]
comp_caution = int(crossed_caution[0]) if len(crossed_caution) else None
comp_target = int(crossed_target[0]) if len(crossed_target) else None

# Elbow: component with max perpendicular distance from the start→end chord
dx, dy = components[last] - components[0], cumulative[last] - cumulative[0]
perp_dist = np.abs(dy * (components - components[0]) - dx * (cumulative - cumulative[0])) / np.hypot(dx, dy)
elbow = df.iloc[[int(np.argmax(perp_dist))]].assign(label=lambda d: "PC " + d[COMPONENT].astype(str))

label_x = (comp_target or components[last]) - 0.4
tooltip_pc = f"PC @{{{COMPONENT}}}"
tooltip_cum = f"Cumulative: @{{{CUMULATIVE}}}%"
tooltip_ind = f"Individual: @{{{INDIVIDUAL}}}%"

# Dark page needs a stronger bar fill to stay visible but subordinate
bar_alpha = 0.28 if THEME == "light" else 0.42

title = "line-pca-variance-cumulative · python · letsplot · anyplot.ai"

anyplot_chrome = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    panel_grid_major_y=element_line(color=GRID, size=0.4),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK),
)

plot = (
    ggplot(df, aes(x=COMPONENT, y=CUMULATIVE))
    # Secondary: individual variance bars (muted, behind the cumulative line)
    + geom_bar(aes(y=INDIVIDUAL), stat="identity", fill=INK_MUTED, alpha=bar_alpha, width=0.65)
    # Threshold reference lines
    + geom_hline(yintercept=THRESHOLD_CAUTION, linetype="dashed", color=ANYPLOT_AMBER, size=1.0)
    + geom_hline(yintercept=THRESHOLD_TARGET, linetype="dashed", color=MATTE_RED, size=1.0)
    # Threshold labels (right-aligned near edge)
    + geom_text(
        data=pd.DataFrame({"x": [label_x], "y": [THRESHOLD_CAUTION - 3.5], "label": [f"{THRESHOLD_CAUTION:.0f}%"]}),
        mapping=aes(x="x", y="y", label="label"),
        color=ANYPLOT_AMBER,
        size=4,
        hjust=1,
    )
    + geom_text(
        data=pd.DataFrame({"x": [label_x], "y": [THRESHOLD_TARGET + 2.5], "label": [f"{THRESHOLD_TARGET:.0f}%"]}),
        mapping=aes(x="x", y="y", label="label"),
        color=MATTE_RED,
        size=4,
        hjust=1,
    )
    # Primary: cumulative variance line (Imprint brand green, first series)
    + geom_line(size=2.0, color=BRAND)
    # Points with lets-plot native tooltips (hover shows both cumulative and individual)
    + geom_point(
        size=4, color=BRAND, alpha=0.9, tooltips=layer_tooltips().line(tooltip_pc).line(tooltip_cum).line(tooltip_ind)
    )
    # Elbow annotation: hollow ring marker + label (spec: annotate elbow if detectable)
    + geom_point(data=elbow, size=9, shape=21, color=INK, fill=ELEVATED_BG)
    + geom_point(data=elbow, size=4, color=BRAND)
    + geom_text(data=elbow, mapping=aes(label="label"), color=INK, size=4.5, hjust=0, nudge_x=0.9, nudge_y=-4)
    + scale_x_continuous(breaks=[1, *range(5, int(components[last]) + 1, 5)])
    + scale_y_continuous(breaks=list(range(0, 101, 10)), limits=[0, cumulative.max() * 1.06])
    + labs(title=title, x=COMPONENT, y=CUMULATIVE)
    + theme_minimal()
    + anyplot_chrome
    + ggsize(800, 450)
)

# Dotted drop lines at the component count where each threshold is first reached (only when reached)
for comp, color in ((comp_caution, ANYPLOT_AMBER), (comp_target, MATTE_RED)):
    if comp is not None:
        plot += geom_vline(xintercept=comp, linetype="dotted", color=color, size=0.8, alpha=0.65)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
