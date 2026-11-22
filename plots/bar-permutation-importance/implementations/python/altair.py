"""anyplot.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
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

# Imprint palette: sequential ramp built from positions 1 and 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE_MEAN = "Mean decrease in model score"  # role: importance_mean
IMPORTANCE_STD = "Std across shuffles"  # role: importance_std

# Data: replace this block with your own table, for example df = pd.read_csv("importance.csv")
df = pd.DataFrame(
    {
        FEATURE: [
            "Location Score",
            "Square Footage",
            "Number of Bedrooms",
            "Year Built",
            "Lot Size",
            "Garage Capacity",
            "Bathroom Count",
            "Distance to Transit",
            "School Rating",
            "Crime Index",
            "Property Tax Rate",
            "HOA Fees",
            "Energy Rating",
            "Basement Area",
            "Pool Presence",
        ],
        IMPORTANCE_MEAN: [
            0.142,
            0.128,
            0.089,
            0.072,
            0.058,
            0.045,
            0.038,
            0.032,
            0.028,
            0.022,
            0.015,
            0.008,
            0.005,
            -0.002,
            -0.008,
        ],
        IMPORTANCE_STD: [
            0.018,
            0.015,
            0.012,
            0.010,
            0.009,
            0.008,
            0.007,
            0.006,
            0.006,
            0.005,
            0.004,
            0.003,
            0.003,
            0.002,
            0.003,
        ],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
feature, mean, std = FEATURE.translate(ESCAPE), IMPORTANCE_MEAN.translate(ESCAPE), IMPORTANCE_STD.translate(ESCAPE)

plot_df = df.assign(
    error_min=df[IMPORTANCE_MEAN] - df[IMPORTANCE_STD], error_max=df[IMPORTANCE_MEAN] + df[IMPORTANCE_STD]
)
y_sort = alt.EncodingSortField(field=mean, order="descending")

bars = (
    alt.Chart(plot_df)
    .mark_bar(size=13)
    .encode(
        x=alt.X(mean, type="quantitative", title=IMPORTANCE_MEAN, axis=alt.Axis(labelFontSize=11, titleFontSize=13)),
        y=alt.Y(feature, type="nominal", sort=y_sort, title=FEATURE, axis=alt.Axis(labelFontSize=11, titleFontSize=13)),
        color=alt.Color(mean, type="quantitative", legend=None, scale=alt.Scale(range=IMPRINT_SEQ)),
        tooltip=[
            alt.Tooltip(feature, type="nominal", title=FEATURE),
            alt.Tooltip(mean, type="quantitative", title=IMPORTANCE_MEAN, format=".4f"),
            alt.Tooltip(std, type="quantitative", title=IMPORTANCE_STD, format=".4f"),
        ],
    )
)

error_bars = (
    alt.Chart(plot_df)
    .mark_errorbar(color=INK, thickness=1.6, ticks=True)
    .encode(
        x=alt.X("error_min", type="quantitative", title=IMPORTANCE_MEAN),
        x2="error_max",
        y=alt.Y(feature, type="nominal", sort=y_sort),
    )
)

zero_line = (
    alt.Chart(pd.DataFrame({"zero": [0]})).mark_rule(color=INK, strokeWidth=1.5, strokeDash=[5, 4]).encode(x="zero:Q")
)

chart = (
    alt.layer(zero_line, bars, error_bars)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            "bar-permutation-importance · python · altair · anyplot.ai", fontSize=16, anchor="middle", offset=12
        ),
    )
    .interactive()
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.12, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
)

# Output: PNG padded (never cropped) to the 3200 x 1800 target, plus HTML
TARGET_W, TARGET_H = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"vl-convert produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}; shrink the view")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
