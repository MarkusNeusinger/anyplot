"""anyplot.ai
pie-basic: Basic Pie Chart
Library: altair 6.3.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-27
"""

import os
import sys


# This file is named altair.py — same as the library. Remove the script
# directory from sys.path so Python finds the real altair package in the venv.
_here = os.path.normcase(os.path.abspath(os.path.dirname(__file__)))
sys.path[:] = [p for p in sys.path if os.path.normcase(os.path.abspath(p if p else os.getcwd())) != _here]

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SMALL_SLICE = 5  # slices below this share (%) get their label pushed further out

# Columns: set these to your table's column names
PROVIDER = "Provider"  # role: category
SHARE = "Market share (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("shares.csv")
df = pd.DataFrame(
    {PROVIDER: ["AWS", "Azure", "Google Cloud", "Alibaba", "Oracle", "Others"], SHARE: [31, 24, 11, 4, 3, 27]}
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
provider, share = PROVIDER.translate(ESCAPE), SHARE.translate(ESCAPE)

plot_df = df.assign(pct=df[SHARE] / df[SHARE].sum() * 100, exploded=df[SHARE] == df[SHARE].max())
plot_df["label"] = plot_df["pct"].round().astype("Int64").astype(str) + "%"
plot_df["end"] = plot_df[SHARE].cumsum()
plot_df["start"] = plot_df["end"] - plot_df[SHARE]
plot_df["mid"] = (plot_df["start"] + plot_df["end"]) / 2
theta_scale = alt.Scale(domain=[0, float(df[SHARE].sum())])
plot_df["small"] = plot_df["pct"] < SMALL_SLICE

base = alt.Chart(plot_df).encode(
    color=alt.Color(
        provider,
        type="nominal",
        title=PROVIDER,
        scale=alt.Scale(domain=df[PROVIDER].tolist(), range=IMPRINT_PALETTE),
        legend=alt.Legend(
            titleFontSize=12,
            labelFontSize=11,
            symbolSize=180,
            orient="none",
            legendX=80,
            legendY=482,
            direction="horizontal",
            columns=len(df),
            titleAnchor="middle",
            titleOrient="top",
        ),
    )
)
tooltip = [alt.Tooltip(provider, title=PROVIDER), alt.Tooltip(share, title=SHARE)]

# Slices that stay joined
pie = (
    base.transform_filter(~alt.datum.exploded)
    .mark_arc(outerRadius=170, innerRadius=0, stroke=PAGE_BG, strokeWidth=2, padAngle=0.02, cornerRadius=3)
    .encode(theta=alt.Theta("start", type="quantitative", scale=theta_scale), theta2="end", tooltip=tooltip)
)

# Exploded slice: the largest one, pulled out of the circle
exploded = (
    base.transform_filter(alt.datum.exploded)
    .mark_arc(
        outerRadius=170, innerRadius=0, radiusOffset=25, stroke=PAGE_BG, strokeWidth=2.5, padAngle=0.04, cornerRadius=3
    )
    .encode(theta=alt.Theta("start", type="quantitative", scale=theta_scale), theta2="end", tooltip=tooltip)
)

# Percentage labels in theme ink (the color override keeps the slice hue off the text)
labels_main = (
    base.transform_filter(~alt.datum.exploded & ~alt.datum.small)
    .mark_text(radius=210, fontSize=16, fontWeight="bold")
    .encode(theta=alt.Theta("mid", type="quantitative", scale=theta_scale), text="label:N", color=alt.value(INK))
)
labels_small = (
    base.transform_filter(~alt.datum.exploded & alt.datum.small)
    .mark_text(radius=200, fontSize=13, fontWeight="bold")
    .encode(theta=alt.Theta("mid", type="quantitative", scale=theta_scale), text="label:N", color=alt.value(INK_SOFT))
)
labels_exploded = (
    base.transform_filter(alt.datum.exploded)
    .mark_text(radius=210, radiusOffset=25, fontSize=16, fontWeight="bold")
    .encode(theta=alt.Theta("mid", type="quantitative", scale=theta_scale), text="label:N", color=alt.value(INK))
)

chart = (
    alt.layer(pie, exploded, labels_main, labels_small, labels_exploded)
    .properties(
        width=600,
        height=600,
        padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        background=PAGE_BG,
        title=alt.Title(
            text="pie-basic · python · altair · anyplot.ai",
            subtitle="Global Cloud Infrastructure Market Share",
            fontSize=16,
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
            anchor="middle",
            color=INK,
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=12, offset=8
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Fit to the 2400 x 2400 canvas (scale an overshoot down as a whole, never crop)
TW, TH = 2400, 2400
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
