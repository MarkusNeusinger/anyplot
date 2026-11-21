"""anyplot.ai
gain-curve: Cumulative Gains Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: the model is position 1
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CALLOUT_SHARE = 20  # population share (%) at which the callout reads off the captured share

# Columns: set these to your table's column names
Y_TRUE = "Actual response (0/1)"  # role: y_true
Y_SCORE = "Predicted probability"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
n_samples = 1000
customer_value = np.random.randn(n_samples)
customer_engagement = np.random.randn(n_samples)
latent_score = 1.5 * customer_value + 1.0 * customer_engagement
true_prob = 1 / (1 + np.exp(-latent_score))
df = pd.DataFrame(
    {
        Y_TRUE: (np.random.rand(n_samples) < true_prob).astype(int),
        Y_SCORE: 1 / (1 + np.exp(-(latent_score + np.random.randn(n_samples) * 0.5))),
    }
)

# Plot: reads only df and the constants above
ranked = df.sort_values(Y_SCORE, ascending=False)
total_positives = ranked[Y_TRUE].sum()
n_rows = len(ranked)
population_pct = np.concatenate([[0], np.arange(1, n_rows + 1) / n_rows * 100])
gains = np.concatenate([[0], ranked[Y_TRUE].cumsum().to_numpy() / total_positives * 100])

# Perfect model: full capture at the positive class rate, flat afterwards
positive_rate = total_positives / n_rows * 100
perfect_x = [0, positive_rate, 100]
perfect_y = [0, 100, 100]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(population_pct, gains, color=IMPRINT_PALETTE[0], linewidth=2.5, label="Model", zorder=3)
ax.plot([0, 100], [0, 100], color=INK_SOFT, linewidth=1.8, linestyle="--", label="Random (baseline)", zorder=2)
ax.plot(perfect_x, perfect_y, color=INK_MUTED, linewidth=1.8, linestyle=":", label="Perfect model", zorder=2)
ax.fill_between(population_pct, gains, population_pct, alpha=0.15, color=IMPRINT_PALETTE[0], zorder=1)

# Callout: captured share at the chosen population share
callout_gain = np.interp(CALLOUT_SHARE, population_pct, gains)
ax.annotate(
    f"Top {CALLOUT_SHARE}% captures {callout_gain:.0f}%\nof positive cases",
    xy=(CALLOUT_SHARE, callout_gain),
    xytext=(40, -40),
    textcoords="offset points",
    fontsize=8,
    color=INK,
    arrowprops={"arrowstyle": "->", "color": IMPRINT_PALETTE[0], "lw": 1.5},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
)

# Style
ax.set_title("gain-curve · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel("Population targeted (%)", fontsize=10, color=INK)
ax.set_ylabel("Positive cases captured (%)", fontsize=10, color=INK)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_aspect("equal")
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, alpha=0.10, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=8, loc="lower right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
