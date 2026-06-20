""" anyplot.ai
line-retention-cohort: User Retention Curve by Cohort
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 90/100 | Updated: 2026-06-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens — Imprint palette
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — 50 simulations per cohort so seaborn can draw 95% CI bands
np.random.seed(42)

cohorts = {"Jan 2025": 1245, "Feb 2025": 1380, "Mar 2025": 1510, "Apr 2025": 1420, "May 2025": 1605}

weeks = np.arange(0, 13)
decay_rates = [0.18, 0.16, 0.14, 0.12, 0.10]
floors = [8, 10, 14, 18, 22]
n_sims = 50

records = []
mean_final = {}

for (cohort_label, cohort_size), decay, floor in zip(cohorts.items(), decay_rates, floors, strict=True):
    label = f"{cohort_label} (n={cohort_size:,})"
    sim_finals = []
    for _ in range(n_sims):
        sim_decay = max(0.05, decay + np.random.normal(0, 0.018))
        retention = 100 * np.exp(-sim_decay * weeks) + floor * (1 - np.exp(-0.3 * weeks))
        retention[0] = 100.0
        noise = np.random.normal(0, 1.5, len(weeks))
        noise[0] = 0
        retention = np.clip(retention + noise, 0, 100)
        sim_finals.append(float(retention[-1]))
        for w, r in zip(weeks, retention, strict=True):
            records.append({"week": w, "retention": r, "cohort": label})
    mean_final[label] = float(np.mean(sim_finals))

df = pd.DataFrame(records)
cohort_labels = list(mean_final.keys())

oldest_mean = mean_final[cohort_labels[0]]
newest_mean = mean_final[cohort_labels[-1]]
delta_pp = newest_mean - oldest_mean

# Seaborn theme with Imprint chrome tokens
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

# Canvas — 3200 × 1800 px (landscape, no bbox_inches to preserve exact size)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot — errorbar=("ci", 95) is seaborn's built-in statistical CI band, drawn natively
sns.lineplot(
    data=df,
    x="week",
    y="retention",
    hue="cohort",
    hue_order=cohort_labels,
    palette=IMPRINT_PALETTE,
    linewidth=2.5,
    errorbar=("ci", 95),
    ax=ax,
)

# 20% retention target reference line
ax.axhline(y=20, color=INK_MUTED, linestyle="--", linewidth=0.9, alpha=0.7, zorder=1)
ax.text(0.3, 17, "20% target", fontsize=8, color=INK_MUTED, va="center", fontstyle="italic")

# +Xpp improvement annotation — replaces per-cohort endpoint labels (change request)
mid_y = (oldest_mean + newest_mean) / 2
ax.annotate(
    "", xy=(12, oldest_mean), xytext=(12, newest_mean), arrowprops={"arrowstyle": "<->", "color": INK_SOFT, "lw": 1.0}
)
ax.text(
    12.25,
    mid_y,
    f"+{delta_pp:.0f}pp\nimprovement",
    fontsize=8,
    fontweight="bold",
    color=INK_SOFT,
    va="center",
    ha="left",
    linespacing=1.3,
)

# Style
title = "line-retention-cohort · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=12)
ax.set_xlabel("Weeks Since Signup", fontsize=10, color=INK, labelpad=8)
ax.set_ylabel("Retained Users (%)", fontsize=10, color=INK, labelpad=8)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.set_xlim(-0.3, 14.2)
ax.set_ylim(0, 108)
ax.set_xticks(weeks)

ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)
ax.xaxis.grid(False)

sns.despine(ax=ax, left=True, bottom=False)

# Legend with Imprint chrome tokens
legend = ax.legend(title="Signup Cohort", fontsize=8, title_fontsize=9, frameon=True, loc="upper right")
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_frame().set_linewidth(0.5)
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

# Save — no bbox_inches to preserve exact 3200×1800 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
