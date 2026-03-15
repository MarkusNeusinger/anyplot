""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-15
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Data - synthetic sedimentary borehole section (depth increasing downward, younger at top)
layers = [
    {"top": 0, "bottom": 12, "lithology": "conglomerate", "formation": "Ogallala Fm", "age": "Miocene"},
    {"top": 12, "bottom": 30, "lithology": "sandstone", "formation": "Arikaree Fm", "age": "Miocene"},
    {"top": 30, "bottom": 50, "lithology": "siltstone", "formation": "White River Fm", "age": "Oligocene"},
    {"top": 50, "bottom": 72, "lithology": "shale", "formation": "Chadron Fm", "age": "Eocene"},
    {"top": 72, "bottom": 95, "lithology": "limestone", "formation": "Niobrara Fm", "age": "Cretaceous"},
    {"top": 95, "bottom": 118, "lithology": "shale", "formation": "Carlile Shale", "age": "Cretaceous"},
    {"top": 118, "bottom": 140, "lithology": "limestone", "formation": "Greenhorn Fm", "age": "Cretaceous"},
    {"top": 140, "bottom": 158, "lithology": "sandstone", "formation": "Dakota Fm", "age": "Cretaceous"},
    {"top": 158, "bottom": 175, "lithology": "siltstone", "formation": "Morrison Fm", "age": "Jurassic"},
    {"top": 175, "bottom": 200, "lithology": "sandstone", "formation": "Entrada Fm", "age": "Jurassic"},
]

# Lithology styles: color, hatch pattern
lithology_styles = {
    "sandstone": {"color": "#F5DEB3", "hatch": "...", "edgecolor": "#8B7355"},
    "shale": {"color": "#A9A9A9", "hatch": "---", "edgecolor": "#555555"},
    "limestone": {"color": "#87CEEB", "hatch": "++", "edgecolor": "#4682B4"},
    "siltstone": {"color": "#C4B69C", "hatch": "//", "edgecolor": "#8B7D6B"},
    "conglomerate": {"color": "#DEB887", "hatch": "ooo", "edgecolor": "#8B6914"},
}

# Age group background colors for subtle shading
age_colors = {
    "Miocene": "#FFF8E7",
    "Oligocene": "#F5F0E0",
    "Eocene": "#EDE8D8",
    "Cretaceous": "#E8EEF5",
    "Jurassic": "#F0E8E0",
}

# Plot
fig, ax = plt.subplots(figsize=(12, 16))

column_left = 1.5
column_width = 5.0
max_depth = 200

# Compute age spans
age_spans = {}
for layer in layers:
    age = layer["age"]
    if age not in age_spans:
        age_spans[age] = {"top": layer["top"], "bottom": layer["bottom"]}
    else:
        age_spans[age]["top"] = min(age_spans[age]["top"], layer["top"])
        age_spans[age]["bottom"] = max(age_spans[age]["bottom"], layer["bottom"])

# Draw subtle age-group background shading
for age, span in age_spans.items():
    bg_rect = mpatches.FancyBboxPatch(
        (column_left - 0.1, span["top"]),
        column_width + 0.2,
        span["bottom"] - span["top"],
        boxstyle="square,pad=0",
        facecolor=age_colors[age],
        edgecolor="none",
        zorder=0,
    )
    ax.add_patch(bg_rect)

# Draw lithology layers
for layer in layers:
    top = layer["top"]
    bottom = layer["bottom"]
    thickness = bottom - top
    style = lithology_styles[layer["lithology"]]

    rect = mpatches.FancyBboxPatch(
        (column_left, top),
        column_width,
        thickness,
        boxstyle="square,pad=0",
        facecolor=style["color"],
        edgecolor=style["edgecolor"],
        linewidth=1.5,
        hatch=style["hatch"],
        zorder=1,
    )
    ax.add_patch(rect)

    mid_depth = (top + bottom) / 2
    ax.text(
        column_left + column_width + 0.4,
        mid_depth,
        layer["formation"],
        fontsize=16,
        va="center",
        ha="left",
        fontweight="semibold",
        color="#2C2C2C",
    )

# Unconformity between Eocene (Chadron Fm, bottom=72) and Cretaceous (Niobrara Fm, top=72)
unconformity_depth = 72
x_wave = np.linspace(column_left, column_left + column_width, 80)
y_wave = unconformity_depth + 0.8 * np.sin(x_wave * 4)
ax.plot(x_wave, y_wave, color="#B22222", linewidth=2.5, zorder=3)
ax.text(
    column_left + column_width + 0.4,
    unconformity_depth,
    "unconformity",
    fontsize=14,
    va="center",
    ha="left",
    fontstyle="italic",
    color="#B22222",
    fontweight="medium",
)

# Age labels on the left with bracket lines
bracket_x = column_left - 1.2
for age, span in age_spans.items():
    mid = (span["top"] + span["bottom"]) / 2
    ax.text(
        column_left - 1.8,
        mid,
        age,
        fontsize=16,
        va="center",
        ha="center",
        fontstyle="italic",
        color="#333333",
        fontweight="medium",
        clip_on=False,
    )
    ax.plot(
        [bracket_x, bracket_x + 0.4],
        [span["top"] + 0.5, span["top"] + 0.5],
        color="#555555",
        linewidth=1.2,
        clip_on=False,
    )
    ax.plot(
        [bracket_x, bracket_x + 0.4],
        [span["bottom"] - 0.5, span["bottom"] - 0.5],
        color="#555555",
        linewidth=1.2,
        clip_on=False,
    )
    ax.plot(
        [bracket_x + 0.2, bracket_x + 0.2],
        [span["top"] + 0.5, span["bottom"] - 0.5],
        color="#555555",
        linewidth=1.2,
        clip_on=False,
    )

# Legend
legend_handles = []
for lith, style in lithology_styles.items():
    patch = mpatches.Patch(
        facecolor=style["color"],
        edgecolor=style["edgecolor"],
        hatch=style["hatch"],
        label=lith.capitalize(),
        linewidth=1.0,
    )
    legend_handles.append(patch)

ax.legend(
    handles=legend_handles,
    loc="upper center",
    bbox_to_anchor=(0.55, -0.03),
    fontsize=16,
    framealpha=0.95,
    edgecolor="#bbbbbb",
    fancybox=True,
    shadow=True,
    title="Lithology",
    title_fontsize=17,
    borderpad=1.0,
    ncol=5,
)

# Style
ax.set_xlim(column_left - 2.8, column_left + column_width + 4.5)
ax.set_ylim(max_depth, 0)
ax.set_ylabel("Depth (m)", fontsize=20, labelpad=10)
ax.set_title("column-stratigraphic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=25)
ax.tick_params(axis="y", labelsize=16, length=6)
ax.set_xticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
