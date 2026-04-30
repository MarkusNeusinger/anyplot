""" anyplot.ai
ridgeline-basic: Basic Ridgeline Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-04-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Monthly temperature distributions (Northern Hemisphere seasonal pattern)
np.random.seed(42)

months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

base_temps = [2, 4, 8, 13, 17, 21, 24, 23, 19, 13, 7, 3]

data = []
for month, base_temp in zip(months, base_temps, strict=True):
    temps = np.random.normal(base_temp, 3.5, 150)
    for temp in temps:
        data.append({"month": month, "temperature": temp})

df = pd.DataFrame(data)

# viridis gradient for 12 months (approved sequential colormap for 6+ groups)
palette = sns.color_palette("viridis", n_colors=12)

# Configure seaborn: transparent axes so figure background shows through
sns.set_theme(
    style="white",
    rc={
        "axes.facecolor": (0, 0, 0, 0),
        "figure.facecolor": PAGE_BG,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
    },
)

# FacetGrid ridgeline layout (January at top → December at bottom)
g = sns.FacetGrid(
    df, row="month", hue="month", aspect=15, height=0.6, palette=palette, row_order=months, hue_order=months
)

# Filled density curves
g.map(sns.kdeplot, "temperature", bw_adjust=0.8, clip_on=False, fill=True, alpha=0.85, linewidth=2.5)

# Outline in PAGE_BG color creates visual separation between overlapping ridges
g.map(sns.kdeplot, "temperature", bw_adjust=0.8, clip_on=False, color=PAGE_BG, linewidth=3)

# Baseline
g.map(plt.axhline, y=0, linewidth=2, linestyle="-", color=INK_SOFT, clip_on=False)


def label(x, color, label):
    ax = plt.gca()
    ax.text(
        -0.02, 0.2, label, fontsize=20, fontweight="bold", color=color, ha="right", va="center", transform=ax.transAxes
    )


g.map(label, "temperature")

# Overlap and cleanup
g.figure.subplots_adjust(hspace=-0.5)
g.set_titles("")
g.set(yticks=[], ylabel="")
g.despine(bottom=True, left=True)

g.axes[-1, 0].set_xlabel("Temperature (°C)", fontsize=22, color=INK)
g.axes[-1, 0].tick_params(axis="x", labelsize=18, colors=INK_SOFT)

g.figure.set_size_inches(16, 9)
g.figure.patch.set_facecolor(PAGE_BG)
g.figure.suptitle("ridgeline-basic · seaborn · anyplot.ai", fontsize=26, y=0.98, fontweight="bold", color=INK)

plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
