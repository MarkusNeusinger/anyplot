""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-15
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn theme for polished styling
sns.set_theme(style="ticks", context="talk", font_scale=1.0)

# Data - synthetic sedimentary section (Western Interior Seaway)
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

df = pd.DataFrame(layers)
df["thickness"] = df["bottom"] - df["top"]
df["mid_depth"] = (df["top"] + df["bottom"]) / 2

# Use seaborn color palette for distinct lithology colors (colorblind-safe)
lith_types = ["sandstone", "shale", "limestone", "siltstone", "conglomerate", "dolomite"]
palette = sns.color_palette("colorblind", n_colors=len(lith_types))
lith_color_map = dict(zip(lith_types, [sns.desaturate(c, 0.7) for c in palette], strict=True))

lithology_styles = {
    "sandstone": {"color": lith_color_map["sandstone"], "hatch": "...", "label": "Sandstone"},
    "shale": {"color": lith_color_map["shale"], "hatch": "---", "label": "Shale"},
    "limestone": {"color": lith_color_map["limestone"], "hatch": "+++", "label": "Limestone"},
    "siltstone": {"color": lith_color_map["siltstone"], "hatch": "//", "label": "Siltstone"},
    "conglomerate": {"color": lith_color_map["conglomerate"], "hatch": "ooo", "label": "Conglomerate"},
    "dolomite": {"color": lith_color_map["dolomite"], "hatch": "xxx", "label": "Dolomite"},
}

# Age period background colors via seaborn palette
age_bg_palette = sns.color_palette("pastel", n_colors=5)
age_list = ["Late Cretaceous", "Late Jurassic", "Middle Jurassic", "Late Triassic", "Early Permian"]
age_bg_colors = {age: (*age_bg_palette[i], 0.10) for i, age in enumerate(age_list)}

total_depth = 180

# Plot - two-panel layout: age brackets on left, column on right
fig, (ax_age, ax) = plt.subplots(1, 2, figsize=(16, 9), width_ratios=[0.18, 0.82], sharey=True)

# Draw lithology layers as patches with hatching
for _, row in df.iterrows():
    style = lithology_styles[row["lithology"]]
    rect = mpatches.FancyBboxPatch(
        (0, row["top"]),
        0.50,
        row["thickness"],
        boxstyle="square,pad=0",
        facecolor=style["color"],
        edgecolor="black",
        linewidth=1.5,
        hatch=style["hatch"],
    )
    ax.add_patch(rect)

    # Formation labels to the right
    ax.text(
        0.55,
        row["mid_depth"],
        row["formation"],
        fontsize=16,
        fontweight="medium",
        va="center",
        ha="left",
        color="#2C2C2C",
    )

# Mark major unconformities with wavy lines for data storytelling
unconformities = [(100, "Cretaceous–Jurassic"), (140, "Jurassic–Triassic"), (162, "Triassic–Permian")]

for depth, label in unconformities:
    x_wave = np.linspace(0, 0.50, 80)
    y_wave = depth + 0.8 * np.sin(x_wave * 40)
    ax.plot(x_wave, y_wave, color="#CC3333", linewidth=2.5, zorder=5)
    ax.text(
        0.55,
        depth + 1.5,
        label,
        fontsize=12,
        fontweight="bold",
        va="top",
        ha="left",
        color="#CC3333",
        fontstyle="italic",
    )

# Age labels on the left panel
age_positions = {}
for _, row in df.iterrows():
    age = row["age"]
    if age not in age_positions:
        age_positions[age] = {"top": row["top"], "bottom": row["bottom"]}
    age_positions[age]["top"] = min(age_positions[age]["top"], row["top"])
    age_positions[age]["bottom"] = max(age_positions[age]["bottom"], row["bottom"])

ax_age.set_xlim(0, 1)
ax_age.set_ylim(total_depth, 0)
ax.set_xlim(-0.02, 1.0)
ax.set_ylim(total_depth, 0)

for age, pos in age_positions.items():
    mid_y = (pos["top"] + pos["bottom"]) / 2
    bg = age_bg_colors[age]

    # Subtle background band
    ax_age.axhspan(pos["top"], pos["bottom"], color=bg, zorder=0)
    ax.axhspan(pos["top"], pos["bottom"], color=bg, zorder=0)

    # Bracket lines
    ax_age.plot(
        [0.85, 0.85], [pos["top"] + 1, pos["bottom"] - 1], color="#555555", linewidth=2.5, solid_capstyle="butt"
    )
    ax_age.plot([0.80, 0.90], [pos["top"] + 1, pos["top"] + 1], color="#555555", linewidth=2)
    ax_age.plot([0.80, 0.90], [pos["bottom"] - 1, pos["bottom"] - 1], color="#555555", linewidth=2)

    # Age text - horizontal, wrapped short
    ax_age.text(
        0.35,
        mid_y,
        age.replace(" ", "\n"),
        fontsize=16,
        fontweight="bold",
        va="center",
        ha="center",
        fontstyle="italic",
        color="#333333",
    )

# Style axes
ax_age.set_ylabel("Depth (m)", fontsize=20, labelpad=10)
ax_age.tick_params(axis="y", labelsize=16)
ax_age.set_yticks(np.arange(0, total_depth + 1, 20))
ax_age.set_xticks([])
sns.despine(ax=ax_age, top=True, right=True, bottom=True)

ax.set_xticks([])
ax.set_ylabel("")
ax.tick_params(axis="y", left=False)
sns.despine(ax=ax, left=True, bottom=True, top=True, right=True)

# Title
fig.suptitle("column-stratigraphic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", y=0.97)

# Legend
legend_handles = [
    mpatches.Patch(facecolor=style["color"], edgecolor="black", hatch=style["hatch"], label=style["label"])
    for style in lithology_styles.values()
]

ax.legend(
    handles=legend_handles,
    loc="upper right",
    fontsize=14,
    framealpha=0.95,
    title="Lithology",
    title_fontsize=16,
    edgecolor="#CCCCCC",
    fancybox=True,
)

plt.subplots_adjust(wspace=0.02)
plt.tight_layout(rect=[0, 0, 1, 0.95])

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
