"""anyplot.ai
bar-feature-importance: Feature Importance Bar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
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

# Imprint sequential colormap: brand green to blue
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Importance score (normalized)"  # role: importance
STD = "Standard deviation"  # role: std

# Data: replace this block with your own table, for example df = pd.read_csv("importances.csv")
df = pd.DataFrame(
    {
        FEATURE: [
            "Income",
            "Credit Score",
            "Age",
            "Employment Years",
            "Debt Ratio",
            "Number of Accounts",
            "Payment History",
            "Loan Amount",
            "Education Level",
            "Home Ownership",
            "Marital Status",
            "Number of Dependents",
        ],
        IMPORTANCE: [0.182, 0.156, 0.124, 0.098, 0.089, 0.078, 0.072, 0.065, 0.051, 0.042, 0.028, 0.015],
        STD: [0.025, 0.022, 0.018, 0.015, 0.014, 0.012, 0.011, 0.010, 0.008, 0.007, 0.005, 0.003],
    }
)

# Plot: reads only df and the constants above
# Ascending order puts the highest importance at the top of a horizontal bar chart
table = df.sort_values(IMPORTANCE).reset_index(drop=True)
values = table[IMPORTANCE].to_numpy()
errors = table[STD].fillna(0).to_numpy()
colors = imprint_seq((values - np.nanmin(values)) / (np.nanmax(values) - np.nanmin(values)))
top = np.nanmax(values + errors)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

bars = ax.barh(
    table[FEATURE],
    values,
    xerr=errors,
    color=colors,
    edgecolor=INK_SOFT,
    linewidth=0.8,
    capsize=3,
    error_kw={"elinewidth": 1.2, "capthick": 1.2, "ecolor": INK_SOFT},
)

# Value labels at the end of each bar, clear of the error bar
for bar, value, err in zip(bars, values, errors, strict=True):
    if np.isnan(value):
        continue
    ax.text(
        value + err + top * 0.015,
        bar.get_y() + bar.get_height() / 2,
        f"{value:.3f}",
        va="center",
        ha="left",
        fontsize=9,
        color=INK_SOFT,
    )

# Style
ax.set_title("bar-feature-importance · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(IMPORTANCE, fontsize=11, color=INK)
ax.set_ylabel(FEATURE, fontsize=11, color=INK)
ax.tick_params(axis="both", labelsize=9, colors=INK_SOFT)
ax.set_xlim(0, top * 1.12)
ax.grid(True, axis="x", alpha=0.15, linewidth=0.6, color=INK_SOFT)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
