"""anyplot.ai
lift-curve: Model Lift Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Seaborn theme with theme-adaptive chrome
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
RANDOM_LIFT = 1.0  # lift of random selection
KEY_PERCENTILES = [10, 20, 30, 40, 50]  # share of the population marked on the curve

# Columns: set these to your table's column names
Y_TRUE = "Responded"  # role: y_true
Y_SCORE = "Model score"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# Simulated customer response prediction for a marketing campaign
np.random.seed(42)
n_samples = 1000
base_response_rate = 0.10
latent_propensity = np.random.normal(0, 1, n_samples)
score = latent_propensity + np.random.normal(0, 0.3, n_samples)
score = (score - score.min()) / (score.max() - score.min())
response_threshold = np.percentile(latent_propensity, 100 * (1 - base_response_rate))
df = pd.DataFrame({Y_TRUE: (latent_propensity >= response_threshold).astype(int), Y_SCORE: score})

# Plot: reads only df and the constants above
ranked = df.dropna().sort_values(Y_SCORE, ascending=False, kind="stable")
n_ranked = len(ranked)
n_targeted = np.arange(1, n_ranked + 1)
baseline_rate = ranked[Y_TRUE].mean()
curve = pd.DataFrame(
    {
        "Population Targeted (%)": n_targeted / n_ranked * 100,
        "Cumulative Lift Ratio": ranked[Y_TRUE].cumsum().to_numpy() / n_targeted / baseline_rate,
    }
)
POPULATION, LIFT = curve.columns

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.lineplot(data=curve, x=POPULATION, y=LIFT, ax=ax, color=BRAND, linewidth=1.8, label="Model lift")

# Random-selection reference line
ax.axhline(RANDOM_LIFT, color=INK_SOFT, linestyle="--", linewidth=1.4, label="Random selection (lift = 1)", zorder=3)

# Key-percentile markers sitting on the curve, with their lift values
marks = curve.iloc[[int(n_ranked * pct / 100) - 1 for pct in KEY_PERCENTILES]]
sns.scatterplot(data=marks, x=POPULATION, y=LIFT, ax=ax, color=BRAND, s=45, edgecolor=PAGE_BG, linewidth=1, zorder=5)
for pop_pct, lift_val in zip(marks[POPULATION], marks[LIFT], strict=True):
    ax.annotate(
        f"{lift_val:.2f}x",
        (pop_pct, lift_val),
        textcoords="offset points",
        xytext=(7, 7),
        ha="left",
        fontsize=8,
        fontweight="bold",
        color=INK,
    )

# Style
ax.set_title("lift-curve · python · seaborn · anyplot.ai", fontsize=12, fontweight="bold", color=INK)
ax.set_xlabel(POPULATION, fontsize=10)
ax.set_ylabel(LIFT, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.6, color=INK)
ax.set_xlim(0, 100)
ax.set_ylim(0, max(curve[LIFT].max(), RANDOM_LIFT) * 1.1)

legend = ax.legend(fontsize=8, loc="upper right", framealpha=0.95)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
