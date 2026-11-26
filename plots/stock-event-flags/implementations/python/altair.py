"""anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-27
"""

import os
import sys


# Prevent this file from shadowing the installed altair package
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the price line, positions 2+ the event types
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
EVENT_SHAPES = ["triangle-up", "diamond", "circle", "square", "triangle-down", "cross", "stroke", "wedge"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Stock Price ($)"  # role: close
EVENT_DATE = "Event date"  # role: event_date
EVENT_TYPE = "Event type"  # role: event_type
EVENT_LABEL = "Event"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
# One row per trading day; the three event columns are filled only on event days.
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=180, freq="B")
rets = np.random.normal(0.0005, 0.018, len(dates))
events = [
    ("2024-01-25", "Earnings", "Q4 Beat"),
    ("2024-02-15", "Dividend", "$0.25 Div"),
    ("2024-03-20", "News", "Product Launch"),
    ("2024-04-24", "Earnings", "Q1 Results"),
    ("2024-05-10", "Dividend", "$0.28 Div"),
    ("2024-06-05", "News", "Partnership"),
    ("2024-07-24", "Earnings", "Q2 Growth"),
    ("2024-08-20", "Split", "2:1 Split"),
]
event_date_col = [pd.NaT] * len(dates)
event_type_col = [None] * len(dates)
event_label_col = [None] * len(dates)
for event_date, event_type, event_label in events:
    i = int(np.abs(dates - pd.Timestamp(event_date)).argmin())
    event_date_col[i], event_type_col[i], event_label_col[i] = dates[i], event_type, event_label
df = pd.DataFrame(
    {
        DATE: dates,
        CLOSE: 100 * np.exp(np.cumsum(rets)),
        EVENT_DATE: event_date_col,
        EVENT_TYPE: event_type_col,
        EVENT_LABEL: event_label_col,
    }
)

# Plot: reads only df and the constants above
FLAG_Y = "Flag level ($)"
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
date_f, close_f, edate_f, etype_f, elabel_f, flag_f = (
    c.translate(ESCAPE) for c in (DATE, CLOSE, EVENT_DATE, EVENT_TYPE, EVENT_LABEL, FLAG_Y)
)

flags_df = df.dropna(subset=[EVENT_TYPE]).reset_index(drop=True)
y_min, y_max = df[CLOSE].min(), df[CLOSE].max()
flag_offset = (y_max - y_min) * 0.18
flags_df["above"] = flags_df.index % 2 == 0
flags_df[FLAG_Y] = np.where(flags_df["above"], flags_df[CLOSE] + flag_offset, flags_df[CLOSE] - flag_offset)

# Connector data: the NaN rows break the line between flags
conn_rows = []
for _, row in flags_df.iterrows():
    conn_rows.append({EVENT_DATE: row[EVENT_DATE], CLOSE: row[CLOSE]})
    conn_rows.append({EVENT_DATE: row[EVENT_DATE], CLOSE: row[FLAG_Y]})
    conn_rows.append({EVENT_DATE: row[EVENT_DATE], CLOSE: np.nan})
df_conn = pd.DataFrame(conn_rows)

# Event types in order of first appearance: colors from palette position 2, one shape each
event_types = list(dict.fromkeys(flags_df[EVENT_TYPE]))
color_scale = alt.Scale(domain=event_types, range=IMPRINT_PALETTE[1 : 1 + len(event_types)])
shape_scale = alt.Scale(domain=event_types, range=EVENT_SHAPES[: len(event_types)])
y_domain = [y_min - flag_offset * 1.8, y_max + flag_offset * 1.8]

price_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.5, color=IMPRINT_PALETTE[0])
    .encode(
        x=alt.X(date_f, type="temporal", title=DATE, axis=alt.Axis(format="%b %Y", labelAngle=-45, tickCount="month")),
        y=alt.Y(close_f, type="quantitative", title=CLOSE, scale=alt.Scale(domain=y_domain)),
        tooltip=[
            alt.Tooltip(date_f, type="temporal", title=DATE),
            alt.Tooltip(close_f, type="quantitative", title=CLOSE, format="$.2f"),
        ],
    )
)

connector_lines = (
    alt.Chart(df_conn)
    .mark_line(strokeDash=[4, 4], strokeWidth=1.5, opacity=0.6, color=INK_SOFT)
    .encode(
        x=alt.X(edate_f, type="temporal"),
        y=alt.Y(close_f, type="quantitative"),
        detail=alt.Detail(edate_f, type="temporal"),
    )
)

flags = (
    alt.Chart(flags_df)
    .mark_point(size=320, filled=True, strokeWidth=2, stroke=PAGE_BG)
    .encode(
        x=alt.X(edate_f, type="temporal"),
        y=alt.Y(flag_f, type="quantitative"),
        color=alt.Color(etype_f, type="nominal", title=EVENT_TYPE, scale=color_scale),
        shape=alt.Shape(etype_f, type="nominal", scale=shape_scale, legend=None),
        tooltip=[
            alt.Tooltip(edate_f, type="temporal", title=EVENT_DATE),
            alt.Tooltip(etype_f, type="nominal", title=EVENT_TYPE),
            alt.Tooltip(elabel_f, type="nominal", title=EVENT_LABEL),
            alt.Tooltip(close_f, type="quantitative", title=CLOSE, format="$.2f"),
        ],
    )
)


def label_layer(rows, dy):
    return (
        alt.Chart(rows)
        .mark_text(fontSize=11, fontWeight="bold", dy=dy)
        .encode(
            x=alt.X(edate_f, type="temporal"),
            y=alt.Y(flag_f, type="quantitative"),
            text=alt.Text(elabel_f, type="nominal"),
            color=alt.Color(etype_f, type="nominal", scale=color_scale, legend=None),
        )
    )


labels_above = label_layer(flags_df[flags_df["above"]], -18)
labels_below = label_layer(flags_df[~flags_df["above"]], 16)

# Title with length-scaled fontsize
title_str = "Tech Stock 2024 · stock-event-flags · python · altair · anyplot.ai"
title_fs = max(11, round(16 * min(1.0, 67 / len(title_str))))

chart = (
    alt.layer(price_line, connector_lines, flags, labels_above, labels_below)
    .properties(
        width=800,
        height=450,
        padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        background=PAGE_BG,
        title=alt.Title(title_str, fontSize=title_fs, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_axisX(grid=False)
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelFontSize=10,
        titleFontSize=10,
        labelColor=INK_SOFT,
        titleColor=INK,
        symbolSize=150,
    )
    .interactive()
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
