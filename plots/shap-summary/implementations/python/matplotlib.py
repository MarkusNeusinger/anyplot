"""anyplot.ai
shap-summary: SHAP Summary Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
TOP_N = 10  # show only the most important features
JITTER = 0.15  # vertical jitter inside a row (layout only)
# Diverging feature-value scale: Imprint blue (low) to Imprint red (high); the neutral
# midpoint is a mid grey so mid-scale dots stay visible on both page backgrounds
imprint_div = LinearSegmentedColormap.from_list("imprint_div", ["#4467A3", "#9C9A90", "#AE3030"])

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature_names
SHAP_VALUE = "SHAP value (impact on model output)"  # role: shap_values
FEATURE_VALUE = "Feature value"  # role: feature_values

# Data: replace this block with your own long table, one row per sample and feature,
# for example df = pd.read_csv("shap_values.csv")
np.random.seed(42)
n_samples = 300
feature_names = [
    "Square Footage",
    "Number of Bedrooms",
    "Age of House (years)",
    "Distance to City (km)",
    "Number of Bathrooms",
    "Garage Size",
    "Lot Size (acres)",
    "School Rating",
    "Crime Rate Index",
    "Year Renovated",
    "Property Tax Rate",
    "Median Income (area)",
]
feature_values = np.random.rand(n_samples, len(feature_names))
importance_scale = np.array([2.5, 1.8, 1.5, 1.4, 1.2, 1.0, 0.9, 0.8, 0.7, 0.5, 0.4, 0.3])
shap_values = np.zeros((n_samples, len(feature_names)))
for i in range(len(feature_names)):
    base_shap = (feature_values[:, i] - 0.5) * importance_scale[i]
    noise = np.random.randn(n_samples) * importance_scale[i] * 0.3
    shap_values[:, i] = base_shap + noise
df = pd.DataFrame(
    {FEATURE: np.tile(feature_names, n_samples), SHAP_VALUE: shap_values.ravel(), FEATURE_VALUE: feature_values.ravel()}
)

# Plot: reads only df and the constants above
importance = df.groupby(FEATURE, sort=False)[SHAP_VALUE].apply(lambda s: s.abs().mean())
top_features = importance.sort_values(ascending=False).index[:TOP_N]  # most important first
rng = np.random.default_rng(42)

title = "shap-summary · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for row, feature in enumerate(top_features[::-1]):  # bottom row first, so the most important ends on top
    rows = df[df[FEATURE] == feature]
    y = row + rng.uniform(-JITTER, JITTER, len(rows))
    scatter = ax.scatter(
        rows[SHAP_VALUE],
        y,
        c=rows[FEATURE_VALUE],
        cmap=imprint_div,
        vmin=df[FEATURE_VALUE].min(),
        vmax=df[FEATURE_VALUE].max(),
        s=14,
        alpha=0.7,
        edgecolors="none",
    )

# Vertical line at SHAP value zero, below the dots
ax.axvline(0, color=INK_SOFT, linewidth=1.2, zorder=0)

# Style
ax.set_yticks(range(len(top_features)), top_features[::-1])
ax.set_xlabel(SHAP_VALUE, fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.grid(True, axis="x", alpha=0.12, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)

# Colorbar
cbar = fig.colorbar(scatter, ax=ax, shrink=0.8, aspect=30, pad=0.02)
cbar.set_label(FEATURE_VALUE, fontsize=10, color=INK)
cbar.set_ticks([df[FEATURE_VALUE].min(), df[FEATURE_VALUE].max()], labels=["Low", "High"])
cbar.ax.tick_params(colors=INK_SOFT, labelcolor=INK_SOFT, labelsize=8)
cbar.outline.set_edgecolor(INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
