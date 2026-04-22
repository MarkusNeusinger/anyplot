""" pyplots.ai
box-basic: Basic Box Plot
Library: altair 6.0.0 | Python 3.14
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - salary distributions across departments
np.random.seed(42)
departments = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
params = {
    "Engineering": (95000, 15000, 80),
    "Marketing": (72000, 12000, 65),
    "Sales": (68000, 18000, 90),
    "HR": (63000, 9000, 55),
    "Finance": (85000, 13000, 70),
}

records = []
for dept, (mean, std, n) in params.items():
    salaries = np.random.normal(mean, std, n)
    salaries = np.clip(salaries, 25000, None)
    for s in salaries:
        records.append({"Department": dept, "Salary": round(s, -2)})

df = pd.DataFrame(records)

# Compute summary statistics for annotations
summary = df.groupby("Department")["Salary"].agg(["median", "std", "min", "max"])
highest_dept = summary["median"].idxmax()
lowest_dept = summary["median"].idxmin()
widest_dept = summary["std"].idxmax()

# Color palette - Python Blue first, then cohesive colorblind-safe tones
colors = ["#306998", "#E5A835", "#4B8BBE", "#7B6D8D", "#2A9D8F"]

# Annotation data for key insights
annotations = pd.DataFrame(
    [
        {
            "Department": highest_dept,
            "y": summary.loc[highest_dept, "max"] + 5000,
            "text": f"\u2191 Highest median: ${summary.loc[highest_dept, 'median']:,.0f}",
        },
        {
            "Department": lowest_dept,
            "y": summary.loc[lowest_dept, "min"] - 5000,
            "text": f"\u2193 Lowest median: ${summary.loc[lowest_dept, 'median']:,.0f}",
        },
        {
            "Department": widest_dept,
            "y": summary.loc[widest_dept, "max"] + 7000,
            "text": f"\u2194 Widest spread (SD ${summary.loc[widest_dept, 'std']:,.0f})",
        },
    ]
)

# Shared x-axis encoding
x_enc = alt.X(
    "Department:N",
    title="Department",
    sort=departments,
    axis=alt.Axis(
        labelFontSize=18, titleFontSize=22, labelAngle=0, domainColor="#999999", tickColor="#999999", titlePadding=12
    ),
)

# Box plot layer
boxes = (
    alt.Chart(df)
    .mark_boxplot(
        size=80,
        median={"stroke": "white", "strokeWidth": 3},
        outliers={"size": 120, "strokeWidth": 1.5, "filled": True, "opacity": 0.7},
    )
    .encode(
        x=x_enc,
        y=alt.Y(
            "Salary:Q",
            title="Salary ($)",
            scale=alt.Scale(domain=[25000, 148000]),
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                format="$,.0f",
                gridOpacity=0.15,
                gridDash=[3, 3],
                domainColor="#999999",
                tickColor="#999999",
                tickCount=8,
                titlePadding=12,
            ),
        ),
        color=alt.Color("Department:N", scale=alt.Scale(domain=departments, range=colors), legend=None),
        tooltip=[
            alt.Tooltip("Department:N"),
            alt.Tooltip("median(Salary):Q", title="Median Salary", format="$,.0f"),
            alt.Tooltip("q1(Salary):Q", title="Q1", format="$,.0f"),
            alt.Tooltip("q3(Salary):Q", title="Q3", format="$,.0f"),
        ],
    )
)

# Annotation text layer (no interactive selection to avoid signal conflict)
annotation_text = (
    alt.Chart(annotations)
    .mark_text(fontSize=14, fontWeight="bold", color="#444444", align="center")
    .encode(x=alt.X("Department:N", sort=departments), y=alt.Y("y:Q"), text=alt.Text("text:N"))
)

# Combine layers with resolve_scale to avoid signal conflicts
chart = (
    alt.layer(boxes, annotation_text)
    .resolve_scale(x="shared", y="shared")
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "box-basic \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            subtitle="Salary distributions across five departments",
            subtitleFontSize=18,
            subtitleColor="#666666",
            anchor="start",
            offset=12,
        ),
    )
    .configure_axis(grid=True, gridOpacity=0.15, gridColor="#CCCCCC")
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
