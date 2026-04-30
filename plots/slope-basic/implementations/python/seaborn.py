""" anyplot.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 83/100 | Updated: 2026-04-30
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

COLOR_INCREASE = "#009E73"  # Okabe-Ito position 1
COLOR_DECREASE = "#D55E00"  # Okabe-Ito position 2

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

# Data — tech company revenue comparison Q1 vs Q4 (four rank crossings)
data = {
    "entity": ["StreamPeak", "DataCore", "CloudSync", "NetPulse", "CodeBase", "ByteFlow", "LogicGrid", "TechVault"],
    "Q1 ($M)": [50, 110, 165, 220, 275, 325, 378, 430],
    "Q4 ($M)": [95, 60, 230, 178, 335, 268, 415, 368],
}

df = pd.DataFrame(data)
df["change"] = df["Q4 ($M)"] - df["Q1 ($M)"]
df["direction"] = df["change"].apply(lambda x: "Increase" if x > 0 else "Decrease")
df = df.sort_values("Q1 ($M)").reset_index(drop=True)

df_melted = df.melt(
    id_vars=["entity", "direction"], value_vars=["Q1 ($M)", "Q4 ($M)"], var_name="Period", value_name="Revenue ($M)"
)
df_melted["period_num"] = df_melted["Period"].map({"Q1 ($M)": 0, "Q4 ($M)": 1})

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

palette = {"Increase": COLOR_INCREASE, "Decrease": COLOR_DECREASE}

sns.lineplot(
    data=df_melted,
    x="period_num",
    y="Revenue ($M)",
    hue="direction",
    units="entity",
    estimator=None,
    palette=palette,
    linewidth=3.5,
    marker="o",
    markersize=12,
    alpha=0.85,
    legend=False,
    ax=ax,
)

# Endpoint labels at both axes
for _, row in df.iterrows():
    color = palette[row["direction"]]
    q1_val = int(row["Q1 ($M)"])
    q4_val = int(row["Q4 ($M)"])

    ax.annotate(
        f"{row['entity']} ({q1_val})",
        xy=(0, q1_val),
        xytext=(-14, 0),
        textcoords="offset points",
        fontsize=14,
        color=color,
        ha="right",
        va="center",
        fontweight="bold",
    )
    ax.annotate(
        f"({q4_val}) {row['entity']}",
        xy=(1, q4_val),
        xytext=(14, 0),
        textcoords="offset points",
        fontsize=14,
        color=color,
        ha="left",
        va="center",
        fontweight="bold",
    )

# Style
ax.set_xticks([0, 1])
ax.set_xticklabels(["Q1 Revenue ($M)", "Q4 Revenue ($M)"], fontsize=16, color=INK_SOFT)
ax.set_xlabel("")
ax.set_ylabel("Revenue ($M)", fontsize=20, color=INK)
ax.set_title("slope-basic · seaborn · anyplot.ai", fontsize=24, fontweight="bold", pad=20, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_xlim(-0.15, 1.15)

y_min = min(df["Q1 ($M)"].min(), df["Q4 ($M)"].min())
y_max = max(df["Q1 ($M)"].max(), df["Q4 ($M)"].max())
y_padding = (y_max - y_min) * 0.10
ax.set_ylim(y_min - y_padding, y_max + y_padding)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Legend
legend_elements = [
    Line2D([0], [0], color=COLOR_INCREASE, linewidth=3.5, marker="o", markersize=10, label="Increase"),
    Line2D([0], [0], color=COLOR_DECREASE, linewidth=3.5, marker="o", markersize=10, label="Decrease"),
]
ax.legend(
    handles=legend_elements, loc="lower right", fontsize=16, framealpha=0.9, facecolor=ELEVATED_BG, edgecolor=INK_SOFT
)

plt.tight_layout()
plt.subplots_adjust(left=0.22, right=0.78)
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
