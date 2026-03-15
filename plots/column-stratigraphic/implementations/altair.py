""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: altair 6.0.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-15
"""

import altair as alt
import pandas as pd


# Data: Synthetic sedimentary section with 10 layers
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

# Lithology color palette (geologically conventional)
lithology_colors = {
    "Sandstone": "#F5D76E",
    "Shale": "#7B8D8E",
    "Limestone": "#5DADE2",
    "Siltstone": "#A9CCE3",
    "Conglomerate": "#E67E22",
}

lithology_order = ["Sandstone", "Shale", "Limestone", "Siltstone", "Conglomerate"]

# Lithology pattern symbols for overlay
pattern_map = {
    "Sandstone": "· · ·",
    "Shale": "— — —",
    "Limestone": "▦ ▦ ▦",
    "Siltstone": "– – –",
    "Conglomerate": "○ ○ ○",
}
layers["pattern_label"] = layers["lithology"].map(pattern_map)

# Identify unique age boundaries for left-side labels
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

# Layer rectangles
rects = (
    alt.Chart(layers)
    .mark_rect(stroke="#333333", strokeWidth=2)
    .encode(
        y=alt.Y(
            "top:Q",
            title="Depth (m)",
            scale=alt.Scale(domain=[0, 200]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        y2="bottom:Q",
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 14]), axis=None),
        x2="x2:Q",
        color=alt.Color(
            "lithology:N",
            title="Lithology",
            scale=alt.Scale(domain=lithology_order, range=[lithology_colors[k] for k in lithology_order]),
            legend=alt.Legend(
                titleFontSize=20,
                labelFontSize=18,
                symbolSize=400,
                orient="bottom",
                titlePadding=10,
                direction="horizontal",
                labelLimit=200,
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
    .transform_calculate(x="2.5", x2="7.5")
)

# Pattern texture labels inside each layer
pattern_text = (
    alt.Chart(layers)
    .mark_text(fontSize=16, color="#555555", opacity=0.6)
    .encode(y=alt.Y("mid_depth:Q"), x=alt.X("x_mid:Q", scale=alt.Scale(domain=[0, 14])), text="pattern_label:N")
    .transform_calculate(x_mid="5")
)

# Formation name labels to the right
formation_labels = (
    alt.Chart(layers)
    .mark_text(fontSize=16, fontWeight="bold", align="left", color="#1a1a1a")
    .encode(y=alt.Y("mid_depth:Q"), x=alt.X("x_pos:Q", scale=alt.Scale(domain=[0, 14])), text="formation:N")
    .transform_calculate(x_pos="7.8")
)

# Age labels to the left
age_labels = (
    alt.Chart(age_df)
    .mark_text(fontSize=15, fontStyle="italic", align="right", color="#444444")
    .encode(y=alt.Y("mid_depth:Q"), x=alt.X("x_pos:Q", scale=alt.Scale(domain=[0, 14])), text="age:N")
    .transform_calculate(x_pos="1.7")
)

# Age boundary lines
age_boundaries = age_df[age_df["top"] > 0][["top"]].copy()
age_boundaries["x1"] = 2.5
age_boundaries["x2"] = 7.5

age_rules = (
    alt.Chart(age_boundaries)
    .mark_rule(strokeDash=[8, 4], strokeWidth=1.5, color="#666666")
    .encode(y=alt.Y("top:Q"), x=alt.X("x1:Q", scale=alt.Scale(domain=[0, 14])), x2="x2:Q")
)

# Combine all layers
chart = (
    (rects + pattern_text + formation_labels + age_labels + age_rules)
    .properties(
        width=1200,
        height=900,
        title=alt.Title(
            "Stratigraphic Column · column-stratigraphic · altair · pyplots.ai", fontSize=26, anchor="middle", offset=20
        ),
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
