"""anyplot.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-11
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_ribbon,
    geom_step,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
Z_95 = 1.96  # normal quantile for the 95% confidence band
SURVIVAL = "Survival Probability"  # derived Kaplan-Meier estimate
CI_LOW = "CI lower"  # derived lower band edge
CI_HIGH = "CI upper"  # derived upper band edge

# Columns: set these to your table's column names
TIME = "Time (months)"  # role: time
EVENT = "Event"  # role: event
GROUP = "Group"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("trial.csv")
np.random.seed(42)
n_per_group = 80
follow_up = 36  # months of follow-up
frames = []
for group_name, hazard_rate in [("Treatment", 0.04), ("Control", 0.08)]:
    times = np.clip(np.random.exponential(scale=1 / hazard_rate, size=n_per_group), 0, follow_up)
    event = (times < follow_up).astype(int)
    event[np.random.random(n_per_group) < 0.2] = 0  # 20% random censoring
    frames.append(pd.DataFrame({TIME: times, EVENT: event, GROUP: group_name}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
obs = df.dropna(subset=[TIME, EVENT])
groups = list(obs[GROUP].unique())
colors = {g: IMPRINT_PALETTE[i] for i, g in enumerate(groups)}

curves = []
censored = []
for name, sub in obs.groupby(GROUP, sort=False):
    t = sub[TIME].to_numpy(dtype=float)
    e = sub[EVENT].to_numpy(dtype=float)
    n_at_risk = len(t)
    survival, var_sum = 1.0, 0.0
    rows = [{TIME: 0.0, SURVIVAL: 1.0, CI_LOW: 1.0, CI_HIGH: 1.0}]
    for u in np.unique(t):
        at_time = t == u
        d = e[at_time].sum()
        if n_at_risk > 0 and d > 0:
            survival *= 1 - d / n_at_risk
            var_sum += d / (n_at_risk * (n_at_risk - d)) if n_at_risk > d else 0
        se = survival * np.sqrt(var_sum)  # Greenwood's formula
        rows.append(
            {
                TIME: u,
                SURVIVAL: survival,
                CI_LOW: max(0.0, survival - Z_95 * se),
                CI_HIGH: min(1.0, survival + Z_95 * se),
            }
        )
        n_at_risk -= at_time.sum()
    km = pd.DataFrame(rows)
    km[GROUP] = name
    curves.append(km)

    # Censoring ticks sit on the curve at their censoring time
    cens = sub[sub[EVENT] == 0][[TIME, GROUP]].copy()
    idx = np.searchsorted(km[TIME].to_numpy(), cens[TIME].to_numpy(), side="right") - 1
    cens[SURVIVAL] = km[SURVIVAL].to_numpy()[idx]
    censored.append(cens)

km_data = pd.concat(curves, ignore_index=True)

# The band steps with its curve: hold each bound until the next event time
bands = []
for _, km in km_data.groupby(GROUP, sort=False):
    held = km.shift(1).iloc[1:].assign(**{TIME: km[TIME].iloc[1:].to_numpy()})
    bands.append(pd.concat([held, km]).sort_values(TIME, kind="stable"))
band_data = pd.concat(bands, ignore_index=True)
band_data[GROUP] = band_data[GROUP].astype(str)
censored_data = pd.concat(censored, ignore_index=True)

title = "survival-kaplan-meier · python · letsplot · anyplot.ai"
title_size = round(16 * (67 / len(title) if len(title) > 67 else 1.0))

plot = (
    ggplot()
    # Confidence interval ribbons
    + geom_ribbon(aes(x=TIME, ymin=CI_LOW, ymax=CI_HIGH, fill=GROUP), data=band_data, alpha=0.2, size=0)
    # Step functions for survival curves
    + geom_step(aes(x=TIME, y=SURVIVAL, color=GROUP), data=km_data, size=1.0)
    # Censored observation tick marks
    + geom_point(aes(x=TIME, y=SURVIVAL, color=GROUP), data=censored_data, shape=3, size=2.5, stroke=1.0)
    + scale_color_manual(values=colors, breaks=groups)
    + scale_fill_manual(values=colors, breaks=groups)
    + scale_y_continuous(limits=[0, 1])
    + labs(x=TIME, y=SURVIVAL, title=title, color=GROUP, fill=GROUP)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=GRID, size=0.3),
        panel_grid_minor=element_line(color=GRID, size=0.2),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=title_size, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")

# lets-plot creates a subdirectory; move files to current directory
if os.path.exists("lets-plot-images"):
    for file in os.listdir("lets-plot-images"):
        shutil.move(f"lets-plot-images/{file}", file)
    os.rmdir("lets-plot-images")
