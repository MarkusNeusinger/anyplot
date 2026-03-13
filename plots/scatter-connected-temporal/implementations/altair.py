""" pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: altair 6.0.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-13
"""

import altair as alt
import numpy as np
import pandas as pd


# Data — US-style unemployment vs inflation over 30 years
np.random.seed(42)
years = np.arange(1994, 2024)
n = len(years)

unemployment = np.zeros(n)
inflation = np.zeros(n)
unemployment[0] = 6.1
inflation[0] = 2.6

for i in range(1, n):
    unemployment[i] = unemployment[i - 1] + np.random.normal(-0.05, 0.6)
    inflation[i] = inflation[i - 1] + np.random.normal(0.02, 0.5)
    unemployment[i] = np.clip(unemployment[i], 3.0, 10.5)
    inflation[i] = np.clip(inflation[i], -0.5, 6.0)

# Add a recession spike around 2008-2010
unemployment[14:17] += np.array([2.5, 4.0, 3.5])
inflation[14:17] -= np.array([1.0, 1.5, 0.5])
unemployment = np.clip(unemployment, 3.0, 10.5)
inflation = np.clip(inflation, -0.5, 6.0)

df = pd.DataFrame(
    {"year": years, "unemployment": np.round(unemployment, 1), "inflation": np.round(inflation, 1), "order": range(n)}
)

# Create line segments with midpoint year for color encoding
segments = []
for i in range(n - 1):
    segments.append(
        {
            "x": df["unemployment"].iloc[i],
            "y": df["inflation"].iloc[i],
            "x2": df["unemployment"].iloc[i + 1],
            "y2": df["inflation"].iloc[i + 1],
            "year": (df["year"].iloc[i] + df["year"].iloc[i + 1]) / 2,
        }
    )
df_segments = pd.DataFrame(segments)

# Label key time points
label_years = [1994, 2000, 2008, 2010, 2015, 2023]
df_labels = df[df["year"].isin(label_years)].copy()

# Axis configuration shared between layers
x_enc = alt.X(
    "unemployment:Q",
    title="Unemployment Rate (%)",
    scale=alt.Scale(domain=[2.5, 8.5], nice=False),
    axis=alt.Axis(
        labelFontWeight="normal",
        titleColor="#333333",
        labelColor="#555555",
        tickColor="#cccccc",
        gridDash=[3, 3],
        domain=False,
    ),
)

y_enc = alt.Y(
    "inflation:Q",
    title="Inflation Rate (%)",
    scale=alt.Scale(domain=[-1.5, 5.8], nice=False),
    axis=alt.Axis(
        labelFontWeight="normal",
        titleColor="#333333",
        labelColor="#555555",
        tickColor="#cccccc",
        gridDash=[3, 3],
        domain=False,
    ),
)

# Shared viridis color scale
viridis_color = alt.Color(
    "year:Q",
    scale=alt.Scale(scheme="viridis", domain=[1994, 2023]),
    legend=alt.Legend(
        title="Year", titleFontSize=16, labelFontSize=15, format="d", gradientLength=300, gradientThickness=12
    ),
)

# Temporal-gradient connecting line segments using mark_rule
lines = (
    alt.Chart(df_segments)
    .mark_rule(strokeWidth=2.5, opacity=0.75)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[2.5, 8.5], nice=False)),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-1.5, 5.8], nice=False)),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color("year:Q", scale=alt.Scale(scheme="viridis", domain=[1994, 2023]), legend=None),
    )
)

# Points colored by temporal progression
points = (
    alt.Chart(df)
    .mark_point(filled=True, size=180, stroke="white", strokeWidth=1.2)
    .encode(
        x=x_enc,
        y=y_enc,
        color=viridis_color,
        tooltip=[
            alt.Tooltip("year:Q", title="Year", format="d"),
            alt.Tooltip("unemployment:Q", title="Unemployment (%)", format=".1f"),
            alt.Tooltip("inflation:Q", title="Inflation (%)", format=".1f"),
        ],
    )
)

# Year annotations for key points
annotations = (
    alt.Chart(df_labels)
    .mark_text(fontSize=16, fontWeight="bold", color="#333333", dy=-16)
    .encode(x=alt.X("unemployment:Q"), y=alt.Y("inflation:Q"), text=alt.Text("year:Q", format="d"))
)

# Compose layers
chart = (
    (lines + points + annotations)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "scatter-connected-temporal · altair · pyplots.ai",
            fontSize=28,
            color="#222222",
            subtitle="Unemployment vs. Inflation — tracing the Phillips curve path (1994–2023)",
            subtitleFontSize=16,
            subtitleColor="#777777",
            subtitlePadding=6,
        ),
    )
    .configure_axis(
        labelFontSize=18, titleFontSize=22, titlePadding=12, grid=True, gridOpacity=0.15, gridColor="#cccccc"
    )
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
