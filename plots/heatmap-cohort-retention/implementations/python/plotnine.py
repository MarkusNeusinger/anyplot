"""heatmap-cohort-retention — Cohort Retention Heatmap
Library: plotnine | Python
Imprint palette (imprint_seq: blue→green), theme-adaptive chrome
"""

# Remove script dir from sys.path first to prevent self-shadowing the 'plotnine' library import
import sys as _sys


_sys.path = [p for p in _sys.path if p != __file__.rsplit("/", 1)[0]]
del _sys

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_gradient,
    scale_x_continuous,
    scale_y_discrete,
    theme,
    theme_minimal,
)


# Theme-adaptive chrome — Imprint palette
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data — SaaS monthly cohort retention, Jan–Oct 2024
np.random.seed(42)
cohorts = [
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
]
n_cohorts = len(cohorts)
cohort_sizes = [1200, 1350, 980, 1100, 1450, 1280, 1050, 1380, 1150, 1020]

rows = []
for i, cohort in enumerate(cohorts):
    max_periods = n_cohorts - i
    for period in range(max_periods):
        if period == 0:
            retention = 100.0
        else:
            base_decay = 100 * np.exp(-0.28 * period)
            noise = np.random.uniform(-2, 2)
            # Stronger trend: newer cohorts retain better (product maturity effect)
            trend_bonus = i * 2.8
            retention = np.clip(base_decay + noise + trend_bonus, 5, 100)
        rows.append(
            {"cohort": cohort, "period": period, "retention_rate": round(retention, 1), "cohort_size": cohort_sizes[i]}
        )

df = pd.DataFrame(rows)

# y-axis: cohort labels with cohort size; reversed so Jan 2024 appears at top
df["cohort_label"] = df.apply(lambda r: f"{r['cohort']} (n={r['cohort_size']:,})", axis=1)
cohort_labels = [f"{c} (n={s:,})" for c, s in zip(cohorts, cohort_sizes, strict=True)]
df["cohort_label"] = pd.Categorical(df["cohort_label"], categories=cohort_labels[::-1], ordered=True)

# Cell text: dark ink on bright green tiles (high retention), light on dark blue (low)
# Imprint seq: low → #4467A3 (blue), high → #009E73 (green)
df["text_color"] = df["retention_rate"].apply(lambda v: "#1A1A17" if v >= 60 else "#FFFDF6")
df["label"] = df["retention_rate"].apply(lambda v: f"{v:.0f}%")

# Storytelling: M4 retention improvement Jan→Jun 2024 (both cohorts have data at period 4)
compare_period = 4
jan_m4 = df[(df["cohort"] == "Jan 2024") & (df["period"] == compare_period)]["retention_rate"].values[0]
jun_m4 = df[(df["cohort"] == "Jun 2024") & (df["period"] == compare_period)]["retention_rate"].values[0]
improvement = jun_m4 - jan_m4

# Build plot — square 2400×2400 canvas
plot = (
    ggplot(df, aes(x="period", y="cohort_label", fill="retention_rate"))
    + geom_tile(color=PAGE_BG, size=0.5)
    + geom_text(aes(label="label", color="text_color"), size=2.8, fontweight="bold")
    + scale_fill_gradient(low="#4467A3", high="#009E73", limits=(0, 100), name="Retention %")
    + scale_color_identity()
    + scale_x_continuous(breaks=list(range(n_cohorts)), labels=[f"M{i}" for i in range(n_cohorts)])
    + scale_y_discrete(expand=(0, 0))
    + annotate(
        "text",
        x=7.5,
        y=3,
        label=f"M{compare_period}: +{improvement:.0f}pp\nJan→Jun 2024",
        size=3.0,
        color=INK_MUTED,
        ha="center",
    )
    + labs(
        x="Months Since Signup",
        y="",
        title="heatmap-cohort-retention · python · plotnine · anyplot.ai",
        subtitle="SaaS monthly cohorts — newer signups retain significantly better month over month",
    )
    + theme_minimal()
    + theme(
        figure_size=(6, 6),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK),
        plot_subtitle=element_text(size=9, ha="center", color=INK_SOFT, style="italic"),
        axis_title_x=element_text(size=10, color=INK),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        axis_text_y=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_ticks=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color="none"),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
)

# Save — square 2400×2400 at dpi=400 (6 in × 400 dpi = 2400 px)
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
