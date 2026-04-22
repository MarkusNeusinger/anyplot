""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-15
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn theme for polished styling
sns.set_theme(
    style="ticks",
    context="talk",
    font_scale=1.0,
    rc={"axes.linewidth": 1.2, "patch.linewidth": 1.5, "hatch.linewidth": 1.0},
)

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
df["col_width"] = 1.0

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

# Build thickness data for side panel (seaborn distinctive feature)
thickness_df = df[["lithology", "thickness"]].copy()
thickness_df["lithology"] = thickness_df["lithology"].str.title()

# Plot - three-panel layout: age brackets | stratigraphic column | thickness strip
fig, (ax_age, ax, ax_thick) = plt.subplots(1, 3, figsize=(16, 9), width_ratios=[0.16, 0.54, 0.30])

# Use sns.barplot for the lithology layers (seaborn plotting function)
sns.barplot(
    data=df,
    y="formation",
    x="col_width",
    color="#306998",
    ax=ax,
    edgecolor="black",
    linewidth=1.5,
    order=df["formation"].tolist(),
    width=0.98,
)

# Reposition bars from categorical to proportional depth scale and add hatching
col_width = 0.55
for i, (_, row) in enumerate(df.iterrows()):
    bar = ax.patches[i]
    style = lithology_styles[row["lithology"]]
    bar.set_facecolor(style["color"])
    bar.set_hatch(style["hatch"])
    bar.set_y(row["top"])
    bar.set_height(row["thickness"])
    bar.set_x(0)
    bar.set_width(col_width)

# Switch to continuous depth axis
ax.set_ylim(total_depth, 0)
ax.set_yticks([])

# Formation labels to the right of each layer
for _, row in df.iterrows():
    ax.text(
        col_width + 0.05,
        row["mid_depth"],
        row["formation"],
        fontsize=15,
        fontweight="medium",
        va="center",
        ha="left",
        color="#2C2C2C",
    )

# Mark major unconformities with wavy lines for data storytelling
unconformities = [(100, "Cretaceous–Jurassic"), (140, "Jurassic–Triassic"), (162, "Triassic–Permian")]

for depth, label in unconformities:
    x_wave = np.linspace(0, col_width, 80)
    y_wave = depth + 0.8 * np.sin(x_wave * 40)
    ax.plot(x_wave, y_wave, color="#CC3333", linewidth=2.5, zorder=5)
    # Place unconformity labels above the wavy line, inside column
    ax.text(
        col_width / 2,
        depth - 2.0,
        label,
        fontsize=10,
        fontweight="bold",
        va="bottom",
        ha="center",
        color="#CC3333",
        fontstyle="italic",
        zorder=6,
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "none", "pad": 1.5},
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
ax.set_xlim(-0.02, 1.20)

for age, pos in age_positions.items():
    mid_y = (pos["top"] + pos["bottom"]) / 2
    bg = age_bg_colors[age]

    # Subtle background band across both panels
    ax_age.axhspan(pos["top"], pos["bottom"], color=bg, zorder=0)
    ax.axhspan(pos["top"], pos["bottom"], color=bg, zorder=0)

    # Bracket lines
    ax_age.plot(
        [0.85, 0.85], [pos["top"] + 1, pos["bottom"] - 1], color="#555555", linewidth=2.5, solid_capstyle="butt"
    )
    ax_age.plot([0.80, 0.90], [pos["top"] + 1, pos["top"] + 1], color="#555555", linewidth=2)
    ax_age.plot([0.80, 0.90], [pos["bottom"] - 1, pos["bottom"] - 1], color="#555555", linewidth=2)

    # Age text
    ax_age.text(
        0.35,
        mid_y,
        age.replace(" ", "\n"),
        fontsize=15,
        fontweight="bold",
        va="center",
        ha="center",
        fontstyle="italic",
        color="#333333",
    )

# Style age axis
ax_age.set_ylabel("Depth (m)", fontsize=20, labelpad=10)
ax_age.tick_params(axis="y", labelsize=16)
ax_age.set_yticks(np.arange(0, total_depth + 1, 20))
ax_age.set_xticks([])
sns.despine(ax=ax_age, top=True, right=True, bottom=True)

ax.set_xticks([])
ax.set_xlabel("")
ax.set_ylabel("")
ax.tick_params(axis="y", left=False, labelleft=False)
sns.despine(ax=ax, left=True, bottom=True, top=True, right=True)

# Right panel: seaborn stripplot showing layer thicknesses by lithology
# Uses distinctive seaborn categorical visualization (strip plot with jitter)
lith_order = [s["label"] for s in lithology_styles.values()]
strip_palette = {s["label"]: s["color"] for s in lithology_styles.values()}
sns.stripplot(
    data=thickness_df,
    x="thickness",
    y="lithology",
    ax=ax_thick,
    palette=strip_palette,
    hue="lithology",
    order=lith_order,
    size=14,
    marker="D",
    edgecolor="black",
    linewidth=1.0,
    jitter=False,
    legend=False,
)
ax_thick.set_xlabel("Thickness (m)", fontsize=16)
ax_thick.set_ylabel("")
ax_thick.tick_params(axis="both", labelsize=13)
ax_thick.set_title("Layer Thickness", fontsize=16, fontweight="medium", pad=8)
ax_thick.xaxis.grid(True, alpha=0.3, linewidth=0.8)
sns.despine(ax=ax_thick, top=True, right=True)

# Lithology legend on the thickness panel (avoids overlapping column labels)
legend_handles = [
    mpatches.Patch(facecolor=style["color"], edgecolor="black", hatch=style["hatch"], label=style["label"])
    for style in lithology_styles.values()
]

ax_thick.legend(
    handles=legend_handles,
    loc="lower right",
    fontsize=12,
    framealpha=0.95,
    title="Lithology",
    title_fontsize=14,
    edgecolor="#CCCCCC",
    fancybox=True,
)

# Title
fig.suptitle("column-stratigraphic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", y=0.97)

plt.subplots_adjust(wspace=0.08)
plt.tight_layout(rect=[0, 0, 1, 0.95])

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
