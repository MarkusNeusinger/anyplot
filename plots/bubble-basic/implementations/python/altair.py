"""anyplot.ai
bubble-basic: Basic Bubble Chart
Library: altair 6.3.0 | Python 3.13.15
Quality: 96/100 | Created: 2026-09-27
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

# Imprint palette (canonical order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
stage_colors = IMPRINT_PALETTE[:4]

# Data — tech startup metrics: funding vs revenue, sized by segment share, colored by stage
np.random.seed(42)
n = 49

stages = np.random.choice(["Seed", "Series A", "Series B", "Growth"], size=n, p=[0.25, 0.30, 0.25, 0.20])

stage_funding = {"Seed": (6, 3.5), "Series A": (15, 5.5), "Series B": (40, 9), "Growth": (60, 12)}
funding_m = np.array([np.random.normal(*stage_funding[s]) for s in stages])
funding_m = np.clip(funding_m, 1, 80)

revenue_m = funding_m * np.random.uniform(0.6, 1.6, size=n) + np.random.normal(5, 3.5, size=n)
revenue_m = np.clip(revenue_m, 2, 118)

# Segment share (%) of each company's own addressable segment, not a single global
# market — so per-stage totals need not sum to 100%. Drawn independently of Stage
# (a single wide distribution) so bubble size carries genuinely new information
# rather than tracking the color-encoded cohort.
market_share = np.clip(np.random.normal(30, 13, size=n), 8, 62)

df = pd.DataFrame(
    {
        "Funding ($M)": np.round(funding_m, 1),
        "Revenue ($M)": np.round(revenue_m, 1),
        "Segment Share (%)": np.round(market_share, 1),
        "Stage": pd.Categorical(stages, categories=["Seed", "Series A", "Series B", "Growth"], ordered=True),
    }
)

# Add two counter-examples so funding and revenue don't form a single
# near-linear cloud: a high-funded, low-revenue laggard, and a
# capital-efficient, low-funded high-revenue climber.
outlier_laggard = pd.DataFrame(
    {
        "Funding ($M)": [68.5],
        "Revenue ($M)": [7.2],
        "Segment Share (%)": [22.0],
        "Stage": pd.Categorical(["Series B"], categories=["Seed", "Series A", "Series B", "Growth"], ordered=True),
    }
)
outlier_climber = pd.DataFrame(
    {
        "Funding ($M)": [11.0],
        "Revenue ($M)": [54.0],
        "Segment Share (%)": [31.0],
        "Stage": pd.Categorical(["Series A"], categories=["Seed", "Series A", "Series B", "Growth"], ordered=True),
    }
)
df = pd.concat([df, outlier_laggard, outlier_climber], ignore_index=True)

title = "bubble-basic · python · altair · anyplot.ai"

# Legend-bound point selection — clicking a Stage in the legend spotlights that
# cohort by dimming the rest, an interactive capability distinctive to Altair's
# Vega-Lite selection grammar (preserved in the saved interactive HTML). The
# default "select all" state renders every bubble at the same 0.5 opacity, so
# the static PNG shows no highlight — only the saved HTML is interactive.
stage_selection = alt.selection_point(fields=["Stage"], bind="legend")

# Plot — bubble layer
bubbles = (
    alt.Chart(df)
    .mark_circle(stroke=PAGE_BG, strokeWidth=2)
    .encode(
        order=alt.Order(
            "Segment Share (%):Q", sort="descending"
        ),  # largest bubbles drawn first (behind), smallest on top so overlapping clusters stay legible
        x=alt.X(
            "Funding ($M):Q", scale=alt.Scale(domain=[0, 85], nice=False), axis=alt.Axis(domain=False, ticks=False)
        ),
        y=alt.Y(
            "Revenue ($M):Q", scale=alt.Scale(domain=[0, 125], nice=False), axis=alt.Axis(domain=False, ticks=False)
        ),
        size=alt.Size(
            "Segment Share (%):Q",
            scale=alt.Scale(range=[50, 1500], domain=[8, 62]),
            legend=alt.Legend(
                title="Segment Share (%)",
                titleFontSize=11,
                labelFontSize=12,
                values=[10, 25, 40, 55],
                symbolFillColor=INK_SOFT,  # neutral fill (not a categorical hue) - the size legend applies to every Stage, not just Seed
                symbolStrokeColor=PAGE_BG,
                symbolOpacity=0.65,
                direction="vertical",
            ),
        ),
        color=alt.Color(
            "Stage:N",
            scale=alt.Scale(domain=["Seed", "Series A", "Series B", "Growth"], range=stage_colors),
            legend=alt.Legend(
                title="Stage",
                titleFontSize=11,
                labelFontSize=12,
                symbolType="circle",
                symbolSize=200,
                symbolStrokeWidth=0,
                symbolOpacity=0.65,
            ),
        ),
        opacity=alt.condition(stage_selection, alt.value(0.5), alt.value(0.1)),
        tooltip=["Stage:N", "Funding ($M):Q", "Revenue ($M):Q", "Segment Share (%):Q"],
    )
    .add_params(stage_selection)
)

chart = (
    bubbles.properties(
        width=620,
        height=320,
        background=PAGE_BG,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        title=alt.Title(
            title,
            fontSize=16,
            fontWeight="bold",
            color=INK,
            anchor="middle",
            subtitle="Tech Startup Metrics — Funding vs Revenue by Stage & Segment Share",
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
            subtitlePadding=4,
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0, continuousWidth=620, continuousHeight=320)
    .configure_axis(
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=12,
        titleFontSize=12,
    )
    .configure_legend(
        fillColor=ELEVATED_BG, strokeWidth=0, labelColor=INK_SOFT, titleColor=INK, orient="right", padding=10
    )
)

# Save PNG
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# PAD to exact 3200×1800 (do not crop — cropping clips title/axis labels)
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

# Save HTML
chart.save(f"plot-{THEME}.html")
