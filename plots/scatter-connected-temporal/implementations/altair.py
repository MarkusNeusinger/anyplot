""" pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: altair 6.0.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-13
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

# Label key time points with nudged positions to avoid crowding
label_years = [1994, 2000, 2008, 2010, 2015, 2023]
df_labels = df[df["year"].isin(label_years)].copy()
nudge = {2015: (-0.25, 0.35), 2023: (0.25, -0.35)}
df_labels["label_x"] = df_labels.apply(lambda r: r["unemployment"] + nudge.get(r["year"], (0, 0))[0], axis=1)
df_labels["label_y"] = df_labels.apply(lambda r: r["inflation"] + nudge.get(r["year"], (0, 0))[1], axis=1)

# Shared axis encodings
x_scale = alt.Scale(domain=[2.5, 8.5], nice=False)
y_scale = alt.Scale(domain=[-1.5, 5.8], nice=False)
axis_config = {
    "labelFontWeight": "normal",
    "titleColor": "#333333",
    "labelColor": "#555555",
    "tickColor": "#cccccc",
    "gridDash": [3, 3],
    "domain": False,
}

x_enc = alt.X("unemployment:Q", title="Unemployment Rate (%)", scale=x_scale, axis=alt.Axis(**axis_config))
y_enc = alt.Y("inflation:Q", title="Inflation Rate (%)", scale=y_scale, axis=alt.Axis(**axis_config))

# Shared viridis color scale
viridis_scale = alt.Scale(scheme="viridis", domain=[1994, 2023])
viridis_legend = alt.Legend(
    title="Year", titleFontSize=16, labelFontSize=15, format="d", gradientLength=300, gradientThickness=12
)

# Connecting path in temporal order — neutral gray to avoid color conflicts
path = alt.Chart(df).mark_line(strokeWidth=2.5, opacity=0.35, color="#666666").encode(x=x_enc, y=y_enc, order="order:Q")

# Points colored by temporal progression — carries the viridis legend
points = (
    alt.Chart(df)
    .mark_point(filled=True, size=180, stroke="white", strokeWidth=1.2)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color("year:Q", scale=viridis_scale, legend=viridis_legend),
        tooltip=[
            alt.Tooltip("year:Q", title="Year", format="d"),
            alt.Tooltip("unemployment:Q", title="Unemployment (%)", format=".1f"),
            alt.Tooltip("inflation:Q", title="Inflation (%)", format=".1f"),
        ],
    )
)

# Year annotations for key points with nudged positions
annotations = (
    alt.Chart(df_labels)
    .mark_text(fontSize=16, fontWeight="bold", color="#333333", dy=-16)
    .encode(x=alt.X("label_x:Q"), y=alt.Y("label_y:Q"), text=alt.Text("year:Q", format="d"))
)

# Compose layers
chart = (
    (path + points + annotations)
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
    .configure_legend(orient="right", padding=10)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
