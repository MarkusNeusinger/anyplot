""" pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: altair 6.0.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-07
"""

import altair as alt
import pandas as pd


# Data - NPV sensitivity analysis for a capital investment project
base_npv = 250.0  # Base case NPV in $M

parameters = [
    ("Discount Rate", 195.0, 320.0),
    ("Revenue Growth", 200.0, 310.0),
    ("Operating Costs", 210.0, 305.0),
    ("Terminal Value", 215.0, 295.0),
    ("CapEx Estimate", 218.0, 288.0),
    ("Tax Rate", 225.0, 280.0),
    ("Working Capital", 232.0, 272.0),
    ("Inflation Rate", 238.0, 265.0),
]

records = []
for param, low, high in parameters:
    records.append({"parameter": param, "value": low, "side": "Low Scenario", "span": abs(high - low)})
    records.append({"parameter": param, "value": high, "side": "High Scenario", "span": abs(high - low)})

df = pd.DataFrame(records)

# Sort order by total range (widest at top)
sort_order = [p for p, _, _ in sorted(parameters, key=lambda x: abs(x[2] - x[1]))]

# Plot
bars = (
    alt.Chart(df)
    .mark_bar(cornerRadius=3, height=38)
    .encode(
        x=alt.X("value:Q", title="Net Present Value ($M)", scale=alt.Scale(domain=[180, 330])),
        x2=alt.X2("base:Q"),
        y=alt.Y("parameter:N", sort=sort_order, title=None),
        color=alt.Color(
            "side:N",
            scale=alt.Scale(domain=["Low Scenario", "High Scenario"], range=["#306998", "#E8853A"]),
            title=None,
        ),
        tooltip=["parameter:N", "side:N", "value:Q"],
    )
    .transform_calculate(base=str(base_npv))
)

# Base case reference line
rule = (
    alt.Chart(pd.DataFrame({"x": [base_npv]}))
    .mark_rule(strokeDash=[6, 4], strokeWidth=2, color="#333333")
    .encode(x="x:Q")
)

# Base case label
label = (
    alt.Chart(pd.DataFrame({"x": [base_npv], "label": [f"Base Case: ${base_npv:.0f}M"]}))
    .mark_text(align="left", dx=6, dy=-140, fontSize=16, fontWeight="bold", color="#333333")
    .encode(x="x:Q", text="label:N")
)

chart = (
    (bars + rule + label)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("bar-tornado-sensitivity \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="start"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .configure_legend(labelFontSize=16, symbolSize=300, orient="bottom", direction="horizontal")
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
