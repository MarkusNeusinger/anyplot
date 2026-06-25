""" anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: matplotlib 3.11.0 | Python 3.13.14
Quality: 89/100 | Updated: 2026-06-25
"""

import os

import matplotlib.pyplot as plt
import numpy as np


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1

# Data: IoT sensor temperature readings (°C) — bimodal mix of offices and server rooms
np.random.seed(7)
office = np.random.normal(loc=22.0, scale=1.8, size=160)
servers = np.random.normal(loc=18.5, scale=0.9, size=90)
temps = np.concatenate([office, servers])
t_min = temps.min()

# Canvas — 3200 × 1800 px landscape (figsize × dpi, no bbox_inches='tight')
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# ECDF step function
ax.ecdf(temps, color=BRAND, linewidth=2.5)

# Quartile reference guides (Q1, Q2, Q3)
quartiles = [25, 50, 75]
q_values = np.percentile(temps, quartiles)
for q, v in zip(quartiles, q_values, strict=True):
    yf = q / 100
    ax.plot([t_min - 0.3, v], [yf, yf], color=INK_MUTED, linestyle=":", linewidth=0.8, alpha=0.6)
    ax.plot([v, v], [0, yf], color=INK_MUTED, linestyle=":", linewidth=0.8, alpha=0.6)
    ax.annotate(
        f"Q{q // 25}  {v:.1f}°C", xy=(v, yf), xytext=(5, 5), textcoords="offset points", fontsize=8, color=INK_MUTED
    )

# Chrome
title = "Sensor Temperatures · ecdf-basic · python · matplotlib · anyplot.ai"
title_fs = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fs, fontweight="medium", color=INK)
ax.set_xlabel("Temperature (°C)", fontsize=10, color=INK)
ax.set_ylabel("Cumulative Proportion", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.set_ylim(0, 1.02)
ax.set_xlim(left=t_min - 0.5)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

fig.subplots_adjust(left=0.09, right=0.97, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
