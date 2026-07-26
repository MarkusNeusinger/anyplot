"""anyplot.ai
waffle-basic: Basic Waffle Chart
Library: altair 6.2.2 | Python 3.13.14
Quality: 83/100 | Updated: 2026-07-26
"""

import os
import sys

import pandas as pd
from PIL import Image


# Fix import conflict: import from parent directory to avoid local module shadowing
original_path = sys.path[:]
sys.path = [p for p in sys.path if not p.endswith("python")]
try:
    import altair as alt
finally:
    sys.path = original_path


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data - Budget allocation with 5 categories including a small one
categories = ["Engineering", "Marketing", "Operations", "Design", "Legal"]
values = [40, 28, 18, 10, 4]  # Percentages (sum to 100)

# Build 10x10 grid (100 squares, each = 1%)
squares = []
square_idx = 0
for cat, val in zip(categories, values, strict=True):
    for _ in range(val):
        row = square_idx // 10
        col = square_idx % 10
        squares.append({"category": cat, "row": row, "col": col})
        square_idx += 1

df = pd.DataFrame(squares)

# Mandated title format, plus a data-driven subtitle for storytelling
title_text = "waffle-basic · python · altair · anyplot.ai"
subtitle_text = f"{categories[0]} commands {values[0]}% of the budget — the single largest allocation"
title_fontsize = max(11, round(16 * min(1.0, 67 / len(title_text))))

# Click a legend entry to isolate its share of the grid (idiomatic altair
# interactivity — dims the rest; only visible in the exported HTML, the
# static PNG keeps the default "nothing selected yet" full-opacity state).
legend_click = alt.selection_point(fields=["category"], bind="legend")

label_map = ", ".join(f"'{cat}': '{val}'" for cat, val in zip(categories, values, strict=True))

chart = (
    alt.Chart(df)
    .mark_rect(stroke=ELEVATED_BG, strokeWidth=3, cornerRadius=5)
    .encode(
        x=alt.X("col:O", axis=None),
        y=alt.Y("row:O", axis=None, sort="descending"),
        color=alt.Color(
            "category:N",
            scale=alt.Scale(domain=categories, range=IMPRINT),
            legend=alt.Legend(
                title="Category",
                titleFontSize=14,
                labelFontSize=12,
                symbolSize=220,
                orient="right",
                labelExpr=f"datum.label + ' (' + {{{label_map}}}[datum.label] + '%)'",
            ),
        ),
        opacity=alt.condition(legend_click, alt.value(1.0), alt.value(0.25)),
        tooltip=[alt.Tooltip("category:N", title="Category")],
    )
    .add_params(legend_click)
    .properties(
        width=430,
        height=430,
        background=PAGE_BG,
        title=alt.Title(
            title_text,
            subtitle=subtitle_text,
            fontSize=title_fontsize,
            subtitleFontSize=round(title_fontsize * 0.55),
            subtitleColor=INK_SOFT,
            anchor="middle",
            color=INK,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# PAD-only to the canonical square target (2400x2400) — never crop, cropping
# would clip the title/subtitle/legend and trigger the AR-09 edge-clip check.
TW, TH = 2400, 2400
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}x{_h}, exceeds target {TW}x{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")
