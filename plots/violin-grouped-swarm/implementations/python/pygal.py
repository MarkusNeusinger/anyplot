"""anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
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
def compute_kde(values, grid):
    """Gaussian KDE with Silverman's rule bandwidth."""
    n = len(values)
    std = np.std(values)
    iqr = np.percentile(values, 75) - np.percentile(values, 25)
    spread = min(std, iqr / 1.34) if iqr > 0 else std
    bandwidth = 0.9 * spread * n ** (-0.2) if spread > 0 else 1.0
    density = np.exp(-0.5 * ((grid[:, None] - values[None, :]) / bandwidth) ** 2).sum(axis=1)
    return density / (n * bandwidth * np.sqrt(2 * np.pi))


def compute_swarm_positions(values, center_x, width):
    """Spread points sideways within value bins so they do not stack."""
    order = np.argsort(values)
    positions = np.full(len(values), center_x, dtype=float)
    sorted_values = values[order]
    value_span = sorted_values[-1] - sorted_values[0]
    bin_height = value_span / 15 if value_span > 0 else 1.0
    bins = []
    bin_start = sorted_values[0]
    for idx, v in zip(order, sorted_values, strict=True):
        if not bins or v - bin_start > bin_height:
            bins.append([])
            bin_start = v
        bins[-1].append(idx)
    for members in bins:
        offsets = np.linspace(-width / 2, width / 2, len(members)) if len(members) > 1 else [0.0]
        for idx, off in zip(members, offsets, strict=True):
            positions[idx] = center_x + off
    return positions


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
        density = compute_kde(values, grid)
        density = density / density.max() * half_width

        left = [(center_x - d, y) for y, d in zip(grid, density, strict=True)]
        right = [(center_x + d, y) for y, d in zip(grid[::-1], density[::-1], strict=True)]
        violins[level].append(left + right + [left[0]])

        swarm_x = compute_swarm_positions(values, center_x, width=half_width * 0.7)
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
    major_label_font_size=44,
    legend_font_size=44,
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
    legend_at_bottom_columns=len(levels),
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    range=(0, top),
    xrange=(x_lo, x_hi),
    margin=50,
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
