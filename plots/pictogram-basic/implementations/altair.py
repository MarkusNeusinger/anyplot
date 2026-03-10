"""pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: altair 6.0.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-10
"""

import altair as alt
import pandas as pd


# Data - Fruit production (thousands of tonnes)
categories = ["Apples", "Oranges", "Bananas", "Grapes", "Mangoes"]
values = [35, 22, 18, 12, 8]
# Colorblind-safe palette (no red-green conflict): steel blue, amber, teal, purple, coral
colors = ["#306998", "#E8A838", "#2A9D8F", "#9B59B6", "#D55E00"]
unit_value = 5
max_icons = max(v // unit_value + (1 if v % unit_value else 0) for v in values)
top_value = max(values)

# Build row data: one row per icon position
rows = []
for cat, val, color in zip(categories, values, colors, strict=True):
    full_icons = val // unit_value
    remainder = (val % unit_value) / unit_value

    for i in range(full_icons):
        rows.append({"category": cat, "col": i, "opacity": 1.0, "color": color, "value": val})

    if remainder > 0:
        rows.append({"category": cat, "col": full_icons, "opacity": round(remainder, 2), "color": color, "value": val})

df = pd.DataFrame(rows)

# Category sort order (by value descending)
sort_order = [c for _, c in sorted(zip(values, categories, strict=True), reverse=True)]

# Plot - circles arranged in a grid
chart = (
    alt.Chart(df)
    .mark_point(size=1200, filled=True, strokeWidth=0)
    .encode(
        x=alt.X(
            "col:Q",
            title=None,
            scale=alt.Scale(domain=[-0.4, max_icons + 0.8]),
            axis=alt.Axis(labels=False, ticks=False, domain=False, grid=False),
        ),
        y=alt.Y(
            "category:N",
            title=None,
            sort=sort_order,
            scale=alt.Scale(type="band", paddingInner=0.45, paddingOuter=0.15),
            axis=alt.Axis(
                labelFontSize=22,
                labelFontWeight="bold",
                labelColor="#333333",
                ticks=False,
                domain=False,
                grid=False,
                labelPadding=18,
            ),
        ),
        color=alt.Color("color:N", scale=None),
        opacity=alt.Opacity("opacity:Q", scale=alt.Scale(domain=[0, 1]), legend=None),
        tooltip=[alt.Tooltip("category:N", title="Category"), alt.Tooltip("value:Q", title="Production (k tonnes)")],
    )
)

# Value labels at end of each row - emphasize top category
label_data = []
for cat, val in zip(categories, values, strict=True):
    icon_count = val // unit_value + (1 if val % unit_value else 0)
    label_data.append(
        {"category": cat, "col": icon_count + 0.3, "label": f"{val}k", "value": val, "is_top": val == top_value}
    )

label_df = pd.DataFrame(label_data)

# Top category label (bold, larger, darker)
top_labels = (
    alt.Chart(label_df[label_df["is_top"]])
    .mark_text(align="left", baseline="middle", fontSize=22, fontWeight="bold", color="#222222")
    .encode(x=alt.X("col:Q"), y=alt.Y("category:N", sort=sort_order), text=alt.Text("label:N"))
)

# Other category labels
other_labels = (
    alt.Chart(label_df[~label_df["is_top"]])
    .mark_text(align="left", baseline="middle", fontSize=18, fontWeight="bold", color="#777777")
    .encode(x=alt.X("col:Q"), y=alt.Y("category:N", sort=sort_order), text=alt.Text("label:N"))
)

# Highlight bar behind top category for visual storytelling
top_cat = sort_order[0]
highlight_df = pd.DataFrame([{"category": top_cat}])
highlight = (
    alt.Chart(highlight_df)
    .mark_bar(color="#306998", opacity=0.07, cornerRadius=6)
    .encode(y=alt.Y("category:N", sort=sort_order), x=alt.value(0), x2=alt.value(1480))
)

# Combine layers with compact height for better canvas utilization
combined = (
    (highlight + chart + top_labels + other_labels)
    .properties(
        width=1480,
        height=800,
        title=alt.Title(
            text="pictogram-basic \u00b7 altair \u00b7 pyplots.ai",
            subtitle=[
                "Global Fruit Production Comparison",
                f"\u25cf = {unit_value}k tonnes  |  partial \u25cf = fractional amount",
            ],
            fontSize=28,
            subtitleFontSize=16,
            subtitleColor="#888888",
            anchor="start",
            offset=20,
        ),
    )
    .configure_view(strokeWidth=0)
)

# Save
combined.save("plot.png", scale_factor=3.0)
combined.save("plot.html")
