""" anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-27
"""

import os

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

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = ANYPLOT_PALETTE[0]

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

# Data — 180 trading days; 2:1 split applied at May 2025 to show real price adjustment
np.random.seed(42)
n_days = 180
dates = pd.date_range("2025-01-02", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.018, n_days)
price = 150 * np.cumprod(1 + returns)

split_date = pd.Timestamp("2025-05-08")
split_idx = dates.searchsorted(split_date)
price[split_idx:] = price[split_idx:] * 0.5

df = pd.DataFrame({"date": dates, "close": price})

# Event type styling — anyplot palette positions 2–5
event_colors = {
    "earnings": ANYPLOT_PALETTE[1],
    "dividend": ANYPLOT_PALETTE[2],
    "split": ANYPLOT_PALETTE[3],
    "news": ANYPLOT_PALETTE[4],
}
event_markers = {"earnings": "s", "dividend": "D", "split": "^", "news": "o"}

events = pd.DataFrame(
    {
        "event_date": pd.to_datetime(
            [
                "2025-01-28",
                "2025-02-14",
                "2025-03-15",
                "2025-04-22",
                "2025-05-08",
                "2025-05-28",
                "2025-06-18",
                "2025-07-24",
            ]
        ),
        "event_type": ["earnings", "dividend", "news", "earnings", "split", "dividend", "news", "earnings"],
        "event_label": [
            "Q4 Earnings",
            "Div $0.50",
            "Product Launch",
            "Q1 Earnings",
            "2:1 Split",
            "Div $0.55",
            "Partnership",
            "Q2 Earnings",
        ],
    }
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(data=df, x="date", y="close", ax=ax, color=BRAND, linewidth=2.0, label="Stock Price")
y_base = df["close"].min() * 0.9
ax.fill_between(df["date"], y_base, df["close"], alpha=0.07, color=BRAND)

# Flags — percentage-based offset keeps proportions consistent across the split
for idx, (_, event) in enumerate(events.iterrows()):
    event_date = event["event_date"]
    event_type = event["event_type"]
    event_label = event["event_label"]

    closest_idx = int(np.abs(df["date"] - event_date).values.argmin())
    actual_date = df["date"].iloc[closest_idx]
    price_at_event = df["close"].iloc[closest_idx]

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
        event_label,
        xy=(actual_date, flag_y),
        fontsize=7,
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

# Legend — lower right avoids the early-session price area and first-event flags
legend_elements = [Line2D([0], [0], color=BRAND, linewidth=2.0, label="Stock Price")]
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
    loc="lower right",
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
ax.set_xlabel("Date", fontsize=10, color=INK)
ax.set_ylabel("Stock Price ($)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

fig.autofmt_xdate(rotation=30)
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
