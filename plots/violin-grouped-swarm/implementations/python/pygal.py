""" anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: pygal 3.1.3 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TASK = "Task Type"  # role: category
LEVEL = "Expertise"  # role: group
RESPONSE = "Response Time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
means = {
    "Simple": {"Novice": (450, 80), "Expert": (280, 50)},
    "Medium": {"Novice": (850, 150), "Expert": (520, 90)},
    "Complex": {"Novice": (1400, 250), "Expert": (780, 120)},
}
rows = []
for task, levels in means.items():
    for level, (mu, sigma) in levels.items():
        for value in np.clip(np.random.normal(mu, sigma, 40), 100, 2000):
            rows.append({TASK: task, LEVEL: level, RESPONSE: value})
df = pd.DataFrame(rows)


# Plot: reads only df and the constants above
tasks = df[TASK].dropna().unique().tolist()
levels = df[LEVEL].dropna().unique().tolist()
slot = 0.9 / len(levels)
half_width = slot * 0.4
n_grid = 60

violins = {level: [] for level in levels}
swarms = {level: [] for level in levels}
for i, task in enumerate(tasks):
    for j, level in enumerate(levels):
        values = df.loc[(df[TASK] == task) & (df[LEVEL] == level), RESPONSE].dropna().to_numpy(dtype=float)
        if len(values) == 0:
            continue
        center_x = i + 1 + (j - (len(levels) - 1) / 2) * slot

        v_min, v_max = values.min(), values.max()
        padding = (v_max - v_min) * 0.15 if v_max > v_min else max(abs(v_max) * 0.05, 1.0)
        grid = np.linspace(v_min - padding, v_max + padding, n_grid)
        if np.ptp(values) > 0 and len(values) > 1:
            density = gaussian_kde(values, bw_method="silverman")(grid)
        else:
            density = np.exp(-0.5 * ((grid - v_min) / padding) ** 2)
        density = density / density.max() * half_width

        left = [(center_x - d, y) for y, d in zip(grid, density, strict=True)]
        right = [(center_x + d, y) for y, d in zip(grid[::-1], density[::-1], strict=True)]
        violins[level].append(left + right + [left[0]])

        # Swarm: points in the same value bin spread sideways, scaled to the local violin width
        bin_edges = np.linspace(v_min, v_max, 16)
        bin_ids = np.digitize(values, bin_edges[1:-1])
        swarm_x = np.full(len(values), center_x)
        for b in np.unique(bin_ids):
            members = np.flatnonzero(bin_ids == b)
            members = members[np.argsort(values[members])]
            local_half = np.interp(values[members].mean(), grid, density) * 0.75
            if len(members) > 1:
                swarm_x[members] = center_x + np.linspace(-local_half, local_half, len(members))
        swarms[level].append(list(zip(swarm_x.tolist(), values.tolist(), strict=True)))

# Series order: per group, one violin series then one swarm series
series_colors = [IMPRINT_PALETTE[j] for j in range(len(levels)) for _ in range(2)]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    colors=tuple(series_colors),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=56,
    legend_font_size=48,
    value_font_size=36,
    opacity=0.45,
    opacity_hover=0.6,
    stroke_width=2.5,
)

top = max(y for shapes in violins.values() for shape in shapes for _, y in shape) * 1.03
x_lo, x_hi = 0.4, len(tasks) + 0.6
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="violin-grouped-swarm · python · pygal · anyplot.ai",
    x_title=TASK,
    y_title=RESPONSE,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=max(len(levels), 8),
    legend_box_size=40,
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    range=(0, top),
    xrange=(x_lo, x_hi),
    margin=50,
    margin_bottom=110,
)

# One interrupted series per group keeps the legend to one entry per group. pygal
# closes a filled series down to the zero line at its first and last point, so
# the series opens and ends on an anchor left of the plot area, where it is clipped.
anchor = [(x_lo - 1.0, 0.0)]
for level in levels:
    outline = anchor.copy()
    for violin in violins[level]:
        outline += [(None, None)] + violin
    outline += [(None, None)] + anchor
    chart.add(str(level), outline, show_dots=False, allow_interruptions=True)
    points = [p for swarm in swarms[level] for p in swarm]
    chart.add(None, points, stroke=False, fill=False, show_dots=True, dots_size=6)

chart.x_labels = [{"value": i + 1, "label": str(task)} for i, task in enumerate(tasks)]

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
