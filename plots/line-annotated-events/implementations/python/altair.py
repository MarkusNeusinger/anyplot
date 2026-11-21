""" anyplot.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: altair 6.3.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-21
"""

import os
import sys


sys.path.pop(0)

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: the line takes position 1, event types take the following positions
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
PRICE = "Stock price ($)"  # role: value
EVENT_DATE = "Event date"  # role: event_date
EVENT_LABEL = "Event"  # role: event_label
EVENT_TYPE = "Event type"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv");
# a row with a non-empty EVENT_LABEL marks an event on that row's date
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=250, freq="B")  # business days over one year
prices = 150 * np.exp(np.cumsum(np.random.normal(0.0005, 0.015, len(dates))))

event_rows = pd.DataFrame(
    {
        DATE: pd.to_datetime(["2024-02-15", "2024-04-25", "2024-06-10", "2024-07-24", "2024-09-18", "2024-11-05"]),
        EVENT_LABEL: ["Q4 Earnings", "Q1 Earnings", "Product Launch", "Q2 Earnings", "Analyst Upgrade", "Q3 Earnings"],
        EVENT_TYPE: ["Earnings", "Earnings", "Product", "Earnings", "Analyst", "Earnings"],
    }
)
event_rows[EVENT_DATE] = event_rows[DATE]
df = pd.DataFrame({DATE: dates, PRICE: prices}).merge(event_rows, on=DATE, how="left")

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
f_date, f_price = DATE.translate(ESCAPE), PRICE.translate(ESCAPE)
f_elabel, f_etype = EVENT_LABEL.translate(ESCAPE), EVENT_TYPE.translate(ESCAPE)
f_edate = EVENT_DATE.translate(ESCAPE)

VIEW_H = 320  # inner view height in px, see the canvas rule
price_max = df[PRICE].max()
price_lo, price_hi = df[PRICE].min() * 0.95, price_max * 1.12

# Alternate marker heights so neighbouring labels stay apart
events = df.dropna(subset=[EVENT_LABEL]).reset_index(drop=True)
events = events.assign(y_position=[price_max * (1.08 if i % 2 == 0 else 1.02) for i in range(len(events))])

type_names = list(events[EVENT_TYPE].unique())
type_scale = alt.Scale(domain=type_names, range=IMPRINT_PALETTE[1 : 1 + len(type_names)])
type_color = alt.Color(f_etype, type="nominal", title=EVENT_TYPE, scale=type_scale, sort=None)

line = (
    alt.Chart(df)
    .mark_line(strokeWidth=2, color=IMPRINT_PALETTE[0])
    .encode(
        x=alt.X(f_date, type="temporal", title=DATE),
        y=alt.Y(f_price, type="quantitative", title=PRICE, scale=alt.Scale(domain=[price_lo, price_hi])),
    )
)

rules = (
    alt.Chart(events)
    .mark_rule(strokeWidth=1.5, strokeDash=[5, 3], opacity=0.7)
    .encode(
        x=alt.X(f_edate, type="temporal"),
        y=alt.Y("y_position", type="quantitative"),
        y2=alt.value(VIEW_H),
        color=type_color,
    )
)

markers = (
    alt.Chart(events)
    .mark_point(size=110, filled=True, opacity=1, stroke=INK, strokeWidth=1)
    .encode(
        x=alt.X(f_edate, type="temporal"),
        y=alt.Y("y_position", type="quantitative"),
        color=type_color,
        tooltip=[
            alt.Tooltip(f_elabel, title=EVENT_LABEL),
            alt.Tooltip(f_etype, title=EVENT_TYPE),
            alt.Tooltip(f_edate, type="temporal", title=EVENT_DATE),
        ],
    )
)

labels = (
    alt.Chart(events)
    .mark_text(align="center", baseline="bottom", fontSize=11, fontWeight="bold", color=INK, dy=-9)
    .encode(x=alt.X(f_edate, type="temporal"), y=alt.Y("y_position", type="quantitative"), text=f_elabel)
)

chart = (
    alt.layer(line, rules, markers, labels)
    .properties(
        width=620,
        height=VIEW_H,
        background=PAGE_BG,
        title=alt.Title("line-annotated-events · python · altair · anyplot.ai", fontSize=18, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=12,
        titleColor=INK,
        titleFontSize=14,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        labelFontSize=12,
        titleColor=INK,
        titleFontSize=13,
        symbolSize=110,
        padding=6,
    )
)

# Output
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    # wide axis titles or a tall legend (other data) overshoot: re-save smaller instead of cropping
    chart.save(f"plot-{THEME}.png", scale_factor=4.0 * min(TW / img.width, TH / img.height) * 0.99)
    img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.size != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
chart.interactive().save(f"plot-{THEME}.html")
