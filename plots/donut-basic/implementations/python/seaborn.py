""" anyplot.ai
donut-basic: Basic Donut Chart
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 84/100 | Updated: 2026-04-24
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

# Theme
sns.set_theme(
    context="talk", style="white", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK}
)

# Plot
fig, ax = plt.subplots(figsize=(13.5, 13.5), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

wedges, _ = ax.pie(
    budget["amount"],
    colors=OKABE_ITO[: len(budget)],
    startangle=90,
    counterclock=False,
    wedgeprops={"width": 0.38, "edgecolor": PAGE_BG, "linewidth": 3},
)

# External two-line labels (department + share) placed along wedge bisector
for wedge, dept, share in zip(wedges, budget["department"], budget["share"], strict=True):
    angle = np.deg2rad((wedge.theta2 + wedge.theta1) / 2)
    x_label = 1.18 * np.cos(angle)
    y_label = 1.18 * np.sin(angle)
    ha = "left" if np.cos(angle) >= 0 else "right"
    ax.text(x_label, y_label, f"{dept}\n{share:.1f}%", ha=ha, va="center", fontsize=18, color=INK, linespacing=1.3)

# Center metric: total budget
ax.text(0, 0.08, "Total Budget", ha="center", va="center", fontsize=20, color=INK_SOFT)
ax.text(0, -0.08, f"${total / 1_000_000:.2f}M", ha="center", va="center", fontsize=40, fontweight="bold", color=INK)

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
