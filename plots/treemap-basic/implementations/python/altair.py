""" pyplots.ai
treemap-basic: Basic Treemap
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import altair as alt
import pandas as pd


# Data - Market capitalization by sector and company (in billions USD)
data = [
    {"category": "Technology", "subcategory": "Apple", "value": 2800},
    {"category": "Technology", "subcategory": "Microsoft", "value": 2400},
    {"category": "Technology", "subcategory": "Google", "value": 1800},
    {"category": "Technology", "subcategory": "NVIDIA", "value": 1200},
    {"category": "Finance", "subcategory": "JPMorgan", "value": 500},
    {"category": "Finance", "subcategory": "BofA", "value": 300},
    {"category": "Finance", "subcategory": "Wells Fargo", "value": 200},
    {"category": "Healthcare", "subcategory": "UnitedHealth", "value": 450},
    {"category": "Healthcare", "subcategory": "J&J", "value": 380},
    {"category": "Healthcare", "subcategory": "Pfizer", "value": 250},
    {"category": "Energy", "subcategory": "Exxon", "value": 420},
    {"category": "Energy", "subcategory": "Chevron", "value": 300},
    {"category": "Consumer", "subcategory": "Amazon", "value": 1500},
    {"category": "Consumer", "subcategory": "Walmart", "value": 400},
    {"category": "Consumer", "subcategory": "Tesla", "value": 600},
]

df = pd.DataFrame(data)

# Canvas dimensions for 16:9 aspect ratio (4800x2700 at scale_factor=3)
width = 1600
height = 900

# Color palette - Python Blue first, then colorblind-safe colors
colors = {
    "Technology": "#306998",
    "Finance": "#FFD43B",
    "Healthcare": "#4ECDC4",
    "Energy": "#E07A5F",
    "Consumer": "#81B29A",
}

# Compute category totals and sort
category_totals = df.groupby("category")["value"].sum().sort_values(ascending=False)
sorted_cats = list(category_totals.index)
cat_values = list(category_totals.values)
total_value = sum(cat_values)

# Simple strip layout - categories as vertical strips, subcategories stacked within
cat_rects = {}
current_x = 0
for cat, val in zip(sorted_cats, cat_values, strict=False):
    rect_width = (val / total_value) * width
    cat_rects[cat] = {"x": current_x, "y": 0, "dx": rect_width, "dy": height}
    current_x += rect_width

# Compute subcategory rectangles within each category (stacked vertically)
all_rects = []
for cat in sorted_cats:
    cat_df = df[df["category"] == cat].sort_values("value", ascending=False)
    cat_rect = cat_rects[cat]
    cat_total = cat_df["value"].sum()

    current_y = 0
    for _, row in cat_df.iterrows():
        rect_height = (row["value"] / cat_total) * cat_rect["dy"]
        all_rects.append(
            {
                "category": cat,
                "subcategory": row["subcategory"],
                "value": row["value"],
                "x": cat_rect["x"],
                "y": current_y,
                "dx": cat_rect["dx"],
                "dy": rect_height,
            }
        )
        current_y += rect_height

rects_df = pd.DataFrame(all_rects)

# Calculate corner and center coordinates for Altair
rects_df["x2"] = rects_df["x"] + rects_df["dx"]
rects_df["y2"] = rects_df["y"] + rects_df["dy"]
rects_df["x_center"] = rects_df["x"] + rects_df["dx"] / 2
rects_df["y_center"] = rects_df["y"] + rects_df["dy"] / 2
rects_df["display_value"] = rects_df["value"].apply(lambda x: f"${x}B")

# Determine which rectangles are large enough for labels
rects_df["area"] = rects_df["dx"] * rects_df["dy"]
min_area_for_label = width * height * 0.02

# Treemap rectangles with white borders
rects_chart = (
    alt.Chart(rects_df)
    .mark_rect(stroke="#ffffff", strokeWidth=3)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, width]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, height]), axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color(
            "category:N",
            scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())),
            legend=alt.Legend(title="Sector", titleFontSize=22, labelFontSize=18, symbolSize=400, orient="right"),
        ),
        tooltip=[
            alt.Tooltip("category:N", title="Sector"),
            alt.Tooltip("subcategory:N", title="Company"),
            alt.Tooltip("display_value:N", title="Market Cap"),
        ],
    )
)

# Filter for large rectangles that can fit labels
labels_df = rects_df[rects_df["area"] >= min_area_for_label].copy()

# Company name labels (white bold text)
name_labels = (
    alt.Chart(labels_df)
    .mark_text(fontSize=20, fontWeight="bold", color="#ffffff", dy=-10)
    .encode(
        x=alt.X("x_center:Q", scale=alt.Scale(domain=[0, width])),
        y=alt.Y("y_center:Q", scale=alt.Scale(domain=[0, height])),
        text="subcategory:N",
    )
)

# Value labels (white text, smaller)
value_labels = (
    alt.Chart(labels_df)
    .mark_text(fontSize=16, color="#ffffff", dy=10)
    .encode(
        x=alt.X("x_center:Q", scale=alt.Scale(domain=[0, width])),
        y=alt.Y("y_center:Q", scale=alt.Scale(domain=[0, height])),
        text="display_value:N",
    )
)

# Combine all layers
chart = (
    alt.layer(rects_chart, name_labels, value_labels)
    .properties(
        width=width,
        height=height,
        title=alt.Title(text="treemap-basic · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
)

# Save outputs - scale_factor=3 gives 4800x2700
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
