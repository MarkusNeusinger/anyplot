""" pyplots.ai
violin-split: Split Violin Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Test scores (%) by department comparing control vs treatment groups
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "HR"]
data = []

for dept in departments:
    # Control group - baseline performance
    if dept == "Engineering":
        control_scores = np.random.normal(72, 12, 100)
        treatment_scores = np.random.normal(85, 10, 100)  # Larger improvement
    elif dept == "Marketing":
        control_scores = np.random.normal(68, 15, 100)
        treatment_scores = np.random.normal(78, 12, 100)
    elif dept == "Sales":
        control_scores = np.random.normal(75, 14, 100)
        treatment_scores = np.random.normal(80, 11, 100)
    else:  # HR
        control_scores = np.random.normal(70, 10, 100)
        treatment_scores = np.random.normal(76, 9, 100)

    for score in control_scores:
        data.append({"Department": dept, "Score (%)": np.clip(score, 30, 100), "Group": "Control"})
    for score in treatment_scores:
        data.append({"Department": dept, "Score (%)": np.clip(score, 30, 100), "Group": "Treatment"})

df = pd.DataFrame(data)

# Calculate quartile statistics for inner markers
quartile_data = (
    df.groupby(["Department", "Group"])["Score (%)"]
    .agg(median="median", q1=lambda x: x.quantile(0.25), q3=lambda x: x.quantile(0.75))
    .reset_index()
)

# Merge quartile data back to main dataframe so we have a single data source
df_with_quartiles = df.merge(quartile_data, on=["Department", "Group"])

# Create split violin using density transform with xOffset for split
base = alt.Chart().transform_density(
    density="Score (%)", as_=["Score (%)", "density"], groupby=["Department", "Group"], extent=[30, 100]
)

# For split violin: Control goes left (negative), Treatment goes right (positive)
split_violin = (
    base.transform_calculate(signed_density="datum.Group === 'Control' ? -datum.density : datum.density")
    .mark_area(orient="horizontal", opacity=0.8)
    .encode(
        x=alt.X("signed_density:Q", title=None, axis=alt.Axis(labels=False, ticks=False, domain=False), stack=None),
        y=alt.Y("Score (%):Q", title="Score (%)", scale=alt.Scale(domain=[30, 100])),
        color=alt.Color(
            "Group:N",
            scale=alt.Scale(domain=["Control", "Treatment"], range=["#306998", "#FFD43B"]),
            legend=alt.Legend(title="Group", titleFontSize=18, labelFontSize=16, symbolSize=400, orient="right"),
        ),
    )
)

# IQR rule (vertical line from q1 to q3) - uses aggregate values from data
iqr_rule = (
    alt.Chart()
    .transform_aggregate(q1="min(q1)", q3="max(q3)", groupby=["Department", "Group"])
    .mark_rule(size=5, opacity=0.9)
    .encode(
        y=alt.Y("q1:Q", scale=alt.Scale(domain=[30, 100])),
        y2="q3:Q",
        xOffset=alt.XOffset("Group:N", scale=alt.Scale(domain=["Control", "Treatment"], range=[-20, 20])),
        color=alt.Color("Group:N", scale=alt.Scale(domain=["Control", "Treatment"], range=["#1a3d5c", "#b8941a"])),
    )
)

# Median point marker (diamond shape for visibility)
median_marker = (
    alt.Chart()
    .transform_aggregate(median="min(median)", groupby=["Department", "Group"])
    .mark_point(size=120, filled=True, shape="diamond", opacity=1)
    .encode(
        y=alt.Y("median:Q", scale=alt.Scale(domain=[30, 100])),
        xOffset=alt.XOffset("Group:N", scale=alt.Scale(domain=["Control", "Treatment"], range=[-20, 20])),
        color=alt.value("white"),
        stroke=alt.Color("Group:N", scale=alt.Scale(domain=["Control", "Treatment"], range=["#1a3d5c", "#b8941a"])),
        strokeWidth=alt.value(2),
    )
)

# Layer violin, IQR, and median markers with shared data
layered = alt.layer(split_violin, iqr_rule, median_marker, data=df_with_quartiles)

# Facet by department with better aspect ratio
chart = (
    layered.properties(width=300, height=380)
    .facet(column=alt.Column("Department:N", title=None, header=alt.Header(labelFontSize=20, labelPadding=15)))
    .resolve_scale(x="independent")
    .properties(title=alt.Title("violin-split · altair · pyplots.ai", fontSize=28))
    .configure_facet(spacing=50)
    .configure_view(stroke=None)
    .configure_axis(labelFontSize=16, titleFontSize=20, titlePadding=15)
    .configure_title(anchor="middle", offset=20)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
