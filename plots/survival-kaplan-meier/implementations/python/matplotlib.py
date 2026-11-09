""" anyplot.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.duration.survfunc import SurvfuncRight


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
HALF_SURVIVAL = 0.5  # median survival is where the curve first reaches this probability
Z_95 = 1.96  # normal quantile for the 95% pointwise confidence band

# Columns: set these to your table's column names
TIME = "Time (months)"  # role: time
EVENT = "Event (1 = death, 0 = censored)"  # role: event
GROUP = "Arm"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("trial.csv")
np.random.seed(42)
n_per_group = 80
treatment_times = np.clip(np.random.exponential(scale=24, size=n_per_group), 0.5, 60)
treatment_events = 1 - np.random.binomial(1, 0.25, n_per_group)
control_times = np.clip(np.random.exponential(scale=16, size=n_per_group), 0.5, 60)
control_events = 1 - np.random.binomial(1, 0.20, n_per_group)
df = pd.DataFrame(
    {
        TIME: np.concatenate([treatment_times, control_times]),
        EVENT: np.concatenate([treatment_events, control_events]),
        GROUP: ["Treatment Group"] * n_per_group + ["Control Group"] * n_per_group,
    }
)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

median_lines = []
for i, (arm, rows) in enumerate(df.dropna(subset=[TIME, EVENT]).groupby(GROUP, sort=False)):
    color = IMPRINT_PALETTE[i]
    km = SurvfuncRight(rows[TIME].to_numpy(dtype=float), rows[EVENT].to_numpy(dtype=float))
    times = np.concatenate([[0.0], km.surv_times])
    surv = np.concatenate([[1.0], km.surv_prob])
    se = np.concatenate([[0.0], km.surv_prob_se])

    ax.step(times, surv, where="post", color=color, linewidth=2.5, label=arm, zorder=3)
    ax.fill_between(
        times,
        np.clip(surv - Z_95 * se, 0, 1),
        np.clip(surv + Z_95 * se, 0, 1),
        step="post",
        alpha=0.18,
        color=color,
        linewidth=0,
    )

    # Censored observations: tick marks at the step curve's height at each censoring time
    censored = rows.loc[rows[EVENT] == 0, TIME].to_numpy(dtype=float)
    censor_surv = surv[np.searchsorted(times, censored, side="right") - 1]
    ax.scatter(censored, censor_surv, marker="|", s=70, color=color, linewidth=1.4, zorder=4)

    reached = np.flatnonzero(surv <= HALF_SURVIVAL)
    if reached.size:
        median = times[reached[0]]
        ax.vlines(median, 0, HALF_SURVIVAL, color=color, linestyle=":", linewidth=1.3, alpha=0.8)
        median_lines.append(f"{arm} median: {median:.1f} mo")

# Median survival annotation
if median_lines:
    ax.axhline(HALF_SURVIVAL, color=INK_SOFT, linestyle=":", linewidth=1.0, alpha=0.6)
    ax.text(
        0.98,
        0.74,
        "\n".join(median_lines),
        transform=ax.transAxes,
        fontsize=8,
        color=INK,
        ha="right",
        va="top",
        bbox={"boxstyle": "round,pad=0.5", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
    )

# Style
ax.set_title("survival-kaplan-meier · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(TIME, fontsize=10, color=INK)
ax.set_ylabel("Survival probability", fontsize=10, color=INK)
ax.set_xlim(0, df[TIME].max() * 1.05)
ax.set_ylim(0, 1.05)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT, length=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

leg = ax.legend(title=GROUP, fontsize=8, title_fontsize=8, loc="upper right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
