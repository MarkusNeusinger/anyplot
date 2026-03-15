""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-15
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Data - synthetic sedimentary section with 10 layers
layers = [
    {"top": 0, "bottom": 15, "lithology": "sandstone", "formation": "Dakota Fm", "age": "Late Cretaceous"},
    {"top": 15, "bottom": 30, "lithology": "shale", "formation": "Graneros Sh", "age": "Late Cretaceous"},
    {"top": 30, "bottom": 52, "lithology": "limestone", "formation": "Greenhorn Ls", "age": "Late Cretaceous"},
    {"top": 52, "bottom": 65, "lithology": "shale", "formation": "Carlile Sh", "age": "Late Cretaceous"},
    {"top": 65, "bottom": 78, "lithology": "siltstone", "formation": "Niobrara Fm", "age": "Late Cretaceous"},
    {"top": 78, "bottom": 100, "lithology": "limestone", "formation": "Fort Hays Ls", "age": "Late Cretaceous"},
    {"top": 100, "bottom": 118, "lithology": "conglomerate", "formation": "Morrison Fm", "age": "Late Jurassic"},
    {"top": 118, "bottom": 140, "lithology": "sandstone", "formation": "Entrada Ss", "age": "Middle Jurassic"},
    {"top": 140, "bottom": 162, "lithology": "shale", "formation": "Chinle Fm", "age": "Late Triassic"},
    {"top": 162, "bottom": 180, "lithology": "dolomite", "formation": "Kaibab Fm", "age": "Early Permian"},
]

lithology_styles = {
    "sandstone": {"color": "#F5DEB3", "hatch": "...", "label": "Sandstone"},
    "shale": {"color": "#A9A9A9", "hatch": "---", "label": "Shale"},
    "limestone": {"color": "#87CEEB", "hatch": "+++", "label": "Limestone"},
    "siltstone": {"color": "#C4A882", "hatch": "//", "label": "Siltstone"},
    "conglomerate": {"color": "#D2B48C", "hatch": "ooo", "label": "Conglomerate"},
    "dolomite": {"color": "#B0C4DE", "hatch": "xxx", "label": "Dolomite"},
}

total_depth = 180

# Plot
fig, ax = plt.subplots(figsize=(10, 16))

for layer in layers:
    top = layer["top"]
    bottom = layer["bottom"]
    thickness = bottom - top
    style = lithology_styles[layer["lithology"]]

    rect = mpatches.FancyBboxPatch(
        (0, top),
        1,
        thickness,
        boxstyle="square,pad=0",
        facecolor=style["color"],
        edgecolor="black",
        linewidth=1.5,
        hatch=style["hatch"],
    )
    ax.add_patch(rect)

    mid_y = top + thickness / 2
    ax.text(1.08, mid_y, layer["formation"], fontsize=14, fontweight="medium", va="center", ha="left")

age_positions = {}
for layer in layers:
    age = layer["age"]
    mid_y = (layer["top"] + layer["bottom"]) / 2
    if age not in age_positions:
        age_positions[age] = {"sum": 0, "count": 0, "top": layer["top"], "bottom": layer["bottom"]}
    age_positions[age]["sum"] += mid_y
    age_positions[age]["count"] += 1
    age_positions[age]["top"] = min(age_positions[age]["top"], layer["top"])
    age_positions[age]["bottom"] = max(age_positions[age]["bottom"], layer["bottom"])

for age, pos in age_positions.items():
    avg_y = pos["sum"] / pos["count"]
    ax.text(
        -0.08,
        avg_y,
        age,
        fontsize=12,
        fontweight="medium",
        va="center",
        ha="right",
        fontstyle="italic",
        color="#444444",
    )
    ax.plot([-0.02, -0.02], [pos["top"], pos["bottom"]], color="#888888", linewidth=2, solid_capstyle="butt")

# Style
ax.set_xlim(-0.5, 1.8)
ax.set_ylim(total_depth, 0)
ax.set_ylabel("Depth (m)", fontsize=20, labelpad=10)
ax.set_title("column-stratigraphic · seaborn · pyplots.ai", fontsize=22, fontweight="medium", pad=20)

ax.set_yticks(np.arange(0, total_depth + 1, 20))
ax.tick_params(axis="y", labelsize=14)
ax.set_xticks([])

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)

legend_handles = []
for _lith, style in lithology_styles.items():
    patch = mpatches.Patch(facecolor=style["color"], edgecolor="black", hatch=style["hatch"], label=style["label"])
    legend_handles.append(patch)

ax.legend(
    handles=legend_handles,
    loc="upper right",
    bbox_to_anchor=(1.55, 1.0),
    fontsize=12,
    framealpha=0.9,
    title="Lithology",
    title_fontsize=14,
)

plt.tight_layout()

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
