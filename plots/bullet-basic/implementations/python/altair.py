"""anyplot.ai
bullet-basic: Basic Bullet Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import os
import sys


# Prevent self-import: this file is named altair.py; remove the script directory
# from sys.path so `import altair` finds the installed package, not this file.
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if not p or os.path.abspath(p) != _this_dir]

import altair as alt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 carries the single measure bar
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BAND_NAMES = ["Poor", "Satisfactory", "Good"]  # qualitative ranges, low to high
# Grayscale bands in a steady light-to-dark progression, adapted to each page
BAND_COLORS = ["#e8e8e8", "#c8c8c8", "#a0a0a0"] if THEME == "light" else ["#2e2e2e", "#3e3e3e", "#545454"]

# Columns: set these to your table's column names
LABEL = "Metric"  # role: label
ACTUAL = "Actual (% of goal)"  # role: actual
TARGET = "Target (% of goal)"  # role: target
POOR_LIMIT = "Poor limit (% of goal)"  # role: ranges
SATISFACTORY_LIMIT = "Satisfactory limit (% of goal)"  # role: extra
GOOD_LIMIT = "Good limit (% of goal)"  # role: extra
ACTUAL_RAW = "Actual value"  # role: extra
START = "Band start"  # role: extra
END = "Band end"  # role: extra
BAND = "Performance band"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("kpis.csv")
# Four KPIs on different scales, each normalised to percent of its top threshold
values = pd.DataFrame(
    {
        LABEL: ["Revenue ($K)", "Profit ($K)", "New Customers", "Satisfaction"],
        ACTUAL: [275, 85, 320, 4.2],
        TARGET: [250, 100, 300, 4.5],
        POOR_LIMIT: [150, 50, 200, 3.0],
        SATISFACTORY_LIMIT: [200, 75, 275, 4.0],
        GOOD_LIMIT: [300, 125, 350, 5.0],
    }
)
df = values.copy()
for col in [ACTUAL, TARGET, POOR_LIMIT, SATISFACTORY_LIMIT, GOOD_LIMIT]:
    df[col] = values[col] / values[GOOD_LIMIT] * 100
df[ACTUAL_RAW] = values[ACTUAL]

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
metric_order = df[LABEL].tolist()
y_scale = alt.Scale(paddingInner=0.22, paddingOuter=0.15)
x_title = "Performance (% of Goal)"
x_scale = alt.Scale(domain=[0, df[GOOD_LIMIT].max() * 1.15])


def y_enc(**kwargs):
    return alt.Y(LABEL.translate(ESCAPE), type="nominal", sort=metric_order, scale=y_scale, **kwargs)


# Band segments: each band runs from the previous threshold to its own
limits = [POOR_LIMIT, SATISFACTORY_LIMIT, GOOD_LIMIT]
edges = [0 * df[POOR_LIMIT], *[df[r] for r in limits]]
df_bands = pd.concat(
    [
        pd.DataFrame({LABEL: df[LABEL], START: edges[i], END: edges[i + 1], BAND: name})
        for i, name in enumerate(BAND_NAMES)
    ],
    ignore_index=True,
)

bands = (
    alt.Chart(df_bands)
    .mark_bar()
    .encode(
        y=y_enc(title=None, axis=alt.Axis(labelFontSize=12, labelFontWeight="bold")),
        x=alt.X(START.translate(ESCAPE), type="quantitative", title=x_title, scale=x_scale),
        x2=alt.X2(END.translate(ESCAPE)),
        color=alt.Color(
            BAND.translate(ESCAPE),
            type="nominal",
            title=BAND,
            sort=BAND_NAMES,
            scale=alt.Scale(domain=BAND_NAMES, range=BAND_COLORS),
            legend=alt.Legend(orient="bottom", direction="horizontal", titleFontSize=10, labelFontSize=10),
        ),
        tooltip=[
            alt.Tooltip(LABEL.translate(ESCAPE), type="nominal", title=LABEL),
            alt.Tooltip(BAND.translate(ESCAPE), type="nominal", title=BAND),
        ],
    )
)

# Measure bar: one color, zero to the actual value
measure = (
    alt.Chart(df)
    .mark_bar(size=26, color=IMPRINT_PALETTE[0])
    .encode(
        y=y_enc(),
        x=alt.X(ACTUAL.translate(ESCAPE), type="quantitative", scale=x_scale),
        tooltip=[
            alt.Tooltip(LABEL.translate(ESCAPE), type="nominal", title=LABEL),
            alt.Tooltip(ACTUAL.translate(ESCAPE), type="quantitative", title=ACTUAL, format=".1f"),
        ],
    )
)

# Target marker: thin tick perpendicular to the bar, in the page's ink color
target = (
    alt.Chart(df)
    .mark_tick(color=INK, thickness=4, size=48)
    .encode(
        y=y_enc(),
        x=alt.X(TARGET.translate(ESCAPE), type="quantitative", scale=x_scale),
        tooltip=[
            alt.Tooltip(LABEL.translate(ESCAPE), type="nominal", title=LABEL),
            alt.Tooltip(TARGET.translate(ESCAPE), type="quantitative", title=TARGET, format=".1f"),
        ],
    )
)

# Actual-value label (original unit) at the end of each bar
labels = (
    alt.Chart(df)
    .mark_text(align="left", dx=8, fontSize=12, fontWeight="bold", color=INK)
    .encode(
        y=y_enc(),
        x=alt.X(ACTUAL.translate(ESCAPE), type="quantitative", scale=x_scale),
        text=alt.Text(ACTUAL_RAW.translate(ESCAPE), type="quantitative"),
    )
)

title_str = "bullet-basic · python · altair · anyplot.ai"
chart = (
    alt.layer(bands, measure, target, labels)
    .properties(
        width=800,
        height=450,
        padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        background=PAGE_BG,
        title=alt.Title(title_str, fontSize=16, color=INK, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        grid=False,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=12,
        labelFontSize=10,
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=None, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
