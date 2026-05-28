""" anyplot.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-27
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
# Use INK_SOFT in dark mode so ring gaps remain visible against dark arc segments
RING_STROKE = PAGE_BG if THEME == "light" else INK_SOFT

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3"]

# Portfolio data
holdings = pd.DataFrame(
    {
        "asset": [
            "Apple Inc.",
            "Microsoft",
            "Amazon",
            "Nvidia",
            "US Treasury 10Y",
            "Corporate Bonds",
            "Municipal Bonds",
            "Gold ETF",
            "Real Estate Fund",
            "Commodities",
        ],
        "weight": [15.0, 12.0, 10.0, 8.0, 18.0, 12.0, 5.0, 8.0, 7.0, 5.0],
        "category": [
            "Equities",
            "Equities",
            "Equities",
            "Equities",
            "Fixed Income",
            "Fixed Income",
            "Fixed Income",
            "Alternatives",
            "Alternatives",
            "Alternatives",
        ],
    }
)

# Category totals for outer ring — is_dominant flags Equities (45%) for visual emphasis
category_totals = (
    holdings.groupby("category").agg(total_weight=("weight", "sum"), num_holdings=("asset", "count")).reset_index()
)
category_totals["is_dominant"] = (category_totals["category"] == "Equities").astype(int)

# Color scale using Imprint palette (green=equities growth, purple=fixed income, blue=alternatives)
category_domain = ["Equities", "Fixed Income", "Alternatives"]
color_scale = alt.Scale(domain=category_domain, range=IMPRINT_PALETTE)

# Category selection drives drill-down of the inner ring
category_sel = alt.selection_point(fields=["category"], empty=True)

# Outer ring: category-level totals — click to drill down
# Equities (dominant at 45%) gets a thicker stroke for subtle visual emphasis
outer_ring = (
    alt.Chart(category_totals)
    .mark_arc(innerRadius=175, outerRadius=248, stroke=RING_STROKE)
    .encode(
        theta=alt.Theta("total_weight:Q", stack=True),
        color=alt.Color(
            "category:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Asset Class",
                titleFontSize=14,
                labelFontSize=12,
                orient="right",
                symbolSize=200,
                titleColor=INK,
                labelColor=INK_SOFT,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
                padding=8,
                cornerRadius=4,
                symbolStrokeWidth=0,
            ),
        ),
        strokeWidth=alt.condition(alt.datum.is_dominant == 1, alt.value(5), alt.value(2)),
        opacity=alt.condition(category_sel, alt.value(1.0), alt.value(0.25)),
        tooltip=[
            alt.Tooltip("category:N", title="Asset Class"),
            alt.Tooltip("total_weight:Q", title="Allocation (%)", format=".1f"),
            alt.Tooltip("num_holdings:Q", title="Holdings"),
        ],
    )
    .add_params(category_sel)
)

# Inner ring: individual holdings filtered by selection (drill-down detail view)
# When no category selected → shows all 10 holdings; click outer ring → shows only that category
inner_ring = (
    alt.Chart(holdings)
    .transform_filter(category_sel)
    .mark_arc(innerRadius=81, outerRadius=170, stroke=RING_STROKE, strokeWidth=2)
    .encode(
        theta=alt.Theta("weight:Q", stack=True),
        color=alt.Color("category:N", scale=color_scale, legend=None),
        opacity=alt.value(0.85),
        tooltip=[
            alt.Tooltip("asset:N", title="Holding"),
            alt.Tooltip("weight:Q", title="Portfolio Weight (%)", format=".1f"),
            alt.Tooltip("category:N", title="Asset Class"),
        ],
    )
)

# Center text — typographic hierarchy: large primary stat + smaller supporting label
center_pct = (
    alt.Chart(pd.DataFrame({"label": ["100%"]}))
    .mark_text(fontSize=28, fontWeight="bold", align="center", baseline="middle", color=INK, dy=-16)
    .encode(text="label:N")
)
center_sub = (
    alt.Chart(pd.DataFrame({"label": ["10 Holdings"]}))
    .mark_text(fontSize=14, fontWeight="normal", align="center", baseline="middle", color=INK_SOFT, dy=14)
    .encode(text="label:N")
)

# Title — canonical format with language token
title_str = "pie-portfolio-interactive · python · altair · anyplot.ai"
subtitle_str = "Click outer ring to drill into category holdings · click again to reset"

chart = (
    alt.layer(outer_ring, inner_ring, center_pct, center_sub)
    .properties(
        width=366,
        height=406,
        background=PAGE_BG,
        title=alt.Title(
            title_str,
            fontSize=16,
            subtitle=subtitle_str,
            subtitleFontSize=12,
            anchor="middle",
            color=INK,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(stroke=None, fill=PAGE_BG)
    .configure_legend(padding=8, cornerRadius=4, symbolStrokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.15, labelColor=INK_SOFT, titleColor=INK
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# PAD to exact 2400×2400 (square target for pie/donut charts)
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
