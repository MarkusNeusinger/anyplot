"""anyplot.ai
line-filled: Filled Line Plot
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-05-12
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Set seaborn theme
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

# Data - Stock price over 90 trading days with upward trend and volatility
np.random.seed(42)
days = np.arange(90)
# Simulate realistic stock price movement with uptrend and daily volatility
base_price = 100 + days * 0.5  # Steady uptrend
daily_change = np.random.normal(0, 2, size=90)  # Daily volatility (no weekly pattern)
stock_price = base_price + np.cumsum(daily_change)
stock_price = np.maximum(stock_price, 80)  # Floor at realistic minimum

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot line with fill underneath
ax.plot(days, stock_price, color=BRAND, linewidth=3, label="Stock Price")
ax.fill_between(days, stock_price, alpha=0.35, color=BRAND)

# Labels and styling
ax.set_xlabel("Trading Days", fontsize=20, color=INK)
ax.set_ylabel("Stock Price ($)", fontsize=20, color=INK)
ax.set_title("line-filled · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Style spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
    ax.spines[spine].set_linewidth(0.8)

# Subtle y-axis grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Set y-axis to start at 0 for proper area visualization
ax.set_ylim(bottom=0)

# Remove legend (single series, redundant)
if ax.get_legend():
    ax.get_legend().remove()

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
plt.close()
