""" anyplot.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Configure seaborn with theme-adaptive colors
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

# Data: Market share by quarter for tech companies
np.random.seed(42)
quarters = ["Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023", "Q1 2024", "Q2 2024"]
companies = ["Company A", "Company B", "Company C", "Company D"]

# Create realistic market share data with variation
data = {
    "Company A": [35, 33, 30, 28, 26, 24],
    "Company B": [25, 27, 28, 30, 32, 34],
    "Company C": [22, 22, 24, 25, 26, 27],
    "Company D": [18, 18, 18, 17, 16, 15],
}

df = pd.DataFrame(data, index=quarters)

# Normalize to percentages
df_percent = df.div(df.sum(axis=1), axis=0) * 100

# Create cumulative sums for stacking
df_cumsum = df_percent.cumsum(axis=1)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot stacked bars by drawing each segment
x = np.arange(len(quarters))
bar_width = 0.6

# Draw bars from bottom to top
for i, company in enumerate(companies):
    bottom = df_cumsum.iloc[:, i - 1].values if i > 0 else np.zeros(len(quarters))
    heights = df_percent[company].values
    ax.bar(x, heights, bar_width, bottom=bottom, label=company, color=IMPRINT[i], edgecolor=PAGE_BG, linewidth=1.5)

    # Add percentage labels inside segments (only if segment is large enough)
    for j, (h, b) in enumerate(zip(heights, bottom, strict=True)):
        if h > 8:  # Only label if segment is > 8%
            # Determine text color based on background brightness
            text_color = "#1A1A17" if IMPRINT[i] != "#009E73" else "white"
            ax.text(
                x[j], b + h / 2, f"{h:.0f}%", ha="center", va="center", fontsize=14, fontweight="bold", color=text_color
            )

# Styling
ax.set_xlabel("Quarter", fontsize=20, color=INK)
ax.set_ylabel("Market Share (%)", fontsize=20, color=INK)
ax.set_title("bar-stacked-percent · seaborn · anyplot.ai", fontsize=24, color=INK)
ax.set_xticks(x)
ax.set_xticklabels(quarters, fontsize=16, color=INK_SOFT)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)
ax.set_ylim(0, 100)
ax.set_yticks([0, 20, 40, 60, 80, 100])

# Legend inside the plot
ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, 0.95),
    ncol=2,
    fontsize=14,
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)

# Grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.set_axisbelow(True)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
