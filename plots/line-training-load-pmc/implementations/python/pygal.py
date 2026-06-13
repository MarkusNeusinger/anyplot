""" anyplot.ai
line-training-load-pmc: Training Load Performance Management Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 80/100 | Created: 2026-06-13
"""

import os
import sys


# Script filename shadows the installed `pygal` package; remove script dir from path.
sys.path.pop(0)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Palette: reference slot first so CTL gets Imprint position 1 (#009E73)
CHART_COLORS = (
    INK_MUTED,  # TSB = 0 reference line
    "#009E73",  # Fitness (CTL)  — Imprint pos 1
    "#C475FD",  # Fatigue (ATL)  — Imprint pos 2
    "#4467A3",  # Form (TSB)     — Imprint pos 3
    "#BD8233",  # Daily TSS      — Imprint pos 4
    "#AE3030",
    "#2ABCCD",
    "#954477",
)

# Data — 180-day training block (Jan–Jun 2024)
np.random.seed(42)
n_days = 180
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")

# Daily TSS: 3-week build + 1-week recovery pattern
tss = np.zeros(n_days)
for i in range(n_days):
    dow = dates[i].dayofweek  # 0=Mon, 6=Sun
    cycle = (i // 7) % 4  # 0–2 = build, 3 = recovery

    if cycle < 3:
        base = 55 + cycle * 12  # 55 → 67 → 79 TSS across build weeks
    else:
        base = 35  # recovery week

    if dow == 0:  # Monday: rest / very easy
        tss[i] = max(0.0, np.random.normal(12, 6))
    elif dow == 5:  # Saturday: long session
        tss[i] = max(0.0, np.random.normal(base * 1.6, 14))
    elif dow == 6:  # Sunday: medium effort
        tss[i] = max(0.0, np.random.normal(base * 0.9, 10))
    else:  # Tue–Fri: quality / tempo
        tss[i] = max(0.0, np.random.normal(base * 0.75, 12))

# Two-week taper into target race on day 155
for i in range(140, 156):
    tss[i] *= max(0.12, 1.0 - (i - 140) / 18.0)
tss[155] = 0.0  # race day

# EWMA: CTL tau=42 days (fitness), ATL tau=7 days (fatigue)
a_ctl = 1.0 - np.exp(-1.0 / 42)
a_atl = 1.0 - np.exp(-1.0 / 7)

ctl = np.zeros(n_days)
atl = np.zeros(n_days)
tsb = np.zeros(n_days)
ctl[0] = atl[0] = tss[0]

for i in range(1, n_days):
    ctl[i] = ctl[i - 1] + a_ctl * (tss[i] - ctl[i - 1])
    atl[i] = atl[i - 1] + a_atl * (tss[i] - atl[i - 1])
    tsb[i] = ctl[i - 1] - atl[i - 1]  # previous-day CTL minus previous-day ATL

# X-axis: show labels only at month-start positions
x_labels = [d.strftime("%b %Y") if d.day == 1 else "" for d in dates]
x_labels_major = [d.strftime("%b %Y") for d in dates if d.day == 1]

# Title — 52 chars → ratio 1.0 → title_font_size 66
title = "line-training-load-pmc · python · pygal · anyplot.ai"

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=CHART_COLORS,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3.0,
)

# Chart
chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title="Date (2024)",
    y_title="Training Load (TSS pts)",
    show_x_guides=False,
    show_y_guides=True,
    show_dots=False,
    fill=False,
    legend_at_bottom=False,
    show_minor_x_labels=False,
)

chart.x_labels = x_labels
chart.x_labels_major = x_labels_major

# Add series in color-assignment order
chart.add("TSB = 0", [0] * n_days, stroke_style={"width": 1.2, "dasharray": "6 4"})
chart.add("Fitness (CTL)", ctl.tolist(), stroke_style={"width": 5.5})
chart.add("Fatigue (ATL)", atl.tolist(), stroke_style={"width": 3.5})
chart.add("Form (TSB)", tsb.tolist(), stroke_style={"width": 2.5})
chart.add("Daily TSS", tss.tolist(), stroke_style={"width": 1.5})

# Save PNG and interactive HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
