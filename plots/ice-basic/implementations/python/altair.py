""" anyplot.ai
ice-basic: Individual Conditional Expectation (ICE) Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 89/100 | Created: 2026-05-07
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
from sklearn.ensemble import GradientBoostingRegressor  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"
PDP_COLOR = "#C475FD"

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
color_legend = alt.Legend(title="", labelFontSize=16, symbolSize=250, symbolStrokeWidth=3, orient="top-right")

# ICE individual curves — semi-transparent to show density
ice_layer = (
    alt.Chart(ice_df)
    .mark_line(opacity=0.10, strokeWidth=1.5)
    .encode(
        x=alt.X("sqft:Q", title="Square Footage (sq ft)"),
        y=alt.Y("price_k:Q", title="Predicted Price ($K)"),
        detail="obs_id:N",
        color=alt.Color("series:N", scale=color_scale, legend=color_legend),
    )
)

# PDP overlay — bold opaque curve showing average marginal effect
pdp_layer = (
    alt.Chart(pdp_df)
    .mark_line(strokeWidth=5)
    .encode(x="sqft:Q", y="price_k:Q", color=alt.Color("series:N", scale=color_scale, legend=color_legend))
)

# PDP annotation — label near the right end of the curve
pdp_annotation_df = pdp_df.nlargest(15, "sqft").nsmallest(1, "sqft").copy()
pdp_annotation = (
    alt.Chart(pdp_annotation_df)
    .mark_text(align="right", dx=-6, dy=-18, fontSize=16, color=PDP_COLOR, fontWeight="bold")
    .encode(x="sqft:Q", y="price_k:Q", text=alt.value("Partial Dependence"))
)

# Rug plot — actual observed sqft values along the x-axis
rug_df = pd.DataFrame({"sqft": sqft})
rug_layer = (
    alt.Chart(rug_df)
    .mark_tick(thickness=1.5, size=14, opacity=0.45, color=INK_SOFT)
    .encode(x="sqft:Q", y=alt.value(890))
)

chart = (
    alt.layer(ice_layer, pdp_layer, pdp_annotation, rug_layer)
    .properties(
        width=1600, height=900, background=PAGE_BG, title=alt.Title("ice-basic · altair · anyplot.ai", fontSize=28)
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
    )
    .configure_title(color=INK, fontSize=28)
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, labelFontSize=16
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
