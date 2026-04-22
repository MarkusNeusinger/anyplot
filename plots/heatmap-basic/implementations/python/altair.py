""" pyplots.ai
heatmap-basic: Basic Heatmap
Library: altair 6.0.0 | Python 3.14.3
Quality: 88/100 | Updated: 2026-02-16
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - correlation matrix with realistic weather variables
np.random.seed(42)
variables = [
    "Temperature",
    "Humidity",
    "Wind Speed",
    "Pressure",
    "Visibility",
    "Cloud Cover",
    "Precipitation",
    "UV Index",
]

n_samples = 200
raw = np.random.randn(n_samples, len(variables))

# Inject realistic correlations with stronger relationships
raw[:, 1] += raw[:, 0] * 0.6  # Humidity ~ Temperature
raw[:, 5] += raw[:, 1] * 0.7  # Cloud Cover ~ Humidity
raw[:, 6] += raw[:, 5] * 0.65  # Precipitation ~ Cloud Cover
raw[:, 4] -= raw[:, 5] * 0.9  # Visibility inversely ~ Cloud Cover
raw[:, 7] -= raw[:, 5] * 0.7  # UV Index inversely ~ Cloud Cover
raw[:, 7] += raw[:, 0] * 0.5  # UV Index ~ Temperature
raw[:, 3] -= raw[:, 0] * 0.4  # Pressure inversely ~ Temperature
raw[:, 2] += raw[:, 3] * 0.3  # Wind Speed ~ Pressure

corr = np.corrcoef(raw.T)

# Build long-form dataframe using list comprehension
df = pd.DataFrame(
    [
        {"Row": row_var, "Column": col_var, "value": round(corr[i, j], 2)}
        for i, row_var in enumerate(variables)
        for j, col_var in enumerate(variables)
    ]
)

# Axis ordering
axis_order = list(variables)

# Plot - heatmap with colorblind-safe diverging color centered at 0
heatmap = (
    alt.Chart(df)
    .mark_rect(stroke="#ffffff", strokeWidth=1.5, cornerRadius=2)
    .encode(
        x=alt.X(
            "Column:N",
            title="Weather Variable",
            sort=axis_order,
            axis=alt.Axis(
                labelFontSize=15, titleFontSize=18, labelAngle=-45, orient="top", labelPadding=8, titlePadding=10
            ),
        ),
        y=alt.Y(
            "Row:N",
            title="Weather Variable",
            sort=axis_order,
            axis=alt.Axis(labelFontSize=15, titleFontSize=18, labelPadding=8, titlePadding=10),
        ),
        color=alt.Color(
            "value:Q",
            scale=alt.Scale(scheme="blueorange", domain=[-1, 1], domainMid=0),
            legend=alt.Legend(
                title="Correlation",
                titleFontSize=16,
                labelFontSize=14,
                gradientLength=300,
                gradientThickness=16,
                titlePadding=6,
                offset=8,
                direction="vertical",
            ),
        ),
        tooltip=[
            alt.Tooltip("Column:N", title="Column"),
            alt.Tooltip("Row:N", title="Row"),
            alt.Tooltip("value:Q", title="Correlation", format=".2f"),
        ],
    )
)

# Highlight cells with strong correlations using thicker borders
highlight = (
    alt.Chart(df)
    .transform_filter((alt.datum.value >= 0.7) | (alt.datum.value <= -0.7))
    .mark_rect(stroke="#2a2a2a", strokeWidth=2.5, filled=False, cornerRadius=2)
    .encode(x=alt.X("Column:N", sort=axis_order), y=alt.Y("Row:N", sort=axis_order))
)

# Text annotations with adaptive color
text = (
    alt.Chart(df)
    .mark_text(fontSize=15, fontWeight="bold")
    .encode(
        x=alt.X("Column:N", sort=axis_order),
        y=alt.Y("Row:N", sort=axis_order),
        text=alt.Text("value:Q", format=".2f"),
        color=alt.when((alt.datum.value > 0.55) | (alt.datum.value < -0.55))
        .then(alt.value("#ffffff"))
        .otherwise(alt.value("#333333")),
    )
)

# Combine layers and configure
chart = (
    (heatmap + highlight + text)
    .properties(
        width=740,
        height=766,
        title=alt.Title(
            "heatmap-basic · altair · pyplots.ai",
            subtitle=[
                "Pairwise Pearson correlation coefficients for 8 weather metrics.",
                "Bold borders highlight strong relationships (|r| ≥ 0.7).",
            ],
            fontSize=26,
            subtitleFontSize=16,
            subtitleColor="#666666",
            anchor="start",
            offset=16,
        ),
        padding={"left": 20, "right": 20, "top": 20, "bottom": 20},
    )
    .configure_axis(grid=False)
    .configure_view(strokeWidth=0)
)

# Save — target: 3600×3600 square format
chart.save("plot.png", scale_factor=3.6)
chart.save("plot.html")
