""" pyplots.ai
scatter-basic: Basic Scatter Plot
Library: altair 6.0.0 | Python 3.14
Quality: 88/100 | Created: 2025-12-22
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)
n = 100
study_hours = np.concatenate(
    [np.random.uniform(1.5, 3.5, 15), np.random.normal(5.5, 1.3, 70), np.random.uniform(7.5, 9.5, 15)]
)
exam_scores = study_hours * 7 + np.random.normal(0, 7, n) + 28
exam_scores = np.clip(exam_scores, 25, 100)

r = np.corrcoef(study_hours, exam_scores)[0, 1]
df = pd.DataFrame({"hours": study_hours, "score": exam_scores})

# Scatter points
points = (
    alt.Chart(df)
    .mark_point(filled=True, size=150, opacity=0.7, color="#306998", stroke="white", strokeWidth=0.8)
    .encode(
        x=alt.X(
            "hours:Q",
            title="Study Hours per Day (hrs)",
            scale=alt.Scale(domain=[1, 10.5], nice=False),
            axis=alt.Axis(
                tickCount=10,
                labelFontWeight="normal",
                titleColor="#333333",
                labelColor="#555555",
                tickColor="#cccccc",
                gridDash=[3, 3],
                domain=False,
            ),
        ),
        y=alt.Y(
            "score:Q",
            title="Exam Score (%)",
            scale=alt.Scale(domain=[20, 105], nice=False),
            axis=alt.Axis(
                tickCount=9,
                labelFontWeight="normal",
                titleColor="#333333",
                labelColor="#555555",
                tickColor="#cccccc",
                gridDash=[3, 3],
                domain=False,
            ),
        ),
        tooltip=[
            alt.Tooltip("hours:Q", title="Study Hours", format=".1f"),
            alt.Tooltip("score:Q", title="Exam Score (%)", format=".1f"),
        ],
    )
)

# Trend line using Altair's built-in transform_regression
trend = (
    alt.Chart(df)
    .transform_regression("hours", "score")
    .mark_line(strokeDash=[8, 6], strokeWidth=2.5, color="#7a7a7a", opacity=0.7)
    .encode(x="hours:Q", y="score:Q")
)

# Correlation annotation
mid_x = float(study_hours.mean())
mid_y = float(np.polyval(np.polyfit(study_hours, exam_scores, 1), mid_x) + 8)
annotation = (
    alt.Chart(pd.DataFrame({"x": [mid_x], "y": [mid_y], "label": [f"r = {r:.2f}"]}))
    .mark_text(fontSize=20, fontWeight="bold", color="#555555", align="center")
    .encode(x="x:Q", y="y:Q", text="label:N")
)

# Compose layers
chart = (
    (points + trend + annotation)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "scatter-basic · altair · pyplots.ai",
            fontSize=28,
            color="#222222",
            subtitle="Positive correlation between daily study hours and exam performance",
            subtitleFontSize=16,
            subtitleColor="#777777",
            subtitlePadding=6,
        ),
    )
    .configure_axis(
        labelFontSize=18, titleFontSize=22, titlePadding=12, grid=True, gridOpacity=0.15, gridColor="#cccccc"
    )
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
