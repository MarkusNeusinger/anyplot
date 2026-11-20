"""anyplot.ai
bar-stacked: Stacked Bar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is ALWAYS #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column names
QUARTER = "Quarter"  # role: category
PRODUCT = "Product Category"  # role: component
SALES = "Sales (Thousands USD)"  # role: value

# Data: quarterly sales by product category, components ordered largest at the bottom
quarters = ["Q1", "Q2", "Q3", "Q4"]
sales_by_product = {
    "Electronics": [85, 92, 78, 110],
    "Clothing": [62, 71, 65, 88],
    "Home & Garden": [45, 52, 48, 68],
    "Sports": [38, 44, 41, 55],
}
df = pd.DataFrame(
    [
        {QUARTER: quarter, PRODUCT: product, SALES: values[i]}
        for product, values in sales_by_product.items()
        for i, quarter in enumerate(quarters)
    ]
)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
quarter_f, product_f, sales_f = QUARTER.translate(ESCAPE), PRODUCT.translate(ESCAPE), SALES.translate(ESCAPE)
product_order = list(dict.fromkeys(df[PRODUCT]))
df["stack_order"] = df[PRODUCT].map({p: i for i, p in enumerate(product_order)})

totals = df.groupby(QUARTER, sort=False)[SALES].sum().reset_index()

bars = (
    alt.Chart(df)
    .mark_bar(stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        x=alt.X(quarter_f, type="ordinal", title=QUARTER, sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(sales_f, type="quantitative", title=SALES, aggregate="sum"),
        color=alt.Color(
            product_f,
            type="nominal",
            title=PRODUCT,
            sort=None,
            scale=alt.Scale(domain=product_order, range=IMPRINT_PALETTE[: len(product_order)]),
            legend=alt.Legend(symbolSize=300, titlePadding=10, labelLimit=150, padding=8),
        ),
        order=alt.Order("stack_order:Q", sort="ascending"),
        tooltip=[
            alt.Tooltip(quarter_f, type="ordinal", title=QUARTER),
            alt.Tooltip(product_f, type="nominal", title=PRODUCT),
            alt.Tooltip(sales_f, type="quantitative", title=SALES),
        ],
    )
)

labels = (
    alt.Chart(totals)
    .mark_text(fontSize=11, fontWeight="bold", dy=-6, color=INK)
    .encode(
        x=alt.X(quarter_f, type="ordinal", sort=None),
        y=alt.Y(sales_f, type="quantitative"),
        text=alt.Text(sales_f, type="quantitative", format=".0f"),
    )
)

chart = (
    (bars + labels)
    .properties(
        width=580,
        height=340,
        background=PAGE_BG,
        title=alt.Title("bar-stacked · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=13,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=12,
    )
)

# Save: PNG scaled down if oversized, then padded (never cropped) to the 3200 x 1800 target, plus interactive HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:  # other data can widen the legend: scale down, never crop
    img.thumbnail((TW, TH), Image.LANCZOS)
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
