"""anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
SALES = "Sales (thousands USD)"  # role: y
ERROR_LOWER = "Lower error (thousands USD)"  # role: error_lower
ERROR_UPPER = "Upper error (thousands USD)"  # role: error_upper

# Data: replace this block with your own table, for example df = pd.read_csv("sales.csv")
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
        SALES: [42, 55, 48, 61, 73, 68, 82, 78],
        ERROR_LOWER: [5, 8, 6, 9, 7, 10, 8, 6],
        ERROR_UPPER: [12, 15, 10, 18, 14, 20, 16, 12],
    }
)

# Plot: reads only df and the constants above
x_positions = np.arange(len(df))
lower_bound = df[SALES] - df[ERROR_LOWER]
upper_bound = df[SALES] + df[ERROR_UPPER]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Error bars with asymmetric magnitudes
ax.errorbar(
    x_positions,
    df[SALES],
    yerr=[df[ERROR_LOWER], df[ERROR_UPPER]],
    fmt="o",
    markersize=11,
    color=BRAND,
    ecolor=BRAND,
    elinewidth=1.5,
    capsize=5,
    capthick=1.5,
    alpha=0.9,
    label="Median with 10th-90th percentile bounds",
)

# Subtle fill to show confidence region
ax.fill_between(x_positions, lower_bound, upper_bound, alpha=0.15, color=BRAND)

# Style
ax.set_xticks(x_positions, df[MONTH])
ax.set_xlabel(MONTH, fontsize=10, color=INK)
ax.set_ylabel(SALES, fontsize=10, color=INK)
ax.set_title("errorbar-asymmetric · python · matplotlib · anyplot.ai", fontsize=12, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK_SOFT)

# Legend
leg = ax.legend(fontsize=8, loc="upper left", framealpha=0.95)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
for text in leg.get_texts():
    text.set_color(INK_SOFT)

ax.set_ylim(0, np.nanmax(upper_bound) * 1.45)
fig.tight_layout()
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
