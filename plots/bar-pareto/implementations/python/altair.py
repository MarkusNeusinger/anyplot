"""anyplot.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: altair 6.0.0 | Python 3.14.3
Quality: 92/100 | Updated: 2026-06-20
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

VITAL_COLOR = "#009E73"  # Imprint position 1 — vital few bars
LINE_COLOR = "#BD8233"  # Imprint position 4 — cumulative % line

# Data — manufacturing defect analysis
defects = pd.DataFrame(
    {
        "category": [
            "Scratches",
            "Dents",
            "Misalignment",
            "Cracks",
            "Discoloration",
            "Burrs",
            "Warping",
            "Contamination",
            "Missing Parts",
            "Wrong Dimensions",
        ],
        "count": [187, 128, 95, 72, 54, 38, 27, 19, 12, 8],
    }
)

defects = defects.sort_values("count", ascending=False).reset_index(drop=True)
total = defects["count"].sum()
defects["cumulative_pct"] = defects["count"].cumsum() / total * 100
defects["vital_few"] = defects["cumulative_pct"].shift(1, fill_value=0) < 80
sort_order = defects["category"].tolist()

threshold_df = pd.DataFrame({"pct": [80]})

# Title with length-scaled fontsize (floor 11, default 16 at 67 chars)
title_text = "Manufacturing Defect Analysis · bar-pareto · python · altair · anyplot.ai"
n = len(title_text)
title_fs = max(11, round(16 * 67 / n)) if n > 67 else 16

# Bars: vital few → Imprint green, trivial many → theme-adaptive muted
bars = (
    alt.Chart(defects)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X(
            "category:N",
            title="Defect Type",
            sort=sort_order,
            axis=alt.Axis(labelAngle=-45, labelFontSize=10, titleFontSize=12),
        ),
        y=alt.Y("count:Q", title="Frequency", axis=alt.Axis(labelFontSize=10, titleFontSize=12)),
        color=alt.condition(alt.datum.vital_few, alt.value(VITAL_COLOR), alt.value(INK_MUTED)),
        tooltip=[
            alt.Tooltip("category:N", title="Defect"),
            alt.Tooltip("count:Q", title="Count"),
            alt.Tooltip("cumulative_pct:Q", title="Cumulative %", format=".1f"),
        ],
    )
)

# Cumulative % line on secondary y-axis (Imprint ochre)
line = (
    alt.Chart(defects)
    .mark_line(
        color=LINE_COLOR,
        strokeWidth=3,
        point=alt.OverlayMarkDef(color=LINE_COLOR, size=80, filled=True, stroke=PAGE_BG, strokeWidth=1.5),
    )
    .encode(
        x=alt.X("category:N", sort=sort_order),
        y=alt.Y(
            "cumulative_pct:Q",
            title="Cumulative Percentage (%)",
            scale=alt.Scale(domain=[0, 105]),
            axis=alt.Axis(
                labelFontSize=10, titleFontSize=12, titleColor=LINE_COLOR, labelColor=LINE_COLOR, format=".0f"
            ),
        ),
        tooltip=[
            alt.Tooltip("category:N", title="Defect"),
            alt.Tooltip("cumulative_pct:Q", title="Cumulative %", format=".1f"),
        ],
    )
)

# 80% reference line
rule = (
    alt.Chart(threshold_df)
    .mark_rule(strokeDash=[8, 6], strokeWidth=1.5, color=INK_MUTED)
    .encode(y=alt.Y("pct:Q", scale=alt.Scale(domain=[0, 105])))
)

# 80% label
rule_label = (
    alt.Chart(pd.DataFrame({"pct": [80], "label": ["80%"]}))
    .mark_text(align="left", dx=5, dy=-8, fontSize=10, fontWeight="bold", color=INK_MUTED)
    .encode(x=alt.value(10), y=alt.Y("pct:Q", scale=alt.Scale(domain=[0, 105])), text="label:N")
)

# Compose: bars + cumulative line + reference line, independent y-scales
chart = (
    alt.layer(bars, line + rule + rule_label)
    .resolve_scale(y="independent")
    .properties(
        width=620,
        height=308,
        background=PAGE_BG,
        title=alt.Title(
            text=title_text,
            subtitle="Vital few categories (green) account for 80% of all defect occurrences",
            fontSize=title_fs,
            subtitleFontSize=10,
            subtitleColor=INK_SOFT,
            color=INK,
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(domainColor=INK_SOFT, tickColor=INK_SOFT, grid=False, labelColor=INK_SOFT, titleColor=INK)
    .configure_axisY(grid=True, gridDash=[4, 4], gridColor=INK, gridOpacity=0.15)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save and pad to exact 3200 × 1800
TW, TH = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

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
