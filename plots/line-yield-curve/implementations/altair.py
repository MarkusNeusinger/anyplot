"""pyplots.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: altair 6.0.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-14
"""

import altair as alt
import pandas as pd


# Data - U.S. Treasury yield curves on three dates showing normal, flat, and inverted shapes
maturities = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
maturity_years = [1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]

# Jan 2022 - Normal upward-sloping curve (pre-tightening)
yields_normal = [0.08, 0.21, 0.47, 0.78, 1.18, 1.42, 1.63, 1.78, 1.78, 2.11, 2.07]

# Jul 2023 - Inverted curve (peak inversion)
yields_inverted = [5.40, 5.49, 5.52, 5.40, 4.87, 4.56, 4.18, 4.06, 3.96, 4.22, 4.03]

# Jan 2025 - Normalizing curve (post-pivot)
yields_normalizing = [4.34, 4.35, 4.30, 4.16, 4.20, 4.25, 4.38, 4.49, 4.58, 4.87, 4.81]

records = []
for i, mat in enumerate(maturities):
    records.append(
        {
            "maturity": mat,
            "maturity_years": maturity_years[i],
            "yield_pct": yields_normal[i],
            "date": "Jan 2022 (Normal)",
            "order": 1,
        }
    )
    records.append(
        {
            "maturity": mat,
            "maturity_years": maturity_years[i],
            "yield_pct": yields_inverted[i],
            "date": "Jul 2023 (Inverted)",
            "order": 2,
        }
    )
    records.append(
        {
            "maturity": mat,
            "maturity_years": maturity_years[i],
            "yield_pct": yields_normalizing[i],
            "date": "Jan 2025 (Normalizing)",
            "order": 3,
        }
    )

df = pd.DataFrame(records)

# Inversion region shading - where short-term yields exceed long-term yields (Jul 2023)
# The inverted curve has short-term (1M-1Y) yields above long-term (10Y-30Y) yields
# Shade the region from 1M to ~7Y where the curve slopes downward
inversion_df = pd.DataFrame({"x_start": [1 / 12], "x_end": [7], "label": ["Inversion Region"]})

inversion_shade = (
    alt.Chart(inversion_df)
    .mark_rect(opacity=0.08, color="#D45B5B")
    .encode(x=alt.X("x_start:Q"), x2="x_end:Q", y=alt.value(0), y2=alt.value(900))
)

inversion_label = (
    alt.Chart(pd.DataFrame({"x": [0.8], "y": [5.85], "text": ["← Inversion Region (short > long)"]}))
    .mark_text(fontSize=16, align="left", fontStyle="italic", color="#D45B5B", fontWeight="bold")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Colorblind-safe palette: blue, orange, teal
colors = ["#306998", "#E8871E", "#3B9AB2"]
date_order = ["Jan 2022 (Normal)", "Jul 2023 (Inverted)", "Jan 2025 (Normalizing)"]

# Annotation for the peak inversion point
peak_annotation = (
    alt.Chart(pd.DataFrame({"x": [0.5], "y": [5.52], "text": ["Peak: 5.52%"]}))
    .mark_text(fontSize=15, align="left", dx=12, dy=-8, color="#E8871E", fontWeight="bold")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Shared axis config
x_axis = alt.X(
    "maturity_years:Q",
    title="Maturity (Years)",
    scale=alt.Scale(type="log", domain=[0.08, 35]),
    axis=alt.Axis(
        labelFontSize=18,
        titleFontSize=22,
        values=[1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30],
        labelExpr="datum.value < 0.09 ? '1M' : datum.value < 0.3 ? '3M' : datum.value < 0.6 ? '6M' : datum.value + 'Y'",
    ),
)

y_axis = alt.Y(
    "yield_pct:Q", title="Yield (%)", scale=alt.Scale(domain=[0, 6]), axis=alt.Axis(labelFontSize=18, titleFontSize=22)
)

color_enc = alt.Color(
    "date:N",
    scale=alt.Scale(domain=date_order, range=colors),
    legend=alt.Legend(
        title=None, labelFontSize=18, labelLimit=300, orient="top-right", symbolStrokeWidth=4, symbolSize=200
    ),
    sort=date_order,
)

# Plot layers
line = (
    alt.Chart(df)
    .mark_line(strokeWidth=4)
    .encode(
        x=x_axis, y=y_axis, color=color_enc, tooltip=["maturity:N", "yield_pct:Q", "date:N"], order="maturity_years:Q"
    )
)

points = (
    alt.Chart(df)
    .mark_point(size=150, filled=True)
    .encode(
        x="maturity_years:Q",
        y="yield_pct:Q",
        color=alt.Color("date:N", scale=alt.Scale(domain=date_order, range=colors), legend=None, sort=date_order),
        tooltip=["maturity:N", "yield_pct:Q", "date:N"],
    )
)

chart = (
    (inversion_shade + line + points + inversion_label + peak_annotation)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "U.S. Treasury Yield Curves · line-yield-curve · altair · pyplots.ai", fontSize=28, anchor="middle"
        ),
    )
    .configure_axis(gridOpacity=0.2, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.interactive().save("plot.html")
