"""anyplot.ai
qq-basic: Basic Q-Q Plot
Library: matplotlib 3.10.9 | Python 3.14.4
Quality: pending | Updated: 2026-07-24
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — scatter points
REF_COLOR = "#C475FD"  # Imprint palette position 2 — reference line

# Data: systolic blood pressure (mmHg) from a mixed patient cohort
# Bimodal mixture of normotensive (n=75) and hypertensive (n=25) patients
np.random.seed(42)
normotensive = np.random.normal(loc=120, scale=10, size=75)
hypertensive = np.random.normal(loc=155, scale=15, size=25)
bp_readings = np.concatenate([normotensive, hypertensive])

# Standardize for comparison with the N(0,1) reference distribution
bp_std = (bp_readings - bp_readings.mean()) / bp_readings.std(ddof=1)

# Compute Q-Q quantiles via scipy.stats.probplot (idiomatic ecosystem approach)
(theoretical_q, sample_q), _ = stats.probplot(bp_std, dist="norm")
theoretical_q = np.array(theoretical_q)
sample_q = np.array(sample_q)

# 95% pointwise confidence band: where sample quantiles should fall if data were normal
n = len(bp_std)
probs = (np.arange(1, n + 1) - 0.5) / n
phi_z = stats.norm.pdf(theoretical_q)
se = np.sqrt(probs * (1 - probs)) / (np.sqrt(n) * phi_z)
ci_low = theoretical_q - 1.96 * se
ci_high = theoretical_q + 1.96 * se

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# 95% confidence band — points outside reveal non-normality
ax.fill_between(theoretical_q, ci_low, ci_high, color=BRAND, alpha=0.22, label="95% CI band", zorder=1)

# Sample quantile scatter
ax.scatter(theoretical_q, sample_q, s=100, alpha=0.75, color=BRAND, edgecolors=PAGE_BG, linewidths=0.8, zorder=3)

# Reference line y = x
ref_lo = min(theoretical_q.min(), sample_q.min())
ref_hi = max(theoretical_q.max(), sample_q.max())
ax.plot(
    [ref_lo, ref_hi],
    [ref_lo, ref_hi],
    color=REF_COLOR,
    linewidth=2.5,
    linestyle="--",
    label="Reference line (y = x)",
    zorder=2,
)

# Style
ax.set_xlabel("Theoretical Quantiles", fontsize=10, color=INK)
ax.set_ylabel("Sample Quantiles", fontsize=10, color=INK)
ax.set_title("qq-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=8, loc="lower right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
