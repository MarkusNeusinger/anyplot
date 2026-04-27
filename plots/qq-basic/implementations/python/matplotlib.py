"""anyplot.ai
qq-basic: Basic Q-Q Plot
Library: matplotlib | Python 3.13
Quality: pending | Updated: 2026-04-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1 — scatter points
REF_COLOR = "#D55E00"  # Okabe-Ito position 2 — reference line

# Data — sample with slight right skew to show Q-Q deviation clearly
np.random.seed(42)
sample = np.concatenate([np.random.normal(loc=50, scale=10, size=80), np.random.normal(loc=75, scale=5, size=20)])

# Theoretical normal quantiles (Abramowitz & Stegun rational approximation, max error ~1.5e-7)
n = len(sample)
probs = (np.arange(1, n + 1) - 0.5) / n
p_low, p_high = 0.02425, 1 - 0.02425
c = [
    -7.784894002430293e-03,
    -3.223964580411365e-01,
    -2.400758277161838e00,
    -2.549732539343734e00,
    4.374664141464968e00,
    2.938163982698783e00,
]
d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00]
a = [
    -3.969683028665376e01,
    2.209460984245205e02,
    -2.759285104469687e02,
    1.383577518672690e02,
    -3.066479806614716e01,
    2.506628277459239e00,
]
b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02, 6.680131188771972e01, -1.328068155288572e01]

theoretical_q = np.empty(n)
for mask, sign, src in [(probs < p_low, 1, probs), (probs > p_high, -1, 1 - probs)]:
    q = np.sqrt(-2 * np.log(src[mask]))
    theoretical_q[mask] = (
        sign
        * (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
        / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    )
mid = (probs >= p_low) & (probs <= p_high)
q = probs[mid] - 0.5
r = q * q
theoretical_q[mid] = ((((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q) / (
    ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1
)

# Standardize sample to z-scores for comparison with standard normal
sample_sorted = np.sort(sample)
sample_q = (sample_sorted - sample_sorted.mean()) / sample_sorted.std(ddof=1)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.scatter(theoretical_q, sample_q, s=200, alpha=0.7, color=BRAND, edgecolors=PAGE_BG, linewidths=1.5, zorder=3)

line_lo = min(theoretical_q.min(), sample_q.min())
line_hi = max(theoretical_q.max(), sample_q.max())
ax.plot(
    [line_lo, line_hi],
    [line_lo, line_hi],
    color=REF_COLOR,
    linewidth=3,
    linestyle="--",
    label="Reference line (y = x)",
    zorder=2,
)

# Style
ax.set_xlabel("Theoretical Quantiles", fontsize=20, color=INK)
ax.set_ylabel("Sample Quantiles", fontsize=20, color=INK)
ax.set_title("qq-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)
ax.xaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=16, loc="lower right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
