"""anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-05-27
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

# anyplot palette — canonical order; first series is always brand green
ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = ANYPLOT_PALETTE[0]

# Data
np.random.seed(42)
dates = pd.date_range("2025-01-01", periods=180, freq="B")

initial_price = 150.0
returns = np.random.normal(0.0005, 0.02, size=180)
prices = initial_price * np.cumprod(1 + returns)

close = prices
high = close * (1 + np.abs(np.random.normal(0, 0.01, size=180)))
low = close * (1 - np.abs(np.random.normal(0, 0.01, size=180)))
open_price = (close + np.random.normal(0, 1, size=180)).clip(low, high)

df = pd.DataFrame({"date": dates, "open": open_price, "high": high, "low": low, "close": close})

events = [
    {"date": "2025-01-28", "type": "earnings", "label": "Q4"},
    {"date": "2025-02-14", "type": "dividend", "label": "0.50"},
    {"date": "2025-03-10", "type": "news", "label": "Launch"},
    {"date": "2025-04-22", "type": "earnings", "label": "Q1"},
    {"date": "2025-05-08", "type": "split", "label": "2:1"},
    {"date": "2025-05-20", "type": "dividend", "label": "0.50"},
    {"date": "2025-06-25", "type": "news", "label": "Interview"},
    {"date": "2025-07-28", "type": "earnings", "label": "Q2"},
    {"date": "2025-08-20", "type": "dividend", "label": "0.55"},
]

events_df = pd.DataFrame(events)
events_df["date"] = pd.to_datetime(events_df["date"])

# Event colors — palette positions 2-5 (position 1 used by price line)
event_colors = {
    "earnings": ANYPLOT_PALETTE[2],  # #4467A3 blue — financial analytics
    "dividend": ANYPLOT_PALETTE[3],  # #BD8233 ochre — value/commodity
    "split": ANYPLOT_PALETTE[1],  # #C475FD lavender — corporate action
    "news": ANYPLOT_PALETTE[4],  # #AE3030 red — alert semantic fit
}

event_markers = {"earnings": "E", "dividend": "D", "split": "S", "news": "!"}

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Price line — first series, brand green
(price_line,) = ax.plot(df["date"], df["close"], color=BRAND, linewidth=2.5, label="Close Price", zorder=2)

# Light fill under price line
ax.fill_between(df["date"], df["close"].min() * 0.95, df["close"], alpha=0.08, color=BRAND, zorder=1)

price_min = df["close"].min()
price_max = df["close"].max()
price_range = price_max - price_min

# Event flags with alternating heights to avoid overlap
for idx, event in events_df.iterrows():
    event_date = event["date"]
    event_type = event["type"]
    event_label = event["label"]

    price_row = df.loc[df["date"] == event_date, "close"]
    if len(price_row) == 0:
        nearest_idx = np.abs(df["date"] - event_date).argmin()
        price_at_date = df.iloc[nearest_idx]["close"]
    else:
        price_at_date = price_row.values[0]

    color = event_colors.get(event_type, INK_SOFT)
    marker_text = event_markers.get(event_type, "?")

    height_level = idx % 3
    flag_y = price_max + price_range * (0.12 + height_level * 0.12)

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
        f"{marker_text} {event_label}",
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
        zorder=5,
    )

# Legend — price line + all four event types
legend_handles = [price_line] + [mpatches.Patch(color=c, label=et.capitalize()) for et, c in event_colors.items()]
legend_labels = ["Close Price"] + [et.capitalize() for et in event_colors]
leg = ax.legend(handles=legend_handles, labels=legend_labels, loc="upper left", fontsize=8, framealpha=0.9)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Style
title = "stock-event-flags · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel("Date", fontsize=10, color=INK)
ax.set_ylabel("Price (USD)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, labelcolor=INK_SOFT, color=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_ylim(price_min * 0.95, price_max + price_range * 0.55)

plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

fig.subplots_adjust(left=0.09, right=0.97, top=0.91, bottom=0.15)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
