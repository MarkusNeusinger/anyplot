""" anyplot.ai
histogram-stacked: Stacked Histogram
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-12
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Get theme from environment
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Set theme-aware colors
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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data - Response times (ms) from three different server regions
np.random.seed(42)

# Generate response times for three server regions with different characteristics
region_a = np.random.normal(loc=45, scale=12, size=150)  # US East - faster
region_b = np.random.normal(loc=60, scale=15, size=180)  # Europe - medium
region_c = np.random.normal(loc=75, scale=18, size=120)  # Asia Pacific - slower

# Combine into DataFrame
df = pd.DataFrame(
    {
        "Response Time (ms)": np.concatenate([region_a, region_b, region_c]),
        "Region": (["US East"] * len(region_a) + ["Europe"] * len(region_b) + ["Asia Pacific"] * len(region_c)),
    }
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Okabe-Ito palette for stacked histogram
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Stacked histogram using histplot with multiple='stack'
sns.histplot(
    data=df,
    x="Response Time (ms)",
    hue="Region",
    hue_order=["US East", "Europe", "Asia Pacific"],
    multiple="stack",
    bins=20,
    palette=IMPRINT,
    edgecolor="white",
    linewidth=0.8,
    alpha=0.9,
    ax=ax,
)

# Styling
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("Frequency", fontsize=20)
ax.set_title("histogram-stacked · seaborn · anyplot.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.1, linestyle="-", axis="y")

# Adjust legend styling
legend = ax.get_legend()
legend.set_title("Server Region")
legend.get_title().set_fontsize(16)
for text in legend.get_texts():
    text.set_fontsize(14)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
