"""anyplot.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
Z_95 = 1.96  # two-sided 95% normal quantile for the Greenwood band
CI_ALPHA = 0.22  # band opacity: curves and overlapping bands stay distinguishable
TICK_HEIGHT = 0.035  # censoring tick height in survival units

# Columns: set these to your table's column names
TIME = "Time (months)"  # role: time
EVENT = "Event (1 = event, 0 = censored)"  # role: event
GROUP = "Treatment group"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("trial.csv")
np.random.seed(42)
standard_times = np.concatenate([np.random.exponential(scale=18, size=50), np.random.exponential(scale=8, size=30)])
standard_censored = np.random.binomial(1, 0.25, size=80)
experimental_times = np.concatenate(
    [np.random.exponential(scale=28, size=55), np.random.exponential(scale=12, size=25)]
)
experimental_censored = np.random.binomial(1, 0.30, size=80)
df = pd.DataFrame(
    {
        TIME: np.concatenate([standard_times, experimental_times]),
        EVENT: np.concatenate([1 - standard_censored, 1 - experimental_censored]),
        GROUP: ["Standard Treatment"] * 80 + ["Experimental Treatment"] * 80,
    }
)


# Plot: reads only df and the constants above
def hex_to_rgba(color, alpha):
    r, g, b = (int(color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


def steps(x, y):
    """Expand (x, y) knots into a step polyline: flat, then a vertical drop at each x."""
    return list(zip(np.repeat(x, 2)[1:].tolist(), np.repeat(y, 2)[:-1].tolist(), strict=True))


groups = list(df[GROUP].unique())
bands, curves, ticks = [], [], []
for g in groups:
    sub = df[df[GROUP] == g]
    times = sub[TIME].to_numpy()
    events = sub[EVENT].to_numpy()
    t_end = float(np.nanmax(times))

    # Kaplan-Meier estimate with Greenwood variance at each distinct event time
    event_times = np.unique(times[events == 1])
    surv, var_sum = 1.0, 0.0
    knots_t, knots_s, knots_lo, knots_hi = [0.0], [1.0], [1.0], [1.0]
    for t in event_times:
        at_risk = np.sum(times >= t)
        deaths = np.sum((times == t) & (events == 1))
        surv *= 1 - deaths / at_risk
        if at_risk > deaths:
            var_sum += deaths / (at_risk * (at_risk - deaths))
        se = surv * np.sqrt(var_sum)
        knots_t.append(float(t))
        knots_s.append(float(surv))
        knots_lo.append(max(surv - Z_95 * se, 0.0))
        knots_hi.append(min(surv + Z_95 * se, 1.0))
    for knots in (knots_t, knots_s, knots_lo, knots_hi):
        knots.append(knots[-1] if knots is not knots_t else t_end)

    curve = steps(knots_t, knots_s)
    upper = steps(knots_t, knots_hi)
    lower = steps(knots_t, knots_lo)
    curves.append(curve)
    bands.append(upper + lower[::-1])

    # Censoring ticks sit on the curve at each censoring time
    censored = np.sort(times[events == 0])
    heights = np.array(knots_s)[np.searchsorted(knots_t, censored, side="right") - 1]
    tick_points = []
    for ct, h in zip(censored, heights, strict=True):
        tick_points += [(float(ct), float(h) - TICK_HEIGHT / 2), (float(ct), float(h) + TICK_HEIGHT / 2), (None, None)]
    ticks.append(tick_points)

# Series order: bands, curves, ticks; colors follow the same order
series_colors = (
    [hex_to_rgba(IMPRINT_PALETTE[i], CI_ALPHA) for i in range(len(groups))]
    + [IMPRINT_PALETTE[i] for i in range(len(groups))]
    + [IMPRINT_PALETTE[i] for i in range(len(groups))]
)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(series_colors),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=5,
    opacity="1",
    opacity_hover="1",
    guide_stroke_dasharray="0",
    major_guide_stroke_dasharray="0",
    font_family="sans-serif",
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="survival-kaplan-meier · python · pygal · anyplot.ai",
    x_title=TIME,
    y_title="Survival probability",
    show_dots=False,
    stroke=True,
    fill=False,
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=0,
    truncate_legend=-1,
    legend_at_bottom=True,
    range=(0, 1.05),
    include_x_axis=True,
    margin=50,
    spacing=30,
    explicit_size=True,
)

for band in bands:
    chart.add(None, band, fill=True, stroke=True, stroke_style={"width": 0}, show_dots=False)
for g, curve in zip(groups, curves, strict=True):
    chart.add(g, curve, stroke_style={"width": 6}, fill=False)
for tick_points in ticks:
    chart.add(None, tick_points, stroke_style={"width": 4}, show_dots=False, allow_interruptions=True)

chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
