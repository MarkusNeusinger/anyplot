""" anyplot.ai
box-basic: Basic Box Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-28
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — daily PM2.5 air quality readings (ug/m3) across 5 city zones
np.random.seed(42)

zones_config = [
    ("Park", "normal", 8, 3, 90),
    ("Residential", "normal", 18, 5, 80),
    ("Commercial", "normal", 30, 6, 75),
    ("Downtown", "bimodal", None, None, 100),
    ("Industrial", "exponential", None, 14, 70),
]

records = []
for zone, dist, loc, scale, n in zones_config:
    if dist == "bimodal":
        values = np.concatenate([np.random.normal(25, 5, n // 2), np.random.normal(44, 6, n // 2)])
    elif dist == "exponential":
        values = np.random.exponential(scale, n) + 28
    else:
        values = np.random.normal(loc, scale, n)
    values = np.clip(values, 1, None)
    for v in values:
        records.append({"Zone": zone, "PM2.5 (ug/m3)": v})

df = pd.DataFrame(records)
zone_order = ["Park", "Residential", "Commercial", "Downtown", "Industrial"]

# Theme
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
    },
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
palette = dict(zip(zone_order, IMPRINT_PALETTE, strict=True))

sns.boxplot(
    data=df,
    x="Zone",
    y="PM2.5 (ug/m3)",
    hue="Zone",
    order=zone_order,
    hue_order=zone_order,
    palette=palette,
    linewidth=1.5,
    fliersize=0,
    width=0.55,
    legend=False,
    ax=ax,
)

sns.stripplot(
    data=df,
    x="Zone",
    y="PM2.5 (ug/m3)",
    hue="Zone",
    order=zone_order,
    hue_order=zone_order,
    palette=palette,
    size=3,
    alpha=0.25,
    jitter=0.2,
    legend=False,
    ax=ax,
)

# Style
title = "box-basic · python · seaborn · anyplot.ai"
n_chars = len(title)
ratio = 67 / n_chars if n_chars > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))

ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_xlabel("City Zone", fontsize=10, color=INK)
ax.set_ylabel("PM2.5 (ug/m3)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
sns.despine(ax=ax)

plt.tight_layout()

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
