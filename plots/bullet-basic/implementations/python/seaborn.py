"""anyplot.ai
bullet-basic: Basic Bullet Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the single measure-bar color
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Qualitative bands: grayscale, poor (darkest on light) to good (lightest on light), flipped on dark
# so every band stays distinct from its neighbors and from the page
BAND_COLORS = ["#888780", "#AEADA6", "#CECDC7"] if THEME == "light" else ["#3A3A37", "#53534F", "#6E6E69"]

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
BAND_LABELS = ["Poor", "Satisfactory", "Good"]  # qualitative ranges, lowest threshold first

# Columns: set these to your table's column names
METRIC = "Metric"  # role: label
ACTUAL = "Performance (%)"  # role: actual
TARGET = "Target (%)"  # role: target
POOR_LIMIT = "Poor limit (%)"  # role: ranges
SATISFACTORY_LIMIT = "Satisfactory limit (%)"  # role: extra
GOOD_LIMIT = "Good limit (%)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("kpis.csv")
df = pd.DataFrame(
    {
        METRIC: ["Revenue", "Customer\nSatisfaction", "Efficiency", "Quality\nScore"],
        ACTUAL: [78, 85, 35, 91],
        TARGET: [90, 80, 75, 85],
        POOR_LIMIT: [50, 60, 40, 70],
        SATISFACTORY_LIMIT: [75, 80, 60, 85],
        GOOD_LIMIT: [100, 100, 100, 100],
    }
)

# Plot: reads only df and the constants above
n_metrics = len(df)
band_height = 0.65
limit_columns = [POOR_LIMIT, SATISFACTORY_LIMIT, GOOD_LIMIT]
scale_max = float(df[limit_columns].astype(float).max().max())

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Measure bars: seaborn, narrower than the bands, one color throughout
sns.barplot(data=df, x=ACTUAL, y=METRIC, orient="h", color=IMPRINT_PALETTE[0], width=0.28, saturation=1.0, ax=ax)
for patch in ax.patches:
    patch.set_zorder(3)

# Qualitative bands behind the bars, each ending at its threshold
for i, limits in enumerate(df[limit_columns].to_numpy(dtype=float)):
    left = 0
    for limit, color in zip(limits, BAND_COLORS, strict=False):
        if pd.isna(limit):
            continue
        ax.barh(i, limit - left, left=left, height=band_height, color=color, edgecolor="none", zorder=1)
        left = limit

# Target markers: thin line across the band height
for i, target in enumerate(df[TARGET]):
    ax.plot(
        [target, target],
        [i - band_height / 2, i + band_height / 2],
        color=INK,
        linewidth=2.5,
        zorder=4,
        solid_capstyle="butt",
    )

# Value labels just past each bar
for i, actual in enumerate(df[ACTUAL]):
    ax.text(
        actual + scale_max * 0.015,
        i,
        f"{actual:g}%",
        va="center",
        ha="left",
        fontsize=8,
        fontweight="bold",
        color=INK,
        zorder=5,
    )

# Style
ax.set_xlim(0, scale_max * 1.05)
ax.set_ylim(n_metrics - 0.45, -0.55)
ax.set_xlabel(ACTUAL, fontsize=10, color=INK)
ax.set_ylabel("")
ax.set_title("bullet-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=12)
ax.tick_params(axis="y", length=0, labelsize=8)
ax.tick_params(axis="x", labelsize=8)
sns.despine(left=True, top=True, right=True, ax=ax)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK, zorder=2)
ax.yaxis.grid(False)

legend_elements = [
    mpatches.Patch(facecolor=color, label=f"{label} range", edgecolor="none")
    for color, label in zip(BAND_COLORS, BAND_LABELS, strict=False)
]
legend_elements += [
    mpatches.Patch(facecolor=IMPRINT_PALETTE[0], label="Actual", edgecolor="none"),
    plt.Line2D([0], [0], color=INK, linewidth=2.5, label="Target"),
]
ax.legend(
    handles=legend_elements,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.17),
    fontsize=8,
    framealpha=0.9,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    ncols=len(legend_elements),
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
