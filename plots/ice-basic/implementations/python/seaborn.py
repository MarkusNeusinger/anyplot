""" anyplot.ai
ice-basic: Individual Conditional Expectation (ICE) Plot
Library: seaborn 0.13.2 | Python 3.13.15
Quality: 86/100 | Updated: 2026-08-17
"""

import os
import sys


# Prevent this file from shadowing the installed seaborn package
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if not (p and os.path.abspath(p) == _this_dir)]

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import GradientBoostingRegressor


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — ICE lines
PDP_COLOR = "#C475FD"  # Imprint palette position 2 — PDP overlay

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.12,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — synthetic housing dataset
np.random.seed(42)
n_obs = 100
sqft = np.random.uniform(800, 3500, n_obs)
bedrooms = np.random.randint(2, 6, n_obs).astype(float)
age = np.random.uniform(0, 50, n_obs)
distance = np.random.uniform(1, 25, n_obs)

price = 0.15 * sqft + 25.0 * bedrooms - 0.5 * age - 2.5 * distance + np.random.normal(0, 30, n_obs)

X = np.column_stack([sqft, bedrooms, age, distance])
model = GradientBoostingRegressor(n_estimators=150, max_depth=4, random_state=42)
model.fit(X, price)

# Compute ICE matrix — each row is one observation, each column a grid point
n_grid = 60
sqft_grid = np.linspace(800, 3500, n_grid)
ice_matrix = np.zeros((n_obs, n_grid))
for j, val in enumerate(sqft_grid):
    X_tmp = X.copy()
    X_tmp[:, 0] = val
    ice_matrix[:, j] = model.predict(X_tmp)

pdp = ice_matrix.mean(axis=0)

# Long-form DataFrame for seaborn
obs_ids = np.repeat(np.arange(n_obs), n_grid)
sqft_vals = np.tile(sqft_grid, n_obs)
df_ice = pd.DataFrame({"obs_id": obs_ids, "sqft": sqft_vals, "price": ice_matrix.ravel()})

# Plot — 3200x1800 canvas (figsize x dpi), bbox_inches left at default (None)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# ICE lines — one per observation via seaborn lineplot with units
n_lines_before = len(ax.lines)
sns.lineplot(data=df_ice, x="sqft", y="price", units="obs_id", estimator=None, color=BRAND, linewidth=0.6, ax=ax)
for line in ax.lines[n_lines_before:]:
    line.set_alpha(0.15)

# PDP overlay — bold average marginal effect, drawn via seaborn (not raw matplotlib)
sns.lineplot(x=sqft_grid, y=pdp, color=PDP_COLOR, linewidth=3, ax=ax, zorder=5, label="Partial Dependence (PDP)")

# Rug plot — observed sqft distribution
sns.rugplot(x=sqft, color=INK_SOFT, alpha=0.6, height=0.03, expand_margins=False, ax=ax)

# Style
ax.set_xlabel("Square Footage (sq ft)", fontsize=10, color=INK)
ax.set_ylabel("Predicted House Price ($K)", fontsize=10, color=INK)
ax.set_title("ice-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
sns.despine(ax=ax)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

ice_handle = plt.Line2D([0], [0], color=BRAND, alpha=0.5, linewidth=2, label=f"ICE curves (n={n_obs})")
pdp_handle, pdp_label = ax.get_legend_handles_labels()
legend = ax.legend(
    handles=[ice_handle] + pdp_handle, fontsize=8, framealpha=1.0, facecolor=ELEVATED_BG, edgecolor=INK_SOFT
)
for text in legend.get_texts():
    text.set_color(INK)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
