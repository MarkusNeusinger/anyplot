""" anyplot.ai
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
BRAND = "#009E73"  # Okabe-Ito position 1 — ICE individual lines
ACCENT = "#C475FD"  # Okabe-Ito position 2 — PDP average line

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

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# ICE individual lines
for i in range(n_obs):
    ax.plot(sqft_grid, ice_matrix[i], color=BRAND, alpha=0.14, linewidth=0.9)

# PDP average line
ax.plot(sqft_grid, pdp_line, color=ACCENT, linewidth=3.5, zorder=5)

# Rug plot: distribution of observed sqft values
rug_y = ax.get_ylim()[0]
ax.plot(sqft, np.full(n_obs, rug_y), "|", color=INK_MUTED, alpha=0.5, markersize=8, markeredgewidth=1.2)

# Style
ax.set_xlabel("Square Footage (sqft)", fontsize=20, color=INK)
ax.set_ylabel("Predicted House Price ($)", fontsize=20, color=INK)
ax.set_title(
    "House Price by Square Footage · ice-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK
)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend
legend_handles = [
    Line2D([0], [0], color=BRAND, alpha=0.6, linewidth=2, label=f"Individual ICE lines (n={n_obs})"),
    Line2D([0], [0], color=ACCENT, linewidth=3.5, label="Partial dependence (average)"),
]
leg = ax.legend(handles=legend_handles, fontsize=16, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
