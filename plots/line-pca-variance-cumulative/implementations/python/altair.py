""" pyplots.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: altair 6.0.0 | Python 3.14.3
Quality: 96/100 | Created: 2026-02-17
"""

import altair as alt
import numpy as np
import pandas as pd
from sklearn.datasets import load_wine
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Data - PCA on the Wine dataset (13 features)
wine = load_wine()
X_scaled = StandardScaler().fit_transform(wine.data)
pca = PCA().fit(X_scaled)

cumulative_variance = np.cumsum(pca.explained_variance_ratio_) * 100
n_components = np.arange(1, len(cumulative_variance) + 1)

df = pd.DataFrame({"Component": n_components, "Cumulative Variance": cumulative_variance})

# Detect elbow point using maximum distance from diagonal (kneedle method)
x_norm = (n_components - n_components[0]) / (n_components[-1] - n_components[0])
y_norm = (cumulative_variance - cumulative_variance[0]) / (cumulative_variance[-1] - cumulative_variance[0])
distances = np.abs(y_norm - x_norm)
elbow_idx = int(np.argmax(distances))
elbow_component = n_components[elbow_idx]
elbow_value = cumulative_variance[elbow_idx]

# Threshold crossing points
thresholds = pd.DataFrame({"Threshold": [90, 95], "Label": ["90 %", "95 %"]})

crossing_points = []
for thresh in [90, 95]:
    idx = int(np.searchsorted(cumulative_variance, thresh))
    if idx < len(cumulative_variance):
        crossing_points.append(
            {
                "Component": idx + 1,
                "Cumulative Variance": cumulative_variance[idx],
                "Label": f"{thresh} %",
                "Annotation": f"{idx + 1} components",
            }
        )
crossing_df = pd.DataFrame(crossing_points)

# Elbow annotation data
elbow_df = pd.DataFrame(
    [{"Component": elbow_component, "Cumulative Variance": elbow_value, "Marker": f"Elbow (PC {elbow_component})"}]
)

# Shared scale definitions
y_scale = alt.Scale(domain=[20, 105])
x_scale = alt.Scale(domain=[0.5, len(cumulative_variance) + 0.5], nice=False)
threshold_colors = alt.Scale(domain=["90 %", "95 %"], range=["#4E79A7", "#F28E2B"])

# Area fill under the curve for data storytelling
area = (
    alt.Chart(df)
    .mark_area(opacity=0.08, color="#306998")
    .encode(
        x=alt.X("Component:Q", scale=x_scale),
        y=alt.Y("Cumulative Variance:Q", scale=y_scale),
        y2=alt.value({"expr": "height"}),
    )
)

# Cumulative variance line
line = (
    alt.Chart(df)
    .mark_line(strokeWidth=4, color="#306998", interpolate="monotone")
    .encode(
        x=alt.X(
            "Component:Q",
            title="Number of Components",
            scale=x_scale,
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, titlePadding=14, tickMinStep=1),
        ),
        y=alt.Y(
            "Cumulative Variance:Q",
            title="Cumulative Explained Variance (%)",
            scale=y_scale,
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, titlePadding=14, format=".0f"),
        ),
    )
)

# Data point markers
points = (
    alt.Chart(df)
    .mark_point(size=200, color="#306998", filled=True, stroke="white", strokeWidth=2)
    .encode(
        x=alt.X("Component:Q", scale=x_scale),
        y=alt.Y("Cumulative Variance:Q", scale=y_scale),
        tooltip=[
            alt.Tooltip("Component:Q", title="Component"),
            alt.Tooltip("Cumulative Variance:Q", format=".1f", title="Cumulative Variance (%)"),
        ],
    )
)

# Interactive nearest-point selection (Altair distinctive feature)
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["Component"], empty=False)

invisible_selector = (
    alt.Chart(df)
    .mark_point(size=400, opacity=0)
    .encode(x=alt.X("Component:Q", scale=x_scale), y=alt.Y("Cumulative Variance:Q", scale=y_scale))
    .add_params(nearest)
)

highlight_point = (
    alt.Chart(df)
    .mark_point(size=350, color="#306998", filled=True, stroke="#1a3a5c", strokeWidth=3)
    .encode(
        x=alt.X("Component:Q", scale=x_scale),
        y=alt.Y("Cumulative Variance:Q", scale=y_scale),
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
    )
)

# Vertical rule for hover indicator
hover_rule = (
    alt.Chart(df)
    .mark_rule(color="#999", strokeDash=[3, 3], strokeWidth=1)
    .encode(x=alt.X("Component:Q", scale=x_scale))
    .transform_filter(nearest)
)

# Threshold reference lines
threshold_lines = (
    alt.Chart(thresholds)
    .mark_rule(strokeDash=[10, 6], strokeWidth=2, opacity=0.55)
    .encode(
        y=alt.Y("Threshold:Q", scale=y_scale),
        color=alt.Color(
            "Label:N",
            scale=threshold_colors,
            legend=alt.Legend(
                title="Threshold",
                titleFontSize=18,
                titleFontWeight="bold",
                labelFontSize=16,
                orient="right",
                symbolStrokeWidth=3,
                symbolSize=200,
                symbolDash=[10, 6],
                offset=10,
            ),
        ),
    )
)

# Threshold crossing markers with text annotations
crossing_markers = (
    alt.Chart(crossing_df)
    .mark_point(shape="diamond", size=400, filled=True, stroke="white", strokeWidth=2)
    .encode(
        x=alt.X("Component:Q", scale=x_scale),
        y=alt.Y("Cumulative Variance:Q", scale=y_scale),
        color=alt.Color("Label:N", scale=threshold_colors, legend=None),
        tooltip=[
            alt.Tooltip("Component:Q", title="Components needed"),
            alt.Tooltip("Cumulative Variance:Q", format=".1f", title="Variance (%)"),
            alt.Tooltip("Label:N", title="Threshold"),
        ],
    )
)

# Annotations at threshold crossing points
crossing_labels = (
    alt.Chart(crossing_df)
    .mark_text(fontSize=15, fontWeight="bold", dy=-20, align="center")
    .encode(
        x=alt.X("Component:Q", scale=x_scale),
        y=alt.Y("Cumulative Variance:Q", scale=y_scale),
        text=alt.Text("Annotation:N"),
        color=alt.Color("Label:N", scale=threshold_colors, legend=None),
    )
)

# Elbow point marker
elbow_marker = (
    alt.Chart(elbow_df)
    .mark_point(shape="triangle-up", size=500, color="#E45756", filled=True, stroke="white", strokeWidth=2)
    .encode(
        x=alt.X("Component:Q", scale=x_scale),
        y=alt.Y("Cumulative Variance:Q", scale=y_scale),
        tooltip=[
            alt.Tooltip("Component:Q", title="Elbow at component"),
            alt.Tooltip("Cumulative Variance:Q", format=".1f", title="Variance (%)"),
        ],
    )
)

# Elbow label
elbow_label = (
    alt.Chart(elbow_df)
    .mark_text(fontSize=18, fontWeight="bold", color="#E45756", dy=-24, dx=30)
    .encode(
        x=alt.X("Component:Q", scale=x_scale),
        y=alt.Y("Cumulative Variance:Q", scale=y_scale),
        text=alt.Text("Marker:N"),
    )
)

# Combine all layers
chart = (
    (
        area
        + threshold_lines
        + hover_rule
        + line
        + points
        + crossing_markers
        + crossing_labels
        + elbow_marker
        + elbow_label
        + invisible_selector
        + highlight_point
    )
    .properties(
        width=1600,
        height=1000,
        title=alt.Title(
            text="line-pca-variance-cumulative · altair · pyplots.ai", fontSize=28, anchor="middle", offset=16
        ),
    )
    .configure_axis(grid=True, gridOpacity=0.15, gridDash=[4, 4], domainColor="#666")
    .configure_view(strokeWidth=0)
    .configure(padding={"left": 20, "right": 20, "top": 10, "bottom": 20})
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
