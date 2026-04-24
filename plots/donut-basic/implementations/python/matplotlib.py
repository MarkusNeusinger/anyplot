""" anyplot.ai
donut-basic: Basic Donut Chart
Library: matplotlib 3.10.9 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-24
"""

import os

import matplotlib.pyplot as plt


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first segment is always the brand green)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Data - Annual budget allocation by department (USD thousands)
categories = ["Engineering", "Marketing", "Operations", "Sales", "Support"]
values = [480, 210, 155, 125, 55]
total = sum(values)

# Plot (square canvas for circular shapes)
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

wedges, texts, autotexts = ax.pie(
    values,
    labels=categories,
    autopct="%1.1f%%",
    startangle=90,
    colors=OKABE_ITO,
    wedgeprops={"width": 0.42, "edgecolor": PAGE_BG, "linewidth": 3},
    pctdistance=0.78,
    labeldistance=1.08,
    textprops={"fontsize": 20, "color": INK},
)

# Percentage labels sit on the colored wedges — use a light off-white for contrast
for autotext in autotexts:
    autotext.set_fontsize(16)
    autotext.set_color("#F0EFE8")
    autotext.set_fontweight("bold")

# Category labels use theme ink
for text in texts:
    text.set_color(INK)

# Center metric
ax.text(0, 0.08, "Total budget", ha="center", va="center", fontsize=18, color=INK_SOFT)
ax.text(0, -0.06, f"${total:,}K", ha="center", va="center", fontsize=40, fontweight="bold", color=INK)

ax.set_aspect("equal")
ax.set_title(
    "Budget by Department · donut-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
