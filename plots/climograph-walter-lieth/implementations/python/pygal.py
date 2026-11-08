""" anyplot.ai
climograph-walter-lieth: Walter-Lieth Climate Diagram
Library: pygal 3.1.3 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-08
"""

import os
import sys


# Prevent the local pygal.py from shadowing the installed pygal package
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
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

# Columns: set these to your table's column names
MONTH = "Month"  # role: month
TEMPERATURE = "Temperature (°C)"  # role: temperature
PRECIPITATION = "Precipitation (mm)"  # role: precipitation
STATION = "Station"  # role: station_name
ELEVATION = "Elevation (m)"  # role: elevation

# Data: replace this block with your own table, for example df = pd.read_csv("station_normals.csv")
# Athens, Greece — Mediterranean Csa (1991-2020 normals)
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        TEMPERATURE: [9.3, 10.3, 12.4, 16.3, 21.0, 26.1, 28.7, 28.5, 24.1, 19.2, 14.3, 10.7],
        PRECIPITATION: [48, 36, 33, 23, 17, 7, 6, 5, 11, 46, 54, 57],
        STATION: "Athens, Greece",
        ELEVATION: 107,
    }
)

# Plot: both curves on the temperature scale, precipitation divided by MM_PER_DEGREE
months = df[MONTH].astype(str).tolist()
temp = df[TEMPERATURE].to_numpy(dtype=float, na_value=np.nan)
precip = df[PRECIPITATION].to_numpy(dtype=float, na_value=np.nan)
precip_scaled = precip / MM_PER_DEGREE
month_x = np.arange(1, len(df) + 1)  # month numbers; no tick at 0, so pygal draws its left spine
station = df[STATION].iloc[0]
elevation = df[ELEVATION].iloc[0]
temp_annual = np.nanmean(temp)
precip_annual = np.nansum(precip)

# Fill polygons between the straight month-to-month segments, split exactly where the curves cross;
# months missing either value are left out of the fills
valid = ~(np.isnan(temp) | np.isnan(precip))
fx, ft, fp = month_x[valid], temp[valid], precip_scaled[valid]
diff = fp - ft
xs = [fx[0]]
for i in range(len(fx) - 1):
    if diff[i] * diff[i + 1] < 0:
        xs.append(fx[i] + diff[i] / (diff[i] - diff[i + 1]))
    xs.append(fx[i + 1])
xs = np.array(xs)
t_at, p_at = np.interp(xs, fx, ft), np.interp(xs, fx, fp)
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
bottom = min(0.0, np.floor(min(np.nanmin(temp), np.nanmin(precip_scaled)) / 10) * 10)
top = max(35.0, np.ceil(max(np.nanmax(temp), np.nanmax(precip_scaled)) / 10) * 10 + 5)
temp_ticks = list(range(int(bottom), int(top), 10))
precip_range = (MM_PER_DEGREE * temp_ticks[0], MM_PER_DEGREE * temp_ticks[-1])

title = (
    "climograph-walter-lieth · python · pygal · anyplot.ai\n"
    f"{station} · {elevation} m a.s.l. · mean {temp_annual:.1f} °C · total {precip_annual:.0f} mm"
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
# The two curves follow the polygons: their legend boxes become opaque line strokes, centred in the box
curve_legends = ", ".join(f"#activate-serie-{i} rect" for i in (len(polygons), len(polygons) + 1))
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=MONTH,
    y_title=TEMPERATURE,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=40,
    truncate_legend=-1,
    show_x_guides=False,
    show_y_guides=True,
    xrange=(month_x[0] - 0.4, month_x[-1] + 0.4),
    range=(bottom, top),
    secondary_range=precip_range,
    value_formatter=lambda v: f"{v:g} mm",  # the right axis; the left ticks carry their own labels
    margin=40,
    spacing=24,
    css=(
        "file://style.css",
        "file://graph.css",
        f"inline:{polygon_lines} {{ stroke-width: 0 !important; }}",
        f"inline:{curve_legends} {{ height: 8px; transform: translate(0px, 16px); fill-opacity: 1 !important; }}",
        "inline:.axis.y .guides text { transform: translate(-14px, 0px); }",  # clear the right-aligned labels off the spine
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
# A missing month becomes a gap in its curve
chart.add(
    f"{TEMPERATURE}, left axis",
    [(x, None if np.isnan(t) else t) for x, t in zip(month_x, temp, strict=True)],
    dots_size=8,
    formatter=lambda p: f"{p[1]:.1f} °C",
)
chart.add(
    f"{PRECIPITATION}, right axis",
    [(x, None if np.isnan(p) else p) for x, p in zip(month_x, precip, strict=True)],
    secondary=True,
    dots_size=8,
    formatter=lambda p: f"{p[1]:.0f} mm",
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
