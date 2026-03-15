""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: altair 6.0.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-15
"""

import altair as alt
import pandas as pd


# Data: Grand Canyon sedimentary section with 10 layers spanning Cambrian to Permian
layers = pd.DataFrame(
    {
        "top": [0, 15, 35, 55, 70, 90, 110, 135, 155, 175],
        "bottom": [15, 35, 55, 70, 90, 110, 135, 155, 175, 200],
        "lithology": [
            "Sandstone",
            "Shale",
            "Limestone",
            "Siltstone",
            "Sandstone",
            "Conglomerate",
            "Shale",
            "Limestone",
            "Siltstone",
            "Sandstone",
        ],
        "formation": [
            "Cedar Mesa Fm",
            "Organ Rock Fm",
            "White Rim Fm",
            "De Chelly Fm",
            "Coconino Fm",
            "Hermit Fm",
            "Supai Group",
            "Redwall Fm",
            "Temple Butte Fm",
            "Muav Fm",
        ],
        "age": [
            "Permian",
            "Permian",
            "Permian",
            "Permian",
            "Permian",
            "Permian",
            "Pennsylvanian",
            "Mississippian",
            "Devonian",
            "Cambrian",
        ],
    }
)

layers["thickness"] = layers["bottom"] - layers["top"]
layers["mid_depth"] = (layers["top"] + layers["bottom"]) / 2

# Colorblind-safe geological palette
lithology_colors = {
    "Sandstone": "#E8C547",
    "Shale": "#7B8894",
    "Limestone": "#4A90D9",
    "Siltstone": "#9B6DBF",
    "Conglomerate": "#D4772C",
}

lithology_order = ["Sandstone", "Shale", "Limestone", "Siltstone", "Conglomerate"]

# Lithology pattern symbols for geological texture
pattern_symbols = {
    "Sandstone": "·  ·  ·  ·  ·",
    "Shale": "—  —  —  —",
    "Limestone": "▤  ▤  ▤  ▤",
    "Siltstone": "╌  ╌  ╌  ╌",
    "Conglomerate": "◯  ◯  ◯  ◯",
}

# Create multiple pattern rows per layer for denser texture fill
pattern_rows = []
for _, row in layers.iterrows():
    layer_height = row["bottom"] - row["top"]
    n_rows = max(2, int(layer_height / 7))
    spacing = layer_height / (n_rows + 1)
    for i in range(n_rows):
        depth = row["top"] + spacing * (i + 1)
        pattern_rows.append({"depth": depth, "pattern": pattern_symbols[row["lithology"]]})
pattern_df = pd.DataFrame(pattern_rows)

# Identify unique age groups
age_groups = []
current_age = None
for _, row in layers.iterrows():
    if row["age"] != current_age:
        current_age = row["age"]
        group_rows = layers[layers["age"] == current_age]
        age_groups.append(
            {
                "age": current_age,
                "top": group_rows["top"].min(),
                "bottom": group_rows["bottom"].max(),
                "mid_depth": (group_rows["top"].min() + group_rows["bottom"].max()) / 2,
            }
        )
age_df = pd.DataFrame(age_groups)

# Unconformity markers at major geological transitions
unconformity_df = pd.DataFrame({"depth": [110, 155], "label": ["— Unconformity —", "— Great Unconformity —"]})

# Shared scales
x_domain = [0, 16]
x_axis_none = alt.Axis(labels=False, ticks=False, domain=False, grid=False)

# Layer rectangles
rects = (
    alt.Chart(layers)
    .mark_rect(stroke="#2C3E50", strokeWidth=1.5)
    .encode(
        y=alt.Y(
            "top:Q",
            title="Depth (m)",
            scale=alt.Scale(domain=[0, 200], reverse=True),
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                tickCount=10,
                gridColor="#E0E0E0",
                gridDash=[2, 4],
                domainColor="#2C3E50",
            ),
        ),
        y2="bottom:Q",
        x=alt.X("x:Q", scale=alt.Scale(domain=x_domain), axis=None),
        x2="x2:Q",
        color=alt.Color(
            "lithology:N",
            title="Lithology",
            scale=alt.Scale(domain=lithology_order, range=[lithology_colors[k] for k in lithology_order]),
            legend=alt.Legend(
                titleFontSize=20,
                labelFontSize=18,
                symbolSize=500,
                orient="bottom",
                titlePadding=12,
                direction="horizontal",
                labelLimit=200,
                symbolStrokeWidth=1.5,
                padding=20,
                columns=5,
            ),
        ),
        tooltip=[
            alt.Tooltip("formation:N", title="Formation"),
            alt.Tooltip("lithology:N", title="Lithology"),
            alt.Tooltip("age:N", title="Age"),
            alt.Tooltip("top:Q", title="Top (m)"),
            alt.Tooltip("bottom:Q", title="Bottom (m)"),
            alt.Tooltip("thickness:Q", title="Thickness (m)"),
        ],
    )
    .transform_calculate(x="3", x2="9")
)

# Dense pattern texture overlay
pattern_text = (
    alt.Chart(pattern_df)
    .mark_text(fontSize=16, color="#2C3E50", opacity=0.6)
    .encode(y=alt.Y("depth:Q"), x=alt.X("x_mid:Q", scale=alt.Scale(domain=x_domain)), text="pattern:N")
    .transform_calculate(x_mid="6")
)

# Formation name labels to the right
formation_labels = (
    alt.Chart(layers)
    .mark_text(fontSize=17, fontWeight="bold", align="left", color="#1B2631")
    .encode(y=alt.Y("mid_depth:Q"), x=alt.X("x_pos:Q", scale=alt.Scale(domain=x_domain)), text="formation:N")
    .transform_calculate(x_pos="9.4")
)

# Thickness annotations (subtle, on the right)
thickness_labels = (
    alt.Chart(layers)
    .mark_text(fontSize=13, align="right", color="#7F8C8D", fontStyle="italic")
    .encode(y=alt.Y("mid_depth:Q"), x=alt.X("x_pos:Q", scale=alt.Scale(domain=x_domain)), text="label:N")
    .transform_calculate(x_pos="15.8", label="datum.thickness + ' m'")
)

# Age period labels to the left
age_labels = (
    alt.Chart(age_df)
    .mark_text(fontSize=18, fontStyle="italic", fontWeight="bold", align="right", color="#2C3E50")
    .encode(y=alt.Y("mid_depth:Q"), x=alt.X("x_pos:Q", scale=alt.Scale(domain=x_domain)), text="age:N")
    .transform_calculate(x_pos="2.0")
)

# Age bracket vertical lines
age_brackets_v = (
    alt.Chart(age_df)
    .mark_rule(strokeWidth=2.5, color="#2C3E50")
    .encode(y=alt.Y("top:Q"), y2="bottom:Q", x=alt.X("x_pos:Q", scale=alt.Scale(domain=x_domain)))
    .transform_calculate(x_pos="2.5")
)

# Age bracket horizontal ticks (top and bottom of each age group)
bracket_ticks_data = []
for _, row in age_df.iterrows():
    bracket_ticks_data.append({"depth": row["top"]})
    bracket_ticks_data.append({"depth": row["bottom"]})
bracket_ticks_df = pd.DataFrame(bracket_ticks_data)

age_bracket_ticks = (
    alt.Chart(bracket_ticks_df)
    .mark_rule(strokeWidth=2.5, color="#2C3E50")
    .encode(y=alt.Y("depth:Q"), x=alt.X("x1:Q", scale=alt.Scale(domain=x_domain)), x2="x2:Q")
    .transform_calculate(x1="2.5", x2="2.8")
)

# Unconformity markers — red dashed lines at key geological transitions
unconformity_rules = (
    alt.Chart(unconformity_df)
    .mark_rule(strokeWidth=4, color="#C0392B", strokeDash=[8, 4])
    .encode(y=alt.Y("depth:Q"), x=alt.X("x1:Q", scale=alt.Scale(domain=x_domain)), x2="x2:Q")
    .transform_calculate(x1="3", x2="9")
)

unconformity_labels_chart = (
    alt.Chart(unconformity_df)
    .mark_text(fontSize=12, color="#C0392B", fontWeight="bold", align="center", dy=14)
    .encode(y=alt.Y("depth:Q"), x=alt.X("x_mid:Q", scale=alt.Scale(domain=x_domain)), text="label:N")
    .transform_calculate(x_mid="6")
)

# Combine all layers
chart = (
    (
        rects
        + pattern_text
        + formation_labels
        + thickness_labels
        + age_labels
        + age_brackets_v
        + age_bracket_ticks
        + unconformity_rules
        + unconformity_labels_chart
    )
    .properties(
        width=1200,
        height=900,
        title=alt.Title(
            "column-stratigraphic · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            offset=20,
            color="#1B2631",
            subtitle="Grand Canyon Sedimentary Section — Cambrian to Permian",
            subtitleFontSize=18,
            subtitleColor="#566573",
            subtitlePadding=8,
        ),
    )
    .configure_view(strokeWidth=0)
    .configure(background="#FAFBFC")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
