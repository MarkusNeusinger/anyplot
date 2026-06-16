""" anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-27
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_segment,
    geom_smooth,
    geom_text,
    geom_vline,
    ggplot,
    guides,
    labs,
    scale_color_manual,
    scale_shape_manual,
    scale_size_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

color_map = {
    "Earnings": IMPRINT_PALETTE[0],  # #009E73 brand green
    "Dividend": IMPRINT_PALETTE[1],  # #C475FD lavender
    "News": IMPRINT_PALETTE[2],  # #4467A3 blue
    "Split": IMPRINT_PALETTE[3],  # #BD8233 ochre
}
shape_map = {"Earnings": "s", "Dividend": "D", "News": "^", "Split": "o"}
# Earnings get larger markers — primary price catalyst deserves visual emphasis
size_map = {"Earnings": 5, "Dividend": 3, "News": 3, "Split": 3}

# Data
np.random.seed(42)
n_days = 180
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.018, n_days)
price = 150 * np.cumprod(1 + returns)

df_price = pd.DataFrame({"date": dates, "close": price})

# 2:1 split adjustment: halve prices from the day after the split effective date
split_date = pd.Timestamp("2024-05-20")
df_price.loc[df_price["date"] > split_date, "close"] /= 2

events = pd.DataFrame(
    {
        "event_date": pd.to_datetime(
            [
                "2024-01-25",
                "2024-02-15",
                "2024-04-02",
                "2024-04-25",
                "2024-05-20",
                "2024-06-10",
                "2024-07-25",
                "2024-08-15",
            ]
        ),
        "event_type": ["Earnings", "Dividend", "News", "Earnings", "Split", "Dividend", "Earnings", "News"],
        "event_label": [
            "Q4 Beat",
            "Div $0.50",
            "New Product",
            "Q1 Miss",
            "2:1 Split",
            "Div $0.55",
            "Q2 Beat",
            "Partnership",
        ],
    }
)

events["matched_date"] = events["event_date"].apply(
    lambda x: df_price.loc[(df_price["date"] - x).abs().idxmin(), "date"]
)
events["price_at_event"] = events["matched_date"].apply(
    lambda x: df_price.loc[df_price["date"] == x, "close"].values[0]
)

max_price = df_price["close"].max()
min_price = df_price["close"].min()
price_range = max_price - min_price

# Alternate flags above/below price to avoid overlap
flag_offsets = []
for i, (_, row) in enumerate(events.iterrows()):
    if i % 2 == 0:
        flag_offsets.append(row["price_at_event"] + price_range * 0.15 + (i % 3) * price_range * 0.08)
    else:
        flag_offsets.append(row["price_at_event"] - price_range * 0.15 - (i % 3) * price_range * 0.08)

events["flag_y"] = flag_offsets

# Separate earnings labels (larger) from secondary event labels for size hierarchy
events_earnings = events[events["event_type"] == "Earnings"]
events_other = events[events["event_type"] != "Earnings"]

# Plot
plot = (
    ggplot()
    + geom_line(data=df_price, mapping=aes(x="date", y="close"), color=INK_SOFT, size=1.0, alpha=0.9)
    + geom_smooth(
        data=df_price,
        mapping=aes(x="date", y="close"),
        method="lowess",
        color=IMPRINT_PALETTE[0],
        fill=IMPRINT_PALETTE[0],
        size=0.7,
        alpha=0.1,
    )
    + geom_vline(
        data=events, mapping=aes(xintercept="matched_date"), linetype="dashed", color=INK_SOFT, alpha=0.35, size=0.4
    )
    + geom_segment(
        data=events,
        mapping=aes(x="matched_date", xend="matched_date", y="price_at_event", yend="flag_y", color="event_type"),
        size=0.7,
    )
    + geom_point(
        data=events,
        mapping=aes(x="matched_date", y="flag_y", color="event_type", shape="event_type", size="event_type"),
        fill=ELEVATED_BG,
        stroke=1.5,
    )
    + geom_text(
        data=events_other,
        mapping=aes(x="matched_date", y="flag_y", label="event_label", color="event_type"),
        size=3.5,
        ha="center",
        va="bottom",
        nudge_y=price_range * 0.03,
        fontweight="bold",
    )
    + geom_text(
        data=events_earnings,
        mapping=aes(x="matched_date", y="flag_y", label="event_label", color="event_type"),
        size=4,
        ha="center",
        va="bottom",
        nudge_y=price_range * 0.03,
        fontweight="bold",
    )
    + scale_color_manual(values=color_map, name="Event Type")
    + scale_shape_manual(values=shape_map, name="Event Type")
    + scale_size_manual(values=size_map)
    + guides(size="none")
    + scale_x_datetime(date_labels="%b %Y", date_breaks="1 month")
    + labs(title="stock-event-flags · python · plotnine · anyplot.ai", x="Date", y="Stock Price ($)")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        axis_text_x=element_text(rotation=45, ha="right", color=INK_SOFT, size=8),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(color=INK, size=12, weight="bold"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_text(color=INK, size=10, weight="bold"),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
