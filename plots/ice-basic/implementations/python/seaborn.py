""" anyplot.ai
ice-basic: Individual Conditional Expectation (ICE) Plot
Library: seaborn 0.13.2 | Python 3.13.15
Quality: 92/100 | Updated: 2026-08-17
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
from matplotlib.colors import LinearSegmentedColormap, Normalize
from sklearn.ensemble import GradientBoostingRegressor


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — ICE lines (low end of gradient)
PDP_COLOR = "#C475FD"  # Imprint palette position 2 — PDP overlay
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [BRAND, "#4467A3"])

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
bedrooms_vals = np.repeat(bedrooms, n_grid)
df_ice = pd.DataFrame({"obs_id": obs_ids, "sqft": sqft_vals, "price": ice_matrix.ravel(), "bedrooms": bedrooms_vals})

# Plot — 3200x1800 canvas (figsize x dpi), bbox_inches left at default (None)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# ICE lines — one per observation via seaborn lineplot with units, color-coded by
# bedrooms (a second feature) with an Imprint sequential colormap to surface
# interaction effects hidden by the flat single-color band
sns.lineplot(
    data=df_ice,
    x="sqft",
    y="price",
    units="obs_id",
    hue="bedrooms",
    estimator=None,
    palette=imprint_seq,
    linewidth=0.6,
    alpha=0.35,
    legend=False,
    ax=ax,
)

# PDP overlay — bold average marginal effect, drawn via seaborn (not raw matplotlib)
sns.lineplot(x=sqft_grid, y=pdp, color=PDP_COLOR, linewidth=3, ax=ax, zorder=5, label="Partial Dependence (PDP)")

# Rug plot — observed sqft distribution
sns.rugplot(x=sqft, color=INK_SOFT, alpha=0.75, height=0.045, expand_margins=False, ax=ax)

# Colorbar — decodes the bedrooms color gradient on the ICE lines
bedrooms_norm = Normalize(vmin=bedrooms.min(), vmax=bedrooms.max())
sm = plt.cm.ScalarMappable(cmap=imprint_seq, norm=bedrooms_norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, pad=0.02, fraction=0.035)
cbar.set_label(f"Bedrooms (ICE curve color, n={n_obs})", color=INK, fontsize=9)
cbar.ax.tick_params(colors=INK_SOFT, labelsize=7)
cbar.outline.set_edgecolor(INK_SOFT)

# Annotation — calls out the piecewise/staircase PDP shape from the tree ensemble
jump_idx = int(np.argmax(np.abs(np.diff(pdp)))) + 1
ann_x, ann_y = sqft_grid[jump_idx], pdp[jump_idx]
dx = -450 if ann_x > sqft_grid.mean() else 450
dy = 55 if ann_y < pdp.mean() else -55
ax.annotate(
    "Piecewise jump —\ntree-ensemble split",
    xy=(ann_x, ann_y),
    xytext=(ann_x + dx, ann_y + dy),
    fontsize=8,
    color=INK,
    ha="right" if dx < 0 else "left",
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.1},
)

# Style
ax.set_xlabel("Square Footage (sq ft)", fontsize=10, color=INK)
ax.set_ylabel("Predicted House Price ($K)", fontsize=10, color=INK)
ax.set_title("ice-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
sns.despine(ax=ax)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

legend = ax.legend(
    loc="upper left",
    fontsize=8,
    framealpha=0.92,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    fancybox=True,
    borderpad=0.6,
)
legend.get_frame().set_linewidth(0.6)
for text in legend.get_texts():
    text.set_color(INK)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
