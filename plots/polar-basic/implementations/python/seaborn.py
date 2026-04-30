""" anyplot.ai
polar-basic: Basic Polar Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 85/100 | Updated: 2026-04-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

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

df = pd.DataFrame({"theta": theta, "traffic": traffic})

# Plot (square format for radial symmetry)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Start at top (12 o'clock), clockwise direction — set before plotting
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)

# Scatter points: sns.scatterplot with continuous hue for viridis coloring
sns.scatterplot(
    data=df,
    x="theta",
    y="traffic",
    hue="traffic",
    palette="viridis",
    s=280,
    alpha=0.9,
    ax=ax,
    legend=False,
    edgecolor=PAGE_BG,
    linewidth=1.5,
    zorder=5,
)

# Connecting line: sns.lineplot on polar axes
theta_closed = np.append(theta, theta[0])
traffic_closed = np.append(traffic, traffic[0])
df_line = pd.DataFrame({"theta": theta_closed, "traffic": traffic_closed})
sns.lineplot(
    data=df_line,
    x="theta",
    y="traffic",
    color=BRAND,
    linewidth=2.5,
    alpha=0.85,
    ax=ax,
    sort=False,
    estimator=None,
    zorder=4,
)

# Fill under the polygon (no seaborn equivalent for polar fill)
ax.fill(theta_closed, traffic_closed, color=BRAND, alpha=0.12, zorder=3)
ax.set_xlabel("")  # remove "theta" label added by sns.lineplot

# Style
ax.set_title(
    "Website Traffic by Hour · polar-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", pad=28, color=INK
)

# Angular labels: every 2 hours (12 labels) to reduce perimeter crowding
tick_hours = np.arange(0, 24, 2)
tick_theta = tick_hours * (2 * np.pi / 24)
ax.set_xticks(tick_theta)
ax.set_xticklabels([f"{h:02d}:00" for h in tick_hours], fontsize=16, color=INK_SOFT)

# Radial range and label
ax.set_ylim(0, max(traffic) * 1.15)
ax.set_ylabel("Visitors/hr", fontsize=20, labelpad=35, color=INK)
ax.yaxis.set_label_position("right")
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)

# Grid: subtle, theme-adaptive
ax.grid(True, alpha=0.12, linewidth=0.8, color=INK)
ax.spines["polar"].set_color(INK_SOFT)
ax.spines["polar"].set_linewidth(1.0)

# Colorbar via ScalarMappable (seaborn handles point colors; we build the bar explicitly)
norm = Normalize(vmin=traffic.min(), vmax=traffic.max())
sm = ScalarMappable(cmap="viridis", norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.13, shrink=0.75)
cbar.set_label("Traffic Volume", fontsize=16, color=INK)
cbar.ax.tick_params(labelsize=16, colors=INK_SOFT)
plt.setp(cbar.ax.yaxis.get_ticklabels(), color=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)
cbar.ax.set_facecolor(PAGE_BG)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
