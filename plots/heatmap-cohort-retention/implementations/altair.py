""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: altair 6.0.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-16
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)

cohort_labels = [
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
]
n_cohorts = len(cohort_labels)
n_periods = 10
cohort_sizes = np.random.randint(800, 2500, size=n_cohorts)

# Build retention data with realistic decay patterns
rows = []
for i, cohort in enumerate(cohort_labels):
    max_periods = n_cohorts - i
    base_retention = 100.0
    for period in range(max_periods):
        if period == 0:
            retention = 100.0
        elif period == 1:
            retention = np.random.uniform(55, 72)
        else:
            decay = np.random.uniform(0.85, 0.95)
            retention = rows[-1]["retention_rate"] * decay
            retention += np.random.uniform(-2, 2)
            retention = max(5, min(retention, 100))
        rows.append(
            {
                "cohort": cohort,
                "cohort_label": f"{cohort} (n={cohort_sizes[i]:,})",
                "period": period,
                "period_label": f"Month {period}",
                "retention_rate": round(retention, 1),
            }
        )

df = pd.DataFrame(rows)

# Sort orders
cohort_order = [f"{c} (n={s:,})" for c, s in zip(cohort_labels, cohort_sizes, strict=True)]
period_order = [f"Month {p}" for p in range(n_periods)]

# Heatmap rectangles
heatmap = (
    alt.Chart(df)
    .mark_rect(stroke="white", strokeWidth=2.5)
    .encode(
        x=alt.X(
            "period_label:O",
            title="Months Since Signup",
            sort=period_order,
            axis=alt.Axis(labelFontSize=17, titleFontSize=22, labelAngle=0),
        ),
        y=alt.Y(
            "cohort_label:O",
            title="Signup Cohort",
            sort=cohort_order,
            axis=alt.Axis(labelFontSize=15, titleFontSize=22),
        ),
        color=alt.Color(
            "retention_rate:Q",
            scale=alt.Scale(scheme="blues", domain=[0, 100]),
            legend=alt.Legend(title="Retention %", titleFontSize=18, labelFontSize=16, gradientLength=400),
        ),
    )
)

# Text annotations inside cells
text = (
    alt.Chart(df)
    .mark_text(fontSize=16, fontWeight="bold")
    .encode(
        x=alt.X("period_label:O", sort=period_order),
        y=alt.Y("cohort_label:O", sort=cohort_order),
        text=alt.Text("retention_rate:Q", format=".1f"),
        color=alt.condition(alt.datum.retention_rate > 55, alt.value("white"), alt.value("#333333")),
    )
)

# Combine
chart = (
    (heatmap + text)
    .properties(
        width=1400,
        height=900,
        title=alt.Title("heatmap-cohort-retention · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
