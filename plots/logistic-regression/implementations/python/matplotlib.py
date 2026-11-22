"""anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
THRESHOLD = 0.5  # default decision threshold of a binary classifier
JITTER = 0.03  # vertical jitter of the observations

# Column constants
SCORE = "Credit score"  # role: x
APPROVED = "Approved"  # role: y
PROBABILITY = "Probability of approval"  # role: probability
CI_LOWER = "CI lower"  # role: ci_lower
CI_UPPER = "CI upper"  # role: ci_upper

# Data: replace this block with your own table, for example df = pd.read_csv("loans.csv")
# Credit risk scoring: loan approval (0/1) against the applicant's credit score
np.random.seed(42)
n_points = 200
scores = np.concatenate([np.random.normal(550, 80, n_points // 2), np.random.normal(700, 60, n_points // 2)])
scores = np.clip(scores, 300, 850)
approval_prob = 1 / (1 + np.exp(-0.02 * (scores - 620)))
df = pd.DataFrame({SCORE: scores, APPROVED: (np.random.random(n_points) < approval_prob).astype(int)})

# Plot
obs = df.dropna()
X = obs[[SCORE]].to_numpy()
y = obs[APPROVED].to_numpy()
model = LogisticRegression().fit(X, y)
accuracy = model.score(X, y)

# Fitted curve with a 95% band (standard error approximation)
curve = pd.DataFrame({SCORE: np.linspace(df[SCORE].min(), df[SCORE].max(), 300)})
curve[PROBABILITY] = model.predict_proba(curve[[SCORE]].to_numpy())[:, 1]
se = np.sqrt(curve[PROBABILITY] * (1 - curve[PROBABILITY]) / len(obs)) * 2
curve[CI_LOWER] = (curve[PROBABILITY] - 1.96 * se).clip(0, 1)
curve[CI_UPPER] = (curve[PROBABILITY] + 1.96 * se).clip(0, 1)

# Jitter along y only, observations keep their exact x
y_jittered = y + np.random.uniform(-JITTER, JITTER, len(obs))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.fill_between(curve[SCORE], curve[CI_LOWER], curve[CI_UPPER], alpha=0.25, color=IMPRINT_PALETTE[0], label="95% CI")
ax.plot(curve[SCORE], curve[PROBABILITY], color=IMPRINT_PALETTE[0], linewidth=2.5, label="Logistic fit", zorder=3)
ax.axhline(y=THRESHOLD, color=INK_SOFT, linestyle="--", linewidth=1.2, label=f"Decision threshold ({THRESHOLD})")

for outcome, label, color in ((0, "Rejected (0)", IMPRINT_PALETTE[1]), (1, "Approved (1)", IMPRINT_PALETTE[0])):
    mask = y == outcome
    ax.scatter(
        obs[SCORE][mask],
        y_jittered[mask],
        s=36,
        alpha=0.6,
        color=color,
        label=label,
        edgecolors=PAGE_BG,
        linewidth=0.3,
        zorder=2,
    )

# Model annotation
annotation_text = f"Accuracy: {accuracy:.1%}\nCoef: {model.coef_[0][0]:.4f}\nIntercept: {model.intercept_[0]:.2f}"
ax.annotate(
    annotation_text,
    xy=(0.03, 0.96),
    xycoords="axes fraction",
    fontsize=8,
    color=INK,
    verticalalignment="top",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": ELEVATED_BG, "alpha": 0.9, "edgecolor": INK_SOFT},
)

# Labels and styling
ax.set_xlabel(SCORE, fontsize=10, color=INK)
ax.set_ylabel(PROBABILITY, fontsize=10, color=INK)
ax.set_title("logistic-regression · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_xlim(df[SCORE].min(), df[SCORE].max())
ax.set_ylim(-JITTER * 2.5, 1 + JITTER * 2.5)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.grid(True, alpha=0.15, linewidth=0.8, color=INK_SOFT)
ax.set_axisbelow(True)

leg = ax.legend(fontsize=8, loc="lower right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.tight_layout()
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
