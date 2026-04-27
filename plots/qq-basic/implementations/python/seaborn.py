"""anyplot.ai
qq-basic: Basic Q-Q Plot
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-04-27
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

# Data - mixture distribution with right-skewed tail to demonstrate Q-Q deviation
np.random.seed(42)
sample = np.concatenate([np.random.normal(loc=50, scale=10, size=180), np.random.normal(loc=75, scale=5, size=20)])
n = len(sample)

# Theoretical quantiles via Abramowitz & Stegun 26.2.17 rational approximation
p = (np.arange(1, n + 1) - 0.5) / n
t = np.where(p < 0.5, np.sqrt(-2 * np.log(p)), np.sqrt(-2 * np.log(1 - p)))
num = 2.515517 + 0.802853 * t + 0.010328 * t**2
den = 1 + 1.432788 * t + 0.189269 * t**2 + 0.001308 * t**3
theoretical_q = np.where(p < 0.5, -(t - num / den), t - num / den)
sample_q = np.sort((sample - sample.mean()) / sample.std(ddof=1))

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.scatterplot(x=theoretical_q, y=sample_q, ax=ax, s=200, color=BRAND, alpha=0.7, edgecolor=PAGE_BG, linewidth=0.5)

# Reference line (y=x for perfect normal distribution)
q_min = min(theoretical_q.min(), sample_q.min())
q_max = max(theoretical_q.max(), sample_q.max())
ax.plot(
    [q_min, q_max], [q_min, q_max], color=INK_SOFT, linewidth=2.5, linestyle="--", label="Reference (y=x)", zorder=1
)

# Style
ax.set_xlabel("Theoretical Quantiles", fontsize=20, color=INK)
ax.set_ylabel("Sample Quantiles", fontsize=20, color=INK)
ax.set_title("qq-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.legend(fontsize=16, loc="upper left")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.grid(True, alpha=0.10, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
