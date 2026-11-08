""" anyplot.ai
climograph-walter-lieth: Walter-Lieth Climate Diagram
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Created: 2026-06-15
"""

import os
import sys


# Prevent the local pygal.py from shadowing the installed pygal package
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Semantic color exception: precipitation = blue (water), temperature = red (heat)
PRECIP_COLOR = "#4467A3"
TEMP_COLOR = "#AE3030"

# Walter-Lieth convention: 10 °C on the temperature axis lines up with 20 mm on the precipitation axis
MM_PER_DEGREE = 2

# Station: Athens, Greece — Mediterranean Csa (1991-2020 normals)
station = "Athens, Greece"
elevation = 107
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
temp_c = [9.3, 10.3, 12.4, 16.3, 21.0, 26.1, 28.7, 28.5, 24.1, 19.2, 14.3, 10.7]
precip_mm = [48, 36, 33, 23, 17, 7, 6, 5, 11, 46, 54, 57]

# Plot: both curves on the temperature scale, precipitation divided by MM_PER_DEGREE
temp = np.array(temp_c)
precip_scaled = np.array(precip_mm) / MM_PER_DEGREE
month_x = np.arange(1, len(months) + 1)  # month numbers; no tick at 0, so pygal draws its left spine
temp_annual = temp.mean()
precip_annual = sum(precip_mm)

# Fill polygons between the straight month-to-month segments, split exactly where the curves cross
diff = precip_scaled - temp
xs = [month_x[0]]
for i in range(len(months) - 1):
    if diff[i] * diff[i + 1] < 0:
        xs.append(month_x[i] + diff[i] / (diff[i] - diff[i + 1]))
    xs.append(month_x[i + 1])
xs = np.array(xs)
t_at, p_at = np.interp(xs, month_x, temp), np.interp(xs, month_x, precip_scaled)
humid_segment = (p_at[:-1] + p_at[1:]) > (t_at[:-1] + t_at[1:])

polygons = []  # (humid, points): upper curve forward, lower curve back
start = 0
for k in range(1, len(humid_segment) + 1):
    if k == len(humid_segment) or humid_segment[k] != humid_segment[start]:
        upper, lower = (p_at, t_at) if humid_segment[start] else (t_at, p_at)
        idx = list(range(start, k + 1))
        points = [(xs[j], upper[j]) for j in idx] + [(xs[j], lower[j]) for j in idx[::-1]]
        polygons.append((bool(humid_segment[start]), points))
        start = k

# Axes: temperature ticks every 10 °C on the left, the matching mm ticks on the right
top = max(35.0, np.ceil(max(temp.max(), precip_scaled.max()) / 10) * 10 + 5)
temp_ticks = list(range(0, int(top), 10))
precip_range = (MM_PER_DEGREE * temp_ticks[0], MM_PER_DEGREE * temp_ticks[-1])

title = (
    "climograph-walter-lieth · python · pygal · anyplot.ai\n"
    f"{station} · {elevation} m a.s.l. · mean {temp_annual:.1f} °C · total {precip_annual} mm"
)

polygon_colors = tuple(PRECIP_COLOR if humid else TEMP_COLOR for humid, _ in polygons)
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(*polygon_colors, TEMP_COLOR, PRECIP_COLOR),
    opacity=0.45 if THEME == "light" else 0.6,  # the period fills; the curves stay opaque
    opacity_hover=0.75,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=5,
    guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_color=RULE,
    major_guide_stroke_dasharray="none",
    title_font_size=56,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=42,
    tooltip_font_size=36,
)

polygon_lines = ", ".join(f".serie-{i} .line" for i in range(len(polygons)))
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title="Month",
    y_title="Temperature (°C)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=40,
    truncate_legend=-1,
    show_x_guides=False,
    show_y_guides=True,
    xrange=(month_x[0] - 0.4, month_x[-1] + 0.4),
    range=(0, top),
    secondary_range=precip_range,
    value_formatter=lambda v: f"{v:g} mm",  # the right axis; the left ticks carry their own labels
    margin=40,
    spacing=24,
    css=(
        "file://style.css",
        "file://graph.css",
        f"inline:{polygon_lines} {{ stroke-width: 0 !important; }}",
        "inline:.titles text.plot_title { font-weight: bold; }",
        "inline:.titles text.plot_title + text.plot_title { font-weight: normal; font-size: 46px; }",
    ),
)
# With a secondary axis pygal draws the last x tick's guide as a solid line: an unlabelled last tick at the
# right edge makes that line the right axis instead of a stray line through December
chart.x_labels = [{"value": int(x), "label": label} for x, label in zip(month_x, months, strict=True)] + [
    {"value": month_x[-1] + 0.4, "label": ""}
]
chart.y_labels = [{"value": t, "label": f"{t} °C"} for t in temp_ticks]

# Period fills first, so the curves are drawn on top; only the first polygon of each kind is in the legend
seen = set()
for humid, points in polygons:
    name = "Humid period (P above T)" if humid else "Arid period (T above P)"
    chart.add(None if name in seen else name, points, fill=True, show_dots=False)
    seen.add(name)
chart.add(
    "Temperature (°C, left axis)",
    list(zip(month_x, temp, strict=True)),
    dots_size=8,
    formatter=lambda p: f"{p[1]:.1f} °C",
)
chart.add(
    "Precipitation (mm, right axis)",
    list(zip(month_x, precip_mm, strict=True)),
    secondary=True,
    dots_size=8,
    formatter=lambda p: f"{p[1]:.0f} mm",
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
