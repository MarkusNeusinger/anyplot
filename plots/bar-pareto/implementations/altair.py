"""pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: altair 6.0.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-20
"""

import altair as alt
import pandas as pd


# Data - Manufacturing defect analysis
defects = pd.DataFrame(
    {
        "category": [
            "Scratches",
            "Dents",
            "Misalignment",
            "Cracks",
            "Discoloration",
            "Burrs",
            "Warping",
            "Contamination",
            "Missing Parts",
            "Wrong Dimensions",
        ],
        "count": [187, 128, 95, 72, 54, 38, 27, 19, 12, 8],
    }
)

# Sort descending and compute cumulative percentage
defects = defects.sort_values("count", ascending=False).reset_index(drop=True)
total = defects["count"].sum()
defects["cumulative_pct"] = defects["count"].cumsum() / total * 100

# Mark vital few (categories contributing up to ~80%) vs trivial many
defects["vital_few"] = defects["cumulative_pct"].shift(1, fill_value=0) < 80
sort_order = defects["category"].tolist()

# 80% threshold reference data
threshold_df = pd.DataFrame({"pct": [80]})

# Bars - color-coded by vital few (dark blue) vs trivial many (light gray-blue)
bars = (
    alt.Chart(defects)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X(
            "category:N",
            title="Defect Type",
            sort=sort_order,
            axis=alt.Axis(labelAngle=-45, labelFontSize=18, titleFontSize=22),
        ),
        y=alt.Y("count:Q", title="Frequency", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        color=alt.condition(alt.datum.vital_few, alt.value("#306998"), alt.value("#A8C4D9")),
        tooltip=[
            alt.Tooltip("category:N", title="Defect"),
            alt.Tooltip("count:Q", title="Count"),
            alt.Tooltip("cumulative_pct:Q", title="Cumulative %", format=".1f"),
        ],
    )
)

# Cumulative percentage line on secondary y-axis (colorblind-safe dark orange)
line = (
    alt.Chart(defects)
    .mark_line(
        color="#D4770B",
        strokeWidth=3,
        point=alt.OverlayMarkDef(color="#D4770B", size=120, filled=True, stroke="white", strokeWidth=2),
    )
    .encode(
        x=alt.X("category:N", sort=sort_order),
        y=alt.Y(
            "cumulative_pct:Q",
            title="Cumulative Percentage (%)",
            scale=alt.Scale(domain=[0, 105]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, titleColor="#D4770B", labelColor="#D4770B", format=".0f"),
        ),
        tooltip=[
            alt.Tooltip("category:N", title="Defect"),
            alt.Tooltip("cumulative_pct:Q", title="Cumulative %", format=".1f"),
        ],
    )
)

# 80% threshold reference line
rule = (
    alt.Chart(threshold_df)
    .mark_rule(strokeDash=[8, 6], strokeWidth=2, color="#888888")
    .encode(y=alt.Y("pct:Q", scale=alt.Scale(domain=[0, 105])))
)

# 80% label
rule_label = (
    alt.Chart(pd.DataFrame({"pct": [80], "label": ["80%"]}))
    .mark_text(align="left", dx=5, dy=-10, fontSize=18, fontWeight="bold", color="#888888")
    .encode(x=alt.value(10), y=alt.Y("pct:Q", scale=alt.Scale(domain=[0, 105])), text="label:N")
)

# Combine layers: bars use left y-axis, line/rule use right y-axis
chart = (
    alt.layer(bars, line + rule + rule_label)
    .resolve_scale(y="independent")
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            text="Manufacturing Defect Analysis · bar-pareto · altair · pyplots.ai",
            subtitle="Vital few defects (dark) account for 80% of all occurrences",
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#666666",
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False)
    .configure_axisY(grid=True, gridOpacity=0.15, gridDash=[4, 4])
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
