""" pyplots.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-03
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.path import Path


# Style — seaborn theming and context
sns.set_style("white")
sns.set_context("talk", font_scale=1.3)

# Data: Survey tracking 1000 respondents on renewable energy support
# across 4 quarterly waves — shows gradual polarization over time
waves = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"]
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]

# Diverging palette via seaborn: blue (agreement) → gray (neutral) → warm (disagreement)
palette_rgb = sns.diverging_palette(220, 25, n=5, s=80, l=50)
category_colors = {cat: tuple(palette_rgb[i]) for i, cat in enumerate(categories)}

# Respondent counts per category at each wave (total = 1000 per wave)
# Pattern: Neutral shrinks as respondents polarize toward extremes
counts = np.array(
    [
        [120, 150, 180, 210],  # Strongly Agree
        [280, 260, 240, 230],  # Agree
        [300, 250, 200, 160],  # Neutral
        [200, 210, 220, 220],  # Disagree
        [100, 130, 160, 180],  # Strongly Disagree
    ]
)

# Flow transitions between consecutive waves
flows = [
    # Q1 → Q2
    {
        ("Strongly Agree", "Strongly Agree"): 105,
        ("Strongly Agree", "Agree"): 10,
        ("Strongly Agree", "Neutral"): 3,
        ("Strongly Agree", "Disagree"): 1,
        ("Strongly Agree", "Strongly Disagree"): 1,
        ("Agree", "Strongly Agree"): 30,
        ("Agree", "Agree"): 210,
        ("Agree", "Neutral"): 25,
        ("Agree", "Disagree"): 10,
        ("Agree", "Strongly Disagree"): 5,
        ("Neutral", "Strongly Agree"): 10,
        ("Neutral", "Agree"): 30,
        ("Neutral", "Neutral"): 200,
        ("Neutral", "Disagree"): 40,
        ("Neutral", "Strongly Disagree"): 20,
        ("Disagree", "Strongly Agree"): 3,
        ("Disagree", "Agree"): 7,
        ("Disagree", "Neutral"): 20,
        ("Disagree", "Disagree"): 145,
        ("Disagree", "Strongly Disagree"): 25,
        ("Strongly Disagree", "Strongly Agree"): 2,
        ("Strongly Disagree", "Agree"): 3,
        ("Strongly Disagree", "Neutral"): 2,
        ("Strongly Disagree", "Disagree"): 14,
        ("Strongly Disagree", "Strongly Disagree"): 79,
    },
    # Q2 → Q3
    {
        ("Strongly Agree", "Strongly Agree"): 135,
        ("Strongly Agree", "Agree"): 10,
        ("Strongly Agree", "Neutral"): 3,
        ("Strongly Agree", "Disagree"): 1,
        ("Strongly Agree", "Strongly Disagree"): 1,
        ("Agree", "Strongly Agree"): 30,
        ("Agree", "Agree"): 195,
        ("Agree", "Neutral"): 20,
        ("Agree", "Disagree"): 10,
        ("Agree", "Strongly Disagree"): 5,
        ("Neutral", "Strongly Agree"): 10,
        ("Neutral", "Agree"): 25,
        ("Neutral", "Neutral"): 160,
        ("Neutral", "Disagree"): 35,
        ("Neutral", "Strongly Disagree"): 20,
        ("Disagree", "Strongly Agree"): 3,
        ("Disagree", "Agree"): 7,
        ("Disagree", "Neutral"): 15,
        ("Disagree", "Disagree"): 160,
        ("Disagree", "Strongly Disagree"): 25,
        ("Strongly Disagree", "Strongly Agree"): 2,
        ("Strongly Disagree", "Agree"): 3,
        ("Strongly Disagree", "Neutral"): 2,
        ("Strongly Disagree", "Disagree"): 14,
        ("Strongly Disagree", "Strongly Disagree"): 109,
    },
    # Q3 → Q4
    {
        ("Strongly Agree", "Strongly Agree"): 165,
        ("Strongly Agree", "Agree"): 10,
        ("Strongly Agree", "Neutral"): 3,
        ("Strongly Agree", "Disagree"): 1,
        ("Strongly Agree", "Strongly Disagree"): 1,
        ("Agree", "Strongly Agree"): 30,
        ("Agree", "Agree"): 180,
        ("Agree", "Neutral"): 15,
        ("Agree", "Disagree"): 10,
        ("Agree", "Strongly Disagree"): 5,
        ("Neutral", "Strongly Agree"): 10,
        ("Neutral", "Agree"): 30,
        ("Neutral", "Neutral"): 120,
        ("Neutral", "Disagree"): 25,
        ("Neutral", "Strongly Disagree"): 15,
        ("Disagree", "Strongly Agree"): 3,
        ("Disagree", "Agree"): 7,
        ("Disagree", "Neutral"): 20,
        ("Disagree", "Disagree"): 170,
        ("Disagree", "Strongly Disagree"): 20,
        ("Strongly Disagree", "Strongly Agree"): 2,
        ("Strongly Disagree", "Agree"): 3,
        ("Strongly Disagree", "Neutral"): 2,
        ("Strongly Disagree", "Disagree"): 14,
        ("Strongly Disagree", "Strongly Disagree"): 139,
    },
]

# Figure with two panels: main alluvial + net change barplot
fig = plt.figure(figsize=(16, 9))
gs = fig.add_gridspec(1, 2, width_ratios=[5, 1], wspace=0.05)
ax = fig.add_subplot(gs[0, 0])
ax_net = fig.add_subplot(gs[0, 1])

# --- Main alluvial diagram ---
n_waves = len(waves)
x_positions = np.linspace(0, 10, n_waves)
bar_width = 0.55
total_height = 100

node_positions = {}

for wave_idx, wave in enumerate(waves):
    x = x_positions[wave_idx]
    wave_total = counts[:, wave_idx].sum()

    y_bottom = 0
    for cat_idx, category in enumerate(categories):
        height = (counts[cat_idx, wave_idx] / wave_total) * total_height
        y_top = y_bottom + height

        node_positions[(wave_idx, category)] = (y_bottom, y_top)

        rect = mpatches.Rectangle(
            (x - bar_width / 2, y_bottom),
            bar_width,
            height,
            facecolor=category_colors[category],
            edgecolor="white",
            linewidth=2,
        )
        ax.add_patch(rect)

        count_val = counts[cat_idx, wave_idx]

        if wave_idx == 0:
            ax.text(
                x - bar_width / 2 - 0.15,
                (y_bottom + y_top) / 2,
                f"{category}\n(n={count_val})",
                ha="right",
                va="center",
                fontsize=14,
                fontweight="bold",
                color=category_colors[category],
            )
        elif wave_idx == n_waves - 1:
            ax.text(
                x + bar_width / 2 + 0.15,
                (y_bottom + y_top) / 2,
                f"(n={count_val})",
                ha="left",
                va="center",
                fontsize=14,
                fontweight="bold",
                color=category_colors[category],
            )
        else:
            if height > 9:
                ax.text(
                    x,
                    (y_bottom + y_top) / 2,
                    f"n={count_val}",
                    ha="center",
                    va="center",
                    fontsize=13,
                    fontweight="semibold",
                    color="white",
                )

        y_bottom = y_top

    ax.text(x, total_height + 3, wave, ha="center", va="bottom", fontsize=20, fontweight="bold")

# Draw flows between consecutive waves
# Draw changers first (low opacity), then stable flows on top (high opacity)
for flow_idx, flow_dict in enumerate(flows):
    x0 = x_positions[flow_idx]
    x1 = x_positions[flow_idx + 1]

    wave0_total = counts[:, flow_idx].sum()
    wave1_total = counts[:, flow_idx + 1].sum()

    # Sort: changers first, stable last (so stable draws on top)
    sorted_flows = sorted(flow_dict.items(), key=lambda item: item[0][0] == item[0][1])

    source_offsets = {cat: node_positions[(flow_idx, cat)][0] for cat in categories}
    target_offsets = {cat: node_positions[(flow_idx + 1, cat)][0] for cat in categories}

    for (source_cat, target_cat), flow_value in sorted_flows:
        if flow_value <= 0:
            continue

        source_height = (flow_value / wave0_total) * total_height
        target_height = (flow_value / wave1_total) * total_height

        y0_bot = source_offsets[source_cat]
        y0_top = y0_bot + source_height
        y1_bot = target_offsets[target_cat]
        y1_top = y1_bot + target_height

        # Bezier curved band
        band_x0 = x0 + bar_width / 2
        band_x1 = x1 - bar_width / 2
        cx0 = band_x0 + 0.4 * (band_x1 - band_x0)
        cx1 = band_x0 + 0.6 * (band_x1 - band_x0)

        verts = [
            (band_x0, y0_bot),
            (cx0, y0_bot),
            (cx1, y1_bot),
            (band_x1, y1_bot),
            (band_x1, y1_top),
            (cx1, y1_top),
            (cx0, y0_top),
            (band_x0, y0_top),
            (band_x0, y0_bot),
        ]
        codes = [
            Path.MOVETO,
            Path.CURVE4,
            Path.CURVE4,
            Path.CURVE4,
            Path.LINETO,
            Path.CURVE4,
            Path.CURVE4,
            Path.CURVE4,
            Path.CLOSEPOLY,
        ]
        path = Path(verts, codes)

        # Stable flows (same category) get high opacity; changers get slightly higher for visibility
        is_stable = source_cat == target_cat
        alpha = 0.60 if is_stable else 0.28

        color = category_colors[source_cat]
        patch = mpatches.PathPatch(path, facecolor=color, edgecolor=color, linewidth=0.3, alpha=alpha)
        ax.add_patch(patch)

        source_offsets[source_cat] = y0_top
        target_offsets[target_cat] = y1_top

# Main axes style — use seaborn despine
ax.set_xlim(-4.0, 12.0)
ax.set_ylim(-8, 115)
ax.set_aspect("auto")
ax.set_xticks([])
ax.set_yticks([])
sns.despine(ax=ax, left=True, bottom=True, top=True, right=True)
ax.set_facecolor("white")

# --- Net change sidebar using seaborn barplot ---
net_changes = counts[:, -1] - counts[:, 0]
df_net = pd.DataFrame({"Category": categories, "Net Change": net_changes.tolist()})

# Reversed order so bottom-to-top matches alluvial stacking
cat_order = categories[::-1]
sns.barplot(
    data=df_net,
    x="Net Change",
    y="Category",
    hue="Category",
    palette=category_colors,
    legend=False,
    order=cat_order,
    ax=ax_net,
)

# Annotate bars with net change values
for i, cat in enumerate(cat_order):
    val = net_changes[categories.index(cat)]
    sign = "+" if val > 0 else ""
    offset = 5 if val >= 0 else -5
    ha = "left" if val >= 0 else "right"
    ax_net.text(
        val + offset, i, f"{sign}{val}", ha=ha, va="center", fontsize=12, fontweight="bold", color=category_colors[cat]
    )

ax_net.set_title("Net Shift\nQ1 → Q4", fontsize=14, fontweight="bold", pad=15)
ax_net.set_ylabel("")
ax_net.set_xlabel("")
ax_net.tick_params(axis="y", length=0)
ax_net.set_yticklabels([])
ax_net.axvline(0, color="#444444", linewidth=0.8, zorder=0)
ax_net.xaxis.grid(True, alpha=0.15, linewidth=0.5)
sns.despine(ax=ax_net, left=True)
ax_net.set_facecolor("white")

# Title and subtitle
fig.suptitle("alluvial-opinion-flow · seaborn · pyplots.ai", fontsize=24, fontweight="bold", y=0.97)
fig.text(
    0.42,
    0.02,
    "Renewable Energy Survey · 1,000 respondents across 4 waves · Stable flows shown at higher opacity",
    ha="center",
    va="bottom",
    fontsize=14,
    color="#666666",
    style="italic",
)

fig.patch.set_facecolor("white")
fig.subplots_adjust(left=0.12, right=0.98, top=0.90, bottom=0.08, wspace=0.05)
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
