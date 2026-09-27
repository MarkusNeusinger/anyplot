""" anyplot.ai
bubble-basic: Basic Bubble Chart
Library: altair 6.3.0 | Python 3.13.15
Quality: 89/100 | Created: 2026-09-27
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

# Data — tech startup metrics: funding vs revenue, sized by market share, colored by stage
np.random.seed(42)
n = 49

stages = np.random.choice(["Seed", "Series A", "Series B", "Growth"], size=n, p=[0.25, 0.30, 0.25, 0.20])

stage_funding = {"Seed": (6, 3.5), "Series A": (15, 5.5), "Series B": (40, 9), "Growth": (60, 12)}
funding_m = np.array([np.random.normal(*stage_funding[s]) for s in stages])
funding_m = np.clip(funding_m, 1, 80)

revenue_m = funding_m * np.random.uniform(0.6, 1.6, size=n) + np.random.normal(5, 3.5, size=n)
revenue_m = np.clip(revenue_m, 2, 118)

# Market share (%) narrowed to a realistic 10-58 band — a single company holding
# ~95% would imply a near-monopoly, implausible across four competing stage cohorts
stage_share = {"Seed": (14, 4), "Series A": (24, 5), "Series B": (36, 6), "Growth": (48, 7)}
market_share = np.array([np.clip(np.random.normal(*stage_share[s]), 10, 58) for s in stages])

df = pd.DataFrame(
    {
        "Funding ($M)": np.round(funding_m, 1),
        "Revenue ($M)": np.round(revenue_m, 1),
        "Market Share (%)": np.round(market_share, 1),
        "Stage": pd.Categorical(stages, categories=["Seed", "Series A", "Series B", "Growth"], ordered=True),
    }
)

# Add two counter-examples to break the near-linear funding->revenue trend:
# a high-funded, low-revenue laggard, and a capital-efficient, low-funded high-revenue climber.
outlier_laggard = pd.DataFrame(
    {
        "Funding ($M)": [68.5],
        "Revenue ($M)": [7.2],
        "Market Share (%)": [22.0],
        "Stage": pd.Categorical(["Series B"], categories=["Seed", "Series A", "Series B", "Growth"], ordered=True),
    }
)
outlier_climber = pd.DataFrame(
    {
        "Funding ($M)": [11.0],
        "Revenue ($M)": [54.0],
        "Market Share (%)": [31.0],
        "Stage": pd.Categorical(["Series A"], categories=["Seed", "Series A", "Series B", "Growth"], ordered=True),
    }
)
df = pd.concat([df, outlier_laggard, outlier_climber], ignore_index=True)

# Flag top-3 companies by revenue for storytelling annotations
top3_idx = df["Revenue ($M)"].nlargest(3).index.tolist()
df["label"] = ""
for i in top3_idx:
    df.loc[i, "label"] = f"{df.loc[i, 'Stage']} · ${df.loc[i, 'Revenue ($M)']}M"

title = "bubble-basic · python · altair · anyplot.ai"

# Legend-bound point selection — clicking a Stage in the legend spotlights that
# cohort by dimming the rest, an interactive capability distinctive to Altair's
# Vega-Lite selection grammar (preserved in the saved interactive HTML).
stage_selection = alt.selection_point(fields=["Stage"], bind="legend")

# Regression trend — Vega-Lite's transform_regression fits the funding->revenue
# trend server-side (no scipy/sklearn call in this script), a distinctive
# declarative capability that sits underneath the bubbles as context.
trend = (
    alt.Chart(df)
    .transform_regression("Funding ($M)", "Revenue ($M)")
    .mark_line(strokeDash=[5, 4], strokeWidth=1.5, opacity=0.55)
    .encode(x="Funding ($M):Q", y="Revenue ($M):Q", color=alt.value(INK_SOFT))
)

# Plot — bubble layer
bubbles = (
    alt.Chart(df)
    .mark_circle(stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        x=alt.X("Funding ($M):Q", scale=alt.Scale(domain=[0, 85], nice=False), axis=alt.Axis(domain=False, tickSize=6)),
        y=alt.Y(
            "Revenue ($M):Q", scale=alt.Scale(domain=[0, 125], nice=False), axis=alt.Axis(domain=False, tickSize=6)
        ),
        size=alt.Size(
            "Market Share (%):Q",
            scale=alt.Scale(range=[50, 1500], domain=[10, 58]),
            legend=alt.Legend(
                title="Market Share (%)",
                titleFontSize=10,
                labelFontSize=10,
                values=[10, 25, 40, 55],
                symbolFillColor=IMPRINT_PALETTE[0],
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
                titleFontSize=10,
                labelFontSize=10,
                symbolType="circle",
                symbolSize=200,
                symbolStrokeWidth=0,
                symbolOpacity=0.65,
            ),
        ),
        opacity=alt.condition(stage_selection, alt.value(0.5), alt.value(0.1)),
        tooltip=["Stage:N", "Funding ($M):Q", "Revenue ($M):Q", "Market Share (%):Q"],
    )
    .add_params(stage_selection)
)

# Top-3 highlight rings — a stroke-only outline sized to match each bubble gives the
# "top performer" story an instant, at-a-glance visual anchor beyond the text labels.
top3_highlight = (
    alt.Chart(df[df["label"] != ""])
    .mark_circle(filled=False, stroke=INK, strokeWidth=2.5, opacity=0.9)
    .encode(
        x="Funding ($M):Q",
        y="Revenue ($M):Q",
        size=alt.Size("Market Share (%):Q", scale=alt.Scale(range=[50, 1500], domain=[10, 58]), legend=None),
    )
)

# Annotation layers — sort by revenue descending and alternate dy/dx to prevent collision
_labeled = df[df["label"] != ""].sort_values("Revenue ($M)", ascending=False).reset_index(drop=True)
_dy_offsets = [-24, 18, -26]
_dx_offsets = [-14, -18, -14]
_annotation_layers = [
    alt.Chart(_labeled.iloc[[k]])
    .mark_text(align="right", dx=_dx_offsets[k], dy=_dy_offsets[k], fontSize=12, fontWeight="bold")
    .encode(x="Funding ($M):Q", y="Revenue ($M):Q", text="label:N", color=alt.value(INK))
    for k in range(len(_labeled))
]
annotations = alt.layer(*_annotation_layers)

chart = (
    (trend + bubbles + top3_highlight + annotations)
    .properties(
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
            subtitle="Tech Startup Metrics — Funding vs Revenue by Stage & Market Share",
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
        labelFontSize=10,
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
