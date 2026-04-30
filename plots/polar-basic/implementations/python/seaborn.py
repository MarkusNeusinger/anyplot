"""anyplot.ai
polar-basic: Basic Polar Chart
Library: seaborn | Python 3.13
Quality: pending | Updated: 2026-04-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

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

# Data: Hourly website traffic (24-hour cycle)
np.random.seed(42)
hours = np.arange(0, 24)
theta = hours * (2 * np.pi / 24)

base_traffic = 100
morning_peak = 80 * np.exp(-0.5 * ((hours - 10) / 2) ** 2)
evening_peak = 100 * np.exp(-0.5 * ((hours - 20) / 2.5) ** 2)
noise = np.random.normal(0, 10, 24)
traffic = base_traffic + morning_peak + evening_peak + noise
traffic = np.clip(traffic, 20, None)

# Plot (square format for radial symmetry)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Scatter points colored by traffic intensity (continuous → viridis)
scatter = ax.scatter(
    theta, traffic, c=traffic, cmap="viridis", s=280, alpha=0.9, edgecolors=PAGE_BG, linewidths=1.5, zorder=5
)

# Connecting line and fill using BRAND color
theta_closed = np.append(theta, theta[0])
traffic_closed = np.append(traffic, traffic[0])
ax.plot(theta_closed, traffic_closed, color=BRAND, linewidth=2.5, alpha=0.85, zorder=4)
ax.fill(theta_closed, traffic_closed, color=BRAND, alpha=0.12, zorder=3)

# Style
ax.set_title(
    "Website Traffic by Hour · polar-basic · seaborn · anyplot.ai", fontsize=22, fontweight="medium", pad=28, color=INK
)

# Angular labels (24 hours)
ax.set_xticks(np.linspace(0, 2 * np.pi, 24, endpoint=False))
hour_labels = [f"{h:02d}:00" for h in range(24)]
ax.set_xticklabels(hour_labels, fontsize=13, color=INK_SOFT)

# Radial range and label
ax.set_ylim(0, max(traffic) * 1.15)
ax.set_ylabel("Visitors/hr", fontsize=18, labelpad=35, color=INK)
ax.yaxis.set_label_position("right")
ax.tick_params(axis="y", labelsize=13, colors=INK_SOFT)

# Grid: subtle, theme-adaptive
ax.grid(True, alpha=0.12, linewidth=0.8, color=INK)
ax.spines["polar"].set_color(INK_SOFT)
ax.spines["polar"].set_linewidth(1.0)

# Colorbar
cbar = plt.colorbar(scatter, ax=ax, pad=0.13, shrink=0.75)
cbar.set_label("Traffic Volume", fontsize=16, color=INK)
cbar.ax.tick_params(labelsize=13, colors=INK_SOFT)
plt.setp(cbar.ax.yaxis.get_ticklabels(), color=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)
cbar.ax.set_facecolor(PAGE_BG)

# Start at top (12 o'clock), clockwise direction
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
