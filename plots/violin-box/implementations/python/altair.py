"""anyplot.ai
violin-box: Violin Plot with Embedded Box Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
RESPONSE_TIME = "Response time (ms)"  # role: value
SERVER_TIER = "Server tier"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
n_per_group = 80
enterprise_cached = np.random.normal(25, 8, n_per_group // 2)
enterprise_uncached = np.random.normal(55, 12, n_per_group // 2)
df = pd.DataFrame(
    {
        SERVER_TIER: np.repeat(["Basic", "Standard", "Premium", "Enterprise"], n_per_group),
        RESPONSE_TIME: np.concatenate(
            [
                np.random.exponential(120, n_per_group) + 80,  # Basic: higher latency, more variance
                np.random.normal(100, 25, n_per_group),  # Standard: moderate latency
                np.random.normal(60, 15, n_per_group),  # Premium: lower, tighter
                enterprise_cached,  # Enterprise: bimodal (cached / uncached)
                enterprise_uncached,
            ]
        ),
    }
)
df[RESPONSE_TIME] = df[RESPONSE_TIME].clip(lower=5)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
value = RESPONSE_TIME.translate(ESCAPE)
tier = SERVER_TIER.translate(ESCAPE)
groups = list(df[SERVER_TIER].unique())

view_width = 620 // len(groups)  # facets share the 3200 px canvas width

title = "violin-box · python · altair · anyplot.ai"

violin = (
    alt.Chart(df)
    .transform_density(RESPONSE_TIME, as_=[RESPONSE_TIME, "density"], groupby=[SERVER_TIER])
    .mark_area(orient="horizontal", opacity=0.6)
    .encode(
        y=alt.Y(value, type="quantitative", title=RESPONSE_TIME),
        x=alt.X(
            "density:Q",
            stack="center",
            impute=None,
            title=None,
            axis=alt.Axis(labels=False, values=[0], grid=False, ticks=False),
        ),
        color=alt.Color(
            tier, type="nominal", title=SERVER_TIER, sort=None, scale=alt.Scale(domain=groups, range=IMPRINT_PALETTE)
        ),
    )
)

boxplot = (
    alt.Chart(df)
    .mark_boxplot(
        extent="min-max",
        size=14,
        median={"stroke": INK, "strokeWidth": 2},
        rule={"stroke": INK, "strokeWidth": 1.5},
        box={"fill": INK_SOFT, "fillOpacity": 0.3},
        outliers={"size": 60, "strokeWidth": 2, "stroke": INK_SOFT},
    )
    .encode(
        y=alt.Y(value, type="quantitative", title=RESPONSE_TIME), x=alt.value(view_width / 2), color=alt.value(INK_SOFT)
    )
)

chart = (
    alt.layer(violin, boxplot)
    .properties(width=view_width, height=370)
    .facet(
        column=alt.Column(
            tier,
            type="nominal",
            header=alt.Header(titleFontSize=14, labelFontSize=14, labelOrient="bottom", labelColor=INK),
            title=None,
            sort=groups,
        )
    )
    .properties(title=alt.Title(title, fontSize=20, anchor="middle", offset=12, color=INK), background=PAGE_BG)
    .configure_axis(
        labelFontSize=12,
        titleFontSize=14,
        gridOpacity=0.0,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_view(stroke=None, fill=PAGE_BG)
    .configure_legend(disable=True)
    .resolve_scale(x="independent")
)

# Save
TW, TH = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
canvas.save(f"plot-{THEME}.png")
