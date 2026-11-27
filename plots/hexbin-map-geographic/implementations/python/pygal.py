"""anyplot.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: pygal 3.1.3 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-26
"""

import math
import os
import re

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette (categorical, canonical order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# imprint_seq, fields (hexagon cells fill the map): stops low -> high density
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in zip(stops[:-1], stops[1:], strict=True) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Constants
N_BINS = 5  # density classes in the color legend
GRID_COLUMNS = 22  # hexagon columns across the map: detail vs. aggregation
# Coarse outline of California: coast, Oregon border, Nevada border, Colorado River, Mexico border
CALIFORNIA_OUTLINE = [
    (-124.21, 41.99),
    (-120.00, 42.00),
    (-120.00, 39.00),
    (-114.63, 35.00),
    (-114.57, 34.80),
    (-114.14, 34.30),
    (-114.43, 34.08),
    (-114.53, 33.93),
    (-114.50, 33.50),
    (-114.72, 33.40),
    (-114.70, 33.03),
    (-114.72, 32.72),
    (-117.12, 32.53),
    (-117.25, 32.75),
    (-117.28, 33.00),
    (-117.40, 33.20),
    (-117.70, 33.45),
    (-118.10, 33.75),
    (-118.42, 33.73),
    (-118.50, 34.03),
    (-118.80, 34.02),
    (-119.20, 34.15),
    (-119.70, 34.40),
    (-120.47, 34.45),
    (-120.65, 34.60),
    (-120.65, 35.15),
    (-120.90, 35.45),
    (-121.30, 35.70),
    (-121.90, 36.30),
    (-121.95, 36.60),
    (-121.80, 36.80),
    (-122.00, 36.95),
    (-122.40, 37.20),
    (-122.50, 37.50),
    (-122.50, 37.80),
    (-122.95, 38.00),
    (-123.00, 38.30),
    (-123.70, 38.90),
    (-123.80, 39.50),
    (-123.85, 40.00),
    (-124.40, 40.45),
    (-124.10, 41.00),
    (-124.15, 41.70),
    (-124.21, 41.99),
]

# Columns: set these to your table's column names
LAT = "Latitude (°)"  # role: lat
LON = "Longitude (°)"  # role: lon
FRP = "Fire radiative power (MW)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("detections.csv")
# Satellite wildfire hotspot detections in California around five fire-prone regions
rng = np.random.default_rng(42)
regions = [  # (lat, lon, lat spread, lon spread, share of detections, mean power in MW)
    (39.80, -121.40, 0.22, 0.20, 0.26, 28.0),  # Butte / Plumas foothills
    (41.30, -122.90, 0.25, 0.28, 0.20, 22.0),  # Klamath / Siskiyou
    (36.00, -118.60, 0.30, 0.22, 0.20, 18.0),  # Southern Sierra
    (34.35, -118.60, 0.14, 0.30, 0.20, 35.0),  # Los Angeles / Ventura mountains
    (38.90, -122.70, 0.22, 0.18, 0.14, 15.0),  # Mendocino / Lake
]
n_detections = 6000
lat_parts, lon_parts, frp_parts = [], [], []
for r_lat, r_lon, s_lat, s_lon, share, mean_frp in regions:
    n_part = int(n_detections * share)
    lat_parts.append(rng.normal(r_lat, s_lat, n_part))
    lon_parts.append(rng.normal(r_lon, s_lon, n_part))
    frp_parts.append(rng.exponential(mean_frp, n_part))
df = pd.DataFrame(
    {LAT: np.concatenate(lat_parts), LON: np.concatenate(lon_parts), FRP: np.concatenate(frp_parts)}
).round(4)

# Plot: everything below derives from df
df = df.dropna(subset=[LAT, LON])  # a detection without a position cannot be binned
lat_mid = float(df[LAT].mean())
x_scale = math.cos(math.radians(max(-80.0, min(80.0, lat_mid))))  # lon degrees -> equal-distance map units

# Hexagonal binning in map units (flat-top, axial coordinates, cube rounding)
mx = (df[LON].to_numpy() - df[LON].mean()) * x_scale
my = df[LAT].to_numpy() - lat_mid
hex_r = max(mx.max() - mx.min(), my.max() - my.min()) / GRID_COLUMNS / 1.5
qf = (2.0 / 3.0 * mx) / hex_r
rf = (-1.0 / 3.0 * mx + math.sqrt(3.0) / 3.0 * my) / hex_r
q, r, s = np.round(qf), np.round(rf), np.round(-qf - rf)
dq, dr, ds = np.abs(q - qf), np.abs(r - rf), np.abs(s - (-qf - rf))
q = np.where((dq > dr) & (dq > ds), -r - s, q)
r = np.where((dq <= dr) | (dq <= ds), np.where(dr > ds, -q - s, r), r)

cells = (
    df.assign(q=q.astype(int), r=r.astype(int))
    .groupby(["q", "r"])
    .agg(count=(FRP, "size"), total=(FRP, "sum"), mean=(FRP, "mean"))
    .reset_index()
)
cx_map = hex_r * 1.5 * cells["q"].to_numpy()
cy_map = hex_r * math.sqrt(3.0) * (cells["r"].to_numpy() + cells["q"].to_numpy() / 2.0)
cells["lon"] = cx_map / x_scale + df[LON].mean()
cells["lat"] = cy_map + lat_mid

# Density classes from quantiles of the cell counts
inner_edges = np.unique(np.percentile(cells["count"], np.linspace(0, 100, N_BINS + 1)[1:-1]))
cells["bin"] = np.searchsorted(inner_edges, cells["count"].to_numpy(), side="right")
cells = cells.sort_values("bin", kind="stable").reset_index(drop=True)
bin_ids = sorted(cells["bin"].unique())

# Geographic extent (with a small margin) and an equal-distance data aspect
lon_lo, lon_hi = (
    min(df[LON].min(), min(p[0] for p in CALIFORNIA_OUTLINE)),
    max(df[LON].max(), max(p[0] for p in CALIFORNIA_OUTLINE)),
)
lat_lo, lat_hi = (
    min(df[LAT].min(), min(p[1] for p in CALIFORNIA_OUTLINE)),
    max(df[LAT].max(), max(p[1] for p in CALIFORNIA_OUTLINE)),
)
pad_lon, pad_lat = 0.03 * (lon_hi - lon_lo), 0.03 * (lat_hi - lat_lo)
lon_lo, lon_hi, lat_lo, lat_hi = lon_lo - pad_lon, lon_hi + pad_lon, lat_lo - pad_lat, lat_hi + pad_lat

title = "hexbin-map-geographic · python · pygal · anyplot.ai"
colors = (INK_MUTED,) + tuple(ramp_color(SEQ_FIELDS, b / max(N_BINS - 1, 1)) for b in bin_ids)
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color="transparent",
    major_guide_stroke_color="transparent",
    colors=colors,
    opacity=0.78,
    opacity_hover=0.95,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)


# The first pass measures the plot area; the second sets the axis ranges so one degree of
# latitude and the same map distance in longitude span equal pixel lengths
x_range, y_range = (lon_lo, lon_hi), (lat_lo, lat_hi)
corners = [(hex_r * math.cos(math.radians(60 * k)), hex_r * math.sin(math.radians(60 * k))) for k in range(6)]
for render_pass in range(2):
    chart = pygal.XY(
        width=2400,
        height=2400,
        style=custom_style,
        title=title,
        x_title=LON,
        y_title=LAT,
        show_legend=True,
        legend_at_bottom=True,
        legend_at_bottom_columns=N_BINS,
        legend_box_size=30,
        stroke=False,
        dots_size=10,
        show_x_guides=False,
        show_y_guides=False,
        explicit_size=True,
        print_values=False,
        xrange=x_range,
        range=y_range,
    )
    chart.add(None, CALIFORNIA_OUTLINE, stroke=True, show_dots=False, fill=False, stroke_width=5)
    for b in bin_ids:
        part = cells[cells["bin"] == b]
        lo, hi = int(part["count"].min()), int(part["count"].max())
        label = f"count {lo}" if lo == hi else f"count {lo}–{hi}"
        points = [
            {
                "value": (float(c.lon), float(c.lat)),
                "label": f"Detections: {c.count} | FRP sum {c.total:.0f} MW, mean {c.mean:.1f} MW"
                f" | ({c.lat:.2f}°N, {abs(c.lon):.2f}°W)",
            }
            for c in part.itertuples()
        ]
        chart.add(label, points)
    svg = chart.render().decode("utf-8")

    # Fit pixel = offset + scale * data for both axes from the dot markers, in series order
    dots = list(re.finditer(r"<circle\b[^>]*/>", svg))
    assert len(dots) == len(cells), f"{len(dots)} dots for {len(cells)} cells"
    px = np.array([[float(v) for v in re.findall(r'\b(?:cx|cy)="([^"]+)"', m.group(0))[:2]] for m in dots])
    sx, ox = np.polyfit(cells["lon"].to_numpy(), px[:, 0], 1)
    sy, oy = np.polyfit(cells["lat"].to_numpy(), px[:, 1], 1)
    if render_pass == 0:
        width_px, height_px = abs(sx) * (lon_hi - lon_lo), abs(sy) * (lat_hi - lat_lo)
        px_per_map_unit = min(width_px / ((lon_hi - lon_lo) * x_scale), height_px / (lat_hi - lat_lo))
        lon_span, lat_span = width_px / (px_per_map_unit * x_scale), height_px / px_per_map_unit
        lon_c, lat_c = (lon_lo + lon_hi) / 2, (lat_lo + lat_hi) / 2
        x_range = (lon_c - lon_span / 2, lon_c + lon_span / 2)
        y_range = (lat_c - lat_span / 2, lat_c + lat_span / 2)

# Replace each dot marker with the cell's true hexagon, drawn in data space and mapped to pixels
pieces, last = [], 0
for m, c in zip(dots, cells.itertuples(), strict=True):
    pts = " ".join(f"{ox + sx * (c.lon + dx / x_scale):.2f},{oy + sy * (c.lat + dy):.2f}" for dx, dy in corners)
    tag = re.sub(r'\s(cx|cy|r)="[^"]*"', "", m.group(0)).replace(
        "<circle", f'<polygon points="{pts}" stroke="{PAGE_BG}" stroke-width="3" style="fill-opacity:0.8"', 1
    )
    pieces += [svg[last : m.start()], tag]
    last = m.end()
svg = "".join(pieces) + svg[last:]

cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(svg.encode("utf-8"))
