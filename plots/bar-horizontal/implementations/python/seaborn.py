""" anyplot.ai
bar-horizontal: Horizontal Bar Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-07
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Okabe-Ito position 1

# Set theme
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

# Data - Top countries by population
data = {
    "Country": [
        "India",
        "China",
        "United States",
        "Indonesia",
        "Pakistan",
        "Brazil",
        "Nigeria",
        "Bangladesh",
        "Russia",
        "Mexico",
    ],
    "Population (millions)": [1417, 1412, 338, 275, 235, 215, 223, 170, 144, 128],
}
df = pd.DataFrame(data)

# Sort by population descending for visual ranking
df = df.sort_values("Population (millions)", ascending=True)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot horizontal bar chart with Okabe-Ito brand color
bars = ax.barh(df["Country"], df["Population (millions)"], color=BRAND, edgecolor=INK_SOFT, linewidth=1.2)

# Add value labels at the end of bars
for i, (_idx, row) in enumerate(df.iterrows()):
    value = row["Population (millions)"]
    ax.text(value + 20, i, f"{value}M", va="center", fontsize=16, color=INK, fontweight="500")

# Styling
ax.set_xlabel("Population (Millions)", fontsize=20, color=INK, labelpad=12)
ax.set_ylabel("Country", fontsize=20, color=INK, labelpad=12)
ax.set_title("Population by Country (2024)", fontsize=24, color=INK, pad=24, fontweight="600")

# Tick labels
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Grid on x-axis only
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, linestyle="-")
ax.set_axisbelow(True)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.spines["left"].set_linewidth(0.8)
ax.spines["bottom"].set_linewidth(0.8)

# Extend x-axis to accommodate labels
ax.set_xlim(0, 1500)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
plt.close()
