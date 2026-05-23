"""anyplot.ai
map-marker-clustered: Clustered Marker Map
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-23
"""

import os
import sys

import numpy as np


# Remove current directory from sys.path to avoid shadowing the pygal package
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _cwd)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

ANYPLOT_PALETTE = ("#009E73", "#9418DB", "#B71D27", "#16B8F3", "#99B314", "#D359A7", "#BA843E")

# Data: venue locations across central Paris
np.random.seed(42)
N = 420
categories = ["Cafe", "Restaurant", "Bar"]

# Scatter points around central Paris with slight sub-district clustering
lat_center, lon_center = 48.856, 2.352
lats = np.random.normal(lat_center, 0.030, N)
lons = np.random.normal(lon_center, 0.048, N)
cats = np.random.choice(categories, N, p=[0.40, 0.35, 0.25])

# Grid-based clustering (8 rows × 10 cols → up to 80 clusters)
GRID_ROWS, GRID_COLS = 8, 10
lat_min, lat_max = lats.min(), lats.max()
lon_min, lon_max = lons.min(), lons.max()
lat_range = lat_max - lat_min or 1e-6
lon_range = lon_max - lon_min or 1e-6

clusters: dict = {}
for i in range(N):
    row = min(int((lats[i] - lat_min) / lat_range * GRID_ROWS), GRID_ROWS - 1)
    col = min(int((lons[i] - lon_min) / lon_range * GRID_COLS), GRID_COLS - 1)
    key = (row, col)
    if key not in clusters:
        clusters[key] = {"lats": [], "lons": [], "cats": dict.fromkeys(categories, 0)}
    clusters[key]["lats"].append(lats[i])
    clusters[key]["lons"].append(lons[i])
    clusters[key]["cats"][cats[i]] += 1

# Compute centroid and dominant category per cluster cell
cluster_data = []
for data in clusters.values():
    count = len(data["lats"])
    centroid_lat = float(np.mean(data["lats"]))
    centroid_lon = float(np.mean(data["lons"]))
    dominant = max(data["cats"], key=data["cats"].get)
    cafe_n = data["cats"]["Cafe"]
    rest_n = data["cats"]["Restaurant"]
    bar_n = data["cats"]["Bar"]
    cluster_data.append(
        {
            "lat": centroid_lat,
            "lon": centroid_lon,
            "count": count,
            "dominant": dominant,
            "label": (f"{dominant} cluster · {count} venues (☕{cafe_n} 🍽{rest_n} 🍷{bar_n})"),
        }
    )

by_cat = {cat: [] for cat in categories}
for cd in cluster_data:
    by_cat[cd["dominant"]].append(cd)

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ANYPLOT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

# Chart
chart = pygal.XY(
    style=custom_style,
    width=3200,
    height=1800,
    title="Paris Venue Clusters · map-marker-clustered · python · pygal · anyplot.ai",
    x_title="Longitude",
    y_title="Latitude",
    show_dots=True,
    dots_size=12,
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    stroke=False,
)

for cat in categories:
    series_data = [{"value": (cd["lon"], cd["lat"]), "label": cd["label"]} for cd in by_cat[cat]]
    total = sum(cd["count"] for cd in by_cat[cat])
    chart.add(f"{cat} ({total} venues)", series_data)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
