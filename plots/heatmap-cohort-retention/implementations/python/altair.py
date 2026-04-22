""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-16
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

# Custom dark teal-to-gold diverging-inspired sequential palette for sophistication
color_domain = [0, 20, 40, 60, 80, 100]
color_range = ["#f7f7f7", "#d4e8e0", "#7bc8b5", "#2a9d8f", "#264653", "#1d3557"]

# Heatmap rectangles
heatmap = (
    alt.Chart(df)
    .mark_rect(stroke="#e8e8e8", strokeWidth=1.5, cornerRadius=3)
    .encode(
        x=alt.X(
            "period_label:O",
            title="Months Since Signup",
            sort=period_order,
            axis=alt.Axis(
                labelFontSize=17,
                titleFontSize=22,
                titleFontWeight="bold",
                labelAngle=0,
                domainWidth=0,
                tickWidth=0,
                titlePadding=16,
                labelPadding=8,
            ),
        ),
        y=alt.Y(
            "cohort_label:O",
            title="Signup Cohort",
            sort=cohort_order,
            axis=alt.Axis(
                labelFontSize=17,
                titleFontSize=22,
                titleFontWeight="bold",
                domainWidth=0,
                tickWidth=0,
                titlePadding=16,
                labelPadding=8,
            ),
        ),
        color=alt.Color(
            "retention_rate:Q",
            scale=alt.Scale(domain=color_domain, range=color_range),
            legend=alt.Legend(
                title="Retention %",
                titleFontSize=18,
                titleFontWeight="bold",
                labelFontSize=16,
                gradientLength=400,
                gradientThickness=18,
                orient="right",
                offset=12,
            ),
        ),
        tooltip=[
            alt.Tooltip("cohort:N", title="Cohort"),
            alt.Tooltip("period_label:O", title="Period"),
            alt.Tooltip("retention_rate:Q", title="Retention %", format=".1f"),
        ],
    )
)

# Text annotations with suffix
text = (
    alt.Chart(df)
    .mark_text(fontSize=15, fontWeight="bold")
    .encode(
        x=alt.X("period_label:O", sort=period_order),
        y=alt.Y("cohort_label:O", sort=cohort_order),
        text=alt.Text("retention_rate:Q", format=".1f"),
        color=alt.condition(alt.datum.retention_rate > 50, alt.value("white"), alt.value("#333333")),
    )
)

# Percent symbol as separate smaller text layer for polish
pct = (
    alt.Chart(df)
    .mark_text(fontSize=10, fontWeight="normal", dx=20)
    .encode(
        x=alt.X("period_label:O", sort=period_order),
        y=alt.Y("cohort_label:O", sort=cohort_order),
        text=alt.value("%"),
        color=alt.condition(
            alt.datum.retention_rate > 50, alt.value("rgba(255,255,255,0.7)"), alt.value("rgba(51,51,51,0.5)")
        ),
    )
)

# Combine
chart = (
    alt.layer(heatmap, text, pct)
    .properties(
        width=1400,
        height=900,
        title=alt.Title(
            "heatmap-cohort-retention · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            anchor="middle",
            subtitle="Monthly SaaS user retention — earliest cohorts show strongest long-term engagement",
            subtitleFontSize=18,
            subtitleColor="#666666",
            subtitlePadding=8,
        ),
    )
    .configure_view(strokeWidth=0)
    .configure(padding={"left": 20, "right": 20, "top": 20, "bottom": 20}, background="#ffffff")
    .configure_axis(labelColor="#444444", titleColor="#333333")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
