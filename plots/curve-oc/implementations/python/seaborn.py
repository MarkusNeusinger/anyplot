"""anyplot.ai
curve-oc: Operating Characteristic (OC) Curve
Library: seaborn | Python 3.14
Quality: pending | Created: 2026-06-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import binom


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"  # warning / caution anchor for risk markers

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
sns.set_context("notebook", font_scale=1.0)

# Data — OC curves for acceptance sampling plans (binomial CDF)
fraction_defective = np.linspace(0, 0.20, 200)

plans = [
    {"n": 50, "c": 1, "label": "n=50, c=1"},
    {"n": 80, "c": 2, "label": "n=80, c=2"},
    {"n": 100, "c": 2, "label": "n=100, c=2"},
]

rows = []
for plan in plans:
    prob_accept = binom.cdf(plan["c"], plan["n"], fraction_defective)
    for p, pa in zip(fraction_defective, prob_accept, strict=True):
        rows.append({"Fraction Defective (p)": p, "P(Accept)": pa, "Sampling Plan": plan["label"]})

df = pd.DataFrame(rows)

aql = 0.02
ltpd = 0.10

# Risk values for the middle plan (n=80, c=2)
prob_at_aql = binom.cdf(plans[1]["c"], plans[1]["n"], aql)
beta_risk = binom.cdf(plans[1]["c"], plans[1]["n"], ltpd)
alpha_risk = 1 - prob_at_aql

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(
    data=df,
    x="Fraction Defective (p)",
    y="P(Accept)",
    hue="Sampling Plan",
    palette=IMPRINT_PALETTE[:3],
    linewidth=2.5,
    ax=ax,
)

# AQL and LTPD reference lines
ax.axvline(x=aql, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.6)
ax.axvline(x=ltpd, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.6)
ax.text(aql + 0.002, 1.03, f"AQL = {aql}", fontsize=8, color=INK_MUTED, va="bottom")
ax.text(ltpd + 0.002, 1.03, f"LTPD = {ltpd}", fontsize=8, color=INK_MUTED, va="bottom")

# Risk markers using amber (warning/caution anchor)
ax.plot(aql, prob_at_aql, "o", color=ANYPLOT_AMBER, markersize=6, zorder=5)
ax.plot(ltpd, beta_risk, "o", color=ANYPLOT_AMBER, markersize=6, zorder=5)

ax.annotate(
    f"Producer's risk\nα = {alpha_risk:.3f}",
    xy=(aql, prob_at_aql),
    xytext=(aql + 0.020, prob_at_aql - 0.10),
    fontsize=8,
    color=INK_SOFT,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.0},
)

ax.annotate(
    f"Consumer's risk\nβ = {beta_risk:.3f}",
    xy=(ltpd, beta_risk),
    xytext=(ltpd + 0.020, beta_risk + 0.13),
    fontsize=8,
    color=INK_SOFT,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.0},
)

# Style
ax.set_title("curve-oc · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel("Fraction Defective (p)", fontsize=10, color=INK)
ax.set_ylabel("Probability of Acceptance P(a)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_xlim(0, 0.20)
ax.set_ylim(0, 1.10)

# Legend
legend = ax.get_legend()
legend.set_title("Sampling Plan")
plt.setp(legend.get_title(), fontsize=8, fontweight="medium", color=INK)
plt.setp(legend.get_texts(), fontsize=8, color=INK_SOFT)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_frame().set_linewidth(0.5)

plt.tight_layout()

# Save — no bbox_inches='tight' to preserve exact 3200×1800 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
