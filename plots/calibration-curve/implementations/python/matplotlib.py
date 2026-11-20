""" anyplot.ai
calibration-curve: Calibration Curve
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 77/100 | Updated: 2026-11-20
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

# Imprint palette: all eight positions, one per model in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 10  # equal-width probability bins, 0.0-0.1, 0.1-0.2, ...
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]  # one shape per model, so color is not the only cue

# Columns: set these to your table's column names
OUTCOME = "Actual outcome (0 or 1)"  # role: y_true
MODELS = ["Well-calibrated", "Overconfident", "Underconfident"]  # role: y_prob

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
rng = np.random.default_rng(42)
n_samples = 2000
y_true = rng.binomial(1, 0.35, n_samples)
signal = y_true * 2 - 1
df = pd.DataFrame(
    {
        OUTCOME: y_true,
        MODELS[0]: 1 / (1 + np.exp(-(1.2 * signal + rng.normal(0, 1.0, n_samples)))),
        MODELS[1]: 1 / (1 + np.exp(-(2.0 * signal + rng.normal(0, 0.5, n_samples)))),
        MODELS[2]: 1 / (1 + np.exp(-(0.5 * signal + rng.normal(0, 0.8, n_samples)))),
    }
)

# Plot: reads only df and the constants above
edges = np.linspace(0, 1, N_BINS + 1)
outcome = df[OUTCOME].to_numpy(dtype=float)

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(8, 4.5), dpi=400, sharex=True, gridspec_kw={"height_ratios": [3, 1]}, facecolor=PAGE_BG
)
for ax in (ax1, ax2):
    ax.set_facecolor(PAGE_BG)

ax1.plot([0, 1], [0, 1], "--", linewidth=1.2, color=INK_SOFT, alpha=0.7, label="Perfect calibration")

for i, model in enumerate(MODELS):
    prob = df[model].to_numpy(dtype=float)
    valid = ~np.isnan(prob) & ~np.isnan(outcome)
    prob, hit = prob[valid], outcome[valid]

    # Per-bin mean prediction, observed fraction of positives and its standard error
    which = np.digitize(prob, edges[1:-1])
    count = np.bincount(which, minlength=N_BINS)
    filled = count > 0
    mean_pred = np.bincount(which, weights=prob, minlength=N_BINS)[filled] / count[filled]
    frac_pos = np.bincount(which, weights=hit, minlength=N_BINS)[filled] / count[filled]
    stderr = np.sqrt(frac_pos * (1 - frac_pos) / count[filled])
    brier = np.mean((prob - hit) ** 2)

    ax1.fill_between(mean_pred, frac_pos - stderr, frac_pos + stderr, alpha=0.2, color=IMPRINT_PALETTE[i], linewidth=0)
    ax1.plot(
        mean_pred,
        frac_pos,
        marker=MARKERS[i],
        color=IMPRINT_PALETTE[i],
        linewidth=1.8,
        markersize=5,
        label=f"{model} (Brier {brier:.3f})",
    )
    ax2.hist(prob, bins=2 * N_BINS, range=(0, 1), alpha=0.6, color=IMPRINT_PALETTE[i], edgecolor=PAGE_BG, linewidth=0.3)

# Style
ax1.set_title("calibration-curve · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax1.set_ylabel("Fraction of positives", fontsize=10, color=INK)
ax2.set_xlabel("Mean predicted probability", fontsize=10, color=INK)
ax2.set_ylabel("Count", fontsize=10, color=INK)
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)

leg = ax1.legend(fontsize=8, loc="lower right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.5)
plt.setp(leg.get_texts(), color=INK_SOFT)

for ax in (ax1, ax2):
    ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
    ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.97, top=0.92, bottom=0.12, hspace=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
