"""anyplot.ai
pie-basic: Basic Pie Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Created: 2026-05-28
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "text.color": INK,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Column constants
ENERGY_SOURCE = "Energy source"  # role: category
SHARE = "Share of household energy use (%)"  # role: value

# Data
df = pd.DataFrame(
    {
        ENERGY_SOURCE: ["Natural gas", "Electricity", "Heating oil", "Propane", "Wood", "Solar"],
        SHARE: [38, 27, 14, 9, 7, 5],
    }
)

# Plot
n_slices = len(df)
colors = sns.color_palette(IMPRINT_PALETTE, n_slices)
explode = ((df[SHARE] == df[SHARE].max()) * 0.06).tolist()

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
fig.subplots_adjust(top=0.88, bottom=0.14)

wedges, texts, autotexts = ax.pie(
    df[SHARE],
    colors=colors,
    explode=explode,
    autopct="%1.0f%%",
    pctdistance=0.72,
    startangle=90,
    counterclock=False,
    wedgeprops={"edgecolor": PAGE_BG, "linewidth": 2.0},
)

# Label ink follows each slice's luminance: white on dark fills, near-black on light ones
for autotext, color in zip(autotexts, colors, strict=True):
    red, green, blue = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in color]
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    autotext.set_color("#FFFFFF" if luminance < 0.18 else "#1A1A17")
    autotext.set_fontsize(11)
    autotext.set_fontweight("bold")

ax.set_title("pie-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="bold", color=INK, pad=14)

legend = ax.legend(
    wedges,
    df[ENERGY_SOURCE],
    title=ENERGY_SOURCE,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.12),
    ncol=3,
    fontsize=9,
    title_fontsize=9,
    frameon=True,
)
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

# Save — no tight_layout (subplots_adjust sets the margins) and no bbox_inches
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
