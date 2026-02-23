""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: altair 6.0.0 | Python 3.14.3
Quality: 88/100 | Updated: 2026-02-23
"""

import altair as alt
import circlify
import numpy as np
import pandas as pd


np.random.seed(42)

# Data - Department budget allocation by division
labels = [
    "Engineering",
    "R&D",
    "Data Science",
    "QA",
    "Marketing",
    "Sales",
    "Support",
    "Finance",
    "HR",
    "Legal",
    "Operations",
    "IT",
    "Security",
    "Design",
    "Product",
]
values = [850, 750, 460, 195, 420, 680, 210, 290, 180, 150, 320, 380, 170, 240, 550]
groups = ["Technology"] * 4 + ["Revenue"] * 3 + ["Corporate"] * 3 + ["Operations"] * 3 + ["Product"] * 2
n = len(labels)

# Circle packing layout (circlify returns ascending by value)
circles = circlify.circlify(values, show_enclosure=False)
idx_asc = np.argsort(values)
scale = 300

x = np.zeros(n)
y = np.zeros(n)
radii = np.zeros(n)
for ci, oi in zip(circles, idx_asc, strict=True):
    x[oi] = ci.x * scale
    y[oi] = ci.y * scale
    radii[oi] = ci.r * scale

# Colorblind-safe palette (teal replaces sage green for deuteranopia safety)
group_order = ["Technology", "Revenue", "Operations", "Corporate", "Product"]
palette = ["#306998", "#E07A5F", "#8B6DA8", "#2A9D8F", "#FFD43B"]

df = pd.DataFrame(
    {
        "label": labels,
        "value": values,
        "group": groups,
        "x": x,
        "y": y,
        "radius": radii,
        "budget": [f"${v}K" for v in values],
    }
)

# Interactive legend selection — click to highlight a division (Altair-distinctive)
selection = alt.selection_point(fields=["group"], bind="legend")

r_min, r_max = radii.min(), radii.max()
circles_layer = (
    alt.Chart(df)
    .mark_circle(stroke="white", strokeWidth=2.5)
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(padding=r_max * 0.6)),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(padding=r_max * 0.6)),
        size=alt.Size("radius:Q", scale=alt.Scale(range=[r_min**2 * 10, r_max**2 * 10]), legend=None),
        color=alt.Color(
            "group:N",
            scale=alt.Scale(domain=group_order, range=palette),
            legend=alt.Legend(
                title="Division",
                titleFontSize=20,
                titleFontWeight="bold",
                labelFontSize=18,
                symbolSize=350,
                orient="right",
            ),
        ),
        opacity=alt.condition(selection, alt.value(0.9), alt.value(0.15)),
        tooltip=[
            alt.Tooltip("label:N", title="Department"),
            alt.Tooltip("budget:N", title="Budget"),
            alt.Tooltip("group:N", title="Division"),
        ],
    )
    .add_params(selection)
)

# Labels inside larger bubbles (two-line: department + budget)
df_large = df[df["radius"] >= r_min + (r_max - r_min) * 0.25].copy()
df_large["display_text"] = df_large["label"] + "\n" + df_large["budget"]

large_labels = (
    alt.Chart(df_large)
    .mark_text(fontWeight="bold", fontSize=20, lineBreak="\n")
    .encode(
        x="x:Q",
        y="y:Q",
        text="display_text:N",
        color=alt.condition(alt.datum.group == "Product", alt.value("#333333"), alt.value("white")),
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.1)),
    )
)

# Labels for smaller bubbles (department name for identification in static PNG)
df_small = df[df["radius"] < r_min + (r_max - r_min) * 0.25].copy()

small_labels = (
    alt.Chart(df_small)
    .mark_text(fontWeight="bold", fontSize=15)
    .encode(
        x="x:Q",
        y="y:Q",
        text="label:N",
        color=alt.condition(alt.datum.group == "Product", alt.value("#333333"), alt.value("white")),
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.1)),
    )
)

chart = (
    alt.layer(circles_layer, large_labels, small_labels)
    .properties(
        width=1200,
        height=1200,
        title=alt.Title(
            "Department Budget Allocation · bubble-packed · altair · pyplots.ai",
            subtitle="Technology division leads at 39% of total budget — Engineering alone accounts for $850K",
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#555555",
            fontWeight="bold",
            anchor="middle",
        ),
    )
    .configure_view(strokeWidth=0)
)

chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
