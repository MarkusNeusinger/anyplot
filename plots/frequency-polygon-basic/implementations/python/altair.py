"""anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os
import site
import sys


# Workaround for script name shadowing the altair package
sys.path = (
    site.getsitepackages()
    + [site.getusersitepackages()]
    + [p for p in sys.path if p not in site.getsitepackages() + [site.getusersitepackages()]]
)

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

# Constants
BINS = 20  # histogram bins shared by every group
DASHES = [[1, 0], [8, 4], [4, 4], [10, 4, 2, 4], [2, 2], [14, 4], [6, 2], [3, 5]]  # one stroke dash per group

# Columns: set these to your table's column names
RESPONSE_TIME = "Response time (ms)"  # role: values
CONDITION = "Condition"  # role: group
FREQUENCY = "Frequency"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
control = np.random.normal(loc=450, scale=80, size=200)
treatment_a = np.random.normal(loc=380, scale=60, size=200)
treatment_b = np.random.normal(loc=420, scale=100, size=200)
df = pd.DataFrame(
    {
        RESPONSE_TIME: np.concatenate([control, treatment_a, treatment_b]),
        CONDITION: ["Control"] * 200 + ["Treatment A"] * 200 + ["Treatment B"] * 200,
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
groups = list(df[CONDITION].unique())

# Bin edges shared by all groups, so every polygon has its vertices at the same x positions
bin_edges = np.histogram_bin_edges(df[RESPONSE_TIME].dropna(), bins=BINS)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# One polygon per group: bin midpoints, extended to zero at both outer edges
polygons = []
for group in groups:
    counts, _ = np.histogram(df.loc[df[CONDITION] == group, RESPONSE_TIME].dropna(), bins=bin_edges)
    polygons.append(
        pd.DataFrame(
            {
                RESPONSE_TIME: np.concatenate([[bin_edges[0]], bin_centers, [bin_edges[-1]]]),
                FREQUENCY: np.concatenate([[0], counts, [0]]),
                CONDITION: group,
            }
        )
    )
poly = pd.concat(polygons, ignore_index=True)

chart = (
    alt.Chart(poly)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X(RESPONSE_TIME.translate(ESCAPE), type="quantitative", title=RESPONSE_TIME),
        y=alt.Y(FREQUENCY.translate(ESCAPE), type="quantitative", title=FREQUENCY, scale=alt.Scale(domainMin=0)),
        color=alt.Color(
            CONDITION.translate(ESCAPE),
            type="nominal",
            title=CONDITION,
            sort=None,
            scale=alt.Scale(domain=groups, range=IMPRINT_PALETTE),
        ),
        strokeDash=alt.StrokeDash(
            CONDITION.translate(ESCAPE),
            type="nominal",
            title=CONDITION,
            sort=None,
            scale=alt.Scale(domain=groups, range=DASHES),
        ),
    )
    .properties(
        width=580,
        height=320,
        background=PAGE_BG,
        title=alt.Title("frequency-polygon-basic · python · altair · anyplot.ai", fontSize=16),
    )
    .configure_title(anchor="middle", color=INK)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridOpacity=0.10,
        gridColor=INK,
    )
    .configure_legend(
        labelFontSize=10,
        titleFontSize=12,
        symbolStrokeWidth=2.5,
        padding=8,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        titleColor=INK,
        labelColor=INK_SOFT,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
)

# Save: PNG at 4x, padded (never cropped) to the 3200 x 1800 target, then HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}")
if w < TW or h < TH:
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
