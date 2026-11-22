"""anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
"""

import os
import sys


# Work around filename shadowing the altair library
sys.path.pop(0)

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per level in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
PASSENGER_CLASS = "Passenger class"  # role: category_1
OUTCOME = "Survival status"  # role: category_2
PASSENGERS = "Passengers"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("titanic_counts.csv")
df = pd.DataFrame(
    {
        PASSENGER_CLASS: ["1st", "1st", "2nd", "2nd", "3rd", "3rd", "Crew", "Crew"],
        OUTCOME: ["Survived", "Did not survive"] * 4,
        PASSENGERS: [203, 122, 118, 167, 178, 528, 212, 673],
    }
)

# Plot: reads only df and the constants above
# Column widths follow the marginal share of the first variable, heights the conditional share of the second
columns = list(dict.fromkeys(df[PASSENGER_CLASS]))
levels = list(dict.fromkeys(df[OUTCOME]))
table = df.pivot_table(index=PASSENGER_CLASS, columns=OUTCOME, values=PASSENGERS, aggfunc="sum", sort=False)
table = table.reindex(index=columns, columns=levels)
col_total = table.sum(axis=1)
width_share = col_total / col_total.sum()
x_end = width_share.cumsum()
x_start = x_end - width_share

tiles = table.melt(ignore_index=False, var_name="level", value_name="count").rename_axis("column").reset_index()
tiles["share"] = tiles["count"] / tiles["column"].map(col_total)
tiles["y_end"] = 1 - tiles.groupby("column", sort=False)["share"].cumsum() + tiles["share"]
tiles["y_start"] = tiles["y_end"] - tiles["share"]
tiles["x_start"] = tiles["column"].map(x_start)
tiles["x_end"] = tiles["column"].map(x_end)
tiles["x_mid"] = (tiles["x_start"] + tiles["x_end"]) / 2
tiles["y_mid"] = (tiles["y_start"] + tiles["y_end"]) / 2
tiles["percent"] = (tiles["count"] / tiles["count"].sum() * 100).round(1)
tiles["label"] = tiles["count"].map(lambda c: f"{c:g}")

column_labels = pd.DataFrame({"column": columns, "x_mid": ((x_start + x_end) / 2).reindex(columns).to_numpy()})

mosaic = (
    alt.Chart(tiles)
    .mark_rect(stroke=PAGE_BG, strokeWidth=2)
    .encode(
        x=alt.X("x_start:Q", axis=alt.Axis(title=PASSENGER_CLASS, labels=False, ticks=False, domain=False)),
        x2="x_end:Q",
        y=alt.Y("y_start:Q", axis=alt.Axis(title="Share within class", format="%", tickCount=5, grid=False)),
        y2="y_end:Q",
        color=alt.Color(
            "level:N",
            title=OUTCOME,
            sort=None,
            scale=alt.Scale(domain=levels, range=IMPRINT_PALETTE),
            legend=alt.Legend(orient="right", symbolType="square", symbolSize=500),
        ),
        tooltip=[
            alt.Tooltip("column:N", title=PASSENGER_CLASS),
            alt.Tooltip("level:N", title=OUTCOME),
            alt.Tooltip("count:Q", title=PASSENGERS),
            alt.Tooltip("percent:Q", title="Share of all (%)"),
        ],
    )
)

# Count labels: dark ink reads on both Imprint fills in either theme
counts = (
    alt.Chart(tiles)
    .mark_text(fontSize=11, fontWeight="bold", color="#1A1A17")
    .encode(x="x_mid:Q", y="y_mid:Q", text="label:N")
)

# Column names just above the top edge of each column
names = (
    alt.Chart(column_labels)
    .mark_text(fontSize=12, fontWeight="bold", baseline="bottom", dy=-4, color=INK)
    .encode(x="x_mid:Q", y=alt.value(0), text="column:N")
)

chart = (
    alt.layer(mosaic, counts, names)
    .properties(
        width=560,
        height=370,
        background=PAGE_BG,
        title=alt.Title("mosaic-categorical · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=13,
        labelFontSize=11,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=12,
        labelFontSize=11,
        padding=8,
    )
)

# Save outputs, padding (never cropping) to the canonical landscape canvas
TARGET_W, TARGET_H = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair rendered {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
