""" anyplot.ai
point-basic: Point Estimate Plot
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
REFERENCE = 0.0  # the null value: a coefficient of zero means no effect on price

# Columns: set these to your table's column names
PREDICTOR = "Predictor"  # role: category
COEFFICIENT = "Effect on sale price (thousand USD)"  # role: estimate
CI_LOW = "Lower 95% bound"  # role: lower_bound
CI_HIGH = "Upper 95% bound"  # role: upper_bound

# Data: replace this block with your own table, for example df = pd.read_csv("coefficients.csv")
df = pd.DataFrame(
    {
        PREDICTOR: [
            "Garage spaces",
            "Bedrooms",
            "Renovated kitchen",
            "Lot size (per 1,000 sq ft)",
            "Floor area (per 100 sq ft)",
            "Age (per decade)",
            "Distance to city centre (per km)",
            "Busy road frontage",
        ],
        COEFFICIENT: [18.5, 6.2, 27.4, 3.1, 14.8, -9.6, -4.3, -21.7],
        CI_LOW: [9.8, -3.5, 14.9, -4.2, 11.6, -13.1, -7.9, -38.4],
        CI_HIGH: [27.2, 15.9, 39.9, 10.4, 18.0, -6.1, -0.7, -5.0],
    }
)

# Plot: reads only df and the constants above
table = df.sort_values(COEFFICIENT).reset_index(drop=True)
y = table.index.to_numpy()
est = table[COEFFICIENT].to_numpy()
lower = (est - table[CI_LOW].to_numpy()).clip(min=0)
upper = (table[CI_HIGH].to_numpy() - est).clip(min=0)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.axvline(REFERENCE, color=INK_SOFT, linewidth=1.2, linestyle="--", zorder=1)
ax.errorbar(
    est,
    y,
    xerr=[lower, upper],
    fmt="o",
    color=IMPRINT_PALETTE[0],
    ecolor=IMPRINT_PALETTE[0],
    markersize=7,
    markeredgecolor=PAGE_BG,
    markeredgewidth=0.8,
    elinewidth=1.8,
    capsize=4,
    capthick=1.8,
    zorder=3,
)

# Style
ax.set_title("point-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_yticks(y, table[PREDICTOR])
ax.set_xlabel(COEFFICIENT, fontsize=10, color=INK)
ax.set_ylabel(PREDICTOR, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

span = table[CI_HIGH].max() - table[CI_LOW].min()
ax.set_xlim(table[CI_LOW].min() - span * 0.04, table[CI_HIGH].max() + span * 0.04)
ax.set_ylim(-0.6, len(table) - 0.4)

ax.grid(True, axis="x", alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
