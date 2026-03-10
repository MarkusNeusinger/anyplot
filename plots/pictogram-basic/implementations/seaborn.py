""" pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-10
"""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data — Fruit production (thousands of tonnes), sorted by value for visual hierarchy
categories = ["Apples", "Grapes", "Oranges", "Bananas", "Strawberries"]
values = [35, 28, 22, 18, 12]
unit_value = 5

# Seaborn color palette
palette = sns.color_palette(["#306998", "#7A6DAC", "#E4873D", "#F2C53D", "#C44E52"], as_cmap=False)

# Build DataFrame for seaborn plotting
rows = []
for i, (cat, val, color) in enumerate(zip(categories, values, palette, strict=True)):
    full_icons = int(val // unit_value)
    partial = (val % unit_value) / unit_value

    for j in range(full_icons):
        rows.append({"category": cat, "x": j, "y": i, "alpha": 1.0, "color": color})

    if partial > 0:
        r, g, b = mcolors.to_rgb(color)
        faded = (r + (1 - r) * (1 - partial), g + (1 - g) * (1 - partial), b + (1 - b) * (1 - partial))
        rows.append({"category": cat, "x": full_icons, "y": i, "alpha": partial, "color": faded})

df = pd.DataFrame(rows)

# Plot
sns.set_style("white")
sns.set_context("talk", font_scale=1.1)
fig, ax = plt.subplots(figsize=(16, 9))

# Use sns.scatterplot with DataFrame — full icons
df_full = df[df["alpha"] == 1.0]
if not df_full.empty:
    sns.scatterplot(
        data=df_full,
        x="x",
        y="y",
        hue="category",
        palette=dict(zip(categories, [mcolors.to_hex(c) for c in palette], strict=True)),
        s=900,
        marker="o",
        edgecolor="white",
        linewidth=1.5,
        legend=False,
        zorder=3,
        ax=ax,
    )

# Partial icons — plotted with faded colors
df_partial = df[df["alpha"] < 1.0]
for _, row in df_partial.iterrows():
    sns.scatterplot(
        x=[row["x"]],
        y=[row["y"]],
        color=row["color"],
        s=900,
        marker="o",
        edgecolor="white",
        linewidth=1.5,
        legend=False,
        zorder=3,
        ax=ax,
    )

# Highlight the top category with a subtle background band
ax.axhspan(-0.4, 0.4, color="#306998", alpha=0.06, zorder=0)

# Value annotations on the right side for storytelling
for i, (_cat, val) in enumerate(zip(categories, values, strict=True)):
    total_icons = int(val // unit_value) + (1 if val % unit_value > 0 else 0)
    ax.text(
        total_icons * 1.0 + 0.4,
        i,
        f"{val:,}k",
        fontsize=16,
        va="center",
        ha="left",
        color="#555555",
        fontweight="bold" if i == 0 else "normal",
    )

# Labels and styling
ax.set_yticks(range(len(categories)))
ax.set_yticklabels(categories, fontsize=20, fontweight="medium")
ax.tick_params(axis="y", length=0, pad=10)
ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
ax.set_xlabel("")
ax.set_ylabel("")

max_icons = max(val // unit_value for val in values) + 2
ax.set_xlim(-0.7, max_icons * 1.0 + 0.8)
ax.set_ylim(-0.8, (len(categories) - 1) + 0.8)
ax.invert_yaxis()

ax.set_title("pictogram-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)

sns.despine(left=True, bottom=True)

# Legend
legend_y = -0.06
ax.annotate(
    f"\u25cf = {unit_value:,} thousand tonnes   (lighter = partial value)",
    xy=(0.5, legend_y),
    xycoords="axes fraction",
    fontsize=15,
    ha="center",
    va="top",
    color="#666666",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
