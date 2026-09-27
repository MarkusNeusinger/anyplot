"""anyplot.ai
bubble-basic: Basic Bubble Chart
Library: seaborn 0.13.2 | Python 3.13.15
Quality: 92/100 | Updated: 2026-09-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — Countries: healthcare spending vs child mortality, bubble = population
np.random.seed(42)

tier_params = [
    ("Low Income", 35, 380, 85, 30, 15),
    ("Lower-Middle Income", 380, 950, 38, 11, 15),
    ("Upper-Middle Income", 950, 3200, 14, 5, 15),
    ("High Income", 3200, 8500, 5, 2, 15),
]
tier_colors = {t[0]: IMPRINT_PALETTE[i] for i, t in enumerate(tier_params)}

rows = []
for tier, s_min, s_max, m_ctr, m_std, n in tier_params:
    spending = np.random.uniform(s_min, s_max, n)
    mortality = np.clip(np.random.normal(m_ctr, m_std, n), 0.5, 150)
    population = np.clip(np.random.lognormal(3.1, 0.35, n), 10.0, 100.0)
    for s, m, pop in zip(spending, mortality, population, strict=False):
        rows.append(
            {
                "Healthcare Spending ($/year)": round(s, 0),
                "Child Mortality (per 1,000 births)": round(m, 1),
                "Population (M)": round(pop, 1),
                "Income Tier": tier,
            }
        )
df = pd.DataFrame(rows)

# Configure seaborn theme
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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

hue_order = [t[0] for t in tier_params]

# Subtle lowess trend line — makes the inverse spending/mortality
# relationship an explicit visual cue without adding a text callout
sns.regplot(
    data=df,
    x="Healthcare Spending ($/year)",
    y="Child Mortality (per 1,000 births)",
    scatter=False,
    lowess=True,
    ax=ax,
    color=INK_SOFT,
    line_kws={"linewidth": 1.6, "linestyle": "--", "alpha": 0.55},
)

sns.scatterplot(
    data=df,
    x="Healthcare Spending ($/year)",
    y="Child Mortality (per 1,000 births)",
    size="Population (M)",
    hue="Income Tier",
    hue_order=hue_order,
    sizes=(50, 650),
    alpha=0.58,
    palette=tier_colors,
    edgecolor=PAGE_BG,
    linewidth=1.0,
    legend="brief",
    ax=ax,
)

# Style
title = "bubble-basic · python · seaborn · anyplot.ai"
n_chars = len(title)
ratio = 67 / n_chars if n_chars > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))

ax.set_xlabel("Healthcare Spending ($ / year)", fontsize=10, color=INK)
ax.set_ylabel("Child Mortality (per 1,000 births)", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)

# Spending spans two orders of magnitude across tiers, so a linear x-axis
# crushes the Low Income cluster into a sliver; log scale spaces every tier
# evenly and separates its 15 points instead.
ax.set_xscale("log")
ax.set_xticks([100, 300, 1000, 3000, 8000])
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.xaxis.set_minor_formatter(FuncFormatter(lambda x, _: ""))

ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8)

# Move legend first, then configure the resulting object to avoid losing changes.
# Tightened padding (borderpad/labelspacing/handletextpad) and a smaller
# markerscale keep the combined hue+size legend from dominating the upper-right
# quadrant, since the size legend's largest swatch tracks the 650pt max marker.
sns.move_legend(ax, "upper right", frameon=True, borderpad=0.5, labelspacing=0.35, handletextpad=0.5, markerscale=0.85)
legend = ax.get_legend()
legend.set_title("Income Tier / Population (M)", prop={"size": 8})
legend.get_title().set_fontweight("semibold")
legend.get_title().set_color(INK)
tier_names = {t[0] for t in tier_params}
for handle, text_obj in zip(legend.legend_handles, legend.texts, strict=False):
    text_obj.set_fontsize(8)
    text_obj.set_color(INK)
    # Size handles (non-tier labels): the combined hue+size legend renders these
    # as Line2D markers, not patches, so recolor via the marker face/edge setters.
    # alpha is set explicitly to 1.0 (not inherited from the scatter's alpha=0.58)
    # so the swatch stays legible against the dark elevated panel.
    if text_obj.get_text() not in tier_names:
        handle.set_markerfacecolor(INK_SOFT)
        handle.set_markeredgecolor(INK_SOFT)
        handle.set_alpha(1.0)
legend.set_frame_on(True)
legend.get_frame().set_alpha(0.92)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_frame().set_facecolor(ELEVATED_BG)

# Save — no bbox_inches='tight' to preserve exact 3200×1800 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
