"""anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-27
"""

# When run directly (python seaborn.py), this directory is prepended to
# sys.path, which causes local files like matplotlib.py to shadow the
# installed matplotlib package.  Remove it so the venv package is found.
import pathlib as _pathlib
import sys as _sys


try:
    _here = str(_pathlib.Path(__file__).resolve().parent)
    _sys.path = [p for p in _sys.path if p not in ("", _here)]
except NameError:
    pass  # exec() context — sys.path is already clean
del _sys, _pathlib

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

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

# Constants
# Semantic event styling: color (Imprint positions 2-5) and marker per event type; unknown types fall back
EVENT_STYLE = {
    "earnings": (IMPRINT_PALETTE[1], "s"),
    "dividend": (IMPRINT_PALETTE[2], "D"),
    "split": (IMPRINT_PALETTE[3], "^"),
    "news": (IMPRINT_PALETTE[4], "o"),
}
FALLBACK_MARKERS = ["P", "X", "v", "h"]
SPLIT_TYPE = "split"  # an event of this type starts a new price regime, so the trend is fitted per regime

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Stock Price ($)"  # role: close
EVENT_DATE = "Event date"  # role: event_date
EVENT_TYPE = "Event type"  # role: event_type
EVENT_LABEL = "Event label"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("prices_with_events.csv")
# One row per trading day; the event columns are filled on the trading day an event falls on
np.random.seed(42)
n_days = 180
dates = pd.date_range("2025-01-02", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.018, n_days)
price = 150 * np.cumprod(1 + returns)

# A 2:1 split in May 2025 shows a real price adjustment
split_idx = dates.searchsorted(pd.Timestamp("2025-05-08"))
price[split_idx:] = price[split_idx:] * 0.5

event_dates = pd.to_datetime(
    ["2025-01-28", "2025-02-14", "2025-03-15", "2025-04-22", "2025-05-08", "2025-05-28", "2025-06-18", "2025-07-24"]
)
event_types = ["earnings", "dividend", "news", "earnings", "split", "dividend", "news", "earnings"]
event_labels = [
    "Q4 Earnings",
    "Div $0.50",
    "Product Launch",
    "Q1 Earnings",
    "2:1 Split",
    "Div $0.55",
    "Partnership",
    "Q2 Earnings",
]
# Each event sits on the nearest trading day
event_rows = [int(np.abs(dates - d).argmin()) for d in event_dates]

df = pd.DataFrame({DATE: dates, CLOSE: price, EVENT_DATE: pd.NaT, EVENT_TYPE: None, EVENT_LABEL: None})
df.loc[event_rows, EVENT_DATE] = event_dates
df.loc[event_rows, EVENT_TYPE] = event_types
df.loc[event_rows, EVENT_LABEL] = event_labels

# Plot
events = df[df[EVENT_TYPE].notna()]
present_types = list(dict.fromkeys(events[EVENT_TYPE]))
type_order = [t for t in EVENT_STYLE if t in present_types] + [t for t in present_types if t not in EVENT_STYLE]
event_colors, event_markers = {}, {}
for i, etype in enumerate(type_order):
    fallback = (IMPRINT_PALETTE[(i + 1) % len(IMPRINT_PALETTE)], FALLBACK_MARKERS[i % len(FALLBACK_MARKERS)])
    event_colors[etype], event_markers[etype] = EVENT_STYLE.get(etype, fallback)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Stock price line (seaborn lineplot)
sns.lineplot(data=df, x=DATE, y=CLOSE, ax=ax, color=BRAND, linewidth=2.0, label="Stock Price")
y_base = df[CLOSE].min() * 0.9
ax.fill_between(df[DATE], y_base, df[CLOSE], alpha=0.12, color=BRAND)

# Seaborn-distinctive: per-regime linear regression trend with 95% CI.
# Separate regplots before and after a split avoid a spurious slope from the discontinuity;
# the CI bands give statistical context for each period.
split_dates = events.loc[events[EVENT_TYPE] == SPLIT_TYPE, DATE]
if len(split_dates):
    split_date = split_dates.iloc[0]
    segments = [df[df[DATE] < split_date], df[df[DATE] >= split_date]]
else:
    segments = [df]
for df_seg in segments:
    if len(df_seg) > 2:
        # Dates as matplotlib floats match the internal scale of the date axis, so the fit overlays correctly
        sns.regplot(
            x=mdates.date2num(df_seg[DATE].to_numpy()),
            y=df_seg[CLOSE].to_numpy(),
            ax=ax,
            scatter=False,
            color=INK_MUTED,
            ci=95,
            line_kws={"linewidth": 1.0, "linestyle": ":", "alpha": 0.9},
        )

# Flags: percentage-based offset keeps proportions consistent across the split
for idx, (_, event) in enumerate(events.iterrows()):
    actual_date = event[DATE]
    price_at_event = event[CLOSE]
    event_type = event[EVENT_TYPE]

    flag_pct = price_at_event * 0.06 * (1 + (idx % 3) * 0.3)
    if idx % 2 == 0:
        flag_y = price_at_event + flag_pct
        va = "bottom"
    else:
        flag_y = price_at_event - flag_pct
        va = "top"

    color = event_colors[event_type]
    marker = event_markers[event_type]

    ax.plot([actual_date, actual_date], [price_at_event, flag_y], color=color, linestyle="--", linewidth=1.0, alpha=0.7)
    ax.scatter(
        [actual_date], [price_at_event], color=color, s=70, marker=marker, zorder=5, edgecolors=PAGE_BG, linewidths=0.8
    )
    ax.annotate(
        event[EVENT_LABEL],
        xy=(actual_date, flag_y),
        fontsize=8,
        fontweight="bold",
        color=color,
        ha="center",
        va=va,
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": ELEVATED_BG,
            "edgecolor": color,
            "linewidth": 1.0,
            "alpha": 0.95,
        },
    )

# Legend — upper right sits in the empty space above the post-split price, clear of line and flags
legend_elements = [
    Line2D([0], [0], color=BRAND, linewidth=2.0, label="Stock Price"),
    Line2D([0], [0], color=INK_MUTED, linewidth=1.0, linestyle=":", alpha=0.9, label="Trend (95% CI)"),
]
for etype, color in event_colors.items():
    legend_elements.append(
        plt.scatter(
            [],
            [],
            color=color,
            marker=event_markers[etype],
            s=70,
            label=etype.capitalize(),
            edgecolors=PAGE_BG,
            linewidths=0.8,
        )
    )

ax.legend(
    handles=legend_elements,
    loc="upper right",
    fontsize=8,
    title="Events",
    title_fontsize=8,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    framealpha=0.95,
)

# Style
title = "stock-event-flags · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=10)
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(CLOSE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

fig.autofmt_xdate(rotation=30)
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
