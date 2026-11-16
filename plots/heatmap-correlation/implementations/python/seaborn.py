""" anyplot.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap, to_rgb


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
LIGHT_INK = "#F0EFE8"  # annotation color on dark cells
DARK_INK = "#1A1A17"  # annotation color on light cells

# Imprint diverging colormap: red (negative) - page color (zero) - blue (positive)
imprint_div = LinearSegmentedColormap.from_list("imprint_div", ["#AE3030", PAGE_BG, "#4467A3"])

# Constants
CORR_LABEL = "Correlation coefficient"  # color bar title

# Data: replace this block with your own correlation matrix, for example df = observations.corr()
# Real estate features, 200 synthetic listings; df is the labeled square correlation matrix
rng = np.random.default_rng(42)
n_samples = 200
sqft = rng.normal(2000, 500, n_samples)
bedrooms = np.round(sqft / 600 + rng.normal(0, 0.5, n_samples)).clip(1, 6)
bathrooms = np.round(bedrooms * 0.7 + rng.normal(0, 0.3, n_samples)).clip(1, 4)
age = rng.exponential(20, n_samples).clip(0, 80)
price = sqft * 150 + bedrooms * 15000 - age * 2000 + rng.normal(0, 30000, n_samples)
garage = np.round(bedrooms * 0.4 + rng.normal(0, 0.3, n_samples)).clip(0, 3)
lot_size = sqft * 2 + rng.normal(0, 1000, n_samples)
distance = rng.exponential(10, n_samples).clip(1, 40)
crime = distance * 0.3 + rng.normal(5, 2, n_samples)
df = pd.DataFrame(
    {
        "Price ($K)": price / 1000,
        "Area (sq ft)": sqft,
        "Bedrooms": bedrooms,
        "Bathrooms": bathrooms,
        "Age (years)": age,
        "Garage spots": garage,
        "Lot (sq ft)": lot_size,
        "Distance (mi)": distance,
        "Crime index": crime,
    }
).corr()

# Plot
mask = np.triu(np.ones(df.shape, dtype=bool), k=1)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
sns.heatmap(
    df,
    mask=mask,
    annot=True,
    fmt=".2f",
    cmap=imprint_div,
    center=0,
    vmin=-1,
    vmax=1,
    square=True,
    linewidths=0.6,
    linecolor=PAGE_BG,
    cbar_kws={"shrink": 0.75, "ticks": [-1, -0.5, 0, 0.5, 1], "pad": 0.03},
    annot_kws={"size": 7},
    ax=ax,
)

# Annotation color follows cell darkness so numbers stay legible at both ends
norm = plt.Normalize(-1, 1)
for text in ax.texts:
    col, row = int(text.get_position()[0]), int(text.get_position()[1])
    r, g, b = to_rgb(imprint_div(norm(df.iloc[row, col])))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    text.set_color(LIGHT_INK if luminance < 0.4 else DARK_INK)

# Style
ax.set_title("heatmap-correlation · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=12)
ax.set_xlabel("")
ax.set_ylabel("")
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
plt.setp(ax.get_yticklabels(), rotation=0)

cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.set_label(CORR_LABEL, fontsize=9, color=INK)
cbar.outline.set_edgecolor(INK_SOFT)
cbar.ax.set_facecolor(PAGE_BG)

fig.subplots_adjust(left=0.2, right=0.92, top=0.93, bottom=0.17)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
