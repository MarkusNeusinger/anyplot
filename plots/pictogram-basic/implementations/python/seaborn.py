""" anyplot.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-06-03
"""

import os
import sys


# Remove this file's directory from sys.path so "import seaborn" resolves to the library
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p != _this_dir]

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — Developer survey: most-used programming languages (% of respondents)
categories = ["Python", "JavaScript", "Java", "C++", "Go"]
values = [67, 55, 43, 32, 25]
unit_value = 10  # each icon = 10% of respondents

# Category colors from Imprint palette in canonical order
cat_colors = {cat: IMPRINT_PALETTE[i] for i, cat in enumerate(categories)}

# Faded colors for partial icons — blend with PAGE_BG to signal fractional remainder
cat_faded = {}
for i, cat in enumerate(categories):
    rc, gc, bc = mcolors.to_rgb(IMPRINT_PALETTE[i])
    rb, gb, bb = mcolors.to_rgb(PAGE_BG)
    opacity = 0.35
    cat_faded[cat] = mcolors.to_hex(
        (rc * opacity + rb * (1 - opacity), gc * opacity + gb * (1 - opacity), bc * opacity + bb * (1 - opacity))
    )

# Build icon DataFrame — each row is one icon dot
rows = []
for cat, val in zip(categories, values, strict=True):
    full_icons = val // unit_value
    partial = (val % unit_value) / unit_value
    for j in range(full_icons):
        rows.append({"category": cat, "x": j, "icon_type": "full"})
    if partial > 0:
        rows.append({"category": cat, "x": full_icons, "icon_type": "partial"})

df = pd.DataFrame(rows)

# Theme-aware seaborn setup
sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.labelcolor": INK_SOFT,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.set_facecolor(PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Full icons via seaborn stripplot — discrete dot placement along y-axis categories
df_full = df[df["icon_type"] == "full"]
if not df_full.empty:
    sns.stripplot(
        data=df_full,
        x="x",
        y="category",
        hue="category",
        order=categories,
        hue_order=categories,
        palette=cat_colors,
        size=14,
        marker="o",
        edgecolor=PAGE_BG,
        linewidth=0.8,
        jitter=False,
        dodge=False,
        legend=False,
        zorder=3,
        ax=ax,
    )

# Partial icons — faded to signal fractional remainder
df_partial = df[df["icon_type"] == "partial"]
for cat in categories:
    cat_partial = df_partial[df_partial["category"] == cat]
    if not cat_partial.empty:
        sns.stripplot(
            data=cat_partial,
            x="x",
            y="category",
            order=categories,
            color=cat_faded[cat],
            size=14,
            marker="o",
            edgecolor=PAGE_BG,
            linewidth=0.8,
            jitter=False,
            dodge=False,
            legend=False,
            zorder=3,
            ax=ax,
        )

# Subtle highlight band for the top category row
ax.axhspan(-0.4, 0.4, color=IMPRINT_PALETTE[0], alpha=0.07, zorder=0)

# Value annotations to the right of each row
for idx, (_cat, val) in enumerate(zip(categories, values, strict=True)):
    total_icons = val // unit_value + (1 if val % unit_value > 0 else 0)
    ax.text(
        total_icons + 0.3,
        idx,
        f"{val}%",
        fontsize=8,
        va="center",
        ha="left",
        color=INK,
        fontweight="bold" if idx == 0 else "normal",
    )

# Axis styling
ax.set_xlabel(f"Icons (each = {unit_value}% of respondents)", fontsize=10, color=INK_SOFT, labelpad=8)
ax.set_ylabel("")
ax.tick_params(axis="y", length=0, pad=8, labelsize=8, colors=INK)
ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)

max_x_pos = max(v // unit_value + (1 if v % unit_value > 0 else 0) for v in values)
ax.set_xlim(-0.7, max_x_pos + 1.5)

ax.set_title("pictogram-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=14, color=INK)

sns.despine(left=True, bottom=True, ax=ax)

# Unit legend annotation — tertiary text
ax.annotate(
    f"● = {unit_value}% of respondents   (lighter = partial unit)",
    xy=(0.5, -0.10),
    xycoords="axes fraction",
    fontsize=8,
    ha="center",
    va="top",
    color=INK_MUTED,
)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
