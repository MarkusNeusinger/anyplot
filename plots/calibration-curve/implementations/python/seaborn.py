"""anyplot.ai
calibration-curve: Calibration Curve
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per classifier in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]

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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
N_BINS = 10  # equal-width probability bins: 0.0-0.1, 0.1-0.2, ...
HIST_BINS = 20

# Columns: set these to your table's column names
Y_TRUE = "Defaulted"  # role: y_true
Y_PROBS = ["Logistic regression", "Naive Bayes", "Random forest"]  # role: y_prob

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
# Loan-default scores for 2000 hold-out applicants from three credit-risk classifiers
np.random.seed(42)
n_samples = 2000
calibrated = np.clip(np.random.beta(2, 3.5, n_samples), 0.01, 0.99)  # imbalanced: ~36 % default
y_true = np.random.binomial(1, calibrated)  # outcomes drawn from the calibrated probabilities
logit = np.log(calibrated / (1 - calibrated))
overconfident = np.clip(1 / (1 + np.exp(-2.5 * logit)), 0.01, 0.99)  # Naive Bayes: pushed towards 0 and 1
underconfident = np.clip(0.5 + (calibrated - 0.5) * 0.45, 0.01, 0.99)  # forest votes: squeezed towards 0.5
df = pd.DataFrame({Y_TRUE: y_true, Y_PROBS[0]: calibrated, Y_PROBS[1]: overconfident, Y_PROBS[2]: underconfident})

# Plot: reads only df and the constants above
MODEL = "Model"
PRED = "Predicted probability"
long = df.melt(id_vars=Y_TRUE, value_vars=Y_PROBS, var_name=MODEL, value_name=PRED).dropna()
long[Y_TRUE] = long[Y_TRUE].astype(float)
long["bin"] = pd.cut(long[PRED], np.linspace(0, 1, N_BINS + 1), include_lowest=True)

# Per-bin mean prediction vs observed frequency; empty bins drop out (observed=True)
curve = long.groupby([MODEL, "bin"], sort=False, observed=True).agg(
    mean_pred=(PRED, "mean"), frac_pos=(Y_TRUE, "mean"), count=(PRED, "size")
)
curve = curve.reset_index()

# Brier score and expected calibration error per model, shown in the legend
labels = {}
for model, group in long.groupby(MODEL, sort=False):
    brier = np.mean((group[PRED] - group[Y_TRUE]) ** 2)
    bins = curve[curve[MODEL] == model]
    ece = np.sum(bins["count"] * np.abs(bins["frac_pos"] - bins["mean_pred"])) / bins["count"].sum()
    labels[model] = f"{model} (Brier {brier:.3f}, ECE {ece:.3f})"
curve[MODEL] = curve[MODEL].map(labels)
long[MODEL] = long[MODEL].map(labels)

models = list(labels.values())
palette = dict(zip(models, IMPRINT_PALETTE, strict=False))
markers = dict(zip(models, MARKERS, strict=False))

# Square canvas: the reliability diagram is a symmetric 0-1 by 0-1 plot; the histogram below shares its x axis
fig, (ax_cal, ax_hist) = plt.subplots(
    2, 1, figsize=(6, 6), dpi=400, sharex=True, gridspec_kw={"height_ratios": [3, 1]}, layout="constrained"
)

ax_cal.plot([0, 1], [0, 1], linestyle="--", color=INK_MUTED, linewidth=1.4, label="Perfect calibration", zorder=1)
sns.lineplot(
    data=curve,
    x="mean_pred",
    y="frac_pos",
    hue=MODEL,
    style=MODEL,
    hue_order=models,
    style_order=models,
    palette=palette,
    markers=markers,
    dashes=False,
    estimator=None,
    sort=True,
    linewidth=2,
    markersize=7,
    markeredgecolor=PAGE_BG,
    markeredgewidth=0.8,
    ax=ax_cal,
    zorder=3,
)

sns.histplot(
    data=long,
    x=PRED,
    hue=MODEL,
    hue_order=models,
    palette=palette,
    bins=HIST_BINS,
    binrange=(0, 1),
    element="step",
    alpha=0.12,
    linewidth=1.4,
    legend=False,
    ax=ax_hist,
)

# Style
fig.suptitle("calibration-curve · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)

ax_cal.set_xlim(-0.02, 1.02)
ax_cal.set_ylim(-0.02, 1.02)
ax_cal.set_xlabel("")
ax_cal.set_ylabel(f"Fraction of positives ({Y_TRUE})", fontsize=10)
ax_cal.grid(True, linewidth=0.6)
legend = ax_cal.legend(fontsize=7, loc="upper left", frameon=True, framealpha=0.95)
legend.get_frame().set_linewidth(0.6)

ax_hist.set_xlabel(f"{PRED} (curve: bin mean)", fontsize=10)
ax_hist.set_ylabel("Count", fontsize=10)
ax_hist.yaxis.grid(True, linewidth=0.6)

for ax in (ax_cal, ax_hist):
    ax.tick_params(axis="both", labelsize=8, length=0)
    sns.despine(ax=ax)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
