"""anyplot.ai
band-basic: Basic Band Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import os

import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch


# Theme tokens (Imprint palette + theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — first series always #009E73
BAND_COLOR = "#009E73"  # Imprint position 1 — confidence band
LINE_COLOR = "#C475FD"  # Imprint position 2 — center forecast line

# Column names (written as the axis titles read)
DAY = "Day of Month"  # role: x
LOWER = "Lower bound (°C)"  # role: y_lower
UPPER = "Upper bound (°C)"  # role: y_upper
CENTER = "Temperature (°C)"  # role: y_center

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
# 30-day temperature forecast with an asymmetric 95% confidence interval
days = np.arange(1, 31)
temp_forecast = 12 + 6 * np.sin(np.pi * days / 30) + 0.1 * days
uncertainty_base = 0.8 + 0.12 * days
df = pd.DataFrame(
    {
        DAY: days,
        LOWER: temp_forecast - uncertainty_base * 0.7,  # narrower lower tail
        UPPER: temp_forecast + uncertainty_base * 1.3,  # wider upper tail (warm bias)
        CENTER: temp_forecast,
    }
)

# Plot
d = df.dropna().sort_values(DAY)  # rows with a missing value cannot be interpolated
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Gradient band using pcolormesh with gouraud shading
band_rgb = mcolors.to_rgb(BAND_COLOR)
x_fine = np.linspace(d[DAY].min(), d[DAY].max(), 300)
c_fine = np.interp(x_fine, d[DAY], d[CENTER])
lo_fine = np.interp(x_fine, d[DAY], d[LOWER])
hi_fine = np.interp(x_fine, d[DAY], d[UPPER])

n_vert = 100
X = np.tile(x_fine, (n_vert, 1))
Y = np.zeros((n_vert, len(x_fine)))
C = np.zeros((n_vert, len(x_fine)))

for j in range(len(x_fine)):
    Y[:, j] = np.linspace(lo_fine[j], hi_fine[j], n_vert)
    hw = (hi_fine[j] - lo_fine[j]) / 2
    C[:, j] = 1 - np.abs(Y[:, j] - c_fine[j]) / hw

cmap = mcolors.LinearSegmentedColormap.from_list("ci", [(*band_rgb, 0.02), (*band_rgb, 0.22), (*band_rgb, 0.45)])
ax.pcolormesh(X, Y, C, cmap=cmap, shading="gouraud", rasterized=True, zorder=1)

# Boundary dashed lines
ax.plot(d[DAY], d[LOWER], color=BAND_COLOR, lw=1.5, ls="--", alpha=0.65, zorder=2)
ax.plot(d[DAY], d[UPPER], color=BAND_COLOR, lw=1.5, ls="--", alpha=0.65, zorder=2)

# Center forecast line with glow effect
ax.plot(
    d[DAY],
    d[CENTER],
    color=LINE_COLOR,
    linewidth=2.5,
    zorder=3,
    path_effects=[pe.Stroke(linewidth=5, foreground=LINE_COLOR, alpha=0.2), pe.Normal()],
)

# Legend
legend_handles = [
    Patch(facecolor=BAND_COLOR, alpha=0.35, edgecolor=BAND_COLOR, label="95% Confidence Interval"),
    plt.Line2D([0], [0], color=LINE_COLOR, linewidth=2.5, label="Forecast Mean"),
]
leg = ax.legend(handles=legend_handles, fontsize=8, loc="upper left")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Style
title = "band-basic · python · matplotlib · anyplot.ai"
n = len(title)
title_fontsize = max(8, round(12 * 67 / n)) if n > 67 else 12

ax.set_xlabel(DAY, fontsize=10, color=INK)
ax.set_ylabel(CENTER, fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

fig.tight_layout()
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
