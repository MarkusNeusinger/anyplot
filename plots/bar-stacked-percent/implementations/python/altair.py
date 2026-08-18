"""anyplot.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-08
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

# Imprint palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Energy mix by country
data = pd.DataFrame(
    {
        "Country": [
            "USA",
            "USA",
            "USA",
            "USA",
            "China",
            "China",
            "China",
            "China",
            "Germany",
            "Germany",
            "Germany",
            "Germany",
            "Brazil",
            "Brazil",
            "Brazil",
            "Brazil",
            "India",
            "India",
            "India",
            "India",
        ],
        "Source": ["Fossil Fuels", "Nuclear", "Renewables", "Hydro"] * 5,
        "Value": [
            60,
            18,
            15,
            7,  # USA
            65,
            5,
            18,
            12,  # China
            40,
            12,
            38,
            10,  # Germany
            15,
            3,
            12,
            70,  # Brazil
            72,
            3,
            18,
            7,
        ],  # India
    }
)

# Create 100% stacked bar chart
chart = (
    alt.Chart(data)
    .mark_bar(stroke="white", strokeWidth=1)
    .encode(
        x=alt.X("Country:N", axis=alt.Axis(labelFontSize=10, titleFontSize=12, labelAngle=0), title="Country"),
        y=alt.Y(
            "Value:Q",
            stack="normalize",
            axis=alt.Axis(labelFontSize=10, titleFontSize=12, format="%"),
            title="Share of Energy Mix (%)",
        ),
        color=alt.Color(
            "Source:N",
            scale=alt.Scale(domain=["Fossil Fuels", "Nuclear", "Renewables", "Hydro"], range=IMPRINT),
            legend=alt.Legend(
                title="Energy Source",
                titleFontSize=10,
                labelFontSize=10,
                orient="right",
                symbolSize=80,
                symbolStrokeWidth=0,
            ),
        ),
        order=alt.Order("Source:N", sort="descending"),
        tooltip=[
            alt.Tooltip("Country:N", title="Country"),
            alt.Tooltip("Source:N", title="Source"),
            alt.Tooltip("Value:Q", title="Value", format=".1f"),
        ],
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("bar-stacked-percent · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.15, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad the saved PNG up to the canonical landscape canvas (3200x1800).
# vl-convert pads the view with title/axis/legend extents outside width/height,
# so the raw save rarely lands exactly on target - never crop, only pad.
TW, TH = 3200, 1800
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
