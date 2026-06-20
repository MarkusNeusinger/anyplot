""" anyplot.ai
curve-oc: Operating Characteristic (OC) Curve
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 90/100 | Updated: 2026-06-20
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

# Data — Monte Carlo lot-acceptance simulation; seaborn estimates empirical mean + 95% CI
np.random.seed(42)
N_SIMS = 5000  # runs per (plan, defect-level): large N → smooth curves + tight CI bands

fraction_defective = np.linspace(0, 0.20, 50)

plans = [
    {"n": 50, "c": 1, "label": "n=50, c=1"},
    {"n": 80, "c": 2, "label": "n=80, c=2"},
    {"n": 100, "c": 2, "label": "n=100, c=2"},
]

# Long-format DataFrame: each row is one simulated lot-inspection outcome (0 = reject, 1 = accept)
sim_dfs = []
for plan in plans:
    outcomes = np.random.binomial(plan["n"], fraction_defective[:, None], (len(fraction_defective), N_SIMS))
    accepted = (outcomes <= plan["c"]).astype(float)
    sim_dfs.append(
        pd.DataFrame(
            {
                "Fraction Defective (p)": np.repeat(fraction_defective, N_SIMS),
                "P(Accept)": accepted.ravel(),
                "Sampling Plan": plan["label"],
            }
        )
    )

df = pd.concat(sim_dfs, ignore_index=True)

aql = 0.02
ltpd = 0.10

# Theoretical risk values (binomial CDF) for annotation anchors on the n=80/c=2 curve
prob_at_aql = binom.cdf(plans[1]["c"], plans[1]["n"], aql)
beta_risk = binom.cdf(plans[1]["c"], plans[1]["n"], ltpd)
alpha_risk = 1 - prob_at_aql

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# seaborn aggregates empirical runs and adds 95% CI shading — distinctive statistical feature
sns.lineplot(
    data=df,
    x="Fraction Defective (p)",
    y="P(Accept)",
    hue="Sampling Plan",
    palette=IMPRINT_PALETTE[:3],
    linewidth=2.5,
    errorbar=("se", 1.96),
    ax=ax,
)

# AQL and LTPD reference lines
ax.axvline(x=aql, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.6)
ax.axvline(x=ltpd, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.6)
ax.text(aql + 0.002, 1.03, f"AQL = {aql}", fontsize=8, color=INK_MUTED, va="bottom")
ax.text(ltpd + 0.002, 1.03, f"LTPD = {ltpd}", fontsize=8, color=INK_MUTED, va="bottom")

# Risk markers using amber (warning/caution anchor) at theoretical values
ax.plot(aql, prob_at_aql, "o", color=ANYPLOT_AMBER, markersize=6, zorder=5)
ax.plot(ltpd, beta_risk, "o", color=ANYPLOT_AMBER, markersize=6, zorder=5)

# Annotation with filled background so text stands out against reference line dashes
bbox_style = {"boxstyle": "round,pad=0.25", "facecolor": ELEVATED_BG, "edgecolor": INK_MUTED, "alpha": 0.9}
ax.annotate(
    f"Producer's risk\nα = {alpha_risk:.3f}",
    xy=(aql, prob_at_aql),
    xytext=(aql + 0.020, prob_at_aql - 0.10),
    fontsize=8,
    color=INK_SOFT,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.0},
    bbox=bbox_style,
)

ax.annotate(
    f"Consumer's risk\nβ = {beta_risk:.3f}",
    xy=(ltpd, beta_risk),
    xytext=(ltpd + 0.020, beta_risk + 0.13),
    fontsize=8,
    color=INK_SOFT,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.0},
    bbox=bbox_style,
)

# Style
ax.set_title("curve-oc · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel("Fraction Defective (p)", fontsize=10, color=INK)
ax.set_ylabel("Probability of Acceptance P(a)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
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
