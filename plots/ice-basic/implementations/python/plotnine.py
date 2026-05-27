""" anyplot.ai
ice-basic: Individual Conditional Expectation (ICE) Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 87/100 | Created: 2026-05-07
"""

import os
import sys


# Prevent this script from shadowing the plotnine package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p if p else ".") != _here]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_rug,
    ggplot,
    labs,
    scale_x_continuous,
    theme,
)
from sklearn.ensemble import GradientBoostingRegressor  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
VERMILLION = "#C475FD"

# Data — synthetic housing dataset
np.random.seed(42)
n_obs = 120

area = np.random.uniform(600, 4000, n_obs)
bedrooms = np.random.randint(1, 6, n_obs).astype(float)
age_years = np.random.uniform(1, 50, n_obs)
location = np.random.uniform(1, 10, n_obs)

X = np.column_stack([area, bedrooms, age_years, location])
y = area * 120 + bedrooms * 25000 - age_years * 800 + location * 40000 + np.random.normal(0, 25000, n_obs)

model = GradientBoostingRegressor(n_estimators=150, max_depth=3, random_state=42)
model.fit(X, y)

# ICE curves: vary area across a grid, hold all other features at observed values
n_grid = 60
area_grid = np.linspace(area.min(), area.max(), n_grid)

ice_rows = []
for obs_id in range(n_obs):
    X_grid = np.tile(X[obs_id], (n_grid, 1))
    X_grid[:, 0] = area_grid
    preds = model.predict(X_grid)
    for feat_val, pred in zip(area_grid, preds, strict=False):
        ice_rows.append({"observation_id": str(obs_id), "feature_value": feat_val, "prediction": pred / 1000})

ice_df = pd.DataFrame(ice_rows)

# PDP: average prediction across all observations at each grid point
pdp_df = ice_df.groupby("feature_value")["prediction"].mean().reset_index()

# Rug: observed area values
rug_df = pd.DataFrame({"feature_value": area})

# Annotation anchor: PDP value at ~75% of area range (past the step discontinuity)
ann_idx = int(n_grid * 0.75)
ann_x = float(area_grid[ann_idx])
ann_y = float(pdp_df.iloc[ann_idx]["prediction"]) + 25

# Plot
anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24, face="bold"),
    legend_position="none",
    plot_margin=0.025,
)

plot = (
    ggplot(ice_df, aes(x="feature_value", y="prediction", group="observation_id"))
    + geom_line(alpha=0.12, color=BRAND, size=0.5)
    + geom_line(
        data=pdp_df, mapping=aes(x="feature_value", y="prediction"), color=VERMILLION, size=2.5, inherit_aes=False
    )
    + geom_rug(data=rug_df, mapping=aes(x="feature_value"), color=INK_SOFT, alpha=0.4, sides="b", inherit_aes=False)
    + annotate("text", x=ann_x, y=ann_y, label="PDP (avg effect)", color=VERMILLION, size=14)
    + scale_x_continuous(breaks=[1000, 1500, 2000, 2500, 3000, 3500])
    + labs(x="House Area (sq ft)", y="Predicted Price ($000s)", title="ice-basic · plotnine · anyplot.ai")
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, width=16, height=9)
