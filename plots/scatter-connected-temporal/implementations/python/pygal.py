"""anyplot.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: pygal 3.1.3 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
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
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# imprint_seq, the sequential Imprint colormap: brand green (early) to blue (late)
SEQ_EARLY, SEQ_LATE = "#009E73", "#4467A3"

# Columns: set these to your table's column names
URBAN = "Urban population (% of total)"  # role: x
FERTILITY = "Fertility rate (births per woman)"  # role: y
YEAR = "Year"  # role: time

# Data: replace this block with your own table, for example df = pd.read_csv("country.csv")
# Fertility against urbanisation for an emerging economy, 1980-2023
np.random.seed(42)
urban_step = np.random.normal(0.95, 0.3, 44)
urban_step[20:25] = np.random.normal(-0.9, 0.15, 5)  # 2000-2004: a rural return reverses urbanisation
fertility_step = np.random.normal(-0.075, 0.03, 44)
fertility_step[20:25] += 0.11  # fertility climbs back with it, so the path turns back on itself
fertility_step[34:38] += 0.16  # 2014-2017: a pronatalist rebound
df = pd.DataFrame(
    {
        YEAR: range(1980, 2024),
        URBAN: 28 + np.cumsum(urban_step),
        FERTILITY: np.clip(5.6 + np.cumsum(fertility_step), 1.2, 7.0),
    }
)

# Plot: the path in time order, split into five consecutive eras coloured along imprint_seq
path = df.dropna(subset=[YEAR, URBAN, FERTILITY]).sort_values(YEAR).reset_index(drop=True)
xs, ys, times = path[URBAN].astype(float).to_numpy(), path[FERTILITY].astype(float).to_numpy(), path[YEAR].tolist()
n = len(path)
eras = [chunk for chunk in np.array_split(np.arange(n), min(5, max(n - 1, 1))) if len(chunk)]
era_colors = []
for t in np.linspace(0, 1, len(eras)) if len(eras) > 1 else [0.0]:
    rgb = [round(int(SEQ_EARLY[k : k + 2], 16) * (1 - t) + int(SEQ_LATE[k : k + 2], 16) * t) for k in (1, 3, 5)]
    era_colors.append(f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")

x_lo, x_hi = np.floor(xs.min() / 5) * 5, np.ceil(xs.max() / 5) * 5
y_lo, y_hi = np.floor(ys.min() * 2) / 2, np.ceil(ys.max() * 2) / 2
px_x, px_y = 2900 / max(x_hi - x_lo, 1e-9), 1420 / max(y_hi - y_lo, 1e-9)  # about the plot area's pixels per unit

# Time labels on six evenly spaced points, start and end included: each takes the closest spot, across
# or beside the path, whose box keeps clear of every marker and segment
label_size = 44
screen = np.column_stack([xs * px_x, -ys * px_y])  # in px, y pointing down
samples = np.vstack([np.linspace(a, b, 8) for a, b in zip(screen[:-1], screen[1:], strict=True)] or [screen])
labels = []
for i in sorted({int(round(k)) for k in np.linspace(0, n - 1, min(6, n))}):
    text = f"{times[i]} (start)" if i == 0 else f"{times[i]} (end)" if i == n - 1 else f"{times[i]}"
    half_w, half_h = 0.3 * label_size * len(text), 0.4 * label_size
    tangent = screen[min(i + 1, n - 1)] - screen[max(i - 1, 0)]
    normal = np.array([-tangent[1], tangent[0]]) / (np.hypot(*tangent) or 1.0)
    best, best_room = screen[i], -np.inf
    for gap in (26, 44, 70):
        for direction in (normal, -normal, np.array([1.0, 0.0]), np.array([-1.0, 0.0])):
            centre = screen[i] + direction * (gap + abs(direction[0]) * half_w + abs(direction[1]) * half_h)
            # clearance between the label box and the sampled path, less a marker's radius and a margin
            room = np.min(np.maximum(np.abs(samples - centre) - [half_w, half_h], 0).max(axis=1)) - 16
            # and the box stays inside the plot area, clear of the title
            inside = min(
                centre[0] - half_w - x_lo * px_x,
                x_hi * px_x - centre[0] - half_w,
                centre[1] - half_h + y_hi * px_y,
                -y_lo * px_y - centre[1] - half_h,
            )
            room = min(room, inside)
            if room > best_room:
                best, best_room = centre, room
        if best_room > 0:
            break
    labels.append({"value": (best[0] / px_x, -(best[1] + 0.35 * label_size) / px_y), "label": text})

title = "Fertility vs Urbanization · scatter-connected-temporal · python · pygal · anyplot.ai"
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    # series order: the eras, the start and end markers, the time labels
    colors=(*era_colors, era_colors[0], era_colors[-1], INK),
    value_colors=(INK,) * (len(eras) + 3),
    guide_stroke_color=RULE,
    major_guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_dasharray="none",
    font_family=font,
    title_font_family=font,
    title_font_size=max(44, round(66 * 67 / len(title))),  # the long title shrinks from the 67-character default
    label_font_size=46,
    major_label_font_size=46,
    legend_font_size=44,
    value_font_size=0,
    value_label_font_size=label_size,
    tooltip_font_size=36,
    tooltip_font_family=font,
    opacity=1,
    opacity_hover=1,
    stroke_width=5,
    stroke_opacity=1,
    stroke_opacity_hover=1,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=URBAN,
    y_title=FERTILITY,
    xrange=(x_lo, x_hi),
    range=(y_lo, y_hi),
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(eras),
    legend_box_size=40,
    truncate_legend=-1,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda share: f"{share:.0f}%",
    value_formatter=lambda rate: f"{rate:.1f}",
    print_labels=True,
    spacing=24,
    margin=40,
    css=[
        "file://style.css",
        "file://graph.css",
        f"inline:.serie-{len(eras) + 2} text.label {{ text-anchor: middle; }}",
    ],
)

# Each era runs into the first point of the next, so the path stays one unbroken line
for chunk in eras:
    stop = min(chunk[-1] + 2, n)
    era_points = list(zip(xs[chunk[0] : stop], ys[chunk[0] : stop], strict=True))
    chart.add(f"{times[chunk[0]]}–{times[chunk[-1]]}", era_points, dots_size=10)
chart.add(None, [(xs[0], ys[0])], stroke=False, show_dots=True, dots_size=22)
chart.add(None, [(xs[-1], ys[-1])], stroke=False, show_dots=True, dots_size=22)
chart.add(None, labels, stroke=False, show_dots=True, dots_size=0)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
