""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-09
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Cumulative paid claims triangle (10 accident years x 10 development periods)
np.random.seed(42)
accident_years = list(range(2015, 2025))
dev_periods = list(range(1, 11))
n_years = len(accident_years)

# Base initial claims per accident year (increasing trend)
base_claims = np.array([3200, 3500, 3800, 4100, 3900, 4300, 4600, 4200, 4800, 5100]) * 1000

# Age-to-age development factors (decreasing as claims mature)
dev_factors = [2.50, 1.45, 1.22, 1.12, 1.07, 1.04, 1.025, 1.015, 1.008]

# Build the full cumulative triangle
cumulative = np.zeros((n_years, len(dev_periods)))
for i in range(n_years):
    cumulative[i, 0] = base_claims[i] + np.random.normal(0, base_claims[i] * 0.05)
    for j in range(1, len(dev_periods)):
        noise = 1 + np.random.normal(0, 0.01)
        cumulative[i, j] = cumulative[i, j - 1] * dev_factors[j - 1] * noise

# Build long-form dataframe; actual if year_index + dev_index < n_years
rows = []
for i, year in enumerate(accident_years):
    for j, period in enumerate(dev_periods):
        is_projected = (i + j) >= n_years
        amount = round(cumulative[i, j])
        label = f"{amount / 1e6:.1f}M" if amount >= 1e6 else f"{amount / 1e3:.0f}K"
        rows.append(
            {
                "Accident Year": str(year),
                "Development Period": period,
                "Cumulative Amount": amount,
                "Status": "Projected (IBNR)" if is_projected else "Actual",
                "Label": label,
            }
        )

df = pd.DataFrame(rows)

# Legend entries for actual vs projected status
legend_data = pd.DataFrame(
    [{"legend_label": "Actual (Observed)", "legend_order": 0}, {"legend_label": "Projected (IBNR)", "legend_order": 1}]
)

# Development factors row
factor_rows = []
for j, factor in enumerate(dev_factors):
    factor_rows.append({"Accident Year": "Dev Factor", "Development Period": j + 1, "Factor": f"{factor:.3f}"})
df_factors = pd.DataFrame(factor_rows)

# Axis sort orders
year_order = [str(y) for y in accident_years] + ["Dev Factor"]
min_val = df["Cumulative Amount"].min()
max_val = df["Cumulative Amount"].max()

# Shared axis encodings
x_enc = alt.X(
    "Development Period:O",
    axis=alt.Axis(labelFontSize=16, titleFontSize=20, labelAngle=0, orient="top", titlePadding=12),
)
y_enc = alt.Y(
    "Accident Year:N",
    sort=[str(y) for y in accident_years],
    axis=alt.Axis(labelFontSize=16, titleFontSize=20, titlePadding=12),
)

# Heatmap cells with color mapped by status
heatmap = (
    alt.Chart(df)
    .mark_rect(stroke="#ffffff", strokeWidth=1.5, cornerRadius=1)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            "Cumulative Amount:Q",
            scale=alt.Scale(scheme="blues", domain=[min_val, max_val]),
            legend=alt.Legend(
                title="Cumulative Claims",
                titleFontSize=14,
                labelFontSize=12,
                gradientLength=260,
                gradientThickness=14,
                orient="right",
                offset=16,
            ),
        ),
        opacity=alt.when(alt.datum.Status == "Actual").then(alt.value(1.0)).otherwise(alt.value(0.4)),
        tooltip=[
            alt.Tooltip("Accident Year:N"),
            alt.Tooltip("Development Period:O"),
            alt.Tooltip("Cumulative Amount:Q", format=",.0f", title="Cumulative ($)"),
            alt.Tooltip("Status:N"),
        ],
    )
)

# Diagonal border to mark the evaluation date boundary
projected_df = df[df["Status"] == "Projected (IBNR)"].copy()
projected_border = (
    alt.Chart(projected_df)
    .mark_rect(stroke="#d97706", strokeWidth=2.5, strokeDash=[6, 3], filled=False, cornerRadius=1)
    .encode(x=x_enc, y=y_enc)
)

# Text annotations on cells
text = (
    alt.Chart(df)
    .mark_text(fontSize=14, fontWeight="bold")
    .encode(
        x=x_enc,
        y=y_enc,
        text="Label:N",
        color=alt.when(alt.datum["Cumulative Amount"] > (max_val * 0.55))
        .then(alt.value("#ffffff"))
        .otherwise(alt.value("#1a3a5c")),
    )
)

# Development factors row background and text
factor_bg = (
    alt.Chart(df_factors)
    .mark_rect(fill="#f0f4f8", stroke="#c8d4e0", strokeWidth=1, cornerRadius=1)
    .encode(x=alt.X("Development Period:O"), y=alt.Y("Accident Year:N", sort=year_order))
)
factor_text = (
    alt.Chart(df_factors)
    .mark_text(fontSize=13, fontWeight="bold", color="#306998")
    .encode(x=alt.X("Development Period:O"), y=alt.Y("Accident Year:N", sort=year_order), text="Factor:N")
)

# Status legend: actual vs projected distinction
status_legend = (
    alt.Chart(legend_data)
    .mark_square(size=200, stroke="black", strokeWidth=1)
    .encode(
        opacity=alt.Opacity(
            "legend_label:N",
            scale=alt.Scale(domain=["Actual (Observed)", "Projected (IBNR)"], range=[1.0, 0.4]),
            legend=alt.Legend(
                title="Status",
                titleFontSize=14,
                labelFontSize=12,
                orient="right",
                offset=16,
                symbolType="square",
                symbolSize=200,
                symbolStrokeWidth=1.5,
                symbolFillColor="#2171b5",
            ),
        )
    )
)

# Combine all layers
chart = (
    (heatmap + projected_border + text + factor_bg + factor_text + status_legend)
    .properties(
        width=1400,
        height=820,
        title=alt.Title(
            "heatmap-loss-triangle · altair · pyplots.ai",
            subtitle=[
                "Cumulative paid claims development triangle with chain-ladder projections.",
                "Full opacity = actual observed  |  Faded + dashed border = projected (IBNR)  |  Bottom row = age-to-age factors.",
            ],
            fontSize=26,
            subtitleFontSize=15,
            subtitleColor="#666666",
            anchor="start",
            offset=16,
        ),
        padding={"left": 20, "right": 20, "top": 20, "bottom": 20},
    )
    .configure_axis(grid=False, domainWidth=0)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
