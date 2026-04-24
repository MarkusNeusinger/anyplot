""" anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: matplotlib 3.10.9 | Python 3.14.4
Quality: 89/100 | Updated: 2026-04-24
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

# Data: API response times (ms) — log-normal distribution with a long tail
np.random.seed(42)
response_times_ms = np.random.lognormal(mean=4.6, sigma=0.55, size=250)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.ecdf(response_times_ms, color=BRAND, linewidth=3.5)

# Percentile reference lines (p50, p95, p99) — common SRE reading
percentiles = [50, 95, 99]
percentile_values = np.percentile(response_times_ms, percentiles)
for p, v in zip(percentiles, percentile_values, strict=True):
    ax.axhline(y=p / 100, color=INK_SOFT, linestyle=":", linewidth=1.5, alpha=0.6)
    ax.axvline(x=v, ymax=p / 100, color=INK_SOFT, linestyle=":", linewidth=1.5, alpha=0.6)
    ax.annotate(
        f"p{p}  {v:.0f} ms",
        xy=(v, p / 100),
        xytext=(10, -18 if p == 99 else 8),
        textcoords="offset points",
        fontsize=14,
        color=INK_SOFT,
    )

# Style
ax.set_xlabel("Response Time (ms)", fontsize=20, color=INK)
ax.set_ylabel("Cumulative Proportion of Requests", fontsize=20, color=INK)
ax.set_title("API Response Times · ecdf-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_ylim(0, 1.02)
ax.set_xlim(left=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.grid(True, alpha=0.10, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
