"""anyplot.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-06-02
"""

import os

import matplotlib.dates as mdates
import matplotlib.lines as mlines
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
ANYPLOT_AMBER = "#DDCC77"

# Imprint categorical palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data
np.random.seed(42)
dates_range = pd.date_range("2024-01-15", periods=120, freq="D")

confirmed_base = np.concatenate(
    [
        np.linspace(2, 35, 30),
        np.linspace(35, 80, 15),
        np.linspace(80, 120, 10),
        np.linspace(120, 60, 20),
        np.linspace(60, 25, 15),
        np.linspace(25, 45, 10),
        np.linspace(45, 15, 20),
    ]
)
confirmed_counts = np.maximum(0, confirmed_base + np.random.normal(0, 8, 120)).astype(int)
probable_counts = np.maximum(0, confirmed_counts * 0.35 + np.random.normal(0, 3, 120)).astype(int)
suspect_counts = np.maximum(0, confirmed_counts * 0.20 + np.random.normal(0, 2, 120)).astype(int)

# Long-form DataFrame for sns.histplot stacking
rows = []
for i, date in enumerate(dates_range):
    rows.extend([(date, "Confirmed")] * confirmed_counts[i])
    rows.extend([(date, "Probable")] * probable_counts[i])
    rows.extend([(date, "Suspect")] * suspect_counts[i])
cases_df = pd.DataFrame(rows, columns=["onset_date", "case_type"])

daily_totals = confirmed_counts + probable_counts + suspect_counts
cumulative = np.cumsum(daily_totals)

# Configure theme
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

# Plot — 16:9 landscape canvas (3200 × 1800 px)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

# Weekly bins (~17 bins for 120-day outbreak); spec recommends weekly for > 3 months
bin_edges = mdates.date2num(pd.date_range("2024-01-14", periods=19, freq="7D"))

palette = {
    "Confirmed": IMPRINT_PALETTE[0],  # #009E73 green
    "Probable": IMPRINT_PALETTE[1],  # #C475FD lavender
    "Suspect": IMPRINT_PALETTE[2],  # #4467A3 blue
}

sns.histplot(
    data=cases_df,
    x="onset_date",
    hue="case_type",
    hue_order=["Confirmed", "Probable", "Suspect"],
    multiple="stack",
    palette=palette,
    bins=bin_edges,
    edgecolor=PAGE_BG,
    linewidth=0.5,
    legend=True,
    ax=ax,
)

y_max = ax.get_ylim()[1]

# Peak period — amber shading only, no text label (reduces visual competition)
ax.axvspan(pd.Timestamp("2024-02-25"), pd.Timestamp("2024-03-25"), alpha=0.07, color=ANYPLOT_AMBER, zorder=0)

# Cumulative cases on secondary axis
ax2 = ax.twinx()
ax2.plot(dates_range, cumulative, color=INK_SOFT, linewidth=2.0, alpha=0.75, zorder=3)
ax2.set_ylabel("Cumulative Cases", fontsize=10, color=INK_SOFT, labelpad=8)
ax2.tick_params(axis="y", labelsize=8, colors=INK_SOFT)
ax2.spines["right"].set_color(INK_SOFT)
ax2.spines["top"].set_visible(False)
ax2.spines["left"].set_visible(False)
ax2.spines["bottom"].set_visible(False)

# Intervention markers — staggered labels to avoid overlap with peak shading
intervention_dates = [
    (pd.Timestamp("2024-02-20"), "Travel\nRestrictions", -4),
    (pd.Timestamp("2024-03-25"), "Vaccination\nCampaign", 4),
]
for date, label, day_offset in intervention_dates:
    ax.axvline(date, color=INK_MUTED, linewidth=1.4, linestyle="--", alpha=0.85, zorder=5)
    ax.annotate(
        label,
        xy=(date + pd.Timedelta(days=day_offset), y_max * 0.84),
        fontsize=7,
        fontweight="semibold",
        ha="center",
        va="top",
        color=INK,
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": ELEVATED_BG,
            "edgecolor": INK_SOFT,
            "linewidth": 0.8,
            "alpha": 0.92,
        },
    )

# Style
title = "histogram-epidemic · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=10)
ax.set_xlabel("Date of Symptom Onset", fontsize=10, color=INK)
ax.set_ylabel("New Cases (Weekly)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.set_axisbelow(True)

# Combine legend: histogram series + cumulative line
legend = ax.get_legend()
handles = list(legend.legend_handles)
labels = [t.get_text() for t in legend.get_texts()]
legend.remove()
handles.append(mlines.Line2D([], [], color=INK_SOFT, linewidth=2.0, alpha=0.75))
labels.append("Cumulative Cases")
ax.legend(
    handles=handles, labels=labels, fontsize=8, loc="upper left", framealpha=0.92, edgecolor=INK_SOFT, fancybox=False
)

# Margins: room for rotated x-tick labels at bottom, secondary axis label at right
fig.subplots_adjust(bottom=0.20, right=0.87)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
