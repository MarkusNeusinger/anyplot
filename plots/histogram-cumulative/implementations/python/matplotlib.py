"""anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 97/100 | Updated: 2026-05-11
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BINS = 30
PERCENTILES = [25, 50, 75, 90]  # reference levels, in percent
# Label placement per percentile as (dx, dy, alignment): offset points from the crossing
LABEL_OFFSETS = {25: (15, 7, "left"), 50: (15, 7, "left"), 75: (-75, 5, "right"), 90: (-75, -14, "right")}

# Columns: set these to your table's column names
SCORE = "Exam Score (points)"  # role: numeric

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
scores = np.concatenate(
    [
        rng.normal(65, 10, 300),  # Average performers
        rng.normal(85, 5, 150),  # High performers
        rng.normal(45, 8, 50),  # Lower performers
    ]
)
df = pd.DataFrame({SCORE: np.clip(scores, 0, 100)})

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Cumulative histogram as steps, with a faint fill underneath
ax.hist(
    df[SCORE],
    bins=BINS,
    cumulative=True,
    density=True,
    histtype="step",
    linewidth=2,
    color=IMPRINT_PALETTE[0],
    label="Cumulative Distribution",
)
ax.hist(df[SCORE], bins=BINS, cumulative=True, density=True, histtype="stepfilled", alpha=0.2, color=IMPRINT_PALETTE[0])

# Percentile reference lines with value labels
for p in PERCENTILES:
    pct_value = np.nanpercentile(df[SCORE], p)
    ax.axhline(y=p / 100, color=IMPRINT_PALETTE[1], linestyle="--", linewidth=1.2, alpha=0.5)
    ax.axvline(x=pct_value, color=IMPRINT_PALETTE[1], linestyle="--", linewidth=1.2, alpha=0.5)
    dx, dy, ha = LABEL_OFFSETS[p]
    ax.annotate(
        f"{p}th percentile (score ≈ {pct_value:.0f})",
        xy=(pct_value, p / 100),
        xytext=(dx, dy),
        textcoords="offset points",
        fontsize=7,
        color=INK_SOFT,
        ha=ha,
        bbox={"boxstyle": "round,pad=0.5", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.8},
    )

# Style
ax.set_xlabel(SCORE, fontsize=10, color=INK)
ax.set_ylabel("Cumulative Probability", fontsize=10, color=INK)
ax.set_title("histogram-cumulative · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_xlim(0, 100)
ax.set_ylim(0, 1.05)

ax.grid(True, alpha=0.15, linestyle="-", linewidth=0.8, color=INK_SOFT)
ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
    ax.spines[s].set_linewidth(0.8)

leg = ax.legend(fontsize=8, loc="lower right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
for text in leg.get_texts():
    text.set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
