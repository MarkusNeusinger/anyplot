""" anyplot.ai
ice-basic: Individual Conditional Expectation (ICE) Plot
Library: altair 6.2.2 | Python 3.13.15
Quality: 86/100 | Updated: 2026-08-17
"""

import os
import sys


# Prevent this file from shadowing the altair package
_script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402
from sklearn.ensemble import GradientBoostingRegressor  # noqa: E402


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — first series ALWAYS #009E73
BRAND = "#009E73"
PDP_COLOR = "#C475FD"

# Canvas — landscape inner view, see prompts/library/altair.md "Canvas — hard rule"
VIEW_W, VIEW_H = 620, 320
TARGET_W, TARGET_H = 3200, 1800

# Data
np.random.seed(42)
n_obs = 100
sqft = np.random.uniform(800, 3500, n_obs)
bedrooms = np.random.randint(1, 6, n_obs)
house_age = np.random.uniform(0, 50, n_obs)

price = 120 * sqft + 25000 * bedrooms - 600 * house_age + 0.008 * sqft**2 + np.random.normal(0, 25000, n_obs)

X = np.column_stack([sqft, bedrooms, house_age])
model = GradientBoostingRegressor(n_estimators=200, max_depth=4, random_state=42)
model.fit(X, price)

# Build ICE curves — vary square footage across its range for each observation
grid_size = 60
sqft_grid = np.linspace(sqft.min(), sqft.max(), grid_size)

records = []
for obs_id in range(n_obs):
    X_ice = np.column_stack([sqft_grid, np.full(grid_size, bedrooms[obs_id]), np.full(grid_size, house_age[obs_id])])
    preds = model.predict(X_ice)
    for sq, pred in zip(sqft_grid, preds, strict=False):
        records.append({"obs_id": obs_id, "sqft": sq, "price_k": pred / 1000, "series": "ICE Curves"})

ice_df = pd.DataFrame(records)

# PDP: mean prediction at each sqft grid point
pdp_df = ice_df.groupby("sqft", as_index=False)["price_k"].mean()
pdp_df["series"] = "Partial Dependence"

# Shared color scale for legend
color_scale = alt.Scale(domain=["ICE Curves", "Partial Dependence"], range=[BRAND, PDP_COLOR])
color_legend = alt.Legend(title="", labelFontSize=10, symbolSize=120, symbolStrokeWidth=2, orient="top-right")

# Real interactivity in the HTML export: hovering a curve highlights it. The
# unselected (default) branch matches the static PNG state, so the PNG render
# is unaffected — only the interactive HTML gains the hover behavior.
hover = alt.selection_point(fields=["obs_id"], on="pointerover", empty=False)

# ICE individual curves — semi-transparent to show density
ice_layer = (
    alt.Chart(ice_df)
    .mark_line(strokeWidth=1.5)
    .encode(
        x=alt.X("sqft:Q", title="Square Footage (sq ft)"),
        y=alt.Y("price_k:Q", title="Predicted Price ($K)"),
        detail="obs_id:N",
        color=alt.Color("series:N", scale=color_scale, legend=color_legend),
        opacity=alt.condition(hover, alt.value(0.9), alt.value(0.10)),
    )
    .add_params(hover)
)

# PDP overlay — bold opaque curve showing average marginal effect
pdp_layer = (
    alt.Chart(pdp_df)
    .mark_line(strokeWidth=5)
    .encode(x="sqft:Q", y="price_k:Q", color=alt.Color("series:N", scale=color_scale, legend=color_legend))
)

# PDP annotation — anchored at a low-price mid-chart grid point, lifted well
# above the local ICE band into open space and clear of the top-right legend
pdp_sorted = pdp_df.sort_values("sqft").reset_index(drop=True)
pdp_annotation_df = pdp_sorted.iloc[[int(len(pdp_sorted) * 0.30)]]
pdp_annotation = (
    alt.Chart(pdp_annotation_df)
    .mark_text(align="center", dy=-60, fontSize=11, color=PDP_COLOR, fontWeight="bold")
    .encode(x="sqft:Q", y="price_k:Q", text=alt.value("Partial Dependence"))
)

# Rug plot — actual observed sqft values along the x-axis
rug_df = pd.DataFrame({"sqft": sqft})
rug_layer = (
    alt.Chart(rug_df)
    .mark_tick(thickness=1.5, size=8, opacity=0.45, color=INK_SOFT)
    .encode(x="sqft:Q", y=alt.value(VIEW_H - 8))
)

chart = (
    alt.layer(ice_layer, pdp_layer, pdp_annotation, rug_layer)
    .properties(
        width=VIEW_W, height=VIEW_H, background=PAGE_BG, title=alt.Title("ice-basic · altair · anyplot.ai", fontSize=16)
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_title(color=INK, fontSize=16)
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, labelFontSize=10
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# PAD-only to exact target canvas — vl-convert pads title/axis/legend outside
# width/height, so the saved PNG needs a final centered pad, never a crop.
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TARGET_W or _h > TARGET_H:
    raise SystemExit(
        f"altair vl-convert produced {_w}x{_h}, exceeds target {TARGET_W}x{TARGET_H}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TARGET_W or _h < TARGET_H:
    _canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    _canvas.paste(_img, ((TARGET_W - _w) // 2, (TARGET_H - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")
