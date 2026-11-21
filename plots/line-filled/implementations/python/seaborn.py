"""anyplot.ai
line-filled: Filled Line Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1

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

# Columns: set these to your table's column names
DAY = "Trading Days"  # role: x
PRICE = "Stock Price ($)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
days = np.arange(90)
base_price = 100 + days * 0.5  # steady uptrend
daily_change = np.random.normal(0, 2, size=90)  # daily volatility
stock_price = np.maximum(base_price + np.cumsum(daily_change), 80)  # floor at realistic minimum
df = pd.DataFrame({DAY: days, PRICE: stock_price})

# Plot: reads only df and the constants above
df = df.sort_values(DAY)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Fill down to the zero baseline, line on top
ax.fill_between(df[DAY], df[PRICE], 0, alpha=0.35, color=BRAND, linewidth=0)
sns.lineplot(data=df, x=DAY, y=PRICE, color=BRAND, linewidth=2.5, ax=ax)

# Labels and styling
ax.set_xlabel(DAY, fontsize=10)
ax.set_ylabel(PRICE, fontsize=10)
ax.set_title("line-filled · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Despine and subtle y-axis grid
sns.despine(ax=ax)
for spine in ("left", "bottom"):
    ax.spines[spine].set_linewidth(0.8)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Include the baseline so the filled height stays proportional to the value
ax.set_ylim(bottom=0)
ax.set_xlim(df[DAY].min(), df[DAY].max())

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
