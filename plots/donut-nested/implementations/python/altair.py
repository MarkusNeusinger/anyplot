""" anyplot.ai
donut-nested: Nested Donut Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-08
"""

import os

import altair as alt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Market share by region (inner) and product lines within each region (outer)
data = {
    "level_1": ["Americas", "Americas", "Americas", "EMEA", "EMEA", "EMEA", "EMEA", "Asia", "Asia", "Asia", "Asia"],
    "level_2": [
        "Cloud Services",
        "Software Licenses",
        "Consulting",
        "Cloud Services",
        "Software Licenses",
        "Hardware",
        "Support Services",
        "Cloud Services",
        "Hardware",
        "Software Licenses",
        "Training",
    ],
    "value": [420, 280, 150, 320, 240, 180, 160, 380, 200, 220, 140],
}

df = pd.DataFrame(data)

# Calculate parent totals for inner ring
inner_df = df.groupby("level_1", as_index=False)["value"].sum()
inner_df["level_2"] = inner_df["level_1"]

# Color mapping for consistent color families per parent category
# Use Okabe-Ito palette positions with variations for subcategories
color_map = {}
for i, parent in enumerate(inner_df["level_1"]):
    parent_color = IMPRINT[i % len(IMPRINT)]
    parent_children = df[df["level_1"] == parent]["level_2"].tolist()
    color_map[parent] = {}
    for j, child in enumerate(parent_children):
        # Create lighter shades of the parent color for children
        base_rgb = int(parent_color[1:3], 16), int(parent_color[3:5], 16), int(parent_color[5:7], 16)
        # Use different lightness adjustments for each child
        if j == 0:
            color_map[parent][child] = parent_color  # Full saturation
        else:
            # Lighter variants for subsequent children
            factor = 1 + (j * 0.2)
            lighter_rgb = tuple(min(255, int(c * factor)) for c in base_rgb)
            color_map[parent][child] = "#{:02x}{:02x}{:02x}".format(*lighter_rgb)

# Assign colors to outer ring items
outer_colors = []
for _, row in df.iterrows():
    outer_colors.append(color_map[row["level_1"]][row["level_2"]])
df["color"] = outer_colors

# Inner ring colors (use Okabe-Ito positions)
inner_color_map = {}
for i, parent in enumerate(inner_df["level_1"]):
    inner_color_map[parent] = IMPRINT[i % len(IMPRINT)]
inner_df["color"] = inner_df["level_1"].map(inner_color_map)

# Format values for tooltip
df["formatted_value"] = df["value"].apply(lambda x: f"${x}M")
inner_df["formatted_value"] = inner_df["value"].apply(lambda x: f"${x}M")

# Outer ring (child categories)
outer_ring = (
    alt.Chart(df)
    .mark_arc(innerRadius=280, outerRadius=420, stroke=PAGE_BG, strokeWidth=3)
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color("color:N", scale=None, legend=None),
        tooltip=[
            alt.Tooltip("level_1:N", title="Region"),
            alt.Tooltip("level_2:N", title="Product"),
            alt.Tooltip("formatted_value:N", title="Revenue"),
        ],
    )
)

# Inner ring (parent categories)
inner_ring = (
    alt.Chart(inner_df)
    .mark_arc(innerRadius=120, outerRadius=260, stroke=PAGE_BG, strokeWidth=3)
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color("color:N", scale=None, legend=None),
        tooltip=[alt.Tooltip("level_1:N", title="Region"), alt.Tooltip("formatted_value:N", title="Total Revenue")],
    )
)

# Labels for inner ring (region names)
inner_labels = (
    alt.Chart(inner_df)
    .mark_text(radius=185, fontSize=24, fontWeight="bold", color=INK)
    .encode(theta=alt.Theta("value:Q", stack=True), text="level_1:N")
)

# Labels for outer ring (show labels for larger segments)
df["label"] = df.apply(lambda row: row["level_2"] if row["value"] >= 150 else "", axis=1)
outer_labels = (
    alt.Chart(df)
    .mark_text(radius=360, fontSize=16, color=INK_SOFT)
    .encode(theta=alt.Theta("value:Q", stack=True), text="label:N")
)

# Combine all layers
chart = (
    alt.layer(inner_ring, outer_ring, inner_labels, outer_labels)
    .properties(
        width=1600,
        height=1600,
        background=PAGE_BG,
        title=alt.Title("donut-nested · altair · anyplot.ai", fontSize=32, anchor="middle", offset=20, color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=None, strokeWidth=0)
    .configure_title(color=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
