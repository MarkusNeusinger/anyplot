""" anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-26
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — canonical order; first series is always brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
# Semantic event colors (Imprint positions 2-5); unknown types fall back to the palette by position
EVENT_COLORS = {
    "earnings": IMPRINT_PALETTE[2],  # blue — financial analytics
    "dividend": IMPRINT_PALETTE[3],  # ochre — value/commodity
    "split": IMPRINT_PALETTE[1],  # lavender — corporate action
    "news": IMPRINT_PALETTE[4],  # red — alert
}
EVENT_MARKERS = {"earnings": "E", "dividend": "D", "split": "S", "news": "!"}
FLAG_LEVELS = 3  # alternating flag heights
FLAG_GAP = 0.12  # flag spacing as a share of the price range

# Columns: set these to your table's column names
DATE = "date"  # role: date
CLOSE = "close"  # role: close
EVENT_DATE = "event_date"  # role: event_date
EVENT_TYPE = "event_type"  # role: event_type
EVENT_LABEL = "event_label"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("prices_with_events.csv")
# One row per trading day; the event columns are filled only on days with an event.
np.random.seed(42)
dates = pd.date_range("2025-01-01", periods=180, freq="B")
returns = np.random.normal(0.0005, 0.02, size=180)
prices = 150.0 * np.cumprod(1 + returns)
events = pd.DataFrame(
    {
        EVENT_DATE: pd.to_datetime(
            [
                "2025-01-28",
                "2025-02-14",
                "2025-03-10",
                "2025-04-22",
                "2025-05-08",
                "2025-05-20",
                "2025-06-25",
                "2025-07-28",
                "2025-08-20",
            ]
        ),
        EVENT_TYPE: ["earnings", "dividend", "news", "earnings", "split", "dividend", "news", "earnings", "dividend"],
        EVENT_LABEL: ["Q4", "0.50", "Launch", "Q1", "2:1", "0.50", "Interview", "Q2", "0.55"],
    }
)
df = pd.DataFrame({DATE: dates, CLOSE: prices}).merge(events, how="left", left_on=DATE, right_on=EVENT_DATE)

# Plot: reads only df and the constants above
flags = df.dropna(subset=[EVENT_TYPE]).reset_index(drop=True)
present = set(flags[EVENT_TYPE])
event_types = [t for t in EVENT_COLORS if t in present] + sorted(present - set(EVENT_COLORS))
event_colors = {t: EVENT_COLORS.get(t, IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]) for i, t in enumerate(event_types)}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Price line — first series, brand green
(price_line,) = ax.plot(df[DATE], df[CLOSE], color=BRAND, linewidth=2.5, label="Close Price", zorder=2)

price_min = df[CLOSE].min()
price_max = df[CLOSE].max()
price_range = price_max - price_min

# Light fill under price line
ax.fill_between(df[DATE], price_min * 0.95, df[CLOSE], alpha=0.08, color=BRAND, zorder=1)

# Event flags with alternating heights to avoid overlap
for idx, event in flags.iterrows():
    event_date = event[DATE]
    price_at_date = event[CLOSE]
    color = event_colors[event[EVENT_TYPE]]
    marker_text = EVENT_MARKERS.get(event[EVENT_TYPE], "?")
    flag_y = price_max + price_range * (FLAG_GAP + (idx % FLAG_LEVELS) * FLAG_GAP)

    # Connector line from price point up to flag
    ax.plot(
        [event_date, event_date],
        [price_at_date, flag_y],
        color=color,
        linestyle="--",
        linewidth=1.2,
        alpha=0.7,
        zorder=3,
    )

    # Marker dot at price level
    ax.scatter([event_date], [price_at_date], color=color, s=80, zorder=4, edgecolors=PAGE_BG, linewidth=1.0)

    # Flag annotation box
    ax.annotate(
        f"{marker_text} {event[EVENT_LABEL]}",
        xy=(event_date, flag_y),
        fontsize=8,
        fontweight="bold",
        color="white",
        ha="center",
        va="center",
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": color,
            "edgecolor": ELEVATED_BG,
            "linewidth": 1.5,
            "alpha": 0.92,
        },
        zorder=10,
    )

# Legend — price line + all four event types
legend_handles = [price_line] + [mpatches.Patch(color=c) for c in event_colors.values()]
legend_labels = ["Close Price"] + [et.capitalize() for et in event_colors]
leg = ax.legend(
    handles=legend_handles,
    labels=legend_labels,
    loc="lower left",
    bbox_to_anchor=(0, 1.01),
    ncol=len(legend_labels),
    fontsize=8,
    framealpha=0.9,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Style
title = "stock-event-flags · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=26)
ax.set_xlabel("Date", fontsize=10, color=INK)
ax.set_ylabel("Price (USD)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, labelcolor=INK_SOFT, color=INK_SOFT)
ax.tick_params(which="both", length=0)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_ylim(price_min * 0.95, price_max + price_range * 0.55)

plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

fig.subplots_adjust(left=0.09, right=0.97, top=0.87, bottom=0.15)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
