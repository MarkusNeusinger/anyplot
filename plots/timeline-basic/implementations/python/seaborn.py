"""anyplot.ai
timeline-basic: Event Timeline
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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

# Columns: set these to your table's column names
DATE = "Date"  # role: date
EVENT = "Event"  # role: event
CATEGORY = "Phase"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("events.csv")
df = pd.DataFrame(
    {
        DATE: pd.to_datetime(
            [
                "2025-03-03",
                "2025-03-24",
                "2025-04-28",
                "2025-06-16",
                "2025-07-07",
                "2025-09-15",
                "2025-10-06",
                "2025-12-01",
                "2026-01-26",
                "2026-02-16",
            ]
        ),
        EVENT: [
            "Permit Granted",
            "Site Cleared",
            "Foundation Poured",
            "Frame Raised",
            "Roof Sealed",
            "Wiring Passed",
            "Plumbing Passed",
            "Drywall Finished",
            "Final Inspection",
            "Keys Handed Over",
        ],
        CATEGORY: [
            "Site prep",
            "Site prep",
            "Foundation",
            "Structure",
            "Structure",
            "Systems",
            "Systems",
            "Finishing",
            "Finishing",
            "Finishing",
        ],
    }
)

# Plot: reads only df and the constants above
df = df.sort_values(DATE).reset_index(drop=True)
side = np.where(np.arange(len(df)) % 2 == 0, 1, -1)  # alternate above / below the axis
categories = list(dict.fromkeys(df[CATEGORY]))
palette = {category: IMPRINT_PALETTE[i] for i, category in enumerate(categories)}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.axhline(0, color=INK_SOFT, linewidth=1.6, zorder=1)

sns.scatterplot(
    data=df,
    x=DATE,
    y=np.zeros(len(df)),
    hue=CATEGORY,
    hue_order=categories,
    palette=palette,
    s=110,
    edgecolor=PAGE_BG,
    linewidth=1.2,
    zorder=3,
    ax=ax,
)

# Connectors and labels: lengths alternate so neighbouring labels never collide
for i, row in df.iterrows():
    reach = side[i] * (0.5 if i % 4 < 2 else 0.8)
    ax.plot([row[DATE], row[DATE]], [0, reach], color=palette[row[CATEGORY]], linewidth=1.3, zorder=2)
    ax.annotate(
        row[EVENT],
        xy=(row[DATE], reach),
        xytext=(0, 4 * side[i]),
        textcoords="offset points",
        ha="center",
        va="bottom" if side[i] > 0 else "top",
        fontsize=8,
        fontweight="bold",
        color=INK,
    )

span = df[DATE].max() - df[DATE].min()
ax.set_xlim(df[DATE].min() - span * 0.07, df[DATE].max() + span * 0.07)
ax.set_ylim(-1.15, 1.15)
ax.set_yticks([])
ax.set_ylabel("")
ax.set_xlabel("")
sns.despine(ax=ax, left=True, bottom=True)

ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.tick_params(axis="x", labelsize=8, length=0, pad=6)

ax.set_title("timeline-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)
ax.legend(
    title=CATEGORY,
    title_fontsize=8,
    fontsize=8,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.1),
    ncol=len(categories),
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    labelcolor=INK,
)
for handle in ax.get_legend().legend_handles:
    handle.set_markersize(7)

fig.subplots_adjust(left=0.04, right=0.96, top=0.9, bottom=0.2)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
