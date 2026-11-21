"""anyplot.ai
forest-basic: Meta-Analysis Forest Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
POOLED_COLOR = IMPRINT_PALETTE[6]

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
    },
)

# Constants
NULL_EFFECT = 0  # a mean difference of zero means no effect
Z_95 = 1.96  # two-sided 95 % interval
POOLED_LABEL = "Pooled Estimate"

# Columns: set these to your table's column names
STUDY = "Study"  # role: study
EFFECT = "Mean Difference (Treatment - Control)"  # role: effect_size
CI_LOWER = "CI lower"  # role: ci_lower
CI_UPPER = "CI upper"  # role: ci_upper
WEIGHT = "Weight (%)"  # role: weight

# Data: replace this block with your own table, for example df = pd.read_csv("studies.csv")
# Meta-analysis of treatment effect (mean difference) from 10 randomized trials
_effects = [-0.45, 0.12, -0.28, -0.52, 0.05, -0.38, -0.15, -0.42, -0.22, -0.35]
_half_widths = [0.35, 0.28, 0.42, 0.25, 0.55, 0.32, 0.38, 0.30, 0.45, 0.28]
df = pd.DataFrame(
    {
        STUDY: [
            "Smith et al. 2018",
            "Johnson et al. 2019",
            "Williams et al. 2019",
            "Brown et al. 2020",
            "Davis et al. 2020",
            "Miller et al. 2021",
            "Wilson et al. 2021",
            "Moore et al. 2022",
            "Taylor et al. 2022",
            "Anderson et al. 2023",
        ],
        EFFECT: _effects,
        CI_LOWER: [e - w for e, w in zip(_effects, _half_widths, strict=True)],
        CI_UPPER: [e + w for e, w in zip(_effects, _half_widths, strict=True)],
        WEIGHT: [12.5, 8.2, 6.8, 14.1, 5.5, 10.3, 7.9, 11.8, 6.2, 9.7],
    }
)

# Plot: reads only df and the constants above
df = df.sort_values(EFFECT, ascending=True).reset_index(drop=True)
n_studies = len(df)

# Pooled estimate: weighted mean with a standard error from the interval half-widths
half_widths = (df[CI_UPPER] - df[CI_LOWER]) / 2
pooled = np.average(df[EFFECT], weights=df[WEIGHT])
pooled_se = np.sqrt(1 / np.sum(df[WEIGHT] / half_widths**2))
pooled_lo, pooled_hi = pooled - Z_95 * pooled_se, pooled + Z_95 * pooled_se

# Rows: pooled diamond at y=0, studies above it
df["row"] = np.arange(n_studies) + 1.5
diamond_y, diamond_h = 0.3, 0.4

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.hlines(df["row"], df[CI_LOWER], df[CI_UPPER], color=BRAND, linewidth=1.4, zorder=1)

# Marker area proportional to study weight
area_per_weight = 16
sns.scatterplot(
    data=df,
    x=EFFECT,
    y="row",
    size=WEIGHT,
    sizes=(df[WEIGHT].min() * area_per_weight, df[WEIGHT].max() * area_per_weight),
    color=BRAND,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    legend=False,
    ax=ax,
    zorder=2,
)

# Pooled diamond: tips at the pooled interval's bounds
ax.add_patch(
    mpatches.Polygon(
        [
            [pooled, diamond_y],
            [pooled_lo, diamond_y + diamond_h / 2],
            [pooled, diamond_y + diamond_h],
            [pooled_hi, diamond_y + diamond_h / 2],
        ],
        closed=True,
        facecolor=POOLED_COLOR,
        edgecolor=INK,
        linewidth=1.0,
        zorder=3,
    )
)

# Null-effect reference line through every row
ax.axvline(NULL_EFFECT, color=INK_SOFT, linestyle="--", linewidth=1.2, zorder=0, alpha=0.7)

# Study names at their rows
ax.set_yticks([*df["row"], diamond_y + diamond_h / 2], [*df[STUDY], POOLED_LABEL], fontsize=8, color=INK)
ax.get_yticklabels()[-1].set_fontweight("bold")
ax.tick_params(axis="y", length=0, pad=6)

# Effect and interval values right of the data, x in axes fraction
rows_text = [
    (r, e, lo, hi, False) for r, e, lo, hi in zip(df["row"], df[EFFECT], df[CI_LOWER], df[CI_UPPER], strict=True)
]
rows_text.append((diamond_y + diamond_h / 2, pooled, pooled_lo, pooled_hi, True))
for y, e, lo, hi, bold in rows_text:
    ax.text(
        0.80,
        y,
        f"{e:.2f} [{lo:.2f}, {hi:.2f}]",
        transform=ax.get_yaxis_transform(),
        fontsize=7,
        va="center",
        ha="left",
        family="monospace",
        fontweight="bold" if bold else "normal",
        color=INK_SOFT,
    )

# Limits: room on the left of the data for nothing, on the right for the value column
x_lo, x_hi = df[CI_LOWER].min(), df[CI_UPPER].max()
span = x_hi - x_lo
ax.set_xlim(x_lo - 0.15 * span, x_hi + 0.90 * span)
ax.set_ylim(-0.1, n_studies + 1.1)

ax.set_xlabel(EFFECT, fontsize=10)
ax.set_ylabel("")
ax.set_title("forest-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=10, color=INK)
ax.tick_params(axis="x", labelsize=8)
ax.grid(axis="x", alpha=0.1, linestyle="--", color=INK, linewidth=0.6)
ax.grid(axis="y", visible=False)
sns.despine(left=True)

plt.subplots_adjust(left=0.17, right=0.97, top=0.91, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
