""" pyplots.ai
pie-basic: Basic Pie Chart
Library: altair 6.0.0 | Python 3.14.0
Quality: 90/100 | Created: 2025-12-23
"""

import altair as alt
import pandas as pd


# Data - Cloud infrastructure market share
data = pd.DataFrame(
    {"category": ["AWS", "Azure", "Google Cloud", "Alibaba", "Oracle", "Others"], "value": [31, 24, 11, 4, 3, 27]}
)

total = data["value"].sum()
data["percentage"] = data["value"] / total * 100
data["label"] = data["percentage"].apply(lambda x: f"{x:.0f}%")
data["order"] = range(len(data))

# Color palette - Python Blue first, cohesive colorblind-safe
colors = ["#306998", "#FFD43B", "#4ECDC4", "#FF6B6B", "#95E1D3", "#A8A8A8"]
domain = data["category"].tolist()

color_scale = alt.Scale(domain=domain, range=colors)

# Shared base with encodings
base = alt.Chart(data).encode(
    theta=alt.Theta("value:Q", stack=True),
    order=alt.Order("order:O"),
    color=alt.Color(
        "category:N",
        scale=color_scale,
        legend=alt.Legend(
            title="Provider",
            titleFontSize=20,
            labelFontSize=18,
            symbolSize=300,
            orient="bottom",
            direction="horizontal",
            columns=6,
            titleAnchor="middle",
        ),
    ),
)

# Main pie slices (non-AWS)
pie = (
    base.transform_filter(alt.datum.category != "AWS")
    .mark_arc(outerRadius=370, innerRadius=0, stroke="#ffffff", strokeWidth=2.5, padAngle=0.02, cornerRadius=3)
    .encode(tooltip=[alt.Tooltip("category:N", title="Provider"), alt.Tooltip("value:Q", title="Market Share (%)")])
)

# Exploded AWS slice — offset via radiusOffset for visible displacement
exploded_aws = (
    base.transform_filter(alt.datum.category == "AWS")
    .mark_arc(
        outerRadius=370, innerRadius=0, radiusOffset=22, stroke="#ffffff", strokeWidth=3, padAngle=0.04, cornerRadius=3
    )
    .encode(tooltip=[alt.Tooltip("category:N", title="Provider"), alt.Tooltip("value:Q", title="Market Share (%)")])
)

# Percentage labels outside slices — larger radius for better separation
text_main = (
    base.transform_filter(alt.datum.category != "AWS")
    .mark_text(radius=420, fontSize=21, fontWeight="bold")
    .encode(text="label:N")
)

# AWS label with matching offset
text_aws = (
    base.transform_filter(alt.datum.category == "AWS")
    .mark_text(radius=420, radiusOffset=22, fontSize=21, fontWeight="bold")
    .encode(text="label:N")
)

# Annotation: AWS callout as market leader
aws_note = (
    alt.Chart(pd.DataFrame({"text": ["AWS leads at 31% — largest single provider"]}))
    .mark_text(fontSize=16, fontStyle="italic", color="#306998", align="left")
    .encode(x=alt.value(720), y=alt.value(100), text="text:N")
)

# Annotation: "Others" insight (positioned below chart, left-aligned)
others_note = (
    alt.Chart(pd.DataFrame({"text": ['"Others" at 27% collectively outpace all but AWS']}))
    .mark_text(fontSize=16, fontStyle="italic", color="#777777", align="left")
    .encode(x=alt.value(100), y=alt.value(980), text="text:N")
)

# Combine all layers — compact layout with legend closer to chart
chart = (
    alt.layer(pie, exploded_aws, text_main, text_aws, aws_note, others_note)
    .properties(
        width=1200,
        height=1000,
        title=alt.Title(
            text="pie-basic · altair · pyplots.ai",
            subtitle="Global Cloud Infrastructure Market Share",
            fontSize=28,
            subtitleFontSize=20,
            subtitleColor="#666666",
            anchor="middle",
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(padding=20, offset=10)
)

# Save as PNG (scale_factor=3 → ~3300x3150 square-ish format)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML
chart.save("plot.html")
