import os
import sys


# Sibling matplotlib.py in this dir would shadow the installed package — remove the dir first
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _here]

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# --- Theme ---
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — canonical order, first series always #009E73
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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# --- Data: NPV sensitivity analysis for a capital investment project ---
parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Material Cost",
    "Labor Cost",
    "Tax Rate",
    "Initial Investment",
    "Operating Margin",
    "Terminal Value",
    "Working Capital",
    "Inflation Rate",
]

base_npv = 120.0  # Base case NPV in $M

# Inverted relationships: lower Material Cost or Tax Rate → higher NPV
low_values = base_npv + np.array([-38, -30, 22, -18, 10, -14, -10, -8, -5, -3], dtype=float)
high_values = base_npv + np.array([32, 28, -18, 22, -8, 11, 13, 9, 6, 4], dtype=float)

# Sort by total impact range — widest bar at top (classic tornado shape)
total_range = np.abs(high_values - low_values)
sort_idx = np.argsort(total_range)
parameters = [parameters[i] for i in sort_idx]
low_values = low_values[sort_idx]
high_values = high_values[sort_idx]

low_delta = low_values - base_npv
high_delta = high_values - base_npv

# Imprint palette: #009E73 (brand green, first series) for Low Scenario
#                  #4467A3 (blue) for High Scenario
color_low = IMPRINT_PALETTE[0]  # #009E73
color_high = IMPRINT_PALETTE[2]  # #4467A3

df_low = pd.DataFrame({"Parameter": parameters, "NPV Delta ($M)": low_delta, "Scenario": "Low Scenario"})
df_high = pd.DataFrame({"Parameter": parameters, "NPV Delta ($M)": high_delta, "Scenario": "High Scenario"})
df = pd.concat([df_low, df_high], ignore_index=True)

# --- Canvas: 3200×1800 px (landscape 16:9) — no bbox_inches='tight' ---
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

sns.barplot(
    data=df,
    y="Parameter",
    x="NPV Delta ($M)",
    hue="Scenario",
    hue_order=["Low Scenario", "High Scenario"],
    palette=[color_low, color_high],
    dodge=False,
    ax=ax,
    zorder=2,
    edgecolor="none",
)

# Widen view to accommodate bar-end annotations without clipping
ax.set_xlim(low_delta.min() - 9, high_delta.max() + 9)

# Relabel x-axis ticks with absolute NPV values (not deltas)
ticks = ax.get_xticks()
ax.set_xticks(ticks)
ax.set_xticklabels([f"${int(t + base_npv)}" for t in ticks])

# Base case reference line
ax.axvline(x=0, color=INK_SOFT, linewidth=1.2, linestyle="--", zorder=3)

# Base case annotation just above the top bar — avoids crowding at the base line
ax.annotate(
    f"Base Case: ${int(base_npv)}M",
    xy=(0, len(parameters) - 0.45),
    xytext=(5, 0),
    textcoords="offset points",
    fontsize=7.5,
    fontweight="bold",
    fontstyle="italic",
    color=INK_SOFT,
    ha="left",
    va="center",
)

# Bar-end value annotations (8pt — larger relative to canvas than previous 12pt@4800px)
for i in range(len(parameters)):
    lv = low_values[i]
    hv = high_values[i]
    ld = low_delta[i]
    hd = high_delta[i]
    neg_x = min(ld, hd)
    pos_x = max(ld, hd)
    ax.text(neg_x - 0.9, i, f"${min(lv, hv):.0f}M", va="center", ha="right", fontsize=8, color=INK_MUTED)
    ax.text(pos_x + 0.9, i, f"${max(lv, hv):.0f}M", va="center", ha="left", fontsize=8, color=INK_MUTED)

# Axis labels and title
ax.set_ylabel("Input Parameter", fontsize=10, color=INK)
ax.set_xlabel("Net Present Value ($M)", fontsize=10, color=INK)
ax.set_title(
    "bar-tornado-sensitivity · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=12, color=INK
)
ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT)
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT)

# Grid and spines
sns.despine(left=True, bottom=False)
ax.yaxis.grid(False)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Legend
ax.legend(fontsize=8, frameon=True, facecolor=ELEVATED_BG, edgecolor=INK_SOFT, loc="upper right")

# Bold top-3 most impactful parameter labels — must come after canvas draw
fig.canvas.draw()
ytick_labels = ax.get_yticklabels()
for i, label in enumerate(ytick_labels):
    if i >= len(parameters) - 3:
        label.set_fontweight("bold")
        label.set_fontsize(9)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
