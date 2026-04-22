""" pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: altair 6.0.0 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-16
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
for i, (cohort_label, info) in enumerate(cohorts.items()):
    retention = 100 * np.exp(-weeks / info["half_life"])
    noise = np.concatenate([[0], np.cumsum(np.random.randn(12) * 1.5)])
    retention = np.clip(retention + noise, 5, 100)
    retention[0] = 100.0
    legend_label = f"{cohort_label} (n={info['size']:,})"
    for w, r in zip(weeks, retention, strict=True):
        rows.append({"Week": w, "Retention (%)": round(r, 1), "Cohort": legend_label, "order": i})

df = pd.DataFrame(rows)

# Colorblind-safe palette (Tol-inspired)
cohort_labels = list(df["Cohort"].unique())
colors = ["#88CCEE", "#44AA99", "#DDCC77", "#CC6677", "#332288"]
order_domain = list(range(5))
opacity_range = [0.45, 0.59, 0.73, 0.87, 1.0]
width_range = [1.8, 2.4, 3.0, 3.6, 4.2]
size_range = [60, 90, 120, 150, 180]

# Interactive highlight on hover
highlight = alt.selection_point(fields=["Cohort"], on="pointerover", empty=False)

# Reference line at 20% retention threshold
threshold_df = pd.DataFrame({"y": [20]})
threshold = alt.Chart(threshold_df).mark_rule(strokeDash=[8, 6], strokeWidth=2, color="#666666").encode(y="y:Q")
threshold_label = (
    alt.Chart(threshold_df)
    .mark_text(text="20% Target", align="left", dx=5, dy=-12, fontSize=16, fontWeight="bold", color="#666666")
    .encode(x=alt.value(20), y="y:Q")
)

# Shared axis encodings
x_enc = alt.X(
    "Week:Q",
    title="Weeks Since Signup",
    scale=alt.Scale(domain=[0, 12]),
    axis=alt.Axis(labelFontSize=18, titleFontSize=22, tickMinStep=1),
)
y_enc = alt.Y(
    "Retention (%):Q",
    title="Retention (%)",
    scale=alt.Scale(domain=[0, 100]),
    axis=alt.Axis(labelFontSize=18, titleFontSize=22, format=".0f"),
)
color_enc = alt.Color(
    "Cohort:N",
    scale=alt.Scale(domain=cohort_labels, range=colors),
    sort=cohort_labels,
    legend=alt.Legend(title="Cohort", titleFontSize=18, labelFontSize=16, symbolStrokeWidth=4, symbolSize=200),
)

# Lines — single Chart, graduated styling via order-based scales
lines = (
    alt.Chart(df)
    .mark_line()
    .encode(
        x=x_enc,
        y=y_enc,
        color=color_enc,
        strokeWidth=alt.condition(
            highlight,
            alt.value(6),
            alt.StrokeWidth("order:O", scale=alt.Scale(domain=order_domain, range=width_range), legend=None),
        ),
        opacity=alt.condition(
            highlight,
            alt.value(1.0),
            alt.Opacity("order:O", scale=alt.Scale(domain=order_domain, range=opacity_range), legend=None),
        ),
        detail="Cohort:N",
        tooltip=["Cohort:N", "Week:Q", "Retention (%):Q"],
    )
    .add_params(highlight)
)

# Points
points = (
    alt.Chart(df)
    .mark_point(filled=True)
    .encode(
        x="Week:Q",
        y="Retention (%):Q",
        color=alt.Color("Cohort:N", scale=alt.Scale(domain=cohort_labels, range=colors), legend=None),
        opacity=alt.condition(
            highlight,
            alt.value(1.0),
            alt.Opacity("order:O", scale=alt.Scale(domain=order_domain, range=opacity_range), legend=None),
        ),
        size=alt.condition(
            highlight,
            alt.value(200),
            alt.Size("order:O", scale=alt.Scale(domain=order_domain, range=size_range), legend=None),
        ),
        tooltip=["Cohort:N", "Week:Q", "Retention (%):Q"],
    )
)

# Combine layers
chart = (
    alt.layer(threshold, threshold_label, lines, points)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "line-retention-cohort · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            subtitle="Newer cohorts retain better — product improvements are working",
            subtitleFontSize=18,
            subtitleColor="#555555",
        ),
    )
    .configure_axis(
        gridColor="#D0D0D0",
        gridOpacity=0.3,
        domainWidth=0,
        tickColor="#888888",
        labelColor="#333333",
        titleColor="#222222",
    )
    .configure_view(strokeWidth=0)
    .configure(background="#FAFAFA")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
