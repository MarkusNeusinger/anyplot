""" anyplot.ai
map-projections: World Map with Different Projections
Library: altair 6.1.0 | Python 3.13.13
Quality: 84/100 | Created: 2026-05-23
"""

import os
import sys


sys.path.pop(0)
import altair as alt
from PIL import Image


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"

# World TopoJSON via vega-datasets CDN
WORLD_URL = "https://cdn.jsdelivr.net/npm/vega-datasets@1.31.1/data/world-110m.json"

MAIN_TITLE = "map-projections · python · altair · anyplot.ai"

# Mercator projection — left panel
sphere_m = alt.Chart(alt.sphere()).mark_geoshape(fill=ELEVATED_BG, stroke=INK_SOFT, strokeWidth=0.4, strokeOpacity=0.6)
graticule_m = alt.Chart(alt.graticule(step=[30, 30])).mark_geoshape(
    filled=False, stroke=INK_SOFT, strokeWidth=0.3, strokeOpacity=0.35
)
countries_m = alt.Chart(alt.topo_feature(WORLD_URL, "countries")).mark_geoshape(
    fill=BRAND, stroke=PAGE_BG, strokeWidth=0.5, fillOpacity=0.88
)

map_mercator = (
    (sphere_m + graticule_m + countries_m)
    .project(type="mercator")
    .properties(
        width=290,
        height=375,
        title=alt.Title(
            text="Mercator",
            subtitle="conformal · distorts area near poles",
            fontSize=12,
            subtitleFontSize=10,
            color=INK,
            subtitleColor=INK_SOFT,
            anchor="middle",
        ),
    )
)

# Equal Earth projection — right panel
sphere_e = alt.Chart(alt.sphere()).mark_geoshape(fill=ELEVATED_BG, stroke=INK_SOFT, strokeWidth=0.4, strokeOpacity=0.6)
graticule_e = alt.Chart(alt.graticule(step=[30, 30])).mark_geoshape(
    filled=False, stroke=INK_SOFT, strokeWidth=0.3, strokeOpacity=0.35
)
countries_e = alt.Chart(alt.topo_feature(WORLD_URL, "countries")).mark_geoshape(
    fill=BRAND, stroke=PAGE_BG, strokeWidth=0.5, fillOpacity=0.88
)

map_equal_earth = (
    (sphere_e + graticule_e + countries_e)
    .project(type="equalEarth")
    .properties(
        width=290,
        height=375,
        title=alt.Title(
            text="Equal Earth",
            subtitle="equal-area · preserves relative country sizes",
            fontSize=12,
            subtitleFontSize=10,
            color=INK,
            subtitleColor=INK_SOFT,
            anchor="middle",
        ),
    )
)

# Combine side by side
chart = (
    alt.hconcat(map_mercator, map_equal_earth, spacing=30)
    .properties(background=PAGE_BG, title=alt.Title(text=MAIN_TITLE, fontSize=16, color=INK, anchor="middle"))
    .configure_view(stroke=None)
)

# Save PNG
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad to target canvas 3200 × 1800
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

# Save HTML
chart.save(f"plot-{THEME}.html")
