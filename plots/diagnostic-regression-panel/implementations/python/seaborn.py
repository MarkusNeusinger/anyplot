""" anyplot.ai
diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Created: 2026-05-13
"""

import os
import sys


sys.path.pop(0)

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import statsmodels.api as sm
from scipy import stats


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"
ACCENT = "#C475FD"
INFLUENCE = "#BD8233"

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

np.random.seed(42)
n = 150
X = np.column_stack([np.random.normal(0, 1, n), np.random.normal(0, 1, n), np.random.uniform(-2, 2, n)])
y = X @ np.array([2.5, -1.8, 0.9]) + 5 + np.random.normal(0, 1.5, n)
y[42] += 12
y[99] -= 10
X[130, 0] = 3.5

X_sm = sm.add_constant(X)
model = sm.OLS(y, X_sm).fit()
infl = model.get_influence()

fitted = np.asarray(model.fittedvalues)
residuals = np.asarray(model.resid)
std_res = infl.resid_studentized_internal
leverage = infl.hat_matrix_diag
cooks_d = infl.cooks_distance[0]

p = X_sm.shape[1]
top3 = list(np.argsort(cooks_d)[-3:])
sorted_idx = np.argsort(std_res)
(theoretical_q, sample_q), (qq_slope, qq_intercept, _) = stats.probplot(std_res)

fig, axes = plt.subplots(2, 2, figsize=(16, 9), facecolor=PAGE_BG)
fig.patch.set_facecolor(PAGE_BG)

regplot_sc_kws = {"color": BRAND, "alpha": 0.65, "s": 70, "edgecolors": PAGE_BG, "linewidths": 0.4, "zorder": 2}
line_kws = {"color": ACCENT, "linewidth": 2.5, "zorder": 3}
annot_kw = {"fontsize": 14, "color": INK_MUTED, "xytext": (14, 10), "textcoords": "offset points"}

# Subplot 1: Residuals vs Fitted — sns.regplot with LOWESS smoother
ax1 = axes[0, 0]
sns.regplot(x=fitted, y=residuals, ax=ax1, lowess=True, ci=None, scatter_kws=regplot_sc_kws, line_kws=line_kws)
ax1.axhline(0, color=INK_SOFT, linewidth=1.2, linestyle="--", alpha=0.7)
for i in top3:
    ax1.annotate(str(i), (fitted[i], residuals[i]), **annot_kw)
ax1.set_xlabel("Fitted Values", fontsize=20, color=INK)
ax1.set_ylabel("Residuals", fontsize=20, color=INK)
ax1.set_title("Residuals vs Fitted", fontsize=20, color=INK, fontweight="medium")
ax1.tick_params(labelsize=16, colors=INK_SOFT)
sns.despine(ax=ax1)
ax1.spines["left"].set_color(INK_SOFT)
ax1.spines["bottom"].set_color(INK_SOFT)
ax1.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Subplot 2: Normal Q-Q — sns.scatterplot with Q-Q reference line
ax2 = axes[0, 1]
sns.scatterplot(
    x=theoretical_q, y=sample_q, ax=ax2, color=BRAND, alpha=0.65, s=70, edgecolor=PAGE_BG, linewidth=0.4, zorder=2
)
xr = np.array([theoretical_q[0], theoretical_q[-1]])
ax2.plot(xr, qq_slope * xr + qq_intercept, color=ACCENT, linewidth=2.5, zorder=3)
for k, orig in enumerate(sorted_idx):
    if orig in top3:
        ax2.annotate(str(orig), (theoretical_q[k], sample_q[k]), **annot_kw)
ax2.set_xlabel("Theoretical Quantiles", fontsize=20, color=INK)
ax2.set_ylabel("Standardized Residuals", fontsize=20, color=INK)
ax2.set_title("Normal Q-Q", fontsize=20, color=INK, fontweight="medium")
ax2.tick_params(labelsize=16, colors=INK_SOFT)
sns.despine(ax=ax2)
ax2.spines["left"].set_color(INK_SOFT)
ax2.spines["bottom"].set_color(INK_SOFT)
ax2.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Subplot 3: Scale-Location — sns.regplot with LOWESS smoother
ax3 = axes[1, 0]
sqrt_abs_res = np.sqrt(np.abs(std_res))
sns.regplot(x=fitted, y=sqrt_abs_res, ax=ax3, lowess=True, ci=None, scatter_kws=regplot_sc_kws, line_kws=line_kws)
for i in top3:
    ax3.annotate(str(i), (fitted[i], sqrt_abs_res[i]), **annot_kw)
ax3.set_xlabel("Fitted Values", fontsize=20, color=INK)
ax3.set_ylabel("√|Standardized Residuals|", fontsize=20, color=INK)
ax3.set_title("Scale-Location", fontsize=20, color=INK, fontweight="medium")
ax3.tick_params(labelsize=16, colors=INK_SOFT)
sns.despine(ax=ax3)
ax3.spines["left"].set_color(INK_SOFT)
ax3.spines["bottom"].set_color(INK_SOFT)
ax3.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Subplot 4: Residuals vs Leverage — sns.scatterplot with Cook's D contours
ax4 = axes[1, 1]
sns.scatterplot(
    x=leverage, y=std_res, ax=ax4, color=BRAND, alpha=0.65, s=70, edgecolor=PAGE_BG, linewidth=0.4, zorder=2
)
ax4.axhline(0, color=INK_SOFT, linewidth=1.2, linestyle="--", alpha=0.7)
y_bound = max(np.abs(std_res).max() * 1.1, 4.0)
lev_rng = np.linspace(max(leverage.min() * 0.5, 1e-4), min(leverage.max() * 1.3, 0.99), 400)
for cd_level, ls in [(0.5, "--"), (1.0, "-")]:
    cd_vals = np.sqrt(cd_level * p * (1 - lev_rng) / lev_rng)
    valid = cd_vals <= y_bound
    if valid.any():
        ax4.plot(
            lev_rng[valid],
            cd_vals[valid],
            color=INFLUENCE,
            linewidth=1.8,
            linestyle=ls,
            alpha=0.8,
            label=f"Cook's D={cd_level}",
        )
        ax4.plot(lev_rng[valid], -cd_vals[valid], color=INFLUENCE, linewidth=1.8, linestyle=ls, alpha=0.8)
for i in top3:
    ax4.annotate(str(i), (leverage[i], std_res[i]), **annot_kw)
ax4.set_ylim(-y_bound, y_bound)
ax4.set_xlabel("Leverage", fontsize=20, color=INK)
ax4.set_ylabel("Standardized Residuals", fontsize=20, color=INK)
ax4.set_title("Residuals vs Leverage", fontsize=20, color=INK, fontweight="medium")
ax4.tick_params(labelsize=16, colors=INK_SOFT)
sns.despine(ax=ax4)
ax4.spines["left"].set_color(INK_SOFT)
ax4.spines["bottom"].set_color(INK_SOFT)
ax4.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax4.legend(fontsize=14, loc="upper right", framealpha=0.9)

fig.suptitle("diagnostic-regression-panel · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
