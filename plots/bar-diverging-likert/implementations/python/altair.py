"""anyplot.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-06-01
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint diverging ramp for marks: matte red -> grey midpoint -> blue
DIV_MARKS = ["#AE3030", "#6B6A63" if THEME == "light" else "#686762", "#4467A3"]


def mix(c1, c2, t):
    """Blend two hex colors in sRGB."""
    a, b = (tuple(int(c[i : i + 2], 16) for i in (1, 3, 5)) for c in (c1, c2))
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b, strict=True))


# Constants
DISAGREE_STRONG = "Strongly Disagree"  # role: strongly_disagree
DISAGREE = "Disagree"  # role: disagree
NEUTRAL = "Neutral"  # role: neutral
AGREE = "Agree"  # role: agree
AGREE_STRONG = "Strongly Agree"  # role: strongly_agree
LEVELS = [DISAGREE_STRONG, DISAGREE, NEUTRAL, AGREE, AGREE_STRONG]  # ordered Likert scale

# Column constants
QUESTION = "Question"  # role: question

# Data - employee engagement survey, 10 questions on a 5-point Likert scale (percent of respondents)
df = pd.DataFrame(
    {
        QUESTION: [
            "I feel valued at work",
            "My manager supports my growth",
            "I have the tools I need",
            "Work-life balance is respected",
            "Communication is transparent",
            "I see career advancement opportunities",
            "The company culture is inclusive",
            "My compensation is fair",
            "I would recommend this workplace",
            "I feel motivated daily",
        ],
        DISAGREE_STRONG: [3, 5, 2, 8, 12, 15, 4, 18, 6, 10],
        DISAGREE: [7, 10, 5, 15, 18, 22, 8, 25, 10, 16],
        NEUTRAL: [12, 15, 10, 14, 20, 18, 12, 15, 14, 18],
        AGREE: [45, 38, 48, 35, 30, 28, 42, 28, 40, 32],
        AGREE_STRONG: [33, 32, 35, 28, 20, 17, 34, 14, 30, 24],
    }
)

# Plot
RESPONSE, SHARE, START, END, MID, LABEL = "Response", "Share (%)", "start", "end", "mid", "label"

# Sort questions by net agreement (agree + strongly agree - disagree - strongly disagree)
net = df[AGREE] + df[AGREE_STRONG] - df[DISAGREE] - df[DISAGREE_STRONG]
question_order = df.loc[net.sort_values().index, QUESTION].tolist()

# Diverging segments: neutral split evenly across the zero midpoint
segments = df.melt(id_vars=QUESTION, value_vars=LEVELS, var_name=RESPONSE, value_name=SHARE)
segments[RESPONSE] = pd.Categorical(segments[RESPONSE], categories=LEVELS, ordered=True)
segments = segments.sort_values([QUESTION, RESPONSE]).reset_index(drop=True)
before = segments.groupby(QUESTION, observed=True)[SHARE].cumsum() - segments[SHARE]
left_of_neutral = segments[QUESTION].map(df.set_index(QUESTION)[[DISAGREE_STRONG, DISAGREE]].sum(axis=1))
half_neutral = segments[QUESTION].map(df.set_index(QUESTION)[NEUTRAL]) / 2
segments[START] = before - left_of_neutral - half_neutral
segments[END] = segments[START] + segments[SHARE]
segments[MID] = (segments[START] + segments[END]) / 2
segments[LABEL] = segments[SHARE].astype(int).astype(str) + "%"

# Ordered colors: five equally spaced steps of the Imprint diverging ramp, in scale order
steps = [
    DIV_MARKS[0],
    mix(DIV_MARKS[0], DIV_MARKS[1], 0.5),
    DIV_MARKS[1],
    mix(DIV_MARKS[1], DIV_MARKS[2], 0.5),
    DIV_MARKS[2],
]

ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
qf, rf = QUESTION.translate(ESCAPE), RESPONSE.translate(ESCAPE)
title_str = "bar-diverging-likert · python · altair · anyplot.ai"
title_fs = max(11, round(16 * 67 / len(title_str))) if len(title_str) > 67 else 16
y_enc = alt.Y(qf, type="nominal", title=None, sort=question_order, axis=alt.Axis(labelFontSize=11, labelLimit=280))

bars = (
    alt.Chart(segments)
    .mark_bar(stroke=PAGE_BG, strokeWidth=1.2)
    .encode(
        x=alt.X(
            START,
            type="quantitative",
            title=SHARE,
            axis=alt.Axis(titleFontSize=12, labelFontSize=10),
            scale=alt.Scale(domain=[segments[START].min() - 4, segments[END].max() + 4]),
        ),
        x2=END,
        y=y_enc,
        color=alt.Color(
            rf,
            type="nominal",
            title=None,
            sort=None,
            scale=alt.Scale(domain=LEVELS, range=steps),
            legend=alt.Legend(labelFontSize=10, symbolSize=200, orient="bottom", direction="horizontal"),
        ),
        tooltip=[
            alt.Tooltip(qf, title=QUESTION),
            alt.Tooltip(rf, title=RESPONSE),
            alt.Tooltip(SHARE.translate(ESCAPE), type="quantitative", title=SHARE),
        ],
    )
)

# In-bar labels only where the segment has room
labels = (
    alt.Chart(segments[segments[SHARE] >= 10])
    .mark_text(fontSize=13, fontWeight="bold", color="#FFFFFF")
    .encode(x=alt.X(MID, type="quantitative"), y=y_enc, text=LABEL)
)

zero_line = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=INK, strokeWidth=1.5).encode(x="x:Q")

chart = (
    alt.layer(zero_line, bars, labels)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(title_str, fontSize=title_fs, anchor="middle", color=INK),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axisX(
        gridOpacity=0.15, gridColor=INK, domainColor=INK_SOFT, tickColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_axisY(grid=False, domainColor=INK_SOFT, tickColor=INK_SOFT, labelColor=INK_SOFT)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=None, padding=8, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")
