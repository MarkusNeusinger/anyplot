"""anyplot.ai
bar-basic: Basic Bar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # regular bars
HIGHLIGHT = IMPRINT_PALETTE[3]  # ochre accent for the top bar

# Constants
TITLE = "bar-basic · python · altair · anyplot.ai"

# Columns
CATEGORY = "Product Category"  # role: category
SALES = "Sales ($)"  # role: value

# Data: product sales by category, sorted descending
df = pd.DataFrame(
    {
        CATEGORY: ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Food"],
        SALES: [45200, 31500, 29800, 21800, 18500, 14200, 13100],
    }
)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
category_field = CATEGORY.translate(ESCAPE)
sales_field = SALES.translate(ESCAPE)

bars = (
    alt.Chart(df)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X(category_field, type="nominal", title=CATEGORY, sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(
            sales_field,
            type="quantitative",
            title=SALES,
            scale=alt.Scale(domain=[0, df[SALES].max() * 1.1]),
            axis=alt.Axis(format="$,.0f"),
        ),
        color=alt.condition(alt.datum[SALES] == df[SALES].max(), alt.value(HIGHLIGHT), alt.value(BRAND)),
        tooltip=[
            alt.Tooltip(category_field, type="nominal", title=CATEGORY),
            alt.Tooltip(sales_field, type="quantitative", title=SALES, format="$,.0f"),
        ],
    )
)

labels = bars.mark_text(align="center", baseline="bottom", dy=-6, fontSize=11).encode(
    text=alt.Text(sales_field, type="quantitative", format="$,.0f"), color=alt.value(INK_SOFT)
)

chart = (
    (bars + labels)
    .properties(
        width=800,
        height=450,
        padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        background=PAGE_BG,
        title=alt.Title(TITLE, fontSize=16, color=INK),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        grid=False,
    )
    .configure_axisY(grid=True, gridOpacity=0.15, gridDash=[4, 4], gridColor=INK_SOFT)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
