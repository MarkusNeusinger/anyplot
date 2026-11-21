""" anyplot.ai
gain-curve: Cumulative Gains Chart
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-21
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

# Imprint palette: canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"

# Configure seaborn theme
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

# Columns: set these to your table's column names
CHURNED = "Churned (1 = yes)"  # role: y_true
CHURN_SCORE = "Predicted churn score"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
n_samples = 1000
# Customer churn scenario with ~30% positive class (churners)
y_true = np.random.choice([0, 1], size=n_samples, p=[0.7, 0.3])
# Correlated prediction scores (a reasonably good model)
noise = np.random.normal(0, 0.15, n_samples)
y_score = np.clip(0.3 + 0.4 * y_true + noise, 0, 1)
df = pd.DataFrame({CHURNED: y_true, CHURN_SCORE: y_score})

# Plot: reads only df and the constants above
# Cumulative gains: rank by score (descending), accumulate captured positives
ranked = df.sort_values(CHURN_SCORE, ascending=False)[CHURNED].to_numpy()
total_positives = ranked.sum()
n_rows = len(ranked)
gains = np.insert(np.cumsum(ranked) / total_positives * 100, 0, 0)
population_pct = np.insert(np.arange(1, n_rows + 1) / n_rows * 100, 0, 0)

# Perfect model reaches 100% at the positive class rate, flat afterwards
positive_rate = total_positives / n_rows * 100
perfect_gains = np.minimum(population_pct / positive_rate * 100, 100)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(x=population_pct, y=gains, ax=ax, color=IMPRINT_PALETTE[0], linewidth=1.75, label="Churn Prediction Model")
sns.lineplot(
    x=[0, 100], y=[0, 100], ax=ax, color=NEUTRAL, linewidth=1.25, linestyle="--", label="Random Selection (Baseline)"
)
sns.lineplot(
    x=population_pct,
    y=perfect_gains,
    ax=ax,
    color=IMPRINT_PALETTE[1],
    linewidth=1.25,
    linestyle=":",
    label="Perfect Model",
)

# Fill between model and baseline to show model lift
ax.fill_between(population_pct, gains, population_pct, alpha=0.2, color=IMPRINT_PALETTE[0])

# Style
ax.set_xlabel("Customers Targeted (%)", fontsize=10, color=INK)
ax.set_ylabel("Churners Captured (%)", fontsize=10, color=INK)
ax.set_title("gain-curve · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_xlim(0, 100)
ax.set_ylim(0, 105)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.1, linewidth=0.8, color=INK)
ax.legend(fontsize=8, loc="upper left", framealpha=0.95)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
