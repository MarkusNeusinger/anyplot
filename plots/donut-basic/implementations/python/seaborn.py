""" anyplot.ai
donut-basic: Basic Donut Chart
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-24
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

# Okabe-Ito palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9"]

# Data — departmental budget allocation (ordered largest → smallest for readability)
budget = pd.DataFrame(
    {
        "department": ["Engineering", "Sales", "Operations", "Marketing", "R&D", "HR"],
        "amount": [520_000, 310_000, 240_000, 150_000, 95_000, 45_000],
    }
)
total = budget["amount"].sum()
budget["share"] = budget["amount"] / total * 100

# Theme — register Okabe-Ito as the default seaborn palette so wedge colors come from sns.color_palette
sns.set_palette(sns.color_palette(OKABE_ITO))
sns.set_theme(
    context="talk",
    style="white",
    palette=sns.color_palette(OKABE_ITO),
    rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK},
)
wedge_colors = sns.color_palette(n_colors=len(budget)).as_hex()

# Plot — standard 3600x3600 square canvas (12in @ 300dpi)
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Emphasize the dominant Engineering segment with a subtle explode offset
explode = [0.03 if i == 0 else 0.0 for i in range(len(budget))]

wedges, _ = ax.pie(
    budget["amount"],
    colors=wedge_colors,
    startangle=90,
    counterclock=False,
    explode=explode,
    wedgeprops={"width": 0.38, "edgecolor": PAGE_BG, "linewidth": 3},
)

# External two-line labels (department + share) placed along wedge bisector.
# Small segments get a larger radius to prevent crowding near the top.
for wedge, dept, share in zip(wedges, budget["department"], budget["share"], strict=True):
    angle = np.deg2rad((wedge.theta2 + wedge.theta1) / 2)
    radius = 1.28 if share < 8 else 1.18
    x_label = radius * np.cos(angle)
    y_label = radius * np.sin(angle)
    ha = "left" if np.cos(angle) >= 0 else "right"
    ax.text(x_label, y_label, f"{dept}\n{share:.1f}%", ha=ha, va="center", fontsize=20, color=INK, linespacing=1.3)

# Center metric: label, thin separator, and bold total
ax.text(0, 0.14, "Total Budget", ha="center", va="center", fontsize=20, color=INK_SOFT)
ax.plot([-0.12, 0.12], [0.02, 0.02], color=INK_SOFT, linewidth=1.2, solid_capstyle="round")
ax.text(0, -0.14, f"${total / 1_000_000:.2f}M", ha="center", va="center", fontsize=44, fontweight="bold", color=INK)

# Title
ax.set_title(
    "FY2026 Budget Allocation · donut-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=28
)

ax.set_aspect("equal")
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.5, 1.5)
ax.set_axis_off()

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
