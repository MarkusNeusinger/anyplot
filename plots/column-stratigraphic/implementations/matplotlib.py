""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-15
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


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

# Plot
fig, ax = plt.subplots(figsize=(10, 16))

column_left = 0.0
column_width = 3.0
max_depth = 200

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
    )
    ax.add_patch(rect)

    mid_depth = (top + bottom) / 2
    ax.text(
        column_left + column_width + 0.3,
        mid_depth,
        layer["formation"],
        fontsize=14,
        va="center",
        ha="left",
        fontweight="medium",
    )

# Age labels on the left with bracket lines
age_spans = {}
for layer in layers:
    age = layer["age"]
    if age not in age_spans:
        age_spans[age] = {"top": layer["top"], "bottom": layer["bottom"]}
    else:
        age_spans[age]["top"] = min(age_spans[age]["top"], layer["top"])
        age_spans[age]["bottom"] = max(age_spans[age]["bottom"], layer["bottom"])

for age, span in age_spans.items():
    mid = (span["top"] + span["bottom"]) / 2
    ax.annotate(age, xy=(-0.3, mid), fontsize=13, va="center", ha="right", fontstyle="italic", color="#333333")
    ax.plot([-0.15, -0.05], [span["top"], span["top"]], color="#333333", linewidth=1.0, clip_on=False)
    ax.plot([-0.15, -0.05], [span["bottom"], span["bottom"]], color="#333333", linewidth=1.0, clip_on=False)
    ax.plot([-0.1, -0.1], [span["top"], span["bottom"]], color="#333333", linewidth=1.0, clip_on=False)

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
    loc="lower right",
    fontsize=13,
    framealpha=0.9,
    edgecolor="#cccccc",
    title="Lithology",
    title_fontsize=14,
)

# Style
ax.set_xlim(-2.5, column_left + column_width + 4.5)
ax.set_ylim(max_depth, 0)
ax.set_ylabel("Depth (m)", fontsize=20)
ax.set_title("column-stratigraphic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="y", labelsize=16)
ax.set_xticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
