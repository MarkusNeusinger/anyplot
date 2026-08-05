"""anyplot.ai
bar-horizontal: Horizontal Bar Chart
Library: seaborn 0.13.2 | Python 3.13.12
Quality: 86/100 | Updated: 2026-08-05
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — most populous countries (UN 2024 estimates)
data = {
    "Country": [
        "India",
        "China",
        "United States",
        "Indonesia",
        "Pakistan",
        "Brazil",
        "Nigeria",
        "Bangladesh",
        "Russia",
        "Mexico",
    ],
    "Population": [1417, 1412, 338, 275, 235, 215, 223, 170, 144, 128],
}
df = pd.DataFrame(data)

# Rank ascending so the largest bar lands at the top of the horizontal axis
order = df.sort_values("Population", ascending=True)["Country"].tolist()
top_country = df.loc[df["Population"].idxmax(), "Country"]

# Focal-point emphasis: color each bar individually via hue=Country (a seaborn-idiomatic
# way to assign one color per category), spotlighting the #1 country in brand green and
# keeping the rest in muted ink — per the spec's "highlight specific bars" guidance.
color_map = {country: (BRAND if country == top_country else INK_MUTED) for country in df["Country"]}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

sns.barplot(
    data=df,
    y="Country",
    x="Population",
    order=order,
    hue="Country",
    palette=color_map,
    legend=False,
    dodge=False,
    edgecolor=PAGE_BG,
    linewidth=1,
    ax=ax,
)

# Value labels at the end of each bar
for container in ax.containers:
    ax.bar_label(container, fmt=lambda v: f"{v:.0f}M", padding=6, fontsize=9, color=INK)

# Mandated title (scales fontsize when longer than the 67-char baseline)
title = "Most Populous Countries (2024) · bar-horizontal · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = round(12 * ratio)
ax.set_title(title, fontsize=title_fontsize, fontweight="bold", color=INK, pad=16)

ax.set_xlabel("Population (millions)", fontsize=10, color=INK)
ax.set_ylabel("Country", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Bold the highlighted tick label to reinforce the visual emphasis
for tick_label in ax.get_yticklabels():
    if tick_label.get_text() == top_country:
        tick_label.set_fontweight("bold")
        tick_label.set_color(INK)

ax.xaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.set_axisbelow(True)
ax.set_xlim(0, df["Population"].max() * 1.12)

sns.despine(ax=ax)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
