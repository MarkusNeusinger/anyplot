"""anyplot.ai
pdp-basic: Partial Dependence Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ICE_STRIDE = 10  # draw every 10th observation's ICE line
BAND_Z = 1.96  # 95% band around the average

# Column constants
FEATURE = "Feature value"  # role: feature_values
PREDICTION = "Partial dependence (average prediction)"  # role: ice_curves
SAMPLE = "Observation"  # role: extra
OBSERVED = "Observed feature value"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("ice.csv")
np.random.seed(42)
X, y = make_regression(n_samples=500, n_features=5, noise=15, random_state=42)
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, y)
pd_result = partial_dependence(model, X, features=[0], kind="both", grid_resolution=80)
ice = pd_result["individual"][0]
grid = pd_result["grid_values"][0]
df = pd.DataFrame(
    {
        SAMPLE: np.repeat(np.arange(ice.shape[0]), ice.shape[1]),
        FEATURE: np.tile(grid, ice.shape[0]),
        PREDICTION: ice.ravel(),
        OBSERVED: np.repeat(X[:, 0], ice.shape[1]),
    }
)

# Plot
BRAND = IMPRINT_PALETTE[0]
RUG = IMPRINT_PALETTE[4]
by_grid = df.groupby(FEATURE)[PREDICTION]
pdp = by_grid.mean()
spread = by_grid.std(ddof=0)
rug_x = df.drop_duplicates(SAMPLE)[OBSERVED]

title = "pdp-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# ICE lines (faint, individual observations)
for _, rows in df[df[SAMPLE] % ICE_STRIDE == 0].groupby(SAMPLE):
    ax.plot(rows[FEATURE], rows[PREDICTION], color=BRAND, alpha=0.08, linewidth=0.5)

# Confidence band
ax.fill_between(
    pdp.index,
    pdp - BAND_Z * spread,
    pdp + BAND_Z * spread,
    alpha=0.2,
    color=BRAND,
    linewidth=0,
    label="95% confidence interval",
)

# Partial dependence line
ax.plot(pdp.index, pdp, color=BRAND, linewidth=2.5, label="Partial dependence")

# Rug along the x axis (x in data units, y in axes fraction)
ax.scatter(
    rug_x,
    np.full(len(rug_x), 0.015),
    transform=ax.get_xaxis_transform(),
    marker="|",
    color=RUG,
    alpha=0.5,
    s=60,
    linewidth=0.6,
    label="Observed feature values",
)

ax.set_xlabel(FEATURE, fontsize=10, color=INK)
ax.set_ylabel(PREDICTION, fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

leg = ax.legend(fontsize=8, loc="upper left", frameon=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.6)
plt.setp(leg.get_texts(), color=INK_SOFT)

ax.grid(True, alpha=0.1, linewidth=0.5, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
