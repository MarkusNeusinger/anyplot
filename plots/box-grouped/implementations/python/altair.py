""" pyplots.ai
box-grouped: Grouped Box Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Employee performance scores across departments and experience levels
np.random.seed(42)

departments = ["Engineering", "Sales", "Marketing", "Support"]
experience_levels = ["Junior", "Mid", "Senior"]

data = []
# Create varied distributions for each combination
distributions = {
    ("Engineering", "Junior"): (65, 12),
    ("Engineering", "Mid"): (75, 10),
    ("Engineering", "Senior"): (85, 8),
    ("Sales", "Junior"): (55, 15),
    ("Sales", "Mid"): (70, 12),
    ("Sales", "Senior"): (80, 10),
    ("Marketing", "Junior"): (60, 14),
    ("Marketing", "Mid"): (72, 11),
    ("Marketing", "Senior"): (82, 9),
    ("Support", "Junior"): (58, 13),
    ("Support", "Mid"): (68, 12),
    ("Support", "Senior"): (78, 10),
}

for dept in departments:
    for exp in experience_levels:
        mean, std = distributions[(dept, exp)]
        n_samples = 50
        values = np.random.normal(mean, std, n_samples)
        # Add some outliers
        if np.random.random() > 0.5:
            values = np.append(values, [mean + 3.5 * std, mean - 3 * std])
        # Clip to realistic range
        values = np.clip(values, 0, 100)
        for v in values:
            data.append({"Department": dept, "Experience": exp, "Performance Score": v})

df = pd.DataFrame(data)

# Create grouped box plot
chart = (
    alt.Chart(df)
    .mark_boxplot(size=60, median={"stroke": "white", "strokeWidth": 2}, outliers={"size": 80})
    .encode(
        x=alt.X("Department:N", title="Department", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y(
            "Performance Score:Q",
            title="Performance Score (%)",
            scale=alt.Scale(domain=[0, 105]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        color=alt.Color(
            "Experience:N",
            title="Experience Level",
            scale=alt.Scale(domain=["Junior", "Mid", "Senior"], range=["#306998", "#FFD43B", "#4ECDC4"]),
            legend=alt.Legend(titleFontSize=20, labelFontSize=18, symbolSize=300, orient="right"),
        ),
        xOffset="Experience:N",
    )
    .properties(
        width=1400, height=800, title=alt.Title(text="box-grouped · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
)

# Save as PNG (scale_factor=3 for 4800x2700 target, adjusted for 1600x900 base)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
