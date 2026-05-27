""" anyplot.ai
ice-basic: Individual Conditional Expectation (ICE) Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 87/100 | Created: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    theme,
)
from lets_plot.export import ggsave
from sklearn.ensemble import GradientBoostingRegressor


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "#D0CEC7" if THEME == "light" else "#2E2E2B"

BRAND = "#009E73"  # Okabe-Ito position 1 — Suburban houses
COLOR2 = "#C475FD"  # Okabe-Ito position 2 — Urban houses

# Data — house price predictions via GradientBoostingRegressor
np.random.seed(42)
n_obs = 100

sqft = np.random.uniform(800, 3500, n_obs)
bedrooms = np.random.randint(2, 6, n_obs).astype(float)
age = np.random.uniform(1, 50, n_obs)
neighborhood = np.random.choice([0, 1], n_obs)

price = sqft * 150 + bedrooms * 12000 - age * 600 + neighborhood * 75000 + np.random.normal(0, 18000, n_obs)

X = np.column_stack([sqft, bedrooms, age, neighborhood])
model = GradientBoostingRegressor(n_estimators=150, max_depth=3, random_state=42)
model.fit(X, price)

sqft_grid = np.linspace(sqft.min(), sqft.max(), 60)

# ICE curves — one line per observation
ice_rows = []
for i in range(n_obs):
    for sq in sqft_grid:
        X_mod = np.array([[sq, bedrooms[i], age[i], neighborhood[i]]])
        pred = model.predict(X_mod)[0] / 1000
        ice_rows.append(
            {
                "sqft": sq,
                "prediction": pred,
                "obs_id": str(i),
                "location": "Urban" if neighborhood[i] == 1 else "Suburban",
            }
        )

ice_df = pd.DataFrame(ice_rows)

# Partial dependence — average prediction across all observations
pdp_rows = []
for sq in sqft_grid:
    X_mod = X.copy()
    X_mod[:, 0] = sq
    pdp_rows.append({"sqft": sq, "prediction": model.predict(X_mod).mean() / 1000})

pdp_df = pd.DataFrame(pdp_rows)

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=GRID_COLOR, size=0.5),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=16),
)

plot = (
    ggplot()
    + geom_line(aes(x="sqft", y="prediction", group="obs_id", color="location"), data=ice_df, alpha=0.15, size=0.8)
    + scale_color_manual(values={"Suburban": BRAND, "Urban": COLOR2})
    + geom_line(aes(x="sqft", y="prediction"), data=pdp_df, color=INK, size=2.5)
    + labs(
        x="Square Footage (sq ft)",
        y="Predicted Price ($K)",
        title="ice-basic · letsplot · anyplot.ai",
        color="Location",
    )
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
