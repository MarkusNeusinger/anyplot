"""anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: pygal 3.1.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-27
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: position 1 is the price line, event types take the following positions in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CONNECTOR_WIDTHS = {"earnings": 3, "split": 4}  # significant events get a heavier connector
DEFAULT_CONNECTOR_WIDTH = 2

DATE = "Date"  # role: date
CLOSE = "Stock Price ($)"  # role: close
EVENT_DATE = "Event date"  # role: event_date
EVENT_TYPE = "Event type"  # role: event_type
EVENT_LABEL = "Event label"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("prices_with_events.csv")
# One row per trading day; event columns are filled on event days only.
np.random.seed(999)
trading_days = pd.bdate_range(start="2023-07-03", periods=200)
returns = np.random.normal(0.0004, 0.016, len(trading_days))
prices = 240.0 * np.cumprod(1 + returns)
events = pd.DataFrame(
    {
        EVENT_DATE: pd.to_datetime(
            [
                "2023-07-27",
                "2023-08-17",
                "2023-09-14",
                "2023-10-26",
                "2023-11-16",
                "2023-12-05",
                "2024-01-25",
                "2024-02-15",
                "2024-03-11",
            ]
        ),
        EVENT_TYPE: ["earnings", "dividend", "news", "earnings", "dividend", "news", "earnings", "dividend", "split"],
        EVENT_LABEL: [
            "Q2 Beat",
            "$0.22",
            "Partnership",
            "Q3 Miss",
            "$0.24",
            "FDA Approval",
            "Q4 Beat",
            "$0.26",
            "2:1 Split",
        ],
    }
)
df = pd.DataFrame({DATE: trading_days, CLOSE: prices}).merge(events, left_on=DATE, right_on=EVENT_DATE, how="left")

# Plot
event_rows = df[df[EVENT_TYPE].notna()]
event_types = list(dict.fromkeys(event_rows[EVENT_TYPE]))
type_color = {t: IMPRINT_PALETTE[(1 + i) % len(IMPRINT_PALETTE)] for i, t in enumerate(event_types)}

# Flags sit above the price range, one height band per event type
max_price = df[CLOSE].max()
price_range = max_price - df[CLOSE].min()
type_height = {t: 0.12 + 0.08 * i for i, t in enumerate(event_types)}

# Series colors in the order they are added: price, one connector per event, one flag group per type
all_colors = tuple(
    [IMPRINT_PALETTE[0]] + [type_color[t] for t in event_rows[EVENT_TYPE]] + [type_color[t] for t in event_types]
)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=all_colors,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=44,
    value_label_font_size=48,
    value_colors=tuple(INK for _ in all_colors),
    stroke_width=3,
)

# First trading day of each month marks the x ticks
month_start = df.index[df[DATE].dt.to_period("M") != df[DATE].dt.to_period("M").shift()].tolist()
month_name = {
    i: df.loc[i, DATE].strftime("%b" if df.loc[i, DATE].month not in (1, df[DATE].iloc[0].month) else "%b %Y")
    for i in month_start
}

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="Tech Stock 2023 · stock-event-flags · python · pygal · anyplot.ai",
    x_title=DATE,
    y_title=CLOSE,
    show_x_guides=False,
    show_y_guides=True,
    stroke=True,
    fill=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(event_types) + 1,
    dots_size=3,
    truncate_label=-1,
    truncate_legend=-1,
    margin=60,
    spacing=30,
    print_labels=True,
    x_value_formatter=lambda i: month_name.get(int(i), ""),
)
chart.x_labels = month_start

# Main price line (first series, brand green)
chart.add("Price", list(zip(df.index, df[CLOSE], strict=True)), dots_size=0, stroke_style={"width": 4})

# Dashed connectors from the price at each event date up to its flag
for idx, row in event_rows.iterrows():
    flag_y = max_price + price_range * type_height[row[EVENT_TYPE]]
    chart.add(
        None,
        [(idx, row[CLOSE]), (idx, flag_y)],
        stroke=True,
        stroke_style={"width": CONNECTOR_WIDTHS.get(row[EVENT_TYPE], DEFAULT_CONNECTOR_WIDTH), "dasharray": "6,4"},
        show_dots=False,
    )

# Flag markers grouped by event type (drives the legend)
for event_type in event_types:
    flags = event_rows[event_rows[EVENT_TYPE] == event_type]
    flag_y = max_price + price_range * type_height[event_type]
    flag_points = [{"value": (idx, flag_y), "label": row[EVENT_LABEL]} for idx, row in flags.iterrows()]
    chart.add(event_type.capitalize(), flag_points, stroke=False, show_dots=True, dots_size=18)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
