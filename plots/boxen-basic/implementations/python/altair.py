"""anyplot.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: altair 6.3.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
"""

import os

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
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette; the letter-value levels are ordered, so they take steps of imprint_seq (green to blue)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]  # the two stops of imprint_seq

# Constants
LEVEL_NAMES = {1: "Fourths", 2: "Eighths", 3: "Sixteenths"}  # deeper letter values are named by their tail, 1/32 ...

# Columns: set these to your table's column names
ENDPOINT = "Endpoint"  # role: category
RESPONSE_TIME = "Response Time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
samples = {
    "API Gateway": np.concatenate([np.random.lognormal(3.5, 0.6, 2000), np.random.uniform(150, 300, 50)]),
    "Database": np.random.lognormal(4.0, 0.8, 2050),
    "Auth Service": np.concatenate([np.random.lognormal(3.2, 0.4, 1900), np.random.uniform(80, 150, 100)]),
    "Cache": np.concatenate([np.random.lognormal(2.5, 0.5, 1950), np.random.uniform(50, 100, 100)]),
}
df = pd.DataFrame(
    {
        ENDPOINT: np.repeat(list(samples), [len(values) for values in samples.values()]),
        RESPONSE_TIME: np.concatenate(list(samples.values())),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
VIEW_W, VIEW_H = 560, 340

groups = df.groupby(ENDPOINT, sort=False)[RESPONSE_TIME]
# Tukey's depth rule: floor(log2 n) - 3 boxes leave 4 to 8 observations beyond the deepest box on each side
depth = (np.floor(np.log2(groups.count())) - 3).clip(lower=1).astype(int)
k_max = int(depth.max())

boxes = pd.DataFrame(
    [
        {
            ENDPOINT: name,
            "Level": level,
            "Lower": values.quantile(0.5 ** (level + 1)),
            "Upper": values.quantile(1 - 0.5 ** (level + 1)),
        }
        for name, values in groups
        for level in range(1, depth[name] + 1)
    ]
)
# Each level is named by its letter value and the share of the data its box holds
level_labels = [
    f"{LEVEL_NAMES.get(level, f'1/{2 ** (level + 1)}')} ({100 * (1 - 0.5**level):.3g}%)"
    for level in range(1, k_max + 1)
]
# Plain, evenly spaced steps of imprint_seq from its green to its blue stop, one per level
seq_rgb = np.array([[int(stop[i : i + 2], 16) for i in (1, 3, 5)] for stop in IMPRINT_SEQ])
steps = np.rint(seq_rgb[0] + np.linspace(0, 1, k_max)[:, None] * (seq_rgb[1] - seq_rgb[0])).astype(int)
level_colors = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in steps]
boxes["Letter value"] = [level_labels[level - 1] for level in boxes["Level"]]
# Widths shrink linearly with depth; the widest box takes 72 % of a category's slot
widest = 0.72 * VIEW_W / df[ENDPOINT].nunique()
boxes["Width"] = widest * (k_max + 1 - boxes["Level"]) / k_max
boxes = boxes.sort_values("Level", ascending=False)  # deepest (tallest, narrowest) drawn first, quartiles on top

deepest = boxes.groupby(ENDPOINT, sort=False).agg(Lower=("Lower", "min"), Upper=("Upper", "max"))
outliers = df[
    (df[RESPONSE_TIME] < df[ENDPOINT].map(deepest["Lower"])) | (df[RESPONSE_TIME] > df[ENDPOINT].map(deepest["Upper"]))
]
medians = groups.median().rename("Median").reset_index()

# Log value axis: response times are right-skewed, and a linear axis squeezes every box under the slowest outlier
low, high = df[RESPONSE_TIME].min() * 0.8, df[RESPONSE_TIME].max() * 1.25
decades = range(int(np.floor(np.log10(low))), int(np.ceil(np.log10(high))) + 1)
y_ticks = [m * 10.0**e for e in decades for m in (1, 2, 5) if low <= m * 10.0**e <= high]
y_scale = alt.Scale(type="log", domain=[low, high], nice=False)
x = alt.X(ENDPOINT.translate(ESCAPE), type="nominal", title=ENDPOINT, sort=df[ENDPOINT].dropna().unique().tolist())

letter_boxes = (
    alt.Chart(boxes)
    .mark_bar(stroke=PAGE_BG, strokeWidth=0.6)
    .encode(
        x=x,
        y=alt.Y(
            "Lower",
            type="quantitative",
            title=f"{RESPONSE_TIME}, log scale",
            scale=y_scale,
            axis=alt.Axis(values=y_ticks, format=",~g"),
        ),
        y2="Upper",
        size=alt.Size("Width", type="quantitative", scale=None),
        color=alt.Color(
            "Letter value",
            type="ordinal",
            title=["Letter value", "(share inside)"],
            scale=alt.Scale(domain=level_labels, range=level_colors),
        ),
        order=alt.Order("Level", sort="descending"),
        tooltip=[
            alt.Tooltip(ENDPOINT.translate(ESCAPE), title=ENDPOINT),
            alt.Tooltip("Letter value", title="Letter value"),
            alt.Tooltip("Lower", title="Lower (ms)", format=".1f"),
            alt.Tooltip("Upper", title="Upper (ms)", format=".1f"),
        ],
    )
)

median_ticks = (
    alt.Chart(medians)
    .mark_tick(color=INK, thickness=2.5, size=widest + 6)
    .encode(
        x=x,
        y=alt.Y("Median", type="quantitative", scale=y_scale),
        tooltip=[alt.Tooltip(ENDPOINT.translate(ESCAPE), title=ENDPOINT), alt.Tooltip("Median", format=".1f")],
    )
)

outlier_points = (
    alt.Chart(outliers)
    .mark_point(shape="circle", filled=False, size=30, strokeWidth=1.2, color=INK_SOFT, opacity=0.85)
    .encode(
        x=x,
        y=alt.Y(RESPONSE_TIME.translate(ESCAPE), type="quantitative", scale=y_scale),
        tooltip=[
            alt.Tooltip(ENDPOINT.translate(ESCAPE), title=ENDPOINT),
            alt.Tooltip(RESPONSE_TIME.translate(ESCAPE), title=RESPONSE_TIME, format=".1f"),
        ],
    )
)

chart = (
    alt.layer(letter_boxes, median_ticks, outlier_points)
    .properties(
        width=VIEW_W,
        height=VIEW_H,
        background=PAGE_BG,
        padding={"left": 12, "right": 12, "top": 10, "bottom": 10},
        title=alt.Title("boxen-basic · python · altair · anyplot.ai", fontSize=16, color=INK, offset=12),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
        titleFontWeight="normal",
        gridColor=INK,
        gridOpacity=0.15,
    )
    .configure_axisX(labelAngle=0, grid=False, ticks=False, labelPadding=8, titlePadding=10)
    .configure_axisY(titlePadding=10)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=RULE,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
        symbolType="square",
        symbolSize=140,
        symbolStrokeWidth=0,
        padding=10,
        offset=16,
    )
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
