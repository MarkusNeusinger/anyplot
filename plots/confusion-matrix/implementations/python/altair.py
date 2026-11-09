""" anyplot.ai
confusion-matrix: Confusion Matrix Heatmap
Library: altair 6.3.0 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import confusion_matrix


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette; counts are continuous, so the cells take imprint_seq (green to blue)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]  # the two stops of imprint_seq

# Constants
CELL_INKS = ["#1A1A17", "#F0EFE8"]  # dark and light ink; each count takes the one that contrasts more with its cell

# Columns: set these to your table's column names
TRUE_LABEL = "True Label"  # role: true_labels
PREDICTED_LABEL = "Predicted Label"  # role: predicted_labels

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
classes = ["Dog", "Cat", "Bird", "Fish"]
outcomes = np.array([[85, 10, 3, 2], [12, 78, 6, 4], [5, 8, 82, 5], [2, 4, 3, 91]])  # rows true, columns predicted
true_grid, predicted_grid = np.meshgrid(classes, classes, indexing="ij")
df = pd.DataFrame(
    {
        TRUE_LABEL: np.repeat(true_grid.ravel(), outcomes.ravel()),
        PREDICTED_LABEL: np.repeat(predicted_grid.ravel(), outcomes.ravel()),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

labelled = df.dropna(subset=[TRUE_LABEL, PREDICTED_LABEL]).astype(str)
class_order = pd.unique(pd.concat([labelled[TRUE_LABEL], labelled[PREDICTED_LABEL]])).tolist()
matrix = confusion_matrix(labelled[TRUE_LABEL], labelled[PREDICTED_LABEL], labels=class_order)
cells = (
    pd.DataFrame(
        matrix, index=pd.Index(class_order, name=TRUE_LABEL), columns=pd.Index(class_order, name=PREDICTED_LABEL)
    )
    .stack()
    .rename("Count")
    .reset_index()
)
top = int(cells["Count"].max())

# Relative luminance (WCAG) of each cell's fill, interpolated in RGB like the color scale below
seq_rgb = np.array([[int(stop[i : i + 2], 16) for i in (1, 3, 5)] for stop in IMPRINT_SEQ]) / 255
ink_rgb = np.array([[int(ink[i : i + 2], 16) for i in (1, 3, 5)] for ink in CELL_INKS]) / 255
fill_rgb = seq_rgb[0] + (cells["Count"].to_numpy() / max(top, 1))[:, None] * (seq_rgb[1] - seq_rgb[0])
fill_lum, ink_lum = [
    np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4) @ [0.2126, 0.7152, 0.0722]
    for rgb in (fill_rgb, ink_rgb)
]
dark_contrast = (fill_lum + 0.05) / (ink_lum[0] + 0.05)
light_contrast = (ink_lum[1] + 0.05) / (fill_lum + 0.05)
cells["Ink"] = np.where(dark_contrast >= light_contrast, CELL_INKS[0], CELL_INKS[1])

x = alt.X(
    PREDICTED_LABEL.translate(ESCAPE),
    type="nominal",
    title=PREDICTED_LABEL,
    sort=class_order,
    axis=alt.Axis(labelAngle=0, ticks=False, domain=False, labelPadding=8),
)
y = alt.Y(
    TRUE_LABEL.translate(ESCAPE),
    type="nominal",
    title=TRUE_LABEL,
    sort=class_order,
    axis=alt.Axis(ticks=False, domain=False, labelPadding=8, labelLimit=100),
)
tooltip = [
    alt.Tooltip(TRUE_LABEL.translate(ESCAPE), title=TRUE_LABEL),
    alt.Tooltip(PREDICTED_LABEL.translate(ESCAPE), title=PREDICTED_LABEL),
    alt.Tooltip("Count", title="Count"),
]

heatmap = (
    alt.Chart(cells)
    .mark_rect(stroke=PAGE_BG, strokeWidth=2.5)
    .encode(
        x=x,
        y=y,
        color=alt.Color(
            "Count",
            type="quantitative",
            title="Count (samples)",
            scale=alt.Scale(domain=[0, top], range=IMPRINT_SEQ, interpolate="rgb"),
            legend=alt.Legend(
                orient="bottom", direction="horizontal", gradientLength=260, gradientThickness=12, tickCount=5
            ),
        ),
        tooltip=tooltip,
    )
)

counts = (
    alt.Chart(cells)
    .mark_text(fontSize=22, fontWeight="bold")
    .encode(
        x=x,
        y=y,
        text=alt.Text("Count", type="quantitative"),
        color=alt.Color("Ink", type="nominal", scale=None),
        tooltip=tooltip,
    )
)

chart = (
    alt.layer(heatmap, counts)
    .resolve_scale(color="independent")  # the count ink is a literal color per cell, not a second color scale
    .properties(
        width=400,
        height=400,
        background=PAGE_BG,
        padding={"left": 12, "right": 12, "top": 10, "bottom": 10},
        title=alt.Title("confusion-matrix · python · altair · anyplot.ai", fontSize=16, color=INK, offset=14),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=12,
        titleFontSize=13,
        titleFontWeight="normal",
        titlePadding=12,
        grid=False,
    )
    .configure_legend(
        titleColor=INK,
        labelColor=INK_SOFT,
        titleFontSize=11,
        labelFontSize=10,
        titleFontWeight="normal",
        titlePadding=8,
        offset=18,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 2400, 2400
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
