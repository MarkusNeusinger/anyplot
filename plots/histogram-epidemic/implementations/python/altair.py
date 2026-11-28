"""anyplot.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: altair 6.1.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-06-02
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (Imprint palette — see default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: full eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
CUMULATIVE_COLOR = IMPRINT_PALETTE[3]  # position 4, ochre: cumulative line

# Constants
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

# Columns: set these to your table's column names
ONSET_DATE = "Date of symptom onset"  # role: onset_date
CASE_COUNT = "New cases"  # role: case_count
CASE_TYPE = "Classification"  # role: case_type
EVENTS = "Intervention"  # role: events
CUMULATIVE = "Cumulative cases"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("cases.csv")
np.random.seed(42)
dates = pd.date_range("2024-01-15", periods=120, freq="D")
days = np.arange(120)
wave1 = 80 * np.exp(-0.5 * ((days - 25) / 6) ** 2)
wave2 = 45 * np.exp(-0.5 * ((days - 55) / 8) ** 2)
wave3 = 25 * np.exp(-0.5 * ((days - 85) / 10) ** 2)
base_rate = wave1 + wave2 + wave3 + 2
confirmed_frac = np.clip(0.6 + 0.2 * np.sin(days / 15), 0.4, 0.85)
probable_frac = np.clip(0.25 - 0.05 * np.sin(days / 15), 0.1, 0.35)
total_cases = np.round(base_rate + np.random.poisson(2, 120)).astype(int)
confirmed = np.round(total_cases * confirmed_frac).astype(int)
probable = np.round(total_cases * probable_frac).astype(int)
suspect = np.clip(total_cases - confirmed - probable, 0, None).astype(int)

df = pd.DataFrame(
    {
        ONSET_DATE: np.tile(dates, 3),
        CASE_COUNT: np.concatenate([confirmed, probable, suspect]),
        CASE_TYPE: ["Confirmed"] * 120 + ["Probable"] * 120 + ["Suspect"] * 120,
    }
)
# An intervention is labelled on one row of its onset date (the first classification)
interventions = {
    "2024-02-10": "Source identified",
    "2024-03-01": "Containment measures",
    "2024-03-20": "Vaccination campaign",
}
df[EVENTS] = df[ONSET_DATE].dt.strftime("%Y-%m-%d").map(interventions).where(df[CASE_TYPE] == "Confirmed")

# Plot: reads only df and the constants above
events = df.dropna(subset=[EVENTS])[[ONSET_DATE, EVENTS]].copy()
type_order = list(df[CASE_TYPE].dropna().unique())
daily_total = df.groupby(ONSET_DATE, as_index=False, sort=True)[CASE_COUNT].sum()
daily_total[CUMULATIVE] = daily_total[CASE_COUNT].cumsum()
max_daily = int(daily_total[CASE_COUNT].max()) + 15
# Staggered label heights so the event labels clear the bars
label_levels = np.array([0.90, 0.73, 0.41])
events["y_pos"] = max_daily * label_levels[np.arange(len(events)) % len(label_levels)]
events["order"] = range(len(events))

color_scale = alt.Scale(domain=type_order, range=IMPRINT_PALETTE)
order_expr = "{" + ", ".join(f"'{t}': {i}" for i, t in enumerate(type_order)) + "}[datum['" + CASE_TYPE + "']]"

bars = (
    alt.Chart(df)
    .mark_bar(stroke=PAGE_BG, strokeWidth=0.5)
    .encode(
        x=alt.X(
            ONSET_DATE.translate(ESCAPE),
            type="temporal",
            title=ONSET_DATE,
            axis=alt.Axis(format="%b %d", labelAngle=-45, tickCount="week"),
        ),
        y=alt.Y(
            CASE_COUNT.translate(ESCAPE), type="quantitative", title=CASE_COUNT, scale=alt.Scale(domain=[0, max_daily])
        ),
        color=alt.Color(
            CASE_TYPE.translate(ESCAPE), type="nominal", scale=color_scale, sort=type_order, title=CASE_TYPE
        ),
        order=alt.Order("order:Q"),
        tooltip=[
            alt.Tooltip(ONSET_DATE.translate(ESCAPE), type="temporal", title=ONSET_DATE, format="%b %d, %Y"),
            alt.Tooltip(CASE_TYPE.translate(ESCAPE), type="nominal", title=CASE_TYPE),
            alt.Tooltip(CASE_COUNT.translate(ESCAPE), type="quantitative", title=CASE_COUNT),
        ],
    )
    .transform_calculate(order=order_expr)
)

# Cumulative line with independent right y-axis
cumulative_line = (
    alt.Chart(daily_total)
    .mark_line(strokeWidth=2.5, interpolate="monotone", color=CUMULATIVE_COLOR)
    .encode(
        x=alt.X(ONSET_DATE.translate(ESCAPE), type="temporal", title=ONSET_DATE),
        y=alt.Y(
            CUMULATIVE.translate(ESCAPE),
            type="quantitative",
            title=CUMULATIVE,
            scale=alt.Scale(domain=[0, daily_total[CUMULATIVE].max() * 1.55]),
            axis=alt.Axis(titleColor=CUMULATIVE_COLOR, labelColor=CUMULATIVE_COLOR, format=",.0f"),
        ),
        tooltip=[
            alt.Tooltip(ONSET_DATE.translate(ESCAPE), type="temporal", title=ONSET_DATE, format="%b %d, %Y"),
            alt.Tooltip(CUMULATIVE.translate(ESCAPE), type="quantitative", title=CUMULATIVE, format=","),
        ],
    )
)

# Vertical intervention rules
rules = (
    alt.Chart(events)
    .mark_rule(strokeDash=[6, 4], strokeWidth=1.5, color=INK_SOFT)
    .encode(x=alt.X(ONSET_DATE.translate(ESCAPE), type="temporal"))
)

# Event labels: horizontal at staggered heights, clear of the bars
rule_labels = (
    alt.Chart(events)
    .mark_text(align="left", dx=4, fontSize=12, fontStyle="italic", color=INK_MUTED)
    .encode(
        x=alt.X(ONSET_DATE.translate(ESCAPE), type="temporal"),
        y=alt.Y("y_pos:Q"),
        text=alt.Text(EVENTS.translate(ESCAPE), type="nominal"),
    )
)

# Peak annotation: the day with the most new cases
peak_row = daily_total.loc[[daily_total[CASE_COUNT].idxmax()]].copy()
peak_row["label"] = peak_row[CASE_COUNT].map(lambda n: f"Peak: {n} cases")
peak_label = (
    alt.Chart(peak_row)
    .mark_text(fontSize=12, fontWeight="bold", color=CUMULATIVE_COLOR, align="right", dy=-10, dx=-14)
    .encode(
        x=alt.X(ONSET_DATE.translate(ESCAPE), type="temporal"),
        y=alt.Y(CASE_COUNT.translate(ESCAPE), type="quantitative"),
        text="label:N",
    )
)

# Title size scaled to the mandated title length (67-char baseline)
title_str = "histogram-epidemic · python · altair · anyplot.ai"
title_fontsize = round(16 * min(1.0, 67 / len(title_str)))

# Layer and compose
bar_layer = alt.layer(bars, rules, rule_labels, peak_label)

chart = (
    alt.layer(bar_layer, cumulative_line)
    .resolve_scale(y="independent")
    .properties(
        width=800,
        height=450,
        padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        background=PAGE_BG,
        title=alt.Title(
            title_str,
            fontSize=title_fontsize,
            anchor="start",
            color=INK,
            subtitle="Daily new cases by classification with cumulative total",
            subtitleFontSize=11,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        gridOpacity=0.15,
        gridColor=INK,
        domainColor=INK_SOFT,
        domainWidth=0,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_legend(
        titleFontSize=10,
        labelFontSize=10,
        symbolSize=150,
        orient="top-right",
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        padding=6,
        cornerRadius=4,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
)

# Save PNG
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Fit-to-canvas safeguard (altair.md): scale down, never crop; centre on PAGE_BG
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
