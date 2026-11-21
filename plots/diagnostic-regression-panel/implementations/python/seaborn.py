"""anyplot.ai
diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: position 1 for the points, 2 for the smoothers, 4 for the Cook's distance contours
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
SMOOTHER = IMPRINT_PALETTE[1]
INFLUENCE = IMPRINT_PALETTE[3]

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

# Constants
COOKS_LEVELS = [(0.5, "--"), (1.0, "-")]  # Cook's distance contour levels and their line styles
N_LABELED = 3  # most influential observations labeled in every panel

# Columns: set these to your table's column names
FITTED = "Fitted values"  # role: fitted
RESIDUALS = "Residuals"  # role: residuals
STD_RESIDUALS = "Standardized residuals"  # role: std_residuals
LEVERAGE = "Leverage"  # role: leverage
COOKS_D = "Cook's distance"  # role: cooks_d

# Data: replace this block with your own table, for example df = pd.read_csv("diagnostics.csv")
np.random.seed(42)
n = 150
X = np.column_stack([np.random.normal(0, 1, n), np.random.normal(0, 1, n), np.random.uniform(-2, 2, n)])
y = X @ np.array([2.5, -1.8, 0.9]) + 5 + np.random.normal(0, 1.5, n)
y[42] += 12  # vertical outlier
y[99] -= 10  # vertical outlier
X[130, 0] = 3.5  # high-leverage point
fit = sm.OLS(y, sm.add_constant(X)).fit()
influence = fit.get_influence()
df = pd.DataFrame(
    {
        FITTED: np.asarray(fit.fittedvalues),
        RESIDUALS: np.asarray(fit.resid),
        STD_RESIDUALS: influence.resid_studentized_internal,
        LEVERAGE: influence.hat_matrix_diag,
        COOKS_D: influence.cooks_distance[0],
    }
)

# Plot: reads only df and the constants above
top = df[COOKS_D].nlargest(N_LABELED).index
sqrt_abs_res = np.sqrt(df[STD_RESIDUALS].abs())
sqrt_label = f"√|{STD_RESIDUALS}|"

# Q-Q: sorted standardized residuals against normal quantiles, each point keeps its observation index
order = np.argsort(df[STD_RESIDUALS].to_numpy())
(theoretical_q, sample_q), (qq_slope, qq_intercept, _) = stats.probplot(df[STD_RESIDUALS])
qq = pd.DataFrame({"theoretical": theoretical_q, "sample": sample_q}, index=df.index[order])

# Parameter count recovered from D = r^2 * h / (p * (1 - h)), so the contours follow the table
h, r, d = df[LEVERAGE], df[STD_RESIDUALS], df[COOKS_D]
n_params = float(np.nanmedian(r**2 * h / ((1 - h) * d)))

fig, axes = plt.subplots(2, 2, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax1, ax2, ax3, ax4 = axes.ravel()

point_kws = {"color": BRAND, "alpha": 0.65, "s": 14, "edgecolor": PAGE_BG, "linewidth": 0.25, "zorder": 2}
reg_point_kws = {**{k: v for k, v in point_kws.items() if k != "linewidth"}, "linewidths": point_kws["linewidth"]}
line_kws = {"color": SMOOTHER, "linewidth": 1.4, "zorder": 3}
annot_kw = {"fontsize": 6.5, "color": INK_MUTED, "xytext": (4, 3), "textcoords": "offset points"}

# Residuals vs Fitted: LOWESS smoother and zero line
sns.regplot(data=df, x=FITTED, y=RESIDUALS, ax=ax1, lowess=True, ci=None, scatter_kws=reg_point_kws, line_kws=line_kws)
ax1.axhline(0, color=INK_SOFT, linewidth=0.8, linestyle="--", alpha=0.7)
for i in top:
    ax1.annotate(str(i), (df.loc[i, FITTED], df.loc[i, RESIDUALS]), **annot_kw)
ax1.set_title("Residuals vs Fitted")

# Normal Q-Q: reference line through the quantiles
sns.scatterplot(data=qq, x="theoretical", y="sample", ax=ax2, **point_kws)
xr = np.array([theoretical_q[0], theoretical_q[-1]])
ax2.plot(xr, qq_slope * xr + qq_intercept, **line_kws)
for i in top:
    ax2.annotate(str(i), (qq.loc[i, "theoretical"], qq.loc[i, "sample"]), **annot_kw)
ax2.set_xlabel("Theoretical quantiles")
ax2.set_ylabel(STD_RESIDUALS)
ax2.set_title("Normal Q-Q")

# Scale-Location: LOWESS smoother on the square root of absolute standardized residuals
sns.regplot(x=df[FITTED], y=sqrt_abs_res, ax=ax3, lowess=True, ci=None, scatter_kws=reg_point_kws, line_kws=line_kws)
for i in top:
    ax3.annotate(str(i), (df.loc[i, FITTED], sqrt_abs_res[i]), **annot_kw)
ax3.set_ylabel(sqrt_label)
ax3.set_title("Scale-Location")

# Residuals vs Leverage: Cook's distance contours, mirrored around zero
sns.scatterplot(data=df, x=LEVERAGE, y=STD_RESIDUALS, ax=ax4, **point_kws)
ax4.axhline(0, color=INK_SOFT, linewidth=0.8, linestyle="--", alpha=0.7)
y_bound = max(df[STD_RESIDUALS].abs().max() * 1.1, 4.0)
lev_rng = np.linspace(max(h.min() * 0.5, 1e-4), min(h.max() * 1.3, 0.99), 400)
for level, ls in COOKS_LEVELS:
    contour = np.sqrt(level * n_params * (1 - lev_rng) / lev_rng)
    inside = contour <= y_bound
    ax4.plot(
        lev_rng[inside], contour[inside], color=INFLUENCE, linewidth=1.2, linestyle=ls, label=f"Cook's D = {level}"
    )
    ax4.plot(lev_rng[inside], -contour[inside], color=INFLUENCE, linewidth=1.2, linestyle=ls)
for i in top:
    ax4.annotate(str(i), (df.loc[i, LEVERAGE], df.loc[i, STD_RESIDUALS]), **annot_kw)
ax4.set_ylim(-y_bound, y_bound)
ax4.set_title("Residuals vs Leverage")
ax4.legend(fontsize=6.5, loc="center right", bbox_to_anchor=(1, 0.74), framealpha=0.9)

# Style
for ax in axes.ravel():
    ax.set_title(ax.get_title(), fontsize=9, color=INK, fontweight="medium")
    ax.set_xlabel(ax.get_xlabel(), fontsize=8, color=INK)
    ax.set_ylabel(ax.get_ylabel(), fontsize=8, color=INK)
    ax.tick_params(labelsize=7, colors=INK_SOFT)
    ax.yaxis.grid(True, alpha=0.10, linewidth=0.6, color=INK)
    sns.despine(ax=ax)

fig.suptitle("diagnostic-regression-panel · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.96))
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
