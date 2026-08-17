"""anyplot.ai
ice-basic: Individual Conditional Expectation (ICE) Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-07
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from sklearn.ensemble import GradientBoostingRegressor


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1 — ICE individual lines
ACCENT = "#C475FD"  # Imprint palette position 2 — PDP average line

# Data: synthetic housing dataset
np.random.seed(42)
n_obs = 120

sqft = np.random.uniform(800, 3500, n_obs)
bedrooms = np.random.choice([2, 3, 4, 5], n_obs, p=[0.15, 0.45, 0.30, 0.10])
age_years = np.random.uniform(1, 40, n_obs)
lot_size = np.random.uniform(3000, 15000, n_obs)

price = sqft * 180 + bedrooms * 12000 - age_years * 1500 + lot_size * 2.5 + np.random.normal(0, 25000, n_obs)

X = np.column_stack([sqft, bedrooms, age_years, lot_size])
y = price

# Train gradient boosting model
model = GradientBoostingRegressor(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42)
model.fit(X, y)

# ICE curves: vary sqft (index 0) across a grid, holding other features at observed values
sqft_grid = np.linspace(sqft.min(), sqft.max(), 70)
ice_matrix = np.zeros((n_obs, len(sqft_grid)))

for j, val in enumerate(sqft_grid):
    X_temp = X.copy()
    X_temp[:, 0] = val
    ice_matrix[:, j] = model.predict(X_temp)

pdp_line = ice_matrix.mean(axis=0)
ice_min = ice_matrix.min(axis=0)
ice_max = ice_matrix.max(axis=0)

# Locate where individual curves diverge most from the average (heterogeneity peak)
spread = ice_matrix.std(axis=0)
divergence_idx = np.argmax(spread)
divergence_sqft = sqft_grid[divergence_idx]
divergence_y = ice_max[divergence_idx]

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Min-max envelope of individual curves — shows the full spread at a glance
ax.fill_between(sqft_grid, ice_min, ice_max, color=BRAND, alpha=0.06, linewidth=0, zorder=1)

# ICE individual lines
for i in range(n_obs):
    ax.plot(sqft_grid, ice_matrix[i], color=BRAND, alpha=0.14, linewidth=0.9, zorder=2)

# PDP average line
ax.plot(sqft_grid, pdp_line, color=ACCENT, linewidth=3, zorder=5)

# Explicit y-limits with headroom for the rug plot so its position is fixed
# regardless of layout adjustments (rug sits inside the bottom margin, never
# overlapping the lowest ICE curve).
y_span = ice_max.max() - ice_min.min()
y_bottom = ice_min.min() - 0.10 * y_span
y_top = ice_max.max() + 0.04 * y_span
ax.set_ylim(y_bottom, y_top)
rug_y = ice_min.min() - 0.055 * y_span
ax.plot(sqft, np.full(n_obs, rug_y), "|", color=INK_MUTED, alpha=0.5, markersize=6, markeredgewidth=1.0, zorder=3)

# Annotation: call out where individual effects diverge most from the average
ax.annotate(
    f"Effects diverge most\naround {divergence_sqft:,.0f} sqft",
    xy=(divergence_sqft, divergence_y),
    xytext=(0.62, 0.90),
    textcoords="axes fraction",
    fontsize=8,
    color=INK_SOFT,
    ha="left",
    va="top",
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "linewidth": 1.0},
    bbox={"facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9, "boxstyle": "round,pad=0.4", "linewidth": 0.8},
)

# Style
ax.set_xlabel("Square Footage (sqft)", fontsize=10, color=INK)
ax.set_ylabel("Predicted House Price ($)", fontsize=10, color=INK)
ax.set_title(
    "House Price by Square Footage · ice-basic · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK
)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Legend
legend_handles = [
    Line2D([0], [0], color=BRAND, alpha=0.6, linewidth=2, label=f"Individual ICE lines (n={n_obs})"),
    Line2D([0], [0], color=BRAND, alpha=0.2, linewidth=8, label="Prediction range (min–max)"),
    Line2D([0], [0], color=ACCENT, linewidth=3, label="Partial dependence (average)"),
]
leg = ax.legend(handles=legend_handles, fontsize=8, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
