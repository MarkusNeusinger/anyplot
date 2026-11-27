"""anyplot.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: plotnine 0.15.9 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
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
    geom_col,
    geom_hline,
    geom_line,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from sklearn.datasets import load_wine
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
BRAND = "#009E73"  # Imprint position 1 — ALWAYS first series
IMPRINT_RED = "#AE3030"  # Imprint matte red — semantic anchor for elbow emphasis

# Constants
THRESHOLDS = (90.0, 95.0, 99.0)  # common variance targets (percent) for choosing the component count

# Columns: set these to your table's column names
N_COMPONENTS = "Number of Principal Components"  # role: n_components
EXPLAINED_VARIANCE_RATIO = "Explained variance ratio"  # role: explained_variance_ratio
CUMULATIVE = "Cumulative Explained Variance (%)"  # role: extra
INDIVIDUAL = "Individual Explained Variance (%)"  # role: extra
LABEL = "Label"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("pca_variance.csv")
pca = PCA().fit(StandardScaler().fit_transform(load_wine().data))
df = pd.DataFrame(
    {
        N_COMPONENTS: np.arange(1, len(pca.explained_variance_ratio_) + 1),
        EXPLAINED_VARIANCE_RATIO: pca.explained_variance_ratio_,
    }
)

# Plot
df[CUMULATIVE] = df[EXPLAINED_VARIANCE_RATIO].cumsum() * 100
df[INDIVIDUAL] = df[EXPLAINED_VARIANCE_RATIO] * 100
first_component = df[N_COMPONENTS].min()

# Elbow: the point where the curve bends most (largest second difference)
bend = np.zeros(len(df))
bend[1:-1] = np.abs(np.diff(df[CUMULATIVE].to_numpy(dtype=float), n=2))
elbow_df = df.iloc[[int(np.nanargmax(bend))]].copy()
elbow_df[LABEL] = [
    f"Elbow: {int(c)} components\n({v:.1f}%)" for c, v in zip(elbow_df[N_COMPONENTS], elbow_df[CUMULATIVE], strict=True)
]

# Name the bars: label above the median bar, placed by a rule over df
bar_label_df = pd.DataFrame(
    {
        N_COMPONENTS: [df[N_COMPONENTS].median()],
        CUMULATIVE: [df[INDIVIDUAL].median() + 5],
        LABEL: ["Bars: individual variance\nper component"],
    }
)

thresholds = pd.DataFrame(
    {N_COMPONENTS: first_component - 0.3, CUMULATIVE: list(THRESHOLDS), LABEL: [f"{t:g}%" for t in THRESHOLDS]}
)

# Title fontsize: scaled by length per plot-generator.md formula
title_str = "line-pca-variance-cumulative · python · plotnine · anyplot.ai"
title_fontsize = max(8, round(12 * min(1.0, 67 / len(title_str))))

plot = (
    ggplot(df, aes(x=N_COMPONENTS, y=CUMULATIVE))
    # Threshold dashed reference lines (structural chrome — INK_SOFT)
    + geom_hline(yintercept=list(THRESHOLDS), linetype="dashed", color=INK_SOFT, size=0.5, alpha=0.6)
    # Individual variance as translucent bars — contextual background layer
    + geom_col(aes(y=INDIVIDUAL), fill=BRAND, width=0.5, alpha=0.15, show_legend=False)
    # Vertical drop-line from elbow to x-axis
    + geom_segment(
        data=elbow_df,
        mapping=aes(x=N_COMPONENTS, xend=N_COMPONENTS, y=0, yend=CUMULATIVE),
        linetype="dotted",
        color=IMPRINT_RED,
        size=0.6,
        alpha=0.6,
    )
    # Main cumulative variance line
    + geom_line(color=BRAND, size=1.0)
    # Data point markers — PAGE_BG fill for theme-adaptive white circles
    + geom_point(color=BRAND, size=2.5, fill=PAGE_BG, stroke=1.2, shape="o")
    # Highlighted elbow point
    + geom_point(
        data=elbow_df,
        mapping=aes(x=N_COMPONENTS, y=CUMULATIVE),
        color=IMPRINT_RED,
        size=5.0,
        fill=IMPRINT_RED,
        stroke=1.5,
        shape="o",
        alpha=0.9,
    )
    # Elbow annotation
    + geom_text(
        data=elbow_df,
        mapping=aes(x=N_COMPONENTS, y=CUMULATIVE, label=LABEL),
        ha="left",
        va="top",
        size=8.5,
        color=IMPRINT_RED,
        fontweight="bold",
        nudge_x=0.4,
        nudge_y=-4.0,
    )
    # Bar name
    + geom_text(
        data=bar_label_df,
        mapping=aes(x=N_COMPONENTS, y=CUMULATIVE, label=LABEL),
        ha="center",
        va="bottom",
        size=8,
        color=INK_SOFT,
    )
    # Threshold labels
    + geom_text(
        data=thresholds,
        mapping=aes(x=N_COMPONENTS, y=CUMULATIVE, label=LABEL),
        ha="left",
        va="bottom",
        size=8,
        color=INK_MUTED,
        nudge_y=0.5,
    )
    # Scales
    + scale_x_continuous(
        breaks=df[N_COMPONENTS].dropna().tolist(),
        labels=df[N_COMPONENTS].dropna().astype(str).tolist(),
        expand=(0.02, 0.4),
    )
    + scale_y_continuous(
        limits=(0, df[CUMULATIVE].max() * 1.02), breaks=range(0, 101, 20), labels=[f"{b}%" for b in range(0, 101, 20)]
    )
    + labs(x=N_COMPONENTS, y=CUMULATIVE, title=title_str)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK_SOFT),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=title_fontsize, color=INK, ha="left"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.12),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        axis_ticks_major_x=element_line(color=INK_SOFT, size=0.3),
        plot_margin=0.02,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
