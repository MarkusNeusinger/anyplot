""" anyplot.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats


# Theme tokens (prompts/default-style-guide.md "Background" and "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per group in order
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
        "grid.alpha": 0.12,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
HALF_SURVIVAL = 0.5  # the survival probability whose crossing is the median survival time
CONFIDENCE = 0.95  # pointwise confidence level of the shaded bands (Greenwood standard error)

# Columns: set these to your table's column names
TIME = "Time since randomization (months)"  # role: time
EVENT = "Death observed (1 = yes, 0 = censored)"  # role: event
GROUP = "Study arm"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("trial.csv")
# A two-arm trial with 36 months of follow-up; patients still alive at the end are censored.
np.random.seed(42)
treatment_time = np.clip(np.random.exponential(scale=24, size=75), 0, 36)
treatment_event = np.random.binomial(1, 0.6, size=75)
treatment_event[treatment_time >= 35] = 0
control_time = np.clip(np.random.exponential(scale=16, size=75), 0, 36)
control_event = np.random.binomial(1, 0.75, size=75)
control_event[control_time >= 35] = 0
df = pd.DataFrame(
    {
        TIME: np.concatenate([treatment_time, control_time]),
        EVENT: np.concatenate([treatment_event, control_event]),
        GROUP: ["Treatment"] * 75 + ["Control"] * 75,
    }
)

# Plot: reads only df and the constants above
SURVIVAL = "Survival probability"
observations = df.dropna(subset=[TIME, EVENT, GROUP])
groups = observations[GROUP].unique()
palette = dict(zip(groups, IMPRINT_PALETTE, strict=False))

# Kaplan-Meier estimate per group: scipy's survival function for right-censored data, which steps
# at every event, stays flat through censored times and so runs to the group's last follow-up
curves, censored, medians = [], [], {}
for group in groups:
    rows = observations[observations[GROUP] == group]
    died = rows[EVENT].astype(float).to_numpy() == 1
    times = rows[TIME].astype(float).to_numpy()
    fit = stats.ecdf(stats.CensoredData(uncensored=times[died], right=times[~died])).sf
    band = fit.confidence_interval(CONFIDENCE)
    curves.append(
        pd.DataFrame(
            {
                GROUP: group,
                TIME: np.r_[0, fit.quantiles],
                SURVIVAL: np.r_[1, fit.probabilities],
                "low": np.r_[1, band.low.probabilities],
                "high": np.r_[1, band.high.probabilities],
            }
        )
    )
    censored.append(pd.DataFrame({GROUP: group, TIME: times[~died], SURVIVAL: fit.evaluate(times[~died])}))
    below_half = fit.quantiles[fit.probabilities <= HALF_SURVIVAL]
    if len(below_half):
        medians[group] = below_half[0]
curves = pd.concat(curves, ignore_index=True)
censored = pd.concat(censored, ignore_index=True)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Confidence bands, stepping with their curves
for group, curve in curves.groupby(GROUP, sort=False):
    ax.fill_between(
        curve[TIME], curve["low"], curve["high"], step="post", color=palette[group], alpha=0.16, linewidth=0
    )

# Survival curves as right-continuous steps
sns.lineplot(
    data=curves,
    x=TIME,
    y=SURVIVAL,
    hue=GROUP,
    palette=palette,
    estimator=None,
    drawstyle="steps-post",
    linewidth=2.2,
    ax=ax,
)

# Censored observations: short ticks on the curve at each censoring time
sns.scatterplot(
    data=censored,
    x=TIME,
    y=SURVIVAL,
    hue=GROUP,
    palette=palette,
    marker="|",
    s=45,
    linewidth=1.3,
    legend=False,
    zorder=4,
    ax=ax,
)

# Median survival: where each curve first reaches half survival, with a drop line to the time axis
ax.axhline(HALF_SURVIVAL, color=INK_MUTED, linestyle=(0, (4, 3)), linewidth=0.9, zorder=1)
for group, median in medians.items():
    ax.plot([median, median], [0, HALF_SURVIVAL], color=palette[group], linestyle=(0, (2, 2)), linewidth=1.2)
    ax.annotate(
        f"median {median:.1f}",
        xy=(median, 0),
        xytext=(3, 3),
        textcoords="offset points",
        ha="left",
        va="bottom",
        fontsize=7,
        color=INK_SOFT,
    )

# Style
ax.set_title("survival-kaplan-meier · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(TIME, fontsize=10)
ax.set_ylabel(SURVIVAL, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.set_xlim(0, observations[TIME].max() * 1.03)
ax.set_ylim(0, curves[SURVIVAL].max() * 1.03)
ax.yaxis.grid(True, linewidth=0.6)
sns.despine(ax=ax)
sns.move_legend(ax, "upper right", frameon=True, fontsize=8, title_fontsize=9)
ax.get_legend().get_title().set_color(INK)
for text in ax.get_legend().get_texts():
    text.set_color(INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
