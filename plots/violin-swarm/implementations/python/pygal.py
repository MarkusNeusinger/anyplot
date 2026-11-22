""" anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: pygal 3.1.3 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-22
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
TEMPERATURE = "Incubation temperature"  # role: category
ACTIVITY = "Enzyme activity (µmol/min)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("enzyme.csv")
rng = np.random.default_rng(7)
df = pd.DataFrame(
    {
        TEMPERATURE: ["15 °C"] * 50 + ["25 °C"] * 50 + ["37 °C"] * 50 + ["50 °C"] * 50,
        ACTIVITY: np.concatenate(
            [
                rng.normal(18, 3.5, 50),
                rng.normal(33, 5.5, 50),
                rng.normal(52, 6, 50),
                np.concatenate([rng.normal(40, 5, 30), rng.normal(14, 4, 20)]),
            ]
        ).clip(min=1),
    }
)

# Plot: reads only df and the constants above
groups = list(dict.fromkeys(df[TEMPERATURE]))
n_groups = len(groups)
half_width = 0.4  # widest half of a violin, in category units
point_gap_x = 0.05  # sideways spacing between neighbouring swarm points
value_span = df[ACTIVITY].max() - df[ACTIVITY].min()
point_gap_y = value_span / 45  # points closer than this in value must sit side by side

violins = []
swarm = []
for i, group in enumerate(groups):
    values = df.loc[df[TEMPERATURE] == group, ACTIVITY].to_numpy()
    centre = i + 1

    # Gaussian KDE with Silverman's bandwidth, evaluated only across the data range
    iqr = np.subtract(*np.percentile(values, [75, 25]))
    bandwidth = 0.9 * min(values.std(), iqr / 1.34) * len(values) ** -0.2
    grid = np.linspace(values.min(), values.max(), 80)
    density = np.exp(-0.5 * ((grid[:, None] - values[None, :]) / bandwidth) ** 2).sum(axis=1)
    density = density / density.max() * half_width

    outline = [(centre - d, y) for y, d in zip(grid, density, strict=True)]
    outline += [(centre + d, y) for y, d in zip(grid[::-1], density[::-1], strict=True)]
    violins.append(outline + outline[:1])

    # Swarm: each point takes the smallest sideways offset that clears its lower neighbours
    placed = []
    for y in np.sort(values):
        limit = np.interp(y, grid, density) * 0.92
        for k in range(200):
            offset = ((k + 1) // 2) * point_gap_x * (1 if k % 2 else -1)
            if abs(offset) > limit:
                offset = 0.0 if k == 0 else np.clip(offset, -limit, limit)
            if all(abs(offset - ox) >= point_gap_x or abs(y - oy) >= point_gap_y for ox, oy in placed):
                break
        placed.append((offset, y))
    swarm.append([(centre + ox, oy) for ox, oy in placed])

# Violin fills take palette positions in order; swarm dots share one chrome-contrast ink
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE) * 2 + (INK,) * len(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    opacity=0.4,
    opacity_hover=0.4,
    stroke_width=3,
)

pad = value_span * 0.06
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="violin-swarm · python · pygal · anyplot.ai",
    x_title=TEMPERATURE,
    y_title=ACTIVITY,
    show_legend=False,
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    range=(float(df[ACTIVITY].min() - pad), float(df[ACTIVITY].max() + pad)),
    xrange=(0.4, n_groups + 0.6),
    margin=60,
    css=(
        "file://style.css",
        "file://graph.css",
        "inline:.serie-0 path,.serie-1 path,.serie-2 path,.serie-3 path,"
        ".serie-4 path,.serie-5 path,.serie-6 path,.serie-7 path{stroke:none}",
    ),
)
chart.x_labels = [{"value": i + 1, "label": str(group)} for i, group in enumerate(groups)]

# pygal closes a filled path down to the baseline and strokes that closing edge too, so each
# violin is a fill series (stroke removed in CSS) plus a stroke-only outline series. Series
# slots 0-7 hold the fills and 8-15 the outlines, one slot per palette colour, so the CSS rule
# above can name the fill slots; slots beyond the groups stay empty.
for slot in range(len(IMPRINT_PALETTE)):
    chart.add(None, violins[slot] if slot < n_groups else [], stroke=True, fill=True, show_dots=False)
for slot in range(len(IMPRINT_PALETTE)):
    chart.add(None, violins[slot] if slot < n_groups else [], stroke=True, fill=False, show_dots=False)
for points in swarm:
    chart.add(None, points, stroke=False, fill=False, show_dots=True, dots_size=11)

# Save outputs with theme-suffixed filenames
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
