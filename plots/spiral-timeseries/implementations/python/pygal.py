""" anyplot.ai
spiral-timeseries: Spiral Time Series Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 84/100 | Created: 2026-05-07
"""

import datetime
import importlib
import math
import os
import sys
import xml.etree.ElementTree as ET


# Remove the script's own directory from sys.path so importlib resolves
# "pygal" to the installed package, not this file (same package name).
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _this_dir]

np = importlib.import_module("numpy")
pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style
cairosvg = importlib.import_module("cairosvg")
mcm = importlib.import_module("matplotlib.cm")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data — daily average temperatures over 5 years (Northern Hemisphere city)
np.random.seed(42)
n_years = 5
days_per_year = 365
n_points = n_years * days_per_year

day_indices = np.arange(n_points)
year_idx = day_indices // days_per_year
day_of_year = day_indices % days_per_year

annual_mean = 12.0  # °C
amplitude = 13.0  # °C seasonal amplitude
temp = (
    annual_mean
    + amplitude * np.cos(2 * np.pi * day_of_year / days_per_year + np.pi)
    + np.random.normal(0, 2.5, n_points)
    + year_idx * 0.4  # subtle multi-year warming trend
)

# Archimedean spiral geometry
base_r = 3.0
rev_gap = 2.5
temp_scale = 0.5  # radial deviation amplitude
t_norm = (temp - annual_mean) / (amplitude + 3.0)

theta = 2 * np.pi * day_of_year / days_per_year - math.pi / 2
radius = base_r + year_idx * rev_gap + temp_scale * t_norm
x_coords = (radius * np.cos(theta)).tolist()
y_coords = (radius * np.sin(theta)).tolist()

# Viridis colormap — 12 temperature buckets for continuous encoding
T_MIN = float(np.percentile(temp, 1))
T_MAX = float(np.percentile(temp, 99))
N_BUCKETS = 12
bucket_edges = np.linspace(T_MIN, T_MAX, N_BUCKETS + 1)


def to_viridis_hex(t):
    r, g, b, _ = mcm.viridis(t)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


bucket_colors = tuple(to_viridis_hex(i / (N_BUCKETS - 1)) for i in range(N_BUCKETS))
bucket_idx = np.clip(np.digitize(temp, bucket_edges[1:]), 0, N_BUCKETS - 1)

# Per-bucket series with year boundary breaks to prevent cross-ring diagonals
base_date = datetime.date(2019, 1, 1)
# Allocate n_points + n_years slots (each year gets a trailing None separator)
bucket_series = [[None] * (n_points + n_years) for _ in range(N_BUCKETS)]
offset = 0
for y in range(n_years):
    for d in range(days_per_year):
        i = y * days_per_year + d
        b = int(bucket_idx[i])
        date_str = (base_date + datetime.timedelta(days=i)).strftime("%b %d, %Y")
        bucket_series[b][offset + d] = {"value": (x_coords[i], y_coords[i]), "label": f"{date_str}: {temp[i]:.1f}°C"}
    offset += days_per_year + 1  # +1 leaves a None gap at year boundary

# Spoke geometry
outer_r = base_r + (n_years - 1) * rev_gap + temp_scale + 1.5  # ~15.0
label_r = outer_r + 1.2  # beyond outer ring, for month text anchors

month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Month radial spokes
spoke_points = []
for m in range(12):
    th = 2 * math.pi * m / 12 - math.pi / 2
    spoke_points.append({"value": (0.0, 0.0)})
    spoke_points.append({"value": (outer_r * math.cos(th), outer_r * math.sin(th))})
    if m < 11:
        spoke_points.append(None)

start_year = 2019

# pygal Style — buckets + spokes
all_colors = bucket_colors + (INK_MUTED,)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=all_colors,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=14,
    value_font_size=22,
    stroke_width=3,
)

chart = pygal.XY(
    style=custom_style,
    width=3600,
    height=3600,
    title="spiral-timeseries · pygal · anyplot.ai",
    show_dots=False,
    stroke=True,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
)

# Temperature-colored spiral arcs (viridis colormap)
for b in range(N_BUCKETS):
    t_low = bucket_edges[b]
    t_high = bucket_edges[b + 1]
    chart.add(f"{t_low:.0f}–{t_high:.0f}°C", bucket_series[b])

# Month guide spokes
chart.add("Month grid", spoke_points)

# --- SVG post-processing: inject permanent month and year text labels ---
svg_bytes = chart.render()
svg_str = svg_bytes.decode("utf-8")

# Register SVG namespace to preserve structure
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

root = ET.fromstring(svg_str)
ns = {"svg": "http://www.w3.org/2000/svg"}
svg_w = float(root.get("width", 3600))
svg_h = float(root.get("height", 3600))

# Estimate plot area from pygal's layout:
# title ~90px, bottom legend ~130px, side margins ~60px
margin_top = 90
margin_bottom = 140
margin_side = 60
plot_w = svg_w - 2 * margin_side
plot_h = svg_h - margin_top - margin_bottom

# Data bounds — use the actual chart data range (spiral + spokes, not label anchors)
all_x = x_coords + [outer_r * math.cos(2 * math.pi * m / 12 - math.pi / 2) for m in range(12)]
all_y = y_coords + [outer_r * math.sin(2 * math.pi * m / 12 - math.pi / 2) for m in range(12)]
data_xmin, data_xmax = min(all_x), max(all_x)
data_ymin, data_ymax = min(all_y), max(all_y)
# Add a small margin (pygal pads the axes)
pad = 0.05
dx = (data_xmax - data_xmin) * pad
dy = (data_ymax - data_ymin) * pad
data_xmin -= dx
data_xmax += dx
data_ymin -= dy
data_ymax += dy


def data_to_svg(dx_val, dy_val):
    sx = margin_side + (dx_val - data_xmin) / (data_xmax - data_xmin) * plot_w
    # SVG y-axis is inverted
    sy = margin_top + (1 - (dy_val - data_ymin) / (data_ymax - data_ymin)) * plot_h
    return sx, sy


# Inject month labels as SVG <text> elements
svg_ns = "http://www.w3.org/2000/svg"
for m in range(12):
    th = 2 * math.pi * m / 12 - math.pi / 2
    mx = label_r * math.cos(th)
    my = label_r * math.sin(th)
    sx, sy = data_to_svg(mx, my)
    text_el = ET.SubElement(root, f"{{{svg_ns}}}text")
    text_el.set("x", f"{sx:.1f}")
    text_el.set("y", f"{sy:.1f}")
    text_el.set("text-anchor", "middle")
    text_el.set("dominant-baseline", "middle")
    text_el.set("font-size", "44")
    text_el.set("font-family", "sans-serif")
    text_el.set("fill", INK_SOFT)
    text_el.text = month_names[m]

# Inject year-start labels at Jan 1 of each ring
for y in range(n_years):
    th = -math.pi / 2  # Jan 1 = 12-o'clock
    r = base_r + y * rev_gap
    lx = r * math.cos(th) + 0.6  # slight rightward offset from vertical axis
    ly = r * math.sin(th) - 0.2
    sx, sy = data_to_svg(lx, ly)
    text_el = ET.SubElement(root, f"{{{svg_ns}}}text")
    text_el.set("x", f"{sx:.1f}")
    text_el.set("y", f"{sy:.1f}")
    text_el.set("text-anchor", "start")
    text_el.set("dominant-baseline", "middle")
    text_el.set("font-size", "44")
    text_el.set("font-family", "sans-serif")
    text_el.set("font-weight", "bold")
    text_el.set("fill", INK)
    text_el.text = str(start_year + y)

modified_svg = ET.tostring(root, encoding="unicode", xml_declaration=False)
modified_svg_bytes = ("<?xml version='1.0' encoding='utf-8'?>\n" + modified_svg).encode("utf-8")

# Save PNG (from modified SVG) and interactive HTML (original with hover labels)
cairosvg.svg2png(bytestring=modified_svg_bytes, write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(svg_bytes)
