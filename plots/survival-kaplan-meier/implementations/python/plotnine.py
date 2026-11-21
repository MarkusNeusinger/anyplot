"""anyplot.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-11
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
    geom_line,
    geom_point,
    geom_ribbon,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
Z_95 = 1.96  # two-sided 95 % confidence interval

# Columns: set these to your table's column names
TENURE = "Subscription time (months)"  # role: time
CHURNED = "Churned"  # role: event
PLAN = "Plan"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("subscribers.csv")
rng = np.random.default_rng(7)
_plans = {"Monthly plan": (140, 0.07), "Annual plan": (110, 0.025)}
_parts = []
for _name, (_n, _hazard) in _plans.items():
    _lifetime = rng.exponential(1 / _hazard, _n)
    _followup = rng.uniform(6, 36, _n)  # staggered sign-up dates, analysis cut-off
    _parts.append(
        pd.DataFrame(
            {
                TENURE: np.minimum(_lifetime, _followup).round(2),
                CHURNED: (_lifetime <= _followup).astype(int),
                PLAN: _name,
            }
        )
    )
df = pd.concat(_parts, ignore_index=True)


# Plot: reads only df and the constants above
def kaplan_meier(group):
    """Step coordinates of the survival curve and its 95 % band, plus the curve at each censoring."""
    group = group.sort_values(TENURE)
    event_times = np.sort(group.loc[group[CHURNED] == 1, TENURE].unique())
    surv, var_sum = 1.0, 0.0
    steps = [(0.0, 1.0, 1.0, 1.0)]
    for t in event_times:
        at_risk = (group[TENURE] >= t).sum()
        deaths = ((group[TENURE] == t) & (group[CHURNED] == 1)).sum()
        surv *= 1 - deaths / at_risk
        if at_risk > deaths:
            var_sum += deaths / (at_risk * (at_risk - deaths))
        half_width = Z_95 * np.sqrt(var_sum)  # log-scale Greenwood interval
        steps.append((t, surv, surv * np.exp(-half_width), min(1.0, surv * np.exp(half_width))))
    steps = pd.DataFrame(steps, columns=["time", "survival", "lower", "upper"])
    last = steps.iloc[-1].copy()
    last["time"] = group[TENURE].max()
    steps.loc[len(steps)] = last

    # Each step row is preceded by a point at its own time with the previous values: flat, then a vertical drop
    prev = steps[["survival", "lower", "upper"]].to_numpy()
    rows = [steps.iloc[0].to_numpy()]
    for i in range(1, len(steps)):
        rows.append([steps.time[i], *prev[i - 1]])
        rows.append(steps.iloc[i].to_numpy())
    stair = pd.DataFrame(rows, columns=steps.columns)

    censored_times = group.loc[group[CHURNED] == 0, TENURE].to_numpy()
    height = steps.survival.to_numpy()[np.searchsorted(steps.time.to_numpy(), censored_times, side="right") - 1]
    ticks = pd.DataFrame({"time": censored_times, "survival": height})

    below = steps.loc[steps.survival <= 0.5, "time"]
    return stair, ticks, (below.iloc[0] if len(below) else np.nan)


plans = df[PLAN].unique().tolist()
curves, ticks, medians = [], [], []
for plan in plans:
    stair, tick, median = kaplan_meier(df[df[PLAN] == plan])
    stair[PLAN] = plan
    tick[PLAN] = plan
    curves.append(stair)
    ticks.append(tick)
    medians.append(pd.DataFrame({"median": [median], PLAN: plan}).dropna())
curves = pd.concat(curves, ignore_index=True)
ticks = pd.concat(ticks, ignore_index=True)
medians = pd.concat(medians, ignore_index=True)

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.1),
    panel_grid_minor=element_blank(),
    axis_ticks_y=element_line(color=INK_SOFT, size=0.3),
    axis_ticks_x=element_blank(),
    panel_border=element_blank(),
    axis_line_y=element_line(color=INK_SOFT, size=0.4),
    axis_line_x=element_blank(),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    plot_title=element_text(color=INK, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.4),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
    legend_position=(0.03, 0.05),
    legend_justification=(0, 0),
)

plot = (
    ggplot()
    + geom_ribbon(curves, aes(x="time", ymin="lower", ymax="upper", fill=PLAN), alpha=0.18)
    + geom_line(curves, aes(x="time", y="survival", color=PLAN), size=1.0)
    + geom_point(ticks, aes(x="time", y="survival", color=PLAN), shape="|", size=3, stroke=0.6)
    + geom_vline(medians, aes(xintercept="median", color=PLAN), linetype="dashed", alpha=0.5, size=0.5)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=plans)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=plans)
    + scale_y_continuous(limits=(0, 1), breaks=[0, 0.25, 0.5, 0.75, 1.0], labels=["0%", "25%", "50%", "75%", "100%"])
    + scale_x_continuous(limits=(0, None), expand=(0, 0, 0.02, 0))
    + labs(
        title="survival-kaplan-meier · python · plotnine · anyplot.ai",
        x=TENURE,
        y="Still subscribed (survival probability)",
        color=PLAN,
        fill=PLAN,
    )
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
