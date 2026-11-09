"""anyplot.ai
line-loss-training: Training Loss Curve
Library: altair 6.1.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-14
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: training loss takes position 1, validation loss position 2
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LOSS_AXIS = "Cross-entropy loss"  # the loss function both curves report

# Columns: set these to your table's column names
EPOCH = "Epoch"  # role: epoch
TRAIN_LOSS = "Training loss"  # role: train_loss
VAL_LOSS = "Validation loss"  # role: val_loss

# Data: replace this block with your own table, for example df = pd.read_csv("history.csv")
np.random.seed(42)
epochs = np.arange(1, 51)
train_loss = 2.5 * np.exp(-0.08 * epochs) + 0.15 + np.random.normal(0, 0.02, len(epochs))
val_loss = 2.5 * np.exp(-0.07 * epochs) + 0.35 + np.random.normal(0, 0.025, len(epochs))
val_loss[25:] = val_loss[25:] + np.linspace(0, 0.35, 25)  # overfitting after epoch 25
df = pd.DataFrame({EPOCH: epochs, TRAIN_LOSS: train_loss, VAL_LOSS: val_loss})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
CURVE, LOSS = "Curve", "Loss"
long_df = df.melt(id_vars=EPOCH, value_vars=[TRAIN_LOSS, VAL_LOSS], var_name=CURVE, value_name=LOSS)
best = df.loc[df[VAL_LOSS].idxmin()]
best_df = pd.DataFrame({EPOCH: [best[EPOCH]], LOSS: [best[VAL_LOSS]]})

x_enc = alt.X(
    EPOCH.translate(ESCAPE),
    type="quantitative",
    title=EPOCH,
    scale=alt.Scale(domain=[df[EPOCH].min(), df[EPOCH].max()], nice=False),
)
y_enc = alt.Y(LOSS, type="quantitative", title=LOSS_AXIS)
color_scale = alt.Scale(domain=[TRAIN_LOSS, VAL_LOSS], range=IMPRINT_PALETTE)
color_enc = alt.Color(
    CURVE,
    type="nominal",
    title=None,
    scale=color_scale,
    legend=alt.Legend(orient="top-right", padding=8, symbolStrokeWidth=3, symbolSize=200),
)
tooltip = [
    alt.Tooltip(EPOCH.translate(ESCAPE), title=EPOCH),
    alt.Tooltip(CURVE, title=CURVE),
    alt.Tooltip(LOSS, title=LOSS_AXIS, format=".3f"),
]

lines = alt.Chart(long_df).mark_line(strokeWidth=2.5).encode(x=x_enc, y=y_enc, color=color_enc)
points = (
    alt.Chart(long_df)
    .mark_point(size=28, filled=True, opacity=0.9)
    .encode(x=x_enc, y=y_enc, color=alt.Color(CURVE, type="nominal", scale=color_scale, legend=None), tooltip=tooltip)
)

# Optimal stopping point: the epoch of minimum validation loss
best_rule = (
    alt.Chart(best_df).mark_rule(color=INK_SOFT, strokeDash=[5, 4], strokeWidth=1.2, opacity=0.8).encode(x=x_enc)
)
best_marker = (
    alt.Chart(best_df)
    .mark_point(shape="diamond", size=220, filled=True, color=IMPRINT_PALETTE[1], stroke=INK, strokeWidth=1.2)
    .encode(x=x_enc, y=alt.Y(LOSS, type="quantitative"))
)
best_label = (
    alt.Chart(best_df)
    .mark_text(align="left", dx=10, dy=-24, fontSize=11, fontWeight="bold", color=INK)
    .encode(
        x=x_enc,
        y=alt.Y(LOSS, type="quantitative"),
        text=alt.value(f"Min validation loss {best[VAL_LOSS]:.3f} at epoch {int(best[EPOCH])}"),
    )
)

title = "line-loss-training · python · altair · anyplot.ai"
chart = (
    alt.layer(best_rule, lines, points, best_marker, best_label)
    .properties(
        width=620,
        height=320,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        background=PAGE_BG,
        title=alt.Title(title, fontSize=16, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0, continuousWidth=620, continuousHeight=320)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        ticks=False,
        gridColor=INK,
        gridOpacity=0.12,
        labelColor=INK_SOFT,
        titleColor=INK,
        titlePadding=8,
    )
    .configure_axisX(grid=False)
    .configure_title(color=INK)
    .configure_legend(
        labelFontSize=10,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        cornerRadius=4,
    )
    .interactive()
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
