""" pyplots.ai
swarm-basic: Basic Swarm Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Employee performance scores across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "HR"]
n_per_dept = [45, 38, 52, 35]

data = []
for dept, n in zip(departments, n_per_dept, strict=True):
    if dept == "Engineering":
        # Higher scores, tighter distribution
        scores = np.random.normal(78, 8, n)
    elif dept == "Marketing":
        # Medium scores, wider spread
        scores = np.random.normal(72, 12, n)
    elif dept == "Sales":
        # Bimodal distribution (some high performers, some struggling)
        scores = np.concatenate([np.random.normal(65, 6, n // 2), np.random.normal(82, 5, n - n // 2)])
    else:  # HR
        # Lower mean, moderate spread with some outliers
        scores = np.concatenate(
            [
                np.random.normal(68, 9, n - 3),
                np.array([45, 92, 95]),  # outliers
            ]
        )

    scores = np.clip(scores, 30, 100)  # Keep scores in valid range
    for score in scores:
        data.append({"Department": dept, "Performance Score": score})

df = pd.DataFrame(data)

# Calculate jitter for swarm effect (spread points horizontally within categories)
df["jitter"] = 0.0
for dept in departments:
    mask = df["Department"] == dept
    dept_scores = df.loc[mask, "Performance Score"].values
    n = len(dept_scores)

    # Sort indices by score value to place similar values near each other
    sorted_idx = np.argsort(dept_scores)
    jitter_values = np.zeros(n)

    # Assign jitter based on local density
    for _i, idx in enumerate(sorted_idx):
        score = dept_scores[idx]
        # Count nearby points
        nearby = np.sum(np.abs(dept_scores - score) < 3)
        # Spread based on position in local cluster
        local_pos = np.sum((dept_scores <= score) & (np.abs(dept_scores - score) < 3))
        jitter_values[idx] = (local_pos - nearby / 2) * 0.08

    df.loc[mask, "jitter"] = jitter_values

# Create numeric x positions for departments
dept_positions = {dept: i for i, dept in enumerate(departments)}
df["x_pos"] = df["Department"].map(dept_positions) + df["jitter"]

# Calculate mean for each department
means = df.groupby("Department")["Performance Score"].mean().reset_index()
means["x_pos"] = means["Department"].map(dept_positions)

# Colors - Python palette
colors = ["#306998", "#FFD43B", "#4B8BBE", "#646464"]

# Create swarm chart
swarm = (
    alt.Chart(df)
    .mark_circle(size=180, opacity=0.7)
    .encode(
        x=alt.X(
            "x_pos:Q",
            scale=alt.Scale(domain=[-0.6, 3.6]),
            axis=alt.Axis(
                values=list(range(4)),
                labelExpr="['Engineering', 'Marketing', 'Sales', 'HR'][datum.value]",
                title="Department",
                labelFontSize=18,
                titleFontSize=22,
                labelAngle=0,
            ),
        ),
        y=alt.Y(
            "Performance Score:Q", scale=alt.Scale(domain=[25, 105]), axis=alt.Axis(labelFontSize=18, titleFontSize=22)
        ),
        color=alt.Color(
            "Department:N",
            scale=alt.Scale(domain=departments, range=colors),
            legend=alt.Legend(titleFontSize=18, labelFontSize=16, orient="right"),
        ),
        tooltip=["Department", "Performance Score"],
    )
)

# Add mean markers
mean_markers = (
    alt.Chart(means)
    .mark_point(shape="diamond", size=400, filled=True, color="#000000", strokeWidth=2)
    .encode(
        x="x_pos:Q",
        y="Performance Score:Q",
        tooltip=[alt.Tooltip("Department"), alt.Tooltip("Performance Score:Q", title="Mean", format=".1f")],
    )
)

# Mean horizontal lines for reference
mean_lines = (
    alt.Chart(means)
    .mark_rule(color="#000000", strokeWidth=2, strokeDash=[4, 4])
    .encode(x=alt.X("x_start:Q"), x2="x_end:Q", y="Performance Score:Q")
    .transform_calculate(x_start="datum.x_pos - 0.35", x_end="datum.x_pos + 0.35")
)

# Combine layers
chart = (
    (swarm + mean_lines + mean_markers)
    .properties(
        width=1400, height=800, title=alt.Title("swarm-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(gridColor="#E0E0E0", gridOpacity=0.3, domainColor="#666666")
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
