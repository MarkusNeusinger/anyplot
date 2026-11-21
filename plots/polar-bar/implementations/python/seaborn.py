"""anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns
DIRECTION = "direction"  # role: direction
FREQUENCY = "frequency"  # role: frequency

# Data
df = pd.DataFrame(
    {
        DIRECTION: ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"],
        FREQUENCY: [45, 38, 52, 41, 35, 48, 42, 39, 36, 44, 50, 43, 47, 46, 40, 37],
    }
)

# Plot
sns.set_theme(style="white", rc={"axes.facecolor": PAGE_BG, "figure.facecolor": PAGE_BG})
fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="polar")

n_bars = len(df)
angles = np.linspace(0, 2 * np.pi, n_bars, endpoint=False)
ax.bar(
    angles,
    df[FREQUENCY],
    width=2 * np.pi / n_bars * 0.66,
    color=IMPRINT_PALETTE[0],
    alpha=0.85,
    edgecolor=INK_SOFT,
    linewidth=0.8,
)

ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_xticks(angles)
ax.set_xticklabels(df[DIRECTION], fontsize=10, color=INK_SOFT)
ax.set_ylim(0, df[FREQUENCY].max() * 1.1)
ax.set_rlabel_position(180 / n_bars)
ax.tick_params(axis="y", labelsize=8, labelcolor=INK_SOFT)
ax.set_title("polar-bar · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=18)
ax.grid(True, alpha=0.25, color=INK_SOFT, linewidth=0.6)
ax.spines["polar"].set_visible(False)

fig.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.08)
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
