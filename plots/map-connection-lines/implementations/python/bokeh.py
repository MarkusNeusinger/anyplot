"""anyplot.ai
map-connection-lines: Connection Lines Map (Origin-Destination)
Library: bokeh 3.10.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # green — connection lines (first series)
ACCENT = IMPRINT_PALETTE[2]  # blue — airport markers

# Simplified continent outlines (approximate polygons for geographic context)
CONT_LON = [
    # Africa
    [-18, -17, -14, -9, 0, 12, 25, 33, 36, 44, 51, 42, 40, 36, 32, 26, 18, 12, 9, 9, 2, -5, -12, -16, -18],
    # Europe
    [
        -9,
        -8,
        -8,
        0,
        6,
        8,
        15,
        17,
        21,
        28,
        32,
        32,
        30,
        32,
        28,
        25,
        28,
        20,
        10,
        3,
        5,
        8,
        10,
        10,
        10,
        5,
        3,
        0,
        -2,
        -5,
        -5,
        -8,
        -9,
    ],
    # North America
    [
        -168,
        -140,
        -130,
        -124,
        -124,
        -118,
        -108,
        -87,
        -82,
        -77,
        -77,
        -66,
        -60,
        -51,
        -53,
        -52,
        -65,
        -74,
        -80,
        -80,
        -75,
        -75,
        -74,
        -67,
        -60,
        -56,
        -63,
        -90,
        -120,
        -155,
        -168,
        -168,
    ],
    # South America
    [
        -77,
        -62,
        -51,
        -49,
        -35,
        -35,
        -39,
        -45,
        -48,
        -52,
        -55,
        -65,
        -68,
        -69,
        -68,
        -63,
        -55,
        -52,
        -52,
        -56,
        -65,
        -67,
        -70,
        -70,
        -75,
        -77,
        -77,
    ],
    # Asia (simplified)
    [
        26,
        29,
        36,
        42,
        55,
        65,
        80,
        100,
        140,
        153,
        150,
        135,
        130,
        125,
        122,
        108,
        103,
        103,
        110,
        115,
        120,
        118,
        100,
        92,
        80,
        68,
        60,
        50,
        44,
        43,
        42,
        40,
        43,
        50,
        50,
        50,
        55,
        60,
        70,
        80,
        90,
        103,
        112,
        120,
        130,
        135,
        142,
        140,
        145,
        150,
        135,
        100,
        60,
        50,
        38,
        30,
        26,
        24,
        26,
        28,
        32,
        32,
        26,
    ],
    # Australia
    [114, 113, 114, 118, 122, 130, 133, 137, 140, 150, 153, 150, 143, 138, 130, 125, 120, 114],
]
CONT_LAT = [
    # Africa
    [14, 20, 24, 30, 32, 37, 37, 30, 22, 12, 12, 2, -10, -18, -26, -34, -35, -25, -12, -3, 5, 5, 4, 12, 14],
    # Europe
    [
        36,
        38,
        44,
        43,
        44,
        47,
        46,
        43,
        40,
        37,
        36,
        38,
        40,
        46,
        55,
        58,
        64,
        70,
        71,
        62,
        58,
        56,
        56,
        55,
        52,
        52,
        51,
        51,
        49,
        48,
        44,
        42,
        36,
    ],
    # North America
    [
        72,
        60,
        55,
        48,
        34,
        32,
        25,
        15,
        9,
        8,
        9,
        10,
        5,
        4,
        6,
        10,
        17,
        18,
        24,
        32,
        35,
        38,
        41,
        44,
        47,
        53,
        65,
        70,
        75,
        60,
        55,
        72,
    ],
    # South America
    [
        10,
        10,
        4,
        4,
        -5,
        -12,
        -18,
        -23,
        -28,
        -33,
        -36,
        -42,
        -48,
        -52,
        -55,
        -55,
        -53,
        -52,
        -45,
        -40,
        -36,
        -30,
        -25,
        -17,
        -10,
        -2,
        10,
    ],
    # Asia
    [
        42,
        42,
        48,
        52,
        62,
        68,
        74,
        78,
        73,
        55,
        44,
        42,
        35,
        32,
        25,
        18,
        2,
        -1,
        -8,
        -3,
        5,
        8,
        18,
        22,
        26,
        22,
        22,
        18,
        12,
        8,
        2,
        -12,
        -20,
        -5,
        12,
        18,
        30,
        40,
        38,
        35,
        40,
        42,
        43,
        50,
        45,
        48,
        52,
        56,
        62,
        68,
        72,
        78,
        70,
        68,
        68,
        65,
        60,
        58,
        56,
        52,
        46,
        42,
        42,
    ],
    # Australia
    [-22, -26, -32, -35, -34, -33, -32, -36, -38, -38, -27, -22, -15, -14, -12, -17, -20, -22],
]

# Data: Major international flight routes between hub airports
airports = {
    "JFK": (40.6413, -73.7781),  # New York
    "LHR": (51.4700, -0.4543),  # London
    "CDG": (49.0097, 2.5479),  # Paris
    "DXB": (25.2532, 55.3657),  # Dubai
    "SIN": (1.3644, 103.9915),  # Singapore
    "HND": (35.5494, 139.7798),  # Tokyo
    "SYD": (-33.9399, 151.1753),  # Sydney
    "LAX": (33.9416, -118.4085),  # Los Angeles
    "SFO": (37.6213, -122.3790),  # San Francisco
    "ORD": (41.9742, -87.9073),  # Chicago
    "FRA": (50.0379, 8.5622),  # Frankfurt
    "AMS": (52.3105, 4.7683),  # Amsterdam
}

routes = [
    ("JFK", "LHR", 4.5),
    ("JFK", "CDG", 2.8),
    ("LAX", "HND", 3.2),
    ("SFO", "SIN", 1.5),
    ("LHR", "DXB", 3.8),
    ("CDG", "DXB", 2.1),
    ("DXB", "SIN", 2.5),
    ("SIN", "SYD", 2.9),
    ("LHR", "SYD", 1.2),
    ("JFK", "FRA", 2.3),
    ("ORD", "LHR", 1.8),
    ("LAX", "SYD", 1.6),
    ("FRA", "SIN", 1.4),
    ("AMS", "HND", 0.9),
    ("CDG", "HND", 1.1),
]


# Build great-circle arcs (spherical interpolation); arcs crossing the antimeridian are split at +-180
def great_circle(lat1, lon1, lat2, lon2, n=80):
    """Points along the great circle from (lat1, lon1) to (lat2, lon2), in degrees, lon unwrapped."""
    p1 = np.array(
        [
            np.cos(np.radians(lat1)) * np.cos(np.radians(lon1)),
            np.cos(np.radians(lat1)) * np.sin(np.radians(lon1)),
            np.sin(np.radians(lat1)),
        ]
    )
    p2 = np.array(
        [
            np.cos(np.radians(lat2)) * np.cos(np.radians(lon2)),
            np.cos(np.radians(lat2)) * np.sin(np.radians(lon2)),
            np.sin(np.radians(lat2)),
        ]
    )
    omega = np.arccos(np.clip(p1 @ p2, -1, 1))
    t = np.linspace(0, 1, n)[:, None]
    pts = (np.sin((1 - t) * omega) * p1 + np.sin(t * omega) * p2) / np.sin(omega)
    lons = np.degrees(np.unwrap(np.arctan2(pts[:, 1], pts[:, 0])))
    lats = np.degrees(np.arcsin(np.clip(pts[:, 2], -1, 1)))
    return lons, lats


def split_at_antimeridian(lons, lats):
    """Wrap lons into [-180, 180] and cut the line wherever it crosses the antimeridian."""
    wraps = np.floor((lons + 180) / 360)
    segments, cur_x, cur_y = [], [lons[0] - 360 * wraps[0]], [lats[0]]
    for i in range(1, len(lons)):
        if wraps[i] != wraps[i - 1]:
            going_east = wraps[i] > wraps[i - 1]
            boundary = 360 * max(wraps[i], wraps[i - 1]) - 180
            share = (boundary - lons[i - 1]) / (lons[i] - lons[i - 1])
            lat_b = lats[i - 1] + share * (lats[i] - lats[i - 1])
            cur_x.append(180.0 if going_east else -180.0)
            cur_y.append(lat_b)
            segments.append((cur_x, cur_y))
            cur_x, cur_y = [-180.0 if going_east else 180.0], [lat_b]
        cur_x.append(lons[i] - 360 * wraps[i])
        cur_y.append(lats[i])
    segments.append((cur_x, cur_y))
    return segments


line_xs, line_ys, line_widths, line_alphas = [], [], [], []
route_labels, passenger_volumes = [], []
volumes = [r[2] for r in routes]
min_vol, max_vol = min(volumes), max(volumes)

for origin, dest, volume in routes:
    o_lat, o_lon = airports[origin]
    d_lat, d_lon = airports[dest]
    arc_lons, arc_lats = great_circle(o_lat, o_lon, d_lat, d_lon)
    normalized = (volume - min_vol) / (max_vol - min_vol) if max_vol > min_vol else 0.5
    for seg_x, seg_y in split_at_antimeridian(arc_lons, arc_lats):
        line_xs.append(list(seg_x))
        line_ys.append(list(seg_y))
        line_widths.append(5 + normalized * 9)
        line_alphas.append(0.5 + normalized * 0.2)
        route_labels.append(f"{origin} → {dest}")
        passenger_volumes.append(f"{volume}M pax/year")

# Airport marker data
airport_names = list(airports.keys())
airport_lons = [airports[a][1] for a in airport_names]
airport_lats = [airports[a][0] for a in airport_names]

# Per-airport label offsets — push European cluster apart to prevent overlap
LABEL_OFFSETS = {
    "LHR": (-70, 44),  # below-left of dot, clear of the arcs arriving from the west
    "AMS": (14, -26),  # above-right; AMS is the northernmost hub (positive y_offset moves down)
    "CDG": (-4, 50),  # directly below its dot
    "FRA": (20, 20),  # below-right of its dot
}
airport_x_offsets = [LABEL_OFFSETS.get(a, (14, 8))[0] for a in airport_names]
airport_y_offsets = [LABEL_OFFSETS.get(a, (14, 8))[1] for a in airport_names]

# Data sources
line_source = ColumnDataSource(
    data={
        "xs": line_xs,
        "ys": line_ys,
        "line_width": line_widths,
        "alpha": line_alphas,
        "route": route_labels,
        "passengers": passenger_volumes,
    }
)
airport_source = ColumnDataSource(
    data={
        "x": airport_lons,
        "y": airport_lats,
        "name": airport_names,
        "x_off": airport_x_offsets,
        "y_off": airport_y_offsets,
    }
)
continent_source = ColumnDataSource(data={"xs": CONT_LON, "ys": CONT_LAT})

# Title font size (scales linearly if title exceeds 67-char baseline)
title = "map-connection-lines · python · bokeh · anyplot.ai"
n = len(title)
title_fs = f"{round(50 * (67 / n if n > 67 else 1.0))}pt"

# Figure — width/height are the exact PNG canvas dimensions
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_range=(-180, 180),
    y_range=(-60, 80),
    x_axis_label="Longitude (°)",
    y_axis_label="Latitude (°)",
    toolbar_location=None,  # omit toolbar so PNG = exactly height=1800 px
    min_border_bottom=160,  # room for 34pt tick labels + 42pt x-axis label
    min_border_left=180,  # room for 34pt tick labels + 42pt y-axis label
    min_border_top=110,  # room for 50pt title
    min_border_right=50,
)

# Continent base map
p.patches(
    xs="xs",
    ys="ys",
    source=continent_source,
    fill_color=INK_MUTED,
    fill_alpha=0.18,
    line_color=INK_SOFT,
    line_width=0.8,
    line_alpha=0.5,
)

# Connection arcs — line width and alpha encode passenger volume
lines_renderer = p.multi_line(
    xs="xs",
    ys="ys",
    source=line_source,
    line_width="line_width",
    line_alpha="alpha",
    line_color=BRAND,
    line_cap="round",
)
p.add_tools(
    HoverTool(
        renderers=[lines_renderer], tooltips=[("Route", "@route"), ("Traffic", "@passengers")], line_policy="interp"
    )
)

# Airport markers
p.scatter(x="x", y="y", source=airport_source, size=18, color=ACCENT, line_color=PAGE_BG, line_width=2, alpha=0.9)
p.text(
    x="x",
    y="y",
    text="name",
    source=airport_source,
    x_offset="x_off",
    y_offset="y_off",
    text_font_size="22pt",
    text_color=INK,
    text_font_style="bold",
)

# Width key: three sample lines (no data) collected in a Legend
legend_items = []
for label, width, alpha in (("Low (~1M)", 5, 0.5), ("Medium (~2.5M)", 9, 0.6), ("High (~4.5M)", 14, 0.7)):
    sample = p.line(x=[0, 1], y=[1000, 1000], line_width=width, line_alpha=alpha, line_color=BRAND, line_cap="round")
    legend_items.append(LegendItem(label=label, renderers=[sample]))
width_key = Legend(
    items=legend_items,
    title="Passengers per year",
    location="top_left",
    label_text_font_size="24pt",
    title_text_font_size="26pt",
    title_text_font_style="bold",
    label_text_color=INK,
    title_text_color=INK,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.9,
    border_line_color=INK_SOFT,
    glyph_width=60,
    glyph_height=30,
    label_standoff=16,
    spacing=10,
    padding=18,
    margin=24,
)
p.add_layout(width_key)

# Theme-adaptive chrome
p.title.text_font_size = title_fs
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.1
p.ygrid.grid_line_alpha = 0.1
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save interactive HTML (required catalog artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
# Force exact viewport to W×H regardless of headless browser chrome overhead
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
