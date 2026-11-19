"""anyplot.ai
violin-split: Split Violin Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-08
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

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
VALUE_RANGE = (0, 100)  # recovery score is a 0-100 scale

CLINIC = "Clinic"  # role: category
RECOVERY = "Recovery Score (0-100)"  # role: value
PERIOD = "Period"  # role: split_group

# Data: replace this block with your own table, for example df = pd.read_csv("recovery.csv")
rng = np.random.default_rng(42)
n_patients = 80
# (mean, std) of the recovery score per clinic, before and after treatment
profile = {
    "Clinic A": {"Before": (45, 12), "After": (72, 10)},
    "Clinic B": {"Before": (50, 15), "After": (68, 12)},
    "Clinic C": {"Before": (42, 10), "After": (78, 8)},
    "Clinic D": {"Before": (55, 18), "After": (65, 14)},
}
rows = []
for clinic, groups in profile.items():
    for period, (mean, std) in groups.items():
        scores = np.clip(rng.normal(mean, std, n_patients), 10, 95)
        rows.append(pd.DataFrame({CLINIC: clinic, PERIOD: period, RECOVERY: scores}))
df = pd.concat(rows, ignore_index=True)

# Plot
clinics = list(dict.fromkeys(df[CLINIC]))
periods = list(dict.fromkeys(df[PERIOD]))
n_clinics = len(clinics)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    # pygal colors series by position: every half violin of a group, then two marker series per half
    colors=tuple(IMPRINT_PALETTE[g] for g in range(len(periods)) for _ in clinics)
    + (INK,) * (2 * n_clinics * len(periods)),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    opacity=0.7,
    opacity_hover=0.9,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="violin-split · python · pygal · anyplot.ai",
    x_title=CLINIC,
    y_title=RECOVERY,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=(3 * n_clinics * len(periods)) // 2
    + 1,  # one legend row: the unlabeled series would add empty rows
    truncate_legend=-1,
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    range=VALUE_RANGE,
    xrange=(0, n_clinics + 1.5),
    margin=40,
)

violin_width = 0.38
n_points = 80
marker_width = 0.04
marker_offset = 0.08

violins = {period: [] for period in periods}
markers = {period: [] for period in periods}

for i, clinic in enumerate(clinics):
    center_x = i + 1.25
    for j, period in enumerate(periods):
        side = -1 if j == 0 else 1  # first group on the left, second on the right
        values = df.loc[(df[CLINIC] == clinic) & (df[PERIOD] == period), RECOVERY].dropna().to_numpy()
        if len(values) < 2:
            continue

        # Gaussian KDE with Silverman's rule
        padding = (values.max() - values.min()) * 0.15
        y_grid = np.linspace(values.min() - padding, values.max() + padding, n_points)
        q1, median, q3 = np.percentile(values, [25, 50, 75])
        bandwidth = 0.9 * min(values.std(), (q3 - q1) / 1.34) * len(values) ** (-0.2)
        density = np.exp(-0.5 * ((y_grid[:, None] - values[None, :]) / bandwidth) ** 2).sum(axis=1)
        density = density / density.max() * violin_width

        outline = [(center_x + side * d, y) for y, d in zip(y_grid, density, strict=True)]
        violins[period].append([(center_x, y_grid[0]), *outline, (center_x, y_grid[-1]), (center_x, y_grid[0])])
        markers[period].append((center_x + side * marker_offset, q1, median, q3))

# Half violins: one legend entry per group, same color in every category
for period in periods:
    for k, shape in enumerate(violins[period]):
        chart.add(period if k == 0 else None, shape, show_dots=False)

# Quartile markers in ink: IQR line and median tick per half, no legend entries
for period in periods:
    for x, q1, median, q3 in markers[period]:
        chart.add(None, [(x, q1), (x, q3)], stroke=True, fill=False, show_dots=False, stroke_style={"width": 6})
        chart.add(
            None,
            [(x - marker_width, median), (x + marker_width, median)],
            stroke=True,
            fill=False,
            show_dots=False,
            stroke_style={"width": 8},
        )

chart.x_labels = (
    [{"value": 0, "label": ""}]
    + [{"value": i + 1.25, "label": clinic} for i, clinic in enumerate(clinics)]
    + [{"value": n_clinics + 1.5, "label": ""}]
)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
