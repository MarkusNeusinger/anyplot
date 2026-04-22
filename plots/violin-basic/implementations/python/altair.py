""" pyplots.ai
violin-basic: Basic Violin Plot
Library: altair 6.0.0 | Python 3.14.3
Quality: 94/100 | Updated: 2026-02-21
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Salary distributions by department with varied shapes
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "Support"]
data = []

for cat in categories:
    if cat == "Engineering":
        values = np.random.normal(92000, 16000, 150)
    elif cat == "Marketing":
        values = np.random.normal(70000, 13000, 150)
    elif cat == "Sales":
        # Bimodal: base salary + high performers with commissions
        values = np.concatenate([np.random.normal(50000, 8000, 75), np.random.normal(92000, 11000, 75)])
    else:  # Support
        values = np.random.normal(55000, 10000, 150)

    for v in values:
        data.append({"Department": cat, "Salary": v})

df = pd.DataFrame(data)

# Department order: unimodal distributions first, bimodal Sales last as focal point
dept_order = ["Support", "Marketing", "Engineering", "Sales"]

# Colors - four fully distinct colorblind-safe hues with Python Blue
# brown, purple, Python Blue, orange — each maximally distinct
palette = ["#8B6C42", "#9467BD", "#306998", "#E5832D"]
color_scale = alt.Scale(domain=dept_order, range=palette)

base = alt.Chart(df)

# Violin shape using kernel density transform
violin = (
    base.transform_density(
        density="Salary",
        as_=["Salary", "density"],
        groupby=["Department"],
        extent=[df["Salary"].min() - 8000, df["Salary"].max() + 8000],
    )
    .mark_area(orient="horizontal", opacity=0.75)
    .encode(
        y=alt.Y("Salary:Q", title="Salary ($)"),
        x=alt.X(
            "density:Q",
            stack="center",
            impute=None,
            title=None,
            axis=alt.Axis(labels=False, values=[0], grid=False, ticks=False),
        ),
        color=alt.Color("Department:N", scale=color_scale, legend=None),
        tooltip=[alt.Tooltip("Department:N"), alt.Tooltip("Salary:Q", format="$,.0f")],
    )
)

# IQR rule via declarative aggregate (one rule per department)
quartile_rule = (
    base.transform_aggregate(q1="q1(Salary)", q3="q3(Salary)", groupby=["Department"])
    .mark_rule(color="#1a1a1a", strokeWidth=5)
    .encode(y="q1:Q", y2="q3:Q")
)

# Median point via declarative aggregate (one dot per department)
median_point = (
    base.transform_aggregate(med="median(Salary)", groupby=["Department"])
    .mark_point(color="white", size=250, filled=True, strokeWidth=3, stroke="#1a1a1a")
    .encode(
        y="med:Q", tooltip=[alt.Tooltip("Department:N"), alt.Tooltip("med:Q", title="Median Salary", format="$,.0f")]
    )
)

# Combine layers and facet by department
chart = (
    alt.layer(violin, quartile_rule, median_point)
    .facet(
        column=alt.Column(
            "Department:N",
            header=alt.Header(labelFontSize=20, labelOrient="bottom", title=None, labelPadding=15),
            sort=dept_order,
        )
    )
    .resolve_scale(x="independent")
    .properties(title=alt.Title("violin-basic · altair · pyplots.ai", fontSize=28, anchor="middle"))
    .configure_facet(spacing=20)
    .configure_view(stroke=None, continuousWidth=350, continuousHeight=750)
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.2, gridDash=[3, 3])
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
