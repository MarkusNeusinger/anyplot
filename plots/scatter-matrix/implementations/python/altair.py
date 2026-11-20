"""anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os
import sys


# Handle module shadowing by removing current directory from path
sys.path = [p for p in sys.path if os.path.abspath(p) != os.getcwd()]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SEPAL_LENGTH = "Sepal length (cm)"  # role: variables
SEPAL_WIDTH = "Sepal width (cm)"  # role: extra
PETAL_LENGTH = "Petal length (cm)"  # role: extra
PETAL_WIDTH = "Petal width (cm)"  # role: extra
VARIABLES = [SEPAL_LENGTH, SEPAL_WIDTH, PETAL_LENGTH, PETAL_WIDTH]
SPECIES = "Species"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("iris.csv")
rng = np.random.default_rng(42)
species_profiles = {
    "Setosa": ([5.0, 3.4, 1.5, 0.25], [0.35, 0.38, 0.17, 0.10]),
    "Versicolor": ([5.9, 2.8, 4.3, 1.3], [0.52, 0.31, 0.47, 0.20]),
    "Virginica": ([6.6, 3.0, 5.5, 2.0], [0.64, 0.32, 0.55, 0.27]),
}
frames = []
for name, (means, sds) in species_profiles.items():
    block = pd.DataFrame(rng.normal(means, sds, size=(50, len(VARIABLES))), columns=VARIABLES)
    block[SPECIES] = name
    frames.append(block)
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
groups = list(dict.fromkeys(df[SPECIES]))
color = alt.Color(
    SPECIES.translate(ESCAPE),
    type="nominal",
    title=SPECIES,
    sort=None,
    scale=alt.Scale(domain=groups, range=IMPRINT_PALETTE[: len(groups)]),
)

CELL = 92
EXTENT = 44
axis = alt.Axis(labelFontSize=11, titleFontSize=13, tickCount=3, titlePadding=6)
y_shown = alt.Axis(labelFontSize=11, titleFontSize=13, tickCount=3, titlePadding=6, minExtent=EXTENT)
y_hidden = alt.Axis(labels=False, ticks=False, title=None)
x_hidden = alt.Axis(labels=False, ticks=False, title=None)
n_vars = len(VARIABLES)


def wrap(name):
    """Split 'Sepal length (cm)' into two title lines so axis titles stay within one cell."""
    head, sep, unit = name.partition(" (")
    return [head, sep.strip() + unit] if sep else name


rows = []
for r, row_var in enumerate(VARIABLES):
    cells = []
    for c, col_var in enumerate(VARIABLES):
        x_axis = axis if r == n_vars - 1 else x_hidden
        x_enc = {"type": "quantitative", "title": wrap(col_var), "axis": x_axis, "scale": alt.Scale(zero=False)}
        if r == c:
            cell = (
                alt.Chart(df)
                .mark_bar(opacity=0.8)
                .encode(
                    x=alt.X(col_var.translate(ESCAPE), bin=alt.Bin(maxbins=15), **x_enc),
                    y=alt.Y(
                        "count()",
                        type="quantitative",
                        title=None,
                        axis=alt.Axis(
                            labels=False,
                            ticks=False,
                            grid=False,
                            titleFontSize=13,
                            titlePadding=6,
                            title=wrap(row_var) if c == 0 else None,
                            minExtent=EXTENT if c == 0 else 0,
                        ),
                    ),
                    color=color,
                )
            )
        else:
            y_axis = y_shown if c == 0 else y_hidden
            cell = (
                alt.Chart(df)
                .mark_circle(size=22, opacity=0.6)
                .encode(
                    x=alt.X(col_var.translate(ESCAPE), **x_enc),
                    y=alt.Y(
                        row_var.translate(ESCAPE),
                        type="quantitative",
                        title=wrap(row_var),
                        axis=y_axis,
                        scale=alt.Scale(zero=False),
                    ),
                    color=color,
                    tooltip=[
                        alt.Tooltip(SPECIES.translate(ESCAPE), title=SPECIES),
                        alt.Tooltip(col_var.translate(ESCAPE), title=col_var, format=".2f"),
                        alt.Tooltip(row_var.translate(ESCAPE), title=row_var, format=".2f"),
                    ],
                )
            )
        cells.append(cell.properties(width=CELL, height=CELL))
    rows.append(alt.hconcat(*cells, spacing=8))

grid = alt.vconcat(*rows, spacing=8)

chart = (
    grid.properties(
        title=alt.Title("scatter-matrix · python · altair · anyplot.ai", fontSize=22, anchor="middle", offset=12),
        background=PAGE_BG,
        padding={"left": 10, "right": 10, "top": 10, "bottom": 10},
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelOverlap=True,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0.5)
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=16,
        labelFontSize=14,
        symbolSize=200,
        orient="top",
        direction="horizontal",
        padding=8,
    )
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical square canvas
TARGET = (2400, 2400)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET[0] or img.height > TARGET[1]:
    # Longer column names or more groups widen the chart: scale it down to fit, never crop
    fit = min(TARGET[0] / img.width, TARGET[1] / img.height)
    img = img.resize((int(img.width * fit), int(img.height * fit)), Image.LANCZOS)
if img.size != TARGET:
    canvas = Image.new("RGB", TARGET, PAGE_BG)
    canvas.paste(img, ((TARGET[0] - img.width) // 2, (TARGET[1] - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
