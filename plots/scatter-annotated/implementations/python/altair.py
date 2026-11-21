"""anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Canvas: landscape 3200 x 1800
TW, TH = 3200, 1800

# Columns
COMPANY = "Company"  # role: label
REVENUE = "Revenue (Billions USD)"  # role: x
MARGIN = "Profit Margin (%)"  # role: y

# Data
df = pd.DataFrame(
    {
        COMPANY: ["NVIDIA", "Apple", "Microsoft", "Amazon", "Google", "Meta", "Adobe", "Oracle", "Tesla", "Intel"],
        REVENUE: [61, 385, 211, 574, 307, 135, 19, 50, 97, 63],
        MARGIN: [55, 25, 35, 6, 22, 20, 34, 26, 11, 8],
    }
)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
x = alt.X(
    REVENUE.translate(ESCAPE), type="quantitative", title=REVENUE, scale=alt.Scale(domain=[0, df[REVENUE].max() * 1.18])
)
y = alt.Y(
    MARGIN.translate(ESCAPE), type="quantitative", title=MARGIN, scale=alt.Scale(domain=[0, df[MARGIN].max() * 1.1])
)

points = (
    alt.Chart(df)
    .mark_point(size=160, filled=True, opacity=0.7, color=BRAND)
    .encode(
        x=x,
        y=y,
        tooltip=[
            alt.Tooltip(COMPANY.translate(ESCAPE), title=COMPANY),
            alt.Tooltip(REVENUE.translate(ESCAPE), title=REVENUE),
            alt.Tooltip(MARGIN.translate(ESCAPE), title=MARGIN),
        ],
    )
)

labels = (
    alt.Chart(df)
    .mark_text(align="left", dx=9, dy=13, fontSize=11, fontWeight="bold", color=INK)
    .encode(x=x, y=y, text=alt.Text(COMPANY.translate(ESCAPE), type="nominal"))
)

chart = (
    (points + labels)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            text="scatter-annotated · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=10,
        titleColor=INK,
        titleFontSize=12,
    )
)

# Save: PNG padded (never cropped) to the exact target, plus interactive HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds target {TW}x{TH}")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
