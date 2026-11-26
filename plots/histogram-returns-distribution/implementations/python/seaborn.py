"""anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-11-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch
from scipy import stats


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
    },
)

# Columns: set these to your table's column names
MONTH = "Month"  # role: date
RETURN = "Monthly return (%)"  # role: returns

# Constants
N_SIGMA = 2  # tail regions lie beyond this many standard deviations from the mean

# Data: replace this block with your own table, for example df = pd.read_csv("returns.csv")
rng = np.random.default_rng(7)
n_months = 300  # 25 years of monthly hedge-fund returns
crash = rng.random(n_months) < 0.07  # occasional drawdown months make the left tail heavy
monthly_returns = np.where(crash, rng.normal(-4.2, 2.6, n_months), rng.normal(0.85, 1.6, n_months))
df = pd.DataFrame({MONTH: pd.date_range("2000-01-31", periods=n_months, freq="ME"), RETURN: monthly_returns})

# Plot
returns = df[RETURN].dropna()
mean_ret = returns.mean()
std_ret = returns.std(ddof=0)
skewness = stats.skew(returns)
kurtosis = stats.kurtosis(returns)

lower_tail = mean_ret - N_SIGMA * std_ret
upper_tail = mean_ret + N_SIGMA * std_ret

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

bins = np.histogram_bin_edges(returns, bins=30)

# Single histplot on the full dataset so all bars share the same density normalization;
# recolor tail-region bars afterward (two-call approach normalizes each subset independently)
sns.histplot(data=df, x=RETURN, bins=bins, stat="density", color=IMPRINT[0], alpha=0.7, ax=ax)
for patch in ax.patches:
    bin_center = patch.get_x() + patch.get_width() / 2
    if bin_center < lower_tail or bin_center > upper_tail:
        patch.set_facecolor(IMPRINT[1])
        patch.set_alpha(0.85)

# Empirical KDE via seaborn
sns.kdeplot(data=df, x=RETURN, ax=ax, color=IMPRINT[0], linewidth=1.5, linestyle=":", alpha=0.8)
kde_line = ax.lines[-1]

# Normal distribution curve fitted to the data
x_range = np.linspace(returns.min() - 0.5, returns.max() + 0.5, 300)
normal_pdf = stats.norm.pdf(x_range, mean_ret, std_ret)
ax.plot(x_range, normal_pdf, color=IMPRINT[2], linewidth=2.0)
normal_line = ax.lines[-1]

# Vertical dashed lines at the tail boundaries
ax.axvline(lower_tail, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.7)
ax.axvline(upper_tail, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.7)

# Statistics text box, upper left: the long tail is on the left, the right side is open
stats_text = (
    f"Statistics\n"
    f"{'─' * 18}\n"
    f"Mean: {mean_ret:.3f}%\n"
    f"Std Dev: {std_ret:.3f}%\n"
    f"Skewness: {skewness:.3f}\n"
    f"Kurtosis: {kurtosis:.3f}"
)
ax.text(
    0.025,
    0.97,
    stats_text,
    transform=ax.transAxes,
    fontsize=8,
    verticalalignment="top",
    horizontalalignment="left",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
    color=INK,
)

ax.set_xlabel(RETURN, fontsize=10)
ax.set_ylabel("Density", fontsize=10)
ax.set_title("histogram-returns-distribution · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium")
ax.tick_params(axis="both", labelsize=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legend: histogram bars first (primary data), then analytical curves; no frame
center_patch = Patch(facecolor=IMPRINT[0], alpha=0.7, label=f"Returns (±{N_SIGMA}σ)")
tail_patch = Patch(facecolor=IMPRINT[1], alpha=0.7, label=f"Tail regions (>{N_SIGMA}σ)")
kde_line.set_label("Empirical KDE")
normal_line.set_label("Normal fit")
ax.legend(handles=[center_patch, tail_patch, kde_line, normal_line], fontsize=8, loc="lower left", frameon=False)

ax.yaxis.grid(True, alpha=0.12, linewidth=0.5)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
