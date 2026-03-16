"""pyplots.ai
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
    "Jan 2025": {"size": 1245, "half_life": 3.5, "order": 0},
    "Feb 2025": {"size": 1102, "half_life": 4.0, "order": 1},
    "Mar 2025": {"size": 1380, "half_life": 4.8, "order": 2},
    "Apr 2025": {"size": 1510, "half_life": 5.5, "order": 3},
    "May 2025": {"size": 1423, "half_life": 6.2, "order": 4},
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
        rows.append({"Week": w, "Retention (%)": round(r, 1), "Cohort": legend_label, "order": info["order"]})

df = pd.DataFrame(rows)

# Colorblind-safe palette: blue → teal → amber → orange → deep blue
# Avoids red-green distinction, uses luminance + hue variation
colors = ["#88CCEE", "#44AA99", "#DDCC77", "#CC6677", "#332288"]
cohort_labels = [f"{c} (n={info['size']:,})" for c, info in cohorts.items()]

# Graduated opacity and stroke width: older cohorts fade, newer ones pop
opacity_map = {0: 0.35, 1: 0.50, 2: 0.65, 3: 0.80, 4: 1.0}
width_map = {0: 1.5, 1: 2.0, 2: 2.5, 3: 3.0, 4: 4.0}

# Interactive highlight on hover
highlight = alt.selection_point(fields=["Cohort"], on="pointerover", empty=False)

# Build per-cohort line + point layers for graduated styling
layers = []
for cohort_label, info in cohorts.items():
    label = f"{cohort_label} (n={info['size']:,})"
    idx = info["order"]
    cohort_df = df[df["Cohort"] == label]

    line = (
        alt.Chart(cohort_df)
        .mark_line(strokeWidth=width_map[idx], opacity=opacity_map[idx])
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
                legend=alt.Legend(
                    title="Cohort", titleFontSize=18, labelFontSize=15, symbolStrokeWidth=4, symbolSize=200
                ),
            ),
            strokeWidth=alt.condition(highlight, alt.value(6), alt.value(width_map[idx])),
            opacity=alt.condition(highlight, alt.value(1.0), alt.value(opacity_map[idx])),
            tooltip=["Cohort:N", "Week:Q", "Retention (%):Q"],
        )
        .add_params(highlight)
    )

    point = (
        alt.Chart(cohort_df)
        .mark_point(filled=True, size=60 + idx * 30)
        .encode(
            x="Week:Q",
            y="Retention (%):Q",
            color=alt.Color("Cohort:N", scale=alt.Scale(domain=cohort_labels, range=colors), legend=None),
            opacity=alt.condition(highlight, alt.value(1.0), alt.value(opacity_map[idx])),
            size=alt.condition(highlight, alt.value(200), alt.value(60 + idx * 30)),
            tooltip=["Cohort:N", "Week:Q", "Retention (%):Q"],
        )
    )

    layers.extend([line, point])

# Reference line at 20% retention threshold
threshold_df = pd.DataFrame({"y": [20]})
threshold = alt.Chart(threshold_df).mark_rule(strokeDash=[8, 6], strokeWidth=2, color="#666666").encode(y="y:Q")

# Threshold label
threshold_label = (
    alt.Chart(threshold_df)
    .mark_text(text="20% Target", align="left", dx=5, dy=-12, fontSize=16, fontWeight="bold", color="#666666")
    .encode(x=alt.value(20), y="y:Q")
)

# Combine layers
chart = (
    alt.layer(threshold, threshold_label, *layers)
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
        domainColor="#888888",
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
