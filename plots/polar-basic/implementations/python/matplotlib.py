"""anyplot.ai
polar-basic: Basic Polar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-04-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
HOURS_PER_DAY = 24  # the cycle the angle wraps around
LABEL_STEP = 3  # hours between angular labels

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: theta
VISITORS = "Visitors per hour"  # role: radius

# Data: replace this block with your own table, for example df = pd.read_csv("footfall.csv")
rng = np.random.default_rng(42)
hours = np.arange(HOURS_PER_DAY)
morning_rush = 62 * np.exp(-((hours - 8) ** 2) / (2 * 1.3**2))
lunch_rush = 85 * np.exp(-((hours - 13) ** 2) / (2 * 1.6**2))
baseline = 6 + 10 * np.exp(-((hours - 17) ** 2) / (2 * 3.0**2))
visitors = np.clip(baseline + morning_rush + lunch_rush + rng.normal(0, 3, HOURS_PER_DAY), 0, None).round()
df = pd.DataFrame({HOUR: hours, VISITORS: visitors})

# Plot: reads only df and the constants above
theta = df[HOUR].to_numpy() * (2 * np.pi / HOURS_PER_DAY)
radius = df[VISITORS].to_numpy()
theta_closed = np.append(theta, theta[0])
radius_closed = np.append(radius, radius[0])

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Filled area from the center to the data gives the cycle its weight
ax.fill_between(theta_closed, 0, radius_closed, color=IMPRINT_PALETTE[0], alpha=0.18)

# Connecting line shows the cyclical pattern
ax.plot(theta_closed, radius_closed, color=IMPRINT_PALETTE[0], linewidth=2.5, alpha=0.9, zorder=2)

# One marker per hourly reading
ax.scatter(theta, radius, s=70, color=IMPRINT_PALETTE[0], zorder=3, edgecolors=PAGE_BG, linewidth=0.8)

# Angular axis: midnight at the top, clockwise, a label every three hours
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
label_hours = np.arange(0, HOURS_PER_DAY, LABEL_STEP)
ax.set_xticks(label_hours * (2 * np.pi / HOURS_PER_DAY))
ax.set_xticklabels([f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}" for h in label_hours], fontsize=10)

# Radial axis: starts at zero and spreads the data over the radius
ax.set_ylim(0, np.nanmax(radius) * 1.1)
ax.set_rlabel_position(67.5)
ax.tick_params(axis="y", labelsize=8)
ax.set_ylabel(VISITORS, fontsize=10, color=INK, labelpad=30)

# Theme-adaptive styling
ax.set_title(
    "Café Footfall · polar-basic · python · matplotlib · anyplot.ai",
    fontsize=11,
    pad=20,
    fontweight="medium",
    color=INK,
)
ax.grid(True, alpha=0.2, linewidth=0.8, color=INK)
ax.spines["polar"].set_color(INK_SOFT)
ax.tick_params(colors=INK_SOFT, labelcolor=INK_SOFT)

fig.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.08)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
