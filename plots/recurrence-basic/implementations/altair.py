""" pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: altair 6.0.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-14
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Logistic map near onset of chaos (r=3.82)
np.random.seed(42)
n_steps = 300
r = 3.82
x = np.zeros(n_steps)
x[0] = 0.1
for i in range(1, n_steps):
    x[i] = r * x[i - 1] * (1 - x[i - 1])

# Time-delay embedding (dimension=3, delay=1)
embedding_dim = 3
delay = 1
n_embedded = n_steps - (embedding_dim - 1) * delay
embedded = np.column_stack([x[d * delay : d * delay + n_embedded] for d in range(embedding_dim)])

# Compute pairwise Euclidean distance matrix
diff = embedded[:, np.newaxis, :] - embedded[np.newaxis, :, :]
distance_matrix = np.sqrt(np.sum(diff**2, axis=2))
threshold = 0.15
recurrence_matrix = distance_matrix < threshold

# Build long-form dataframe for recurrence points with distance values
rows, cols = np.where(recurrence_matrix)
distances = distance_matrix[rows, cols]
df = pd.DataFrame({"time_i": rows, "time_j": cols, "distance": distances})

# Plot - distance-colored recurrence plot using mark_rect for heatmap-style matrix
chart = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X(
            "time_i:O",
            title="Time Index (step)",
            axis=alt.Axis(labelFontSize=16, titleFontSize=20, values=list(range(0, n_embedded, 50)), grid=False),
            scale=alt.Scale(paddingInner=0, paddingOuter=0),
        ),
        y=alt.Y(
            "time_j:O",
            title="Time Index (step)",
            axis=alt.Axis(labelFontSize=16, titleFontSize=20, values=list(range(0, n_embedded, 50)), grid=False),
            scale=alt.Scale(paddingInner=0, paddingOuter=0),
        ),
        color=alt.Color(
            "distance:Q",
            title="Distance",
            scale=alt.Scale(scheme="viridis", reverse=True, domain=[0, threshold]),
            legend=alt.Legend(
                titleFontSize=16, labelFontSize=14, orient="right", gradientLength=300, gradientThickness=16
            ),
        ),
        tooltip=[
            alt.Tooltip("time_i:Q", title="Time i"),
            alt.Tooltip("time_j:Q", title="Time j"),
            alt.Tooltip("distance:Q", title="Distance", format=".4f"),
        ],
    )
    .properties(
        width=1000,
        height=1000,
        title=alt.Title(
            "recurrence-basic · altair · pyplots.ai",
            subtitle=[
                "Logistic map (r = 3.82) · Euclidean distance with ε = 0.15",
                "Bright cells = near-identical states · Diagonal lines reveal deterministic dynamics",
            ],
            fontSize=26,
            subtitleFontSize=17,
            subtitleColor="#555555",
            anchor="start",
            offset=16,
        ),
        padding={"left": 20, "right": 20, "top": 20, "bottom": 20},
    )
    .configure_axis(grid=False)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.6)
chart.save("plot.html")
