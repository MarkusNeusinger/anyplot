"""anyplot.ai
lift-curve: Model Lift Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-10
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
REFERENCE = IMPRINT_PALETTE[4]  # random-selection reference line

# Columns: set these to your table's column names
Y_TRUE = "Responded (0/1)"  # role: y_true
Y_SCORE = "Model score"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
n_samples = 1000
base_rate = 0.15  # 15% baseline response rate
y_true = np.random.binomial(1, base_rate, n_samples)
# Responders get higher scores, non-responders lower ones
y_score = np.where(
    y_true == 1, np.clip(np.random.beta(5, 2, n_samples), 0, 1), np.clip(np.random.beta(2, 5, n_samples), 0, 1)
)
df = pd.DataFrame({Y_TRUE: y_true, Y_SCORE: y_score})

# Plot: reads only df and the constants above
ranked = df.dropna().sort_values(Y_SCORE, ascending=False, kind="stable")
outcomes = ranked[Y_TRUE].to_numpy()
n_total = len(outcomes)
baseline_rate = outcomes.sum() / n_total

# Cumulative lift at each percentage of the population, best-scored first
percentages = np.arange(1, 101)
n_selected = np.ceil(n_total * percentages / 100).astype(int)
lift_values = np.cumsum(outcomes)[n_selected - 1] / n_selected / baseline_rate

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(percentages, lift_values, color=BRAND, linewidth=2.5, label="Model Lift", zorder=3)
ax.axhline(y=1, color=REFERENCE, linestyle="--", linewidth=2, label="Random (Lift = 1)", zorder=2)
ax.fill_between(percentages, 1, lift_values, where=(lift_values > 1), alpha=0.15, color=BRAND, zorder=1)

# Style
title = "lift-curve · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_xlabel("Population Targeted (%)", fontsize=10, color=INK)
ax.set_ylabel("Cumulative Lift", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.set_xlim(0, 100)
ax.set_ylim(0, np.nanmax(lift_values) * 1.15)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

leg = ax.legend(fontsize=8, loc="upper right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
