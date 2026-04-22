""" pyplots.ai
bubble-basic: Basic Bubble Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 96/100 | Updated: 2026-02-16
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data - tech company metrics: revenue vs growth with market cap as bubble size
np.random.seed(42)
n_base = 35

revenue_base = np.random.uniform(5, 120, n_base)  # billions USD
growth_base = 0.4 * (100 - revenue_base) / 100 + np.random.randn(n_base) * 0.08 + 0.05
growth_base = np.clip(growth_base, -0.10, 0.55)
cap_base = revenue_base * (1 + growth_base * 3) * np.random.uniform(0.6, 1.8, n_base)
cap_base = np.clip(cap_base, 5, 400)

# Distinctive outlier companies (concise array construction)
outlier_revenue = np.array([18, 12, 118, 55, 85, 95])
outlier_growth = np.array([0.48, 0.44, 0.02, 0.30, -0.05, -0.08])
outlier_cap = np.array([280, 220, 380, 260, 150, 90])

revenue = np.concatenate([revenue_base, outlier_revenue])
growth_rate = np.concatenate([growth_base, outlier_growth])
market_cap = np.concatenate([cap_base, outlier_cap])

n_total = len(revenue)

# Sector assignment for color encoding (4th variable)
sectors = np.array(
    ["Cloud/SaaS"] * 12
    + ["E-Commerce"] * 8
    + ["Semiconductors"] * 8
    + ["Social Media"] * 7
    + ["Cloud/SaaS", "Cloud/SaaS", "Semiconductors", "E-Commerce", "Semiconductors", "E-Commerce"]
)
sector_names = ["Cloud/SaaS", "E-Commerce", "Semiconductors", "Social Media"]
sector_colors = ["#306998", "#E07B39", "#5BA58B", "#8B6BAE"]

# Scale bubble sizes by area for accurate visual perception
size_scaled = (market_cap / market_cap.max()) * 2200 + 120

# Plot with FiveThirtyEight-inspired styling
fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_facecolor("#FAFAFA")
ax.set_facecolor("#FAFAFA")

# Plot each sector separately for legend
scatter_handles = []
for sector, color in zip(sector_names, sector_colors, strict=True):
    mask = sectors == sector
    sc = ax.scatter(
        revenue[mask],
        growth_rate[mask] * 100,
        s=size_scaled[mask],
        alpha=0.65,
        color=color,
        edgecolors="white",
        linewidths=1.5,
        label=sector,
        zorder=3,
    )
    scatter_handles.append(sc)

# Annotate notable outliers to guide the viewer
annotations = [
    (n_base, "High-Growth\nUnicorn", (-70, 22)),
    (n_base + 2, "Market\nLeader", (-85, 55)),
    (n_base + 3, "Breakout\nPerformer", (60, 35)),
]
for idx, label, offset in annotations:
    ax.annotate(
        label,
        (revenue[idx], growth_rate[idx] * 100),
        fontsize=13,
        fontweight="bold",
        color="#333333",
        ha="center",
        va="bottom",
        xytext=offset,
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "color": "#666666", "lw": 1.2, "connectionstyle": "arc3,rad=0.15"},
        path_effects=[pe.withStroke(linewidth=3, foreground="#FAFAFA")],
    )

# Size legend — positioned lower left to avoid data overlap
legend_caps = [25, 100, 300]
legend_handles = [
    ax.scatter(
        [], [], s=(v / market_cap.max()) * 2200 + 120, c="#AAAAAA", alpha=0.5, edgecolors="white", linewidths=1.2
    )
    for v in legend_caps
]
size_legend = ax.legend(
    legend_handles,
    [f"${v}B" for v in legend_caps],
    title="Market Cap",
    title_fontsize=14,
    fontsize=13,
    loc="lower left",
    framealpha=0.95,
    facecolor="#FAFAFA",
    edgecolor="#DDDDDD",
    scatterpoints=1,
    labelspacing=1.8,
    borderpad=1.2,
)
ax.add_artist(size_legend)

# Sector color legend — positioned upper right, compact, away from data
sector_legend = ax.legend(
    fontsize=13,
    loc="upper right",
    framealpha=0.95,
    facecolor="#FAFAFA",
    edgecolor="#DDDDDD",
    title="Sector",
    title_fontsize=14,
    markerscale=0.5,
    handletextpad=0.6,
    borderpad=0.8,
)

# Axis styling — FiveThirtyEight-inspired
ax.set_xlabel("Annual Revenue ($B)", fontsize=20, color="#333333", labelpad=10)
ax.set_ylabel("Revenue Growth Rate (%)", fontsize=20, color="#333333", labelpad=10)
ax.set_title("bubble-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", color="#222222", pad=16)
ax.tick_params(axis="both", labelsize=16, colors="#555555")

# Spines — remove all, use horizontal grid lines only for clean look
for spine in ax.spines.values():
    spine.set_visible(False)

ax.yaxis.grid(True, alpha=0.3, linewidth=0.8, color="#CCCCCC", zorder=0)
ax.xaxis.grid(False)

# Horizontal baseline at 0% growth for reference
ax.axhline(y=0, color="#999999", linewidth=1.0, linestyle="-", zorder=1, alpha=0.6)

# Expand x-axis slightly for breathing room
ax.set_xlim(-5, 140)
ax.set_ylim(-15, 60)

# Subtle source annotation
ax.text(0.99, 0.01, "pyplots.ai", transform=ax.transAxes, fontsize=11, color="#AAAAAA", ha="right", va="bottom")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="#FAFAFA")
