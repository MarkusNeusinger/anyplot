""" pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-10
"""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data — Fruit production (thousands of tonnes), sorted by value for visual hierarchy
categories = ["Apples", "Grapes", "Oranges", "Bananas", "Strawberries"]
values = [35, 28, 22, 18, 12]
unit_value = 5

# Custom fruit-inspired palette — distinctive and colorblind-safe
fruit_colors = {
    "Apples": "#C23B22",  # rich red
    "Grapes": "#6B5B95",  # deep purple
    "Oranges": "#E08A2C",  # warm orange
    "Bananas": "#D4A843",  # golden yellow
    "Strawberries": "#D45B7A",  # rosy pink
}

# Build faded versions for partial icons
fruit_faded = {}
for cat, hex_color in fruit_colors.items():
    r, g, b = mcolors.to_rgb(hex_color)
    faded = (r + (1 - r) * 0.6, g + (1 - g) * 0.6, b + (1 - b) * 0.6)
    fruit_faded[cat] = mcolors.to_hex(faded)

# Build DataFrame for seaborn stripplot — each row is one icon
rows = []
for cat, val in zip(categories, values, strict=True):
    full_icons = int(val // unit_value)
    partial = (val % unit_value) / unit_value

    for j in range(full_icons):
        rows.append({"category": cat, "x": j, "icon_type": "full"})

    if partial > 0:
        rows.append({"category": cat, "x": full_icons, "icon_type": "partial"})

df = pd.DataFrame(rows)

# Plot setup — use seaborn theming and styling
sns.set_theme(style="white", context="talk", font_scale=1.1)
fig, ax = plt.subplots(figsize=(16, 7.5))

# Use sns.stripplot for categorical dot layout — distinctive seaborn feature
# stripplot places individual observations along a categorical axis
df_full = df[df["icon_type"] == "full"]
if not df_full.empty:
    sns.stripplot(
        data=df_full,
        x="x",
        y="category",
        hue="category",
        order=categories,
        hue_order=categories,
        palette=fruit_colors,
        size=25,
        marker="o",
        edgecolor="white",
        linewidth=1.5,
        jitter=False,
        dodge=False,
        legend=False,
        zorder=3,
        ax=ax,
    )

# Partial icons — use stripplot per category with faded colors
df_partial = df[df["icon_type"] == "partial"]
for cat in categories:
    cat_partial = df_partial[df_partial["category"] == cat]
    if not cat_partial.empty:
        sns.stripplot(
            data=cat_partial,
            x="x",
            y="category",
            order=categories,
            color=fruit_faded[cat],
            size=25,
            marker="o",
            edgecolor="white",
            linewidth=1.5,
            jitter=False,
            dodge=False,
            legend=False,
            zorder=3,
            ax=ax,
        )

# Highlight the top category with a subtle background band
ax.axhspan(-0.4, 0.4, color=fruit_colors[categories[0]], alpha=0.06, zorder=0)

# Value annotations on the right side for storytelling
for idx, val in enumerate(values):
    total_icons = int(val // unit_value) + (1 if val % unit_value > 0 else 0)
    ax.text(
        total_icons + 0.4,
        idx,
        f"{val:,}k",
        fontsize=16,
        va="center",
        ha="left",
        color="#444444",
        fontweight="bold" if idx == 0 else "normal",
    )

# Labels and styling
ax.set_xlabel("Icons (each = 5 thousand tonnes)", fontsize=16, color="#888888", labelpad=12)
ax.set_ylabel("")
ax.tick_params(axis="y", length=0, pad=10, labelsize=20)
ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)

max_icons = max(val // unit_value for val in values) + 2
ax.set_xlim(-0.7, max_icons + 0.8)

ax.set_title("pictogram-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)

sns.despine(left=True, bottom=True)

# Legend annotation
ax.annotate(
    f"\u25cf = {unit_value:,} thousand tonnes   (lighter = partial value)",
    xy=(0.5, -0.08),
    xycoords="axes fraction",
    fontsize=16,
    ha="center",
    va="top",
    color="#666666",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
