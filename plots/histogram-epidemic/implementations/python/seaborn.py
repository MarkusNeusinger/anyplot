"""anyplot.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-28
"""

import os

import matplotlib.dates as mdates
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
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

# Columns: set these to your table's column names
ONSET_DATE = "Date of Symptom Onset"  # role: onset_date
CASE_COUNT = "New Cases"  # role: case_count
CASE_TYPE = "Case classification"  # role: case_type
INTERVENTION = "Intervention"  # role: events

# Data: replace this block with your own table, for example df = pd.read_csv("cases.csv")
# One row per onset date and case classification; the first row of an intervention date also carries its label.
np.random.seed(42)
dates = pd.date_range("2024-01-15", periods=120, freq="D")
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
confirmed = np.maximum(0, confirmed_base + np.random.normal(0, 8, 120)).astype(int)
probable = np.maximum(0, confirmed * 0.35 + np.random.normal(0, 3, 120)).astype(int)
suspect = np.maximum(0, confirmed * 0.20 + np.random.normal(0, 2, 120)).astype(int)
df = pd.DataFrame(
    {
        ONSET_DATE: np.repeat(dates, 3),
        CASE_TYPE: ["Confirmed", "Probable", "Suspect"] * 120,
        CASE_COUNT: np.column_stack([confirmed, probable, suspect]).ravel(),
    }
)
events = [(pd.Timestamp("2024-02-20"), "Travel\nRestrictions"), (pd.Timestamp("2024-03-25"), "Vaccination\nCampaign")]
first_of_day = ~df[ONSET_DATE].duplicated()
df[INTERVENTION] = df[ONSET_DATE].map(dict(events)).where(first_of_day)
df = df.copy()

# Plot
case_types = list(df[CASE_TYPE].dropna().unique())
palette = dict(zip(case_types, sns.color_palette(IMPRINT_PALETTE, n_colors=len(case_types)), strict=False))
interventions = df.dropna(subset=[INTERVENTION])[[ONSET_DATE, INTERVENTION]]

# Weekly bins (spec: weekly for outbreaks longer than 3 months), starting on the first onset date
first_day = df[ONSET_DATE].min()
n_weeks = int(np.ceil(((df[ONSET_DATE].max() - first_day).days + 1) / 7))
week_starts = pd.date_range(first_day, periods=n_weeks + 1, freq="7D")
bin_edges = list(mdates.date2num(week_starts))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.histplot(
    data=df,
    x=ONSET_DATE,
    weights=CASE_COUNT,
    hue=CASE_TYPE,
    hue_order=case_types,
    multiple="stack",
    palette=palette,
    bins=bin_edges,
    edgecolor=PAGE_BG,
    linewidth=0.5,
    legend=True,
    ax=ax,
)
# Headroom above bars and line: the intervention labels sit in this band
ax.set_ylim(0, ax.get_ylim()[1] * 1.25)

# Peak period: the weeks holding at least 75 % of the busiest week's cases
weekly = df.groupby(pd.cut(df[ONSET_DATE], week_starts, right=False, labels=week_starts[:-1]), observed=False)[
    CASE_COUNT
].sum()
peak_weeks = weekly.index[weekly >= 0.75 * weekly.max()]
ax.axvspan(peak_weeks.min(), peak_weeks.max() + pd.Timedelta(days=7), alpha=0.13, color=ANYPLOT_AMBER, zorder=0)
peak_handle = mpatches.Patch(facecolor=ANYPLOT_AMBER, alpha=0.3, edgecolor="none")

# Cumulative cases on a secondary axis
daily_total = df.groupby(ONSET_DATE)[CASE_COUNT].sum()
ax2 = ax.twinx()
cumulative = daily_total.cumsum()
ax2.plot(cumulative.index, cumulative, color=INK_SOFT, linewidth=2.0, alpha=0.75, zorder=3)
ax2.set_ylim(0, cumulative.max() * 1.25)
ax2.set_ylabel("Cumulative Cases", fontsize=10, color=INK_SOFT, labelpad=8)
ax2.tick_params(axis="y", labelsize=8, colors=INK_SOFT)
ax2.spines["right"].set_color(INK_SOFT)
for side in ("top", "left", "bottom"):
    ax2.spines[side].set_visible(False)

# Intervention markers: dashed line plus a label box to the right of it
for date, label in interventions.itertuples(index=False):
    ax.axvline(date, color=INK_MUTED, linewidth=1.4, linestyle="--", alpha=0.85, zorder=5)
    ax.annotate(
        label,
        xy=(mdates.date2num(date), 0.985),
        xycoords=ax.get_xaxis_transform(),
        xytext=(4, 0),
        textcoords="offset points",
        fontsize=8,
        fontweight="semibold",
        ha="left",
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
ax.set_xlabel(ONSET_DATE, fontsize=10, color=INK)
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
handles.append(peak_handle)
labels.append("Peak period")
ax.legend(
    handles=handles, labels=labels, fontsize=8, loc="upper left", framealpha=0.92, edgecolor=INK_SOFT, fancybox=False
)

# Margins: room for rotated x-tick labels at bottom, secondary axis label at right
fig.subplots_adjust(bottom=0.20, right=0.87)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
