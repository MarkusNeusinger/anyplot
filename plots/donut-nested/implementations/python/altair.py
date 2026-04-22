""" pyplots.ai
donut-nested: Nested Donut Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import altair as alt
import pandas as pd


# Data - Budget allocation by department (inner) and expense categories (outer)
data = {
    "level_1": [
        "Engineering",
        "Engineering",
        "Engineering",
        "Engineering",
        "Marketing",
        "Marketing",
        "Marketing",
        "Sales",
        "Sales",
        "Sales",
        "Operations",
        "Operations",
        "Operations",
        "Operations",
    ],
    "level_2": [
        "Salaries",
        "Equipment",
        "Software",
        "Training",
        "Digital Ads",
        "Events",
        "Content",
        "Commissions",
        "Travel",
        "Tools",
        "Facilities",
        "IT Support",
        "Logistics",
        "HR",
    ],
    "value": [450, 120, 80, 50, 200, 150, 100, 180, 120, 50, 160, 100, 90, 50],
}

df = pd.DataFrame(data)

# Calculate parent totals for inner ring
inner_df = df.groupby("level_1", as_index=False)["value"].sum()
inner_df["level_2"] = inner_df["level_1"]  # Use level_1 as label for inner ring

# Color palette - consistent color families per parent category
# Python Blue family for Engineering, Yellow family for Marketing,
# Teal family for Sales, Purple family for Operations
color_map_outer = {
    "Engineering": {"Salaries": "#306998", "Equipment": "#4A89B5", "Software": "#6BA3C8", "Training": "#8DBDD8"},
    "Marketing": {"Digital Ads": "#FFD43B", "Events": "#FFDD66", "Content": "#FFE699"},
    "Sales": {"Commissions": "#2D9D78", "Travel": "#4DB891", "Tools": "#6FD3AB"},
    "Operations": {"Facilities": "#7B68A6", "IT Support": "#9683B8", "Logistics": "#B19FCA", "HR": "#CCBBDC"},
}

# Flatten color map for outer ring
outer_colors = []
for _, row in df.iterrows():
    outer_colors.append(color_map_outer[row["level_1"]][row["level_2"]])
df["color"] = outer_colors

# Inner ring colors (darker shade per category)
inner_color_map = {"Engineering": "#1F4A66", "Marketing": "#D4A800", "Sales": "#1A7553", "Operations": "#5A4980"}
inner_df["color"] = inner_df["level_1"].map(inner_color_map)

# Format values for tooltip
df["formatted_value"] = df["value"].apply(lambda x: f"${x}K")
inner_df["formatted_value"] = inner_df["value"].apply(lambda x: f"${x}K")

# Outer ring (child categories)
outer_ring = (
    alt.Chart(df)
    .mark_arc(innerRadius=280, outerRadius=400, stroke="white", strokeWidth=3)
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color("color:N", scale=None, legend=None),
        tooltip=[
            alt.Tooltip("level_1:N", title="Department"),
            alt.Tooltip("level_2:N", title="Category"),
            alt.Tooltip("formatted_value:N", title="Budget"),
        ],
    )
)

# Inner ring (parent categories)
inner_ring = (
    alt.Chart(inner_df)
    .mark_arc(innerRadius=140, outerRadius=260, stroke="white", strokeWidth=3)
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color("color:N", scale=None, legend=None),
        tooltip=[alt.Tooltip("level_1:N", title="Department"), alt.Tooltip("formatted_value:N", title="Total Budget")],
    )
)

# Labels for inner ring (department names)
inner_labels = (
    alt.Chart(inner_df)
    .mark_text(radius=200, fontSize=22, fontWeight="bold", color="white")
    .encode(theta=alt.Theta("value:Q", stack=True), text="level_1:N")
)

# Labels for outer ring (show all, but only for larger segments)
df["label"] = df.apply(lambda row: row["level_2"] if row["value"] >= 100 else "", axis=1)
outer_labels = (
    alt.Chart(df)
    .mark_text(radius=340, fontSize=16, color="#333333")
    .encode(theta=alt.Theta("value:Q", stack=True), text="label:N")
)

# Combine all layers
chart = (
    alt.layer(inner_ring, outer_ring, inner_labels, outer_labels)
    .properties(
        width=1200,
        height=1200,
        title=alt.Title("donut-nested · altair · pyplots.ai", fontSize=32, anchor="middle", offset=20),
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
