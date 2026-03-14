""" pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: altair 6.0.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-14
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

# Compute pairwise Euclidean distance matrix and apply threshold
diff = embedded[:, np.newaxis, :] - embedded[np.newaxis, :, :]
distance_matrix = np.sqrt(np.sum(diff**2, axis=2))
threshold = 0.15
recurrence_matrix = distance_matrix < threshold

# Build long-form dataframe for recurrence points only (sparse encoding)
rows, cols = np.where(recurrence_matrix == 1)
df = pd.DataFrame({"time_i": rows, "time_j": cols})

# Plot - binary recurrence plot using mark_point for sparse data
recurrence = (
    alt.Chart(df)
    .mark_square(size=4, opacity=1.0)
    .encode(
        x=alt.X(
            "time_i:Q",
            title="Time Index",
            scale=alt.Scale(domain=[0, n_embedded - 1]),
            axis=alt.Axis(labelFontSize=16, titleFontSize=20, tickCount=6, grid=False),
        ),
        y=alt.Y(
            "time_j:Q",
            title="Time Index",
            scale=alt.Scale(domain=[0, n_embedded - 1]),
            axis=alt.Axis(labelFontSize=16, titleFontSize=20, tickCount=6, grid=False),
        ),
        color=alt.value("#306998"),
        tooltip=[alt.Tooltip("time_i:Q", title="Time i"), alt.Tooltip("time_j:Q", title="Time j")],
    )
)

# Combine and configure
chart = (
    recurrence.properties(
        width=780,
        height=780,
        title=alt.Title(
            "recurrence-basic · altair · pyplots.ai",
            subtitle=[
                "Logistic map (r = 3.82) · Euclidean distance with ε = 0.15",
                "Diagonal lines reveal deterministic structure near chaos onset",
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

# Save
chart.save("plot.png", scale_factor=3.6)
chart.save("plot.html")
