""" pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: altair 6.0.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-14
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Logistic map near type-I intermittency (r=3.8284)
# This parameter produces alternating laminar (near-periodic) and burst (chaotic) phases
np.random.seed(42)
n_steps = 152
r = 3.8284
x = np.zeros(n_steps)
x[0] = 0.1
for i in range(1, n_steps):
    x[i] = r * x[i - 1] * (1 - x[i - 1])

# Time-delay embedding (dimension=3, delay=1) per Takens' theorem
embedding_dim = 3
delay = 1
n_embedded = n_steps - (embedding_dim - 1) * delay
embedded = np.column_stack([x[d * delay : d * delay + n_embedded] for d in range(embedding_dim)])

# Compute pairwise Euclidean distance matrix
diff = embedded[:, np.newaxis, :] - embedded[np.newaxis, :, :]
distance_matrix = np.sqrt(np.sum(diff**2, axis=2))
threshold = 0.15
recurrence_matrix = distance_matrix < threshold

# Build long-form dataframe for recurrence points only (non-recurrent = background)
rows, cols = np.where(recurrence_matrix)
distances = distance_matrix[rows, cols]
df = pd.DataFrame({"time_i": rows, "time_j": cols, "distance": distances})

# Interactive selection for cross-highlighting on hover
hover = alt.selection_point(on="pointerover", fields=["time_i"], nearest=True, empty=False)

# Color scale: custom dark-to-bright mapping for better contrast
color_scale = alt.Scale(
    domain=[0, threshold * 0.33, threshold * 0.67, threshold], range=["#fde725", "#35b779", "#31688e", "#1e1e2f"]
)

# Main recurrence heatmap layer
heatmap = (
    alt.Chart(df)
    .mark_rect(stroke=None)
    .encode(
        x=alt.X(
            "time_i:O",
            title="Time Index (step)",
            axis=alt.Axis(
                labelFontSize=16,
                titleFontSize=20,
                titlePadding=14,
                values=list(range(0, n_embedded, 25)),
                grid=False,
                domainColor="#444444",
                tickColor="#444444",
                labelColor="#333333",
                titleColor="#222222",
            ),
            scale=alt.Scale(paddingInner=0, paddingOuter=0),
        ),
        y=alt.Y(
            "time_j:O",
            title="Time Index (step)",
            axis=alt.Axis(
                labelFontSize=16,
                titleFontSize=20,
                titlePadding=14,
                values=list(range(0, n_embedded, 25)),
                grid=False,
                domainColor="#444444",
                tickColor="#444444",
                labelColor="#333333",
                titleColor="#222222",
            ),
            scale=alt.Scale(paddingInner=0, paddingOuter=0),
        ),
        color=alt.Color(
            "distance:Q",
            title="Distance",
            scale=color_scale,
            legend=alt.Legend(
                titleFontSize=16,
                labelFontSize=14,
                orient="right",
                direction="vertical",
                gradientLength=400,
                gradientThickness=16,
                titlePadding=8,
                offset=8,
                labelColor="#333333",
                titleColor="#222222",
            ),
        ),
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.88)),
        tooltip=[
            alt.Tooltip("time_i:Q", title="Time i"),
            alt.Tooltip("time_j:Q", title="Time j"),
            alt.Tooltip("distance:Q", title="Distance", format=".4f"),
        ],
    )
    .add_params(hover)
)

# Annotation markers for key structural features
annotations_data = pd.DataFrame(
    {
        "label": ["Main diagonal (self-recurrence)", "Laminar phase", "Diagonal lines (determinism)"],
        "x": [35, 115, 75],
        "y": [25, 105, 50],
    }
)

# Text shadow for legibility against busy background
annotation_shadow = (
    alt.Chart(annotations_data)
    .mark_text(fontSize=15, fontWeight="bold", color="white", align="left", dx=11, dy=-7, lineBreak="\n", strokeWidth=4)
    .encode(x=alt.X("x:O"), y=alt.Y("y:O"), text="label:N")
)

annotation_marks = (
    alt.Chart(annotations_data)
    .mark_text(fontSize=15, fontWeight="bold", color="#b8220e", align="left", dx=11, dy=-7, lineBreak="\n")
    .encode(x=alt.X("x:O"), y=alt.Y("y:O"), text="label:N")
)

# Annotation connector dots
annotation_dots = (
    alt.Chart(annotations_data)
    .mark_point(size=90, color="#b8220e", filled=True, opacity=0.8)
    .encode(x=alt.X("x:O"), y=alt.Y("y:O"))
)

# Layer the heatmap and annotations
chart = (
    alt.layer(heatmap, annotation_dots, annotation_shadow, annotation_marks)
    .properties(
        width=1150,
        height=1150,
        title=alt.Title(
            "recurrence-basic · altair · pyplots.ai",
            subtitle=[
                "Logistic map at type-I intermittency boundary (r = 3.8284) · ε = 0.15 · Takens embedding (d = 3, τ = 1)",
                "Bright cells = near-identical states · Diagonal lines = deterministic dynamics · Blocks = laminar phases",
            ],
            fontSize=28,
            subtitleFontSize=16,
            subtitleColor="#555555",
            anchor="start",
            offset=18,
            color="#111111",
        ),
        padding={"left": 20, "right": 16, "top": 20, "bottom": 20},
    )
    .configure_axis(grid=False)
    .configure_view(strokeWidth=0, fill="#e8e8ec")
)

# Save
chart.save("plot.png", scale_factor=3.1)
chart.save("plot.html")
