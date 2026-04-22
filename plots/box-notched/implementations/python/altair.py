""" pyplots.ai
box-notched: Notched Box Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Employee performance scores across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Operations"]
data = []

# Create varied distributions to showcase notched box plot features
# Engineering: high scores, tight distribution
engineering = np.random.normal(78, 8, 80)
engineering = np.clip(engineering, 50, 100)
data.extend([{"Department": "Engineering", "Performance Score": v} for v in engineering])

# Marketing: moderate scores, wider distribution with some outliers
marketing = np.concatenate(
    [
        np.random.normal(68, 12, 70),
        np.array([35, 38, 95, 98]),  # outliers
    ]
)
data.extend([{"Department": "Marketing", "Performance Score": v} for v in marketing])

# Sales: bimodal-ish, high variability
sales = np.concatenate([np.random.normal(60, 10, 40), np.random.normal(80, 8, 45)])
data.extend([{"Department": "Sales", "Performance Score": v} for v in sales])

# Operations: lower median, different from Engineering (to show non-overlapping notches)
operations = np.random.normal(62, 10, 75)
operations = np.clip(operations, 30, 95)
data.extend([{"Department": "Operations", "Performance Score": v} for v in operations])

df = pd.DataFrame(data)

# Altair does not natively support notched box plots
# We need to calculate the notch values manually and use layered marks

# Calculate statistics for each group
stats_list = []
for dept in departments:
    values = df[df["Department"] == dept]["Performance Score"].values
    q1 = np.percentile(values, 25)
    median = np.percentile(values, 50)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    n = len(values)

    # Notch calculation: ±1.57 × IQR / √n (95% CI around median)
    notch_size = 1.57 * iqr / np.sqrt(n)
    notch_lower = median - notch_size
    notch_upper = median + notch_size

    # Whiskers at 1.5*IQR
    whisker_lower = max(q1 - 1.5 * iqr, values.min())
    whisker_upper = min(q3 + 1.5 * iqr, values.max())

    # Find actual whisker endpoints (furthest non-outlier)
    non_outliers = values[(values >= q1 - 1.5 * iqr) & (values <= q3 + 1.5 * iqr)]
    whisker_lower = non_outliers.min()
    whisker_upper = non_outliers.max()

    # Outliers
    outliers = values[(values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)]

    stats_list.append(
        {
            "Department": dept,
            "q1": q1,
            "median": median,
            "q3": q3,
            "notch_lower": notch_lower,
            "notch_upper": notch_upper,
            "whisker_lower": whisker_lower,
            "whisker_upper": whisker_upper,
            "outliers": outliers.tolist(),
        }
    )

stats_df = pd.DataFrame(stats_list)

# Prepare outlier data
outlier_data = []
for _, row in stats_df.iterrows():
    for outlier in row["outliers"]:
        outlier_data.append({"Department": row["Department"], "Performance Score": outlier})
outliers_df = pd.DataFrame(outlier_data) if outlier_data else pd.DataFrame(columns=["Department", "Performance Score"])

# Color scale - Python Blue as primary, varied for categories
colors = ["#306998", "#FFD43B", "#4B8BBE", "#E85C41"]
color_scale = alt.Scale(domain=departments, range=colors)

# Box (from Q1 to notch_lower, then notch_lower to notch_upper, then notch_upper to Q3)
# For a notched box, we draw two rectangles: lower box and upper box with a narrower waist at the notch

# Lower box: Q1 to notch_lower (full width)
lower_box = (
    alt.Chart(stats_df)
    .mark_bar(size=60, stroke="black", strokeWidth=2)
    .encode(
        x=alt.X("Department:N", title="Department", axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0)),
        y=alt.Y("q1:Q", title="Performance Score"),
        y2="notch_lower:Q",
        color=alt.Color("Department:N", scale=color_scale, legend=None),
    )
)

# Upper box: notch_upper to Q3 (full width)
upper_box = (
    alt.Chart(stats_df)
    .mark_bar(size=60, stroke="black", strokeWidth=2)
    .encode(
        x="Department:N", y="notch_upper:Q", y2="q3:Q", color=alt.Color("Department:N", scale=color_scale, legend=None)
    )
)

# Notch area: narrower bar from notch_lower to notch_upper
notch_box = (
    alt.Chart(stats_df)
    .mark_bar(size=35, stroke="black", strokeWidth=2)
    .encode(
        x="Department:N",
        y="notch_lower:Q",
        y2="notch_upper:Q",
        color=alt.Color("Department:N", scale=color_scale, legend=None),
    )
)

# Median line (inside the notch)
median_line = alt.Chart(stats_df).mark_tick(color="white", size=35, thickness=3).encode(x="Department:N", y="median:Q")

# Whiskers - vertical lines
whisker_rule = (
    alt.Chart(stats_df)
    .mark_rule(strokeWidth=2, color="black")
    .encode(x="Department:N", y="whisker_lower:Q", y2="whisker_upper:Q")
)

# Whisker caps - horizontal ticks at whisker ends
lower_cap = (
    alt.Chart(stats_df).mark_tick(size=30, thickness=2, color="black").encode(x="Department:N", y="whisker_lower:Q")
)

upper_cap = (
    alt.Chart(stats_df).mark_tick(size=30, thickness=2, color="black").encode(x="Department:N", y="whisker_upper:Q")
)

# Outliers
outliers_chart = (
    alt.Chart(outliers_df)
    .mark_point(size=120, filled=True, opacity=0.8)
    .encode(
        x="Department:N",
        y=alt.Y("Performance Score:Q"),
        color=alt.Color("Department:N", scale=color_scale, legend=None),
    )
    if len(outliers_df) > 0
    else alt.Chart(pd.DataFrame()).mark_point()
)

# Layer all elements
chart = (
    alt.layer(whisker_rule, lower_cap, upper_cap, lower_box, upper_box, notch_box, median_line, outliers_chart)
    .properties(
        width=1600, height=900, title=alt.Title("box-notched · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG (4800x2700 with scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.save("plot.html")
