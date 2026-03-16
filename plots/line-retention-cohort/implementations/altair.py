""" pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: altair 6.0.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-16
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Monthly signup cohorts tracked over 12 weeks
np.random.seed(42)

cohorts = {
    "Jan 2025": {"size": 1245, "half_life": 3.5},
    "Feb 2025": {"size": 1102, "half_life": 4.0},
    "Mar 2025": {"size": 1380, "half_life": 4.8},
    "Apr 2025": {"size": 1510, "half_life": 5.5},
    "May 2025": {"size": 1423, "half_life": 6.2},
}

weeks = np.arange(0, 13)
rows = []
for cohort_label, info in cohorts.items():
    retention = 100 * np.exp(-weeks / info["half_life"])
    noise = np.concatenate([[0], np.cumsum(np.random.randn(12) * 1.5)])
    retention = np.clip(retention + noise, 5, 100)
    retention[0] = 100.0
    legend_label = f"{cohort_label} (n={info['size']:,})"
    for w, r in zip(weeks, retention, strict=True):
        rows.append({"Week": w, "Retention (%)": round(r, 1), "Cohort": legend_label})

df = pd.DataFrame(rows)

# Colors - Python Blue first, cohesive palette for 5 cohorts
colors = ["#306998", "#E15759", "#59A14F", "#EDC948", "#B07AA1"]
cohort_labels = [f"{c} (n={info['size']:,})" for c, info in cohorts.items()]

# Interactive highlight on hover
highlight = alt.selection_point(fields=["Cohort"], on="pointerover", empty=False)

# Lines - newer cohorts are thicker/more opaque
lines = (
    alt.Chart(df)
    .mark_line()
    .encode(
        x=alt.X(
            "Week:Q",
            title="Weeks Since Signup",
            scale=alt.Scale(domain=[0, 12]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, tickMinStep=1),
        ),
        y=alt.Y(
            "Retention (%):Q",
            title="Retention (%)",
            scale=alt.Scale(domain=[0, 100]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, format=".0f"),
        ),
        color=alt.Color(
            "Cohort:N",
            scale=alt.Scale(domain=cohort_labels, range=colors),
            legend=alt.Legend(title="Cohort", titleFontSize=18, labelFontSize=15, symbolStrokeWidth=4, symbolSize=200),
        ),
        strokeWidth=alt.condition(highlight, alt.value(5), alt.value(3)),
        opacity=alt.condition(highlight, alt.value(1), alt.value(0.7)),
        tooltip=["Cohort:N", "Week:Q", "Retention (%):Q"],
    )
    .add_params(highlight)
)

# Points on data values
points = (
    alt.Chart(df)
    .mark_point(filled=True)
    .encode(
        x="Week:Q",
        y="Retention (%):Q",
        color=alt.Color("Cohort:N", scale=alt.Scale(domain=cohort_labels, range=colors), legend=None),
        size=alt.condition(highlight, alt.value(180), alt.value(80)),
        opacity=alt.condition(highlight, alt.value(1), alt.value(0.6)),
        tooltip=["Cohort:N", "Week:Q", "Retention (%):Q"],
    )
)

# Reference line at 20% retention threshold
threshold_df = pd.DataFrame({"y": [20]})
threshold = alt.Chart(threshold_df).mark_rule(strokeDash=[8, 6], strokeWidth=2, color="#888888").encode(y="y:Q")

# Threshold label
threshold_label = (
    alt.Chart(threshold_df)
    .mark_text(text="20% Target", align="left", dx=5, dy=-12, fontSize=16, color="#888888")
    .encode(x=alt.value(20), y="y:Q")
)

# Combine layers
chart = (
    (threshold + threshold_label + lines + points)
    .properties(width=1600, height=900, title=alt.Title("line-retention-cohort · altair · pyplots.ai", fontSize=28))
    .configure_axis(gridColor="#E0E0E0", gridOpacity=0.2)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
