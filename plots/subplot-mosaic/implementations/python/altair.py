"""anyplot.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: altair 6.1.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-14
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LAYOUT = ["AAB", "CDD", "EDD"]  # the mosaic: repeated letters span cells
PANELS = {  # per panel: title and axis titles (the data columns carry only x, y, z)
    "A": {"title": "Daily revenue trend", "xlabel": "Day of quarter", "ylabel": "Revenue ($K)"},
    "B": {"title": "Target reached"},
    "C": {"title": "Sales by region", "xlabel": "Region", "ylabel": "Sales ($K)"},
    "D": {
        "title": "Machine efficiency vs output",
        "xlabel": "Efficiency (%)",
        "ylabel": "Output (units/day)",
        "zlabel": "Quality index",
    },
    "E": {"title": "Traffic by hour", "xlabel": "Hour of day", "ylabel": "Visitors"},
}
GAUGE_MAX = 100  # the gauge is a share of this value
CELL_W, CELL_H, GAP = 188, 168, 14  # outer size of one grid cell and the gap between panels, in view pixels
CHROME_W, CHROME_H = 46, 58  # left axis and bottom axis plus panel title around a view
TARGET = 2400  # square canvas, in pixels

# Columns: set these to your table's column names
PANEL = "Panel"  # role: extra
LABEL = "Label"  # role: extra
X = "x"  # role: x
Y = "y"  # role: y
Z = "z"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("panels.csv")
rng = np.random.default_rng(42)
regions = ["North", "South", "East", "West", "Central"]
traffic = [10, 8, 5, 4, 6, 15, 35, 55, 48, 42, 38, 45, 50, 48, 52, 60, 65, 55, 40, 30, 25, 20, 15, 12]
efficiency = rng.uniform(60, 95, 80)
df = pd.concat(
    [
        pd.DataFrame({PANEL: "A", LABEL: "", X: np.arange(1, 91), Y: np.cumsum(rng.normal(0.4, 2.0, 90)) + 50}),
        pd.DataFrame({PANEL: "B", LABEL: "Score", X: [0], Y: [78]}),
        pd.DataFrame({PANEL: "C", LABEL: regions, X: np.arange(len(regions)), Y: [45, 38, 52, 29, 41]}),
        pd.DataFrame(
            {
                PANEL: "D",
                LABEL: "",
                X: efficiency,
                Y: efficiency * 5.5 + rng.normal(0, 35, 80),
                Z: rng.uniform(0, 1, 80),
            }
        ),
        pd.DataFrame({PANEL: "E", LABEL: "", X: np.arange(len(traffic)), Y: traffic}),
    ],
    ignore_index=True,
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
fx, fy, fz, flabel = (c.translate(ESCAPE) for c in (X, Y, Z, LABEL))


def span(panel):
    """Grid cells a panel covers: (columns, rows), read from the layout string."""
    return max(row.count(panel) for row in LAYOUT), sum(panel in row for row in LAYOUT)


def view_size(panel, chrome_w=CHROME_W, chrome_h=CHROME_H):
    """View size so the panel's outer size is exactly its cells plus the gaps it spans."""
    cols, rows = span(panel)
    return cols * CELL_W + (cols - 1) * GAP - chrome_w, rows * CELL_H + (rows - 1) * GAP - chrome_h


def axes(panel, grid=True, **extra):
    """Axis config shared by every panel."""
    return {"labelFontSize": 9, "titleFontSize": 10, "grid": grid, "titlePadding": 4, **extra}


def base(panel, **kw):
    """A panel chart on its rows of df, titled and sized from the layout."""
    w, h = view_size(panel, **kw)
    return alt.Chart(df[df[PANEL] == panel]), {
        "width": w,
        "height": h,
        "title": alt.Title(PANELS[panel]["title"], fontSize=11, anchor="start", offset=4),
    }


def titles(panel):
    return PANELS[panel]["xlabel"], PANELS[panel]["ylabel"]


# A: wide time series
chart, props = base("A")
xt, yt = titles("A")
chart_a = (
    chart.mark_line(strokeWidth=2, color=IMPRINT_PALETTE[0])
    .encode(
        x=alt.X(fx, type="quantitative", title=xt, axis=alt.Axis(**axes("A", grid=False))),
        y=alt.Y(fy, type="quantitative", title=yt, scale=alt.Scale(zero=False), axis=alt.Axis(**axes("A"))),
    )
    .properties(**props)
)

# B: gauge as a progress ring, the value read from df
chart, props = base("B", chrome_w=0, chrome_h=22)
share = f"datum[{Y!r}] / {GAUGE_MAX} * 2 * PI"
ring = {"innerRadius": 38, "outerRadius": 54}
chart_b = alt.layer(
    chart.mark_arc(theta=0, theta2=2 * np.pi, color=INK_SOFT, opacity=0.25, **ring),
    chart.mark_arc(theta=0, theta2=alt.expr(share), color=IMPRINT_PALETTE[0], **ring),
    chart.mark_text(fontSize=24, fontWeight="bold", color=INK).encode(text=alt.Text(fy, type="quantitative")),
).properties(**props)

# C: bars by region
chart, props = base("C")
xt, yt = titles("C")
chart_c = (
    chart.mark_bar(color=IMPRINT_PALETTE[1], cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        x=alt.X(
            flabel,
            type="nominal",
            title=xt,
            sort=None,
            axis=alt.Axis(**axes("C", grid=False, labelAngle=0, labelFontSize=8)),
        ),
        y=alt.Y(fy, type="quantitative", title=yt, axis=alt.Axis(**axes("C"))),
        tooltip=[alt.Tooltip(flabel, title=xt), alt.Tooltip(fy, title=yt)],
    )
    .properties(**props)
)

# D: scatter, the primary panel spanning two rows and two columns
chart, props = base("D")
xt, yt = titles("D")
imprint_seq = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]
chart_d = (
    chart.mark_circle(size=70, opacity=0.8, stroke=PAGE_BG, strokeWidth=0.6)
    .encode(
        x=alt.X(fx, type="quantitative", title=xt, scale=alt.Scale(zero=False), axis=alt.Axis(**axes("D"))),
        y=alt.Y(fy, type="quantitative", title=yt, scale=alt.Scale(zero=False), axis=alt.Axis(**axes("D"))),
        color=alt.Color(
            fz,
            type="quantitative",
            title=PANELS["D"]["zlabel"],
            scale=alt.Scale(range=imprint_seq),
            legend=alt.Legend(
                orient="none",
                legendX=props["width"]
                - 170
                + CELL_W
                + GAP
                + 10,  # legend coordinates start at the first cell of the row below
                legendY=props["height"] - 62 + CELL_H + GAP + 2,
                direction="horizontal",
                padding=6,
                gradientLength=140,
                gradientThickness=8,
                titleFontSize=10,
                labelFontSize=9,
            ),
        ),
        tooltip=[alt.Tooltip(fx, title=xt), alt.Tooltip(fy, title=yt), alt.Tooltip(fz, title=PANELS["D"]["zlabel"])],
    )
    .properties(**props)
)

# E: area chart of traffic by hour
chart, props = base("E")
xt, yt = titles("E")
chart_e = (
    chart.mark_area(color=IMPRINT_PALETTE[2], opacity=0.6, line={"color": IMPRINT_PALETTE[2], "strokeWidth": 2})
    .encode(
        x=alt.X(fx, type="quantitative", title=xt, axis=alt.Axis(**axes("E", grid=False))),
        y=alt.Y(fy, type="quantitative", title=yt, axis=alt.Axis(**axes("E"))),
        tooltip=[alt.Tooltip(fx, title=xt), alt.Tooltip(fy, title=yt)],
    )
    .properties(**props)
)

# Mosaic "AAB / CDD / EDD": A spans two columns, D spans two rows and two columns
mosaic = (
    alt.vconcat(
        alt.hconcat(chart_a, chart_b, spacing=GAP),
        alt.hconcat(alt.vconcat(chart_c, chart_e, spacing=GAP), chart_d, spacing=GAP),
        spacing=GAP,
    )
    .properties(
        title=alt.Title("subplot-mosaic · python · altair · anyplot.ai", fontSize=14, anchor="middle", offset=10),
        background=PAGE_BG,
        padding={"left": 8, "right": 8, "top": 6, "bottom": 6},
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.1, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save: pad (never crop) to the square target
mosaic.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    fit = min(TARGET / img.width, TARGET / img.height)
    img = img.resize(
        (int(img.width * fit), int(img.height * fit)), Image.LANCZOS
    )  # other data can widen the axes: scale down, never crop
canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
mosaic.save(f"plot-{THEME}.html")
