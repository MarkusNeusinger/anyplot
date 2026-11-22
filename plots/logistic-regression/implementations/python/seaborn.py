"""anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.special import expit
from sklearn.linear_model import LogisticRegression


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
THRESHOLD = 0.5  # default decision threshold

PREDICTOR = "Predictor variable (X)"  # role: x
OUTCOME = "Outcome class"  # role: y
PROBABILITY = "Probability"  # role: probability
CI_LOWER = "CI lower"  # role: ci_lower
CI_UPPER = "CI upper"  # role: ci_upper
OUTCOME_JITTER = "Outcome (jittered)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("observations.csv")
# with a binary outcome column and the fitted probability and 95% CI bounds per row.
rng = np.random.default_rng(42)
n_samples = 200
x_obs = rng.uniform(-3, 3, n_samples)
y_obs = (rng.random(n_samples) < expit(1.5 * x_obs + 0.5)).astype(int)

model = LogisticRegression().fit(x_obs.reshape(-1, 1), y_obs)
prob = model.predict_proba(x_obs.reshape(-1, 1))[:, 1]

n_bootstrap = 100
boot = np.zeros((n_bootstrap, n_samples))
for i in range(n_bootstrap):
    idx = rng.choice(n_samples, n_samples, replace=True)
    boot[i] = LogisticRegression().fit(x_obs[idx].reshape(-1, 1), y_obs[idx]).predict_proba(x_obs.reshape(-1, 1))[:, 1]

df = pd.DataFrame(
    {
        PREDICTOR: x_obs,
        OUTCOME: y_obs,
        PROBABILITY: prob,
        CI_LOWER: np.percentile(boot, 2.5, axis=0),
        CI_UPPER: np.percentile(boot, 97.5, axis=0),
        OUTCOME_JITTER: y_obs + rng.uniform(-0.05, 0.05, n_samples),
    }
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

curve = df.sort_values(PREDICTOR)
ax.fill_between(curve[PREDICTOR], curve[CI_LOWER], curve[CI_UPPER], alpha=0.25, color=IMPRINT_PALETTE[0], linewidth=0)
ax.plot(curve[PREDICTOR], curve[PROBABILITY], color=IMPRINT_PALETTE[0], linewidth=2.5, zorder=5)

for cls, color in zip(sorted(df[OUTCOME].unique()), IMPRINT_PALETTE, strict=False):
    sub = df[df[OUTCOME] == cls]
    ax.scatter(
        sub[PREDICTOR], sub[OUTCOME_JITTER], s=40, alpha=0.6, color=color, edgecolors=PAGE_BG, linewidth=0.3, zorder=4
    )

ax.axhline(y=THRESHOLD, color=INK_SOFT, linestyle="--", linewidth=1.5, zorder=3)

legend_elements = [
    Line2D([0], [0], color=IMPRINT_PALETTE[0], linewidth=2.5, label="Logistic curve"),
    Patch(facecolor=IMPRINT_PALETTE[0], alpha=0.25, label="95% CI"),
    Line2D([0], [0], color=INK_SOFT, linestyle="--", linewidth=1.5, label=f"Decision threshold (p={THRESHOLD})"),
    Line2D(
        [0],
        [0],
        marker="o",
        color="none",
        markerfacecolor=IMPRINT_PALETTE[0],
        markersize=6,
        label="Class 0",
        markeredgecolor=PAGE_BG,
        markeredgewidth=0.3,
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        color="none",
        markerfacecolor=IMPRINT_PALETTE[1],
        markersize=6,
        label="Class 1",
        markeredgecolor=PAGE_BG,
        markeredgewidth=0.3,
    ),
]
ax.legend(handles=legend_elements, fontsize=8, loc="upper left")

observed = df.dropna(subset=[PREDICTOR, OUTCOME])
fitted = LogisticRegression().fit(observed[[PREDICTOR]].to_numpy(), observed[OUTCOME])
accuracy = fitted.score(observed[[PREDICTOR]].to_numpy(), observed[OUTCOME])
ax.annotate(
    f"Accuracy: {accuracy:.1%}\nCoef: {fitted.coef_[0][0]:.2f}, Intercept: {fitted.intercept_[0]:.2f}",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    fontsize=8,
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
    color=INK,
)

ax.set_xlabel(PREDICTOR, fontsize=10)
ax.set_ylabel(PROBABILITY, fontsize=10)
ax.set_title("logistic-regression · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium")
ax.tick_params(axis="both", labelsize=8)
ax.set_ylim(-0.1, 1.1)
pad = 0.1 * (df[PREDICTOR].max() - df[PREDICTOR].min())
ax.set_xlim(df[PREDICTOR].min() - pad, df[PREDICTOR].max() + pad)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
sns.despine(ax=ax)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
