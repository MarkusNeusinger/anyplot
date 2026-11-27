"""anyplot.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: altair 6.3.0 | Python 3.14.10
Quality: 88/100 | Updated: 2026-11-27
"""

import importlib
import os
import sys

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.datasets import load_wine
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Drop script directory from sys.path so `altair` resolves the package, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # the cumulative curve
THRESH_COLORS = [IMPRINT_PALETTE[2], IMPRINT_PALETTE[3]]  # blue, ochre: one per threshold
ELBOW_COLOR = IMPRINT_PALETTE[4]  # matte red: the key decision point

# Constants
THRESHOLDS = [90, 95]  # percent of variance to retain, as the spec's reference lines

# Columns: set these to your table's column names
COMPONENT = "Number of components"  # role: n_components
RATIO = "Explained variance ratio"  # role: explained_variance_ratio

# Data: replace this block with your own table, for example df = pd.read_csv("pca_variance.csv")
wine = load_wine()
pca = PCA().fit(StandardScaler().fit_transform(wine.data))
df = pd.DataFrame(
    {COMPONENT: np.arange(1, len(pca.explained_variance_ratio_) + 1), RATIO: pca.explained_variance_ratio_}
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
CUMULATIVE = "Cumulative explained variance (%)"
CROSSING = "Components needed"
THRESHOLD = "Threshold"
ELBOW = "Elbow"

n_components = df[COMPONENT].to_numpy()
cumulative = df[RATIO].cumsum().to_numpy() * 100
cum_df = pd.DataFrame({COMPONENT: n_components, CUMULATIVE: cumulative})

# Elbow via kneedle: the point farthest from the diagonal between first and last component
x_norm = (n_components - n_components[0]) / (n_components[-1] - n_components[0])
y_norm = (cumulative - cumulative[0]) / (cumulative[-1] - cumulative[0])
elbow_idx = int(np.argmax(np.abs(y_norm - x_norm)))
elbow_df = pd.DataFrame(
    {
        COMPONENT: [n_components[elbow_idx]],
        CUMULATIVE: [cumulative[elbow_idx]],
        ELBOW: [f"Elbow (PC {n_components[elbow_idx]})"],
    }
)

# First component count that reaches each threshold
threshold_df = pd.DataFrame({THRESHOLD: [f"{t} %" for t in THRESHOLDS], CUMULATIVE: THRESHOLDS})
reached = [int(np.searchsorted(cumulative, t)) for t in THRESHOLDS]
crossing_df = pd.DataFrame(
    {
        COMPONENT: [n_components[i] for i in reached if i < len(cumulative)],
        CUMULATIVE: [cumulative[i] for i in reached if i < len(cumulative)],
        THRESHOLD: [f"{t} %" for t, i in zip(THRESHOLDS, reached, strict=True) if i < len(cumulative)],
        CROSSING: [f"{n_components[i]} components" for i in reached if i < len(cumulative)],
    }
)

x_scale = alt.Scale(domain=[n_components.min() - 0.5, n_components.max() + 0.5], nice=False)
y_scale = alt.Scale(domain=[cumulative.min() - 12, cumulative.max() + 5], nice=False)
threshold_scale = alt.Scale(domain=list(threshold_df[THRESHOLD]), range=THRESH_COLORS)

x_enc = alt.X(COMPONENT.translate(ESCAPE), type="quantitative", title=COMPONENT, scale=x_scale)
y_enc = alt.Y(CUMULATIVE.translate(ESCAPE), type="quantitative", title=CUMULATIVE, scale=y_scale)
x_axis = alt.X(
    COMPONENT.translate(ESCAPE), type="quantitative", title=COMPONENT, scale=x_scale, axis=alt.Axis(tickMinStep=1)
)
y_axis = alt.Y(
    CUMULATIVE.translate(ESCAPE), type="quantitative", title=CUMULATIVE, scale=y_scale, axis=alt.Axis(format=".0f")
)
threshold_color = alt.Color(THRESHOLD.translate(ESCAPE), type="nominal", scale=threshold_scale, legend=None)

line = alt.Chart(cum_df).mark_line(strokeWidth=3, color=BRAND, interpolate="monotone").encode(x=x_axis, y=y_axis)

points = (
    alt.Chart(cum_df)
    .mark_point(size=130, color=BRAND, filled=True, stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        x=x_enc,
        y=y_enc,
        tooltip=[
            alt.Tooltip(COMPONENT.translate(ESCAPE), type="quantitative", title=COMPONENT),
            alt.Tooltip(CUMULATIVE.translate(ESCAPE), type="quantitative", format=".1f", title=CUMULATIVE),
        ],
    )
)

# Interactive nearest-point highlight with a guide rule (HTML output)
nearest = alt.selection_point(nearest=True, on="pointerover", fields=[COMPONENT.translate(ESCAPE)], empty=False)

invisible_selector = alt.Chart(cum_df).mark_point(size=300, opacity=0).encode(x=x_enc, y=y_enc).add_params(nearest)

highlight_point = (
    alt.Chart(cum_df)
    .mark_point(size=190, color=BRAND, filled=True, stroke=INK, strokeWidth=2)
    .encode(x=x_enc, y=y_enc, opacity=alt.condition(nearest, alt.value(1), alt.value(0)))
)

hover_rule = (
    alt.Chart(cum_df)
    .mark_rule(color=INK_SOFT, strokeDash=[3, 3], strokeWidth=1, opacity=0.5)
    .encode(x=x_enc)
    .transform_filter(nearest)
)

threshold_lines = (
    alt.Chart(threshold_df)
    .mark_rule(strokeDash=[8, 5], strokeWidth=2, opacity=0.8)
    .encode(
        y=y_enc,
        color=alt.Color(
            THRESHOLD.translate(ESCAPE),
            type="nominal",
            title=THRESHOLD,
            scale=threshold_scale,
            legend=alt.Legend(
                titleFontSize=12,
                titleFontWeight="bold",
                labelFontSize=11,
                orient="right",
                symbolStrokeWidth=2,
                symbolSize=140,
                symbolType="stroke",
                symbolDash=[8, 5],
                offset=8,
            ),
        ),
    )
)

crossing_markers = (
    alt.Chart(crossing_df)
    .mark_point(shape="diamond", size=200, filled=True, stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        x=x_enc,
        y=y_enc,
        color=threshold_color,
        tooltip=[
            alt.Tooltip(COMPONENT.translate(ESCAPE), type="quantitative", title=CROSSING),
            alt.Tooltip(CUMULATIVE.translate(ESCAPE), type="quantitative", format=".1f", title=CUMULATIVE),
            alt.Tooltip(THRESHOLD.translate(ESCAPE), type="nominal", title=THRESHOLD),
        ],
    )
)

crossing_labels = (
    alt.Chart(crossing_df)
    .mark_text(fontSize=11, fontWeight="bold", dy=-30, align="center")
    .encode(x=x_enc, y=y_enc, text=alt.Text(CROSSING.translate(ESCAPE), type="nominal"), color=threshold_color)
)

elbow_marker = (
    alt.Chart(elbow_df)
    .mark_point(shape="triangle-up", size=240, color=ELBOW_COLOR, filled=True, stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        x=x_enc,
        y=y_enc,
        tooltip=[
            alt.Tooltip(COMPONENT.translate(ESCAPE), type="quantitative", title="Elbow at component"),
            alt.Tooltip(CUMULATIVE.translate(ESCAPE), type="quantitative", format=".1f", title=CUMULATIVE),
        ],
    )
)

# dx moves the label right so it clears the triangle
elbow_label = (
    alt.Chart(elbow_df)
    .mark_text(fontSize=12, fontWeight="bold", color=ELBOW_COLOR, dy=20, dx=50)
    .encode(x=x_enc, y=y_enc, text=alt.Text(ELBOW.translate(ESCAPE), type="nominal"))
)

chart = (
    (
        threshold_lines
        + hover_rule
        + line
        + points
        + crossing_markers
        + crossing_labels
        + elbow_marker
        + elbow_label
        + invisible_selector
        + highlight_point
    )
    .properties(
        background=PAGE_BG,
        width=800,
        height=450,
        padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        title=alt.Title(
            text="line-pca-variance-cumulative · python · altair · anyplot.ai", fontSize=16, anchor="middle", offset=12
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        grid=True,
        gridOpacity=0.15,
        gridColor=INK,
        domain=False,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=13,
        titlePadding=10,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=8)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
