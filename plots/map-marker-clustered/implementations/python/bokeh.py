"""anyplot.ai
map-marker-clustered: Clustered Marker Map
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-08
"""

import os
import sys


# Remove the script's own directory from sys.path so "import bokeh" finds the
# installed package instead of this file (also named bokeh.py).
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _this_dir]

import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.events import DocumentReady
from bokeh.io import curdoc, output_file, save
from bokeh.models import ColumnDataSource, CustomJS, HoverTool, LabelSet, Legend, LegendItem, TapTool, WMTSTileSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Tile basemap — USGS The National Map topo tiles: public domain and keyless (ArcGIS z/y/x order).
# The tiles have no dark variant, so they are drawn translucent over the page background, which
# keeps the map quieter than the markers and gives it the theme's tone.
TILE_URL = "https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{Z}/{Y}/{X}"
TILE_ALPHA = 0.55 if THEME == "light" else 0.30

# Imprint palette — canonical order, one position per store type
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CELL_SHARE = 0.18  # cluster cell edge as a share of the visible map height, so clusters split as you zoom in
MIN_SIZE, MAX_SIZE = 55, 130  # cluster marker diameter in screen pixels, smallest to largest count

# Columns: set these to your table's column names
LAT = "Latitude (°)"  # role: lat
LON = "Longitude (°)"  # role: lon
STORE_TYPE = "Store Type"  # role: category
NEIGHBORHOOD = "Neighborhood"  # role: label

# Data: coffee chain store locations across NYC neighborhoods; replace with e.g. df = pd.read_csv("stores.csv")
np.random.seed(42)
neighborhoods = [
    ("Times Square", 40.758, -73.985, 45),
    ("Midtown", 40.755, -73.975, 35),
    ("Upper East", 40.773, -73.965, 28),
    ("Upper West", 40.785, -73.976, 22),
    ("Chelsea", 40.742, -74.000, 18),
    ("SoHo", 40.723, -73.998, 25),
    ("Financial", 40.707, -74.011, 32),
    ("Brooklyn Heights", 40.696, -73.993, 20),
    ("Williamsburg", 40.714, -73.961, 30),
    ("DUMBO", 40.703, -73.988, 15),
]
rows = []
for name, lat, lon, n in neighborhoods:
    rows.append(
        pd.DataFrame(
            {
                LAT: lat + np.random.normal(0, 0.008, n),
                LON: lon + np.random.normal(0, 0.008, n),
                STORE_TYPE: np.random.choice(["Coffee", "Express", "Roastery", "Reserve"], n, p=[0.5, 0.3, 0.15, 0.05]),
                NEIGHBORHOOD: name,
            }
        )
    )
df = pd.concat(rows, ignore_index=True)

# Plot: reads only df and the constants above
stores = df.dropna(subset=[LAT, LON])
categories = list(stores[STORE_TYPE].value_counts().index)  # most common type first, in brand green
category_index = {cat: i for i, cat in enumerate(categories)}

# lat/lon → Web Mercator metres, the projection of the tile basemap
k = 6378137
mercator_x = stores[LON].to_numpy(dtype=float) * (k * np.pi / 180.0)
mercator_y = np.log(np.tan((90 + stores[LAT].to_numpy(dtype=float)) * np.pi / 360.0)) * k

# Every store, with its type as a palette index (-1 when missing); the browser clusters these
store_source = ColumnDataSource(
    data={
        "x": mercator_x,
        "y": mercator_y,
        "cat": [category_index.get(c, -1) for c in stores[STORE_TYPE]],
        "label": stores[NEIGHBORHOOD].astype("string").fillna("").tolist(),
    }
)

# View fitted to the stores, with a margin for the largest marker
pad_x = (np.ptp(mercator_x) or 1000.0) * 0.08
pad_y = (np.ptp(mercator_y) or 1000.0) * 0.08

p = figure(
    width=3200,
    height=1800,
    x_range=(mercator_x.min() - pad_x, mercator_x.max() + pad_x),
    y_range=(mercator_y.min() - pad_y, mercator_y.max() + pad_y),
    x_axis_type="mercator",
    y_axis_type="mercator",
    title="map-marker-clustered · python · bokeh · anyplot.ai",
    tools="pan,wheel_zoom,reset",
    active_scroll="wheel_zoom",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Tile basemap — adds streets/boundaries geographic context
p.add_tile(WMTSTileSource(url=TILE_URL, attribution="Basemap: USGS The National Map"), alpha=TILE_ALPHA)

# Faint individual store markers beneath the clusters
p.scatter(x="x", y="y", source=store_source, size=8, fill_color=IMPRINT_PALETTE[0], fill_alpha=0.20, line_color=None)

# One cluster renderer per store type, filled by the browser
cluster_columns = ["x", "y", "size", "count", "category", "hood", "x0", "x1", "y0", "y1"]
cluster_sources, cluster_renderers, legend_items = [], [], []
for i, cat in enumerate(categories):
    src = ColumnDataSource(data={col: [] for col in cluster_columns})
    renderer = p.scatter(
        x="x",
        y="y",
        source=src,
        size="size",
        fill_color=IMPRINT_PALETTE[i],
        fill_alpha=0.88,
        line_color="white",
        line_width=2.5,
        nonselection_fill_alpha=0.88,
    )
    cluster_sources.append(src)
    cluster_renderers.append(renderer)
    # A twin holding one NaN point (never drawn on the map) gives the legend its glyph even when
    # no cluster currently has this type
    swatch = p.scatter(
        x=[np.nan], y=[np.nan], size=30, fill_color=IMPRINT_PALETTE[i], fill_alpha=0.88, line_color="white"
    )
    legend_items.append(LegendItem(label=str(cat), renderers=[swatch]))

# Cluster count labels
label_source = ColumnDataSource(data={"x": [], "y": [], "text": []})
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=label_source,
        text_font_size="24pt",
        text_font_style="bold",
        text_color="white",
        text_align="center",
        text_baseline="middle",
    )
)

# Grid clustering in the browser: the cell edge follows the visible height, so zooming in splits
# clusters into smaller ones and finally into single stores at their own coordinates
recluster = CustomJS(
    args={
        "stores": store_source,
        "clusters": cluster_sources,
        "labels": label_source,
        "names": [str(c) for c in categories],
        "yr": p.y_range,
        "share": CELL_SHARE,
        "min_size": MIN_SIZE,
        "max_size": MAX_SIZE,
    },
    code="""
    const {x, y, cat, label} = stores.data;
    const cell = (yr.end - yr.start) * share;
    const groups = new Map();
    for (let i = 0; i < x.length; i++) {
        const key = Math.floor(x[i] / cell) + ',' + Math.floor(y[i] / cell);
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(i);
    }
    const found = [];
    for (const members of groups.values()) {
        const tally = new Array(names.length).fill(0);
        const hoods = new Map();
        let sx = 0, sy = 0, x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
        for (const i of members) {
            sx += x[i]; sy += y[i];
            x0 = Math.min(x0, x[i]); x1 = Math.max(x1, x[i]);
            y0 = Math.min(y0, y[i]); y1 = Math.max(y1, y[i]);
            if (cat[i] >= 0) tally[cat[i]] += 1;
            if (label[i]) hoods.set(label[i], (hoods.get(label[i]) || 0) + 1);
        }
        let hood = '', best = 0;
        for (const [h, c] of hoods) if (c > best) { hood = h; best = c; }
        found.push({n: members.length, x: sx / members.length, y: sy / members.length,
                    dom: tally.indexOf(Math.max(...tally)), hood, x0, x1, y0, y1});
    }
    const counts = found.map(f => f.n);
    const lo = Math.min(...counts), hi = Math.max(...counts);
    const out = clusters.map(() => ({x: [], y: [], size: [], count: [], category: [], hood: [],
                                     x0: [], x1: [], y0: [], y1: []}));
    const text = {x: [], y: [], text: []};
    for (const f of found) {
        const d = out[f.dom];
        const size = min_size + Math.sqrt((f.n - lo + 1) / (hi - lo + 1)) * (max_size - min_size);
        d.x.push(f.x); d.y.push(f.y); d.size.push(size); d.count.push(f.n);
        d.category.push(names[f.dom]); d.hood.push(f.hood);
        d.x0.push(f.x0); d.x1.push(f.x1); d.y0.push(f.y0); d.y1.push(f.y1);
        text.x.push(f.x); text.y.push(f.y); text.text.push(String(f.n));
    }
    clusters.forEach((src, k) => { src.data = out[k]; });
    labels.data = text;
    """,
)
curdoc().js_on_event(DocumentReady, recluster)
for rng in (p.x_range, p.y_range):
    rng.js_on_change("start", recluster)
    rng.js_on_change("end", recluster)

# Click a cluster: an animated zoom to the box around its members, which then splits it apart
p.add_tools(
    TapTool(
        renderers=cluster_renderers,
        callback=CustomJS(
            args={"xr": p.x_range, "yr": p.y_range},
            code="""
            const src = cb_data.source;
            const i = src.selected.indices[0];
            if (i === undefined) return;
            const d = src.data;
            src.selected.indices = [];
            const w = xr.end - xr.start, h = yr.end - yr.start;
            const fit = Math.max((d.x1[i] - d.x0[i]) / w, (d.y1[i] - d.y0[i]) / h) * 1.6;
            const scale = Math.min(0.6, Math.max(0.15, d.count[i] > 1 ? fit : 0.4));
            const from = [xr.start, xr.end, yr.start, yr.end];
            const to = [d.x[i] - w * scale / 2, d.x[i] + w * scale / 2,
                        d.y[i] - h * scale / 2, d.y[i] + h * scale / 2];
            const t0 = performance.now(), duration = 600;
            function step(now) {
                const t = Math.min(1, (now - t0) / duration);
                const e = 1 - Math.pow(1 - t, 3);
                const v = from.map((a, j) => a + (to[j] - a) * e);
                xr.setv({start: v[0], end: v[1]});
                yr.setv({start: v[2], end: v[3]});
                if (t < 1) requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
            """,
        ),
    ),
    HoverTool(
        renderers=cluster_renderers,
        tooltips=[("Stores", "@count"), (f"Dominant {STORE_TYPE.lower()}", "@category"), (NEIGHBORHOOD, "@hood")],
    ),
)

# Legend
legend = Legend(
    items=legend_items,
    location="top_left",
    title=STORE_TYPE,
    title_text_font_size="34pt",
    title_text_font_style="bold",
    title_text_color=INK,
    label_text_font_size="34pt",
    label_text_color=INK_SOFT,
    glyph_height=48,
    glyph_width=48,
    spacing=10,
    padding=18,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.92,
    border_line_color=INK_SOFT,
    border_line_width=1,
)
p.add_layout(legend, "right")

# Typography
p.title.text_font_size = "50pt"
p.title.text_color = INK

p.xaxis.axis_label = LON
p.yaxis.axis_label = LAT
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.08
p.ygrid.grid_line_alpha = 0.08

# Theme-adaptive background (shows through the translucent tiles + border area)
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.outline_line_width = 1

# Save HTML (interactive artifact); the document carries the clustering callback
html_path = f"plot-{THEME}.html"
curdoc().add_root(p)
output_file(html_path, title="map-marker-clustered · python · bokeh · anyplot.ai")
save(curdoc())

# Screenshot via headless Chrome (Selenium 4 / Selenium Manager)
# Bokeh 3.9.0 adds a Notifications bar (~139 px) above the figure in the HTML
# page even when toolbar_location=None. Use element screenshot to capture just
# the figure div at its declared 3200×1800 size.
W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H + 200}",  # extra vertical space so figure isn't clipped
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
):
    opts.add_argument(arg)

driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H + 200)
driver.get(f"file://{Path(html_path).resolve()}")
time.sleep(8)  # extended wait for the tile layer: the USGS server answers in about 0.5 s per tile
driver.find_element(By.CSS_SELECTOR, ".bk-Figure").screenshot(f"plot-{THEME}.png")
driver.quit()
