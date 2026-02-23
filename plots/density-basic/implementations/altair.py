"""pyplots.ai
density-basic: Basic Density Plot
Library: altair 6.0.0 | Python 3.14.3
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - bimodal distribution showing two student groups with distinct performance
np.random.seed(42)
values = np.concatenate(
    [
        np.random.normal(loc=38, scale=7, size=200),  # Group A — foundational course
        np.random.normal(loc=72, scale=8, size=150),  # Group B — advanced course
    ]
)
values = np.clip(values, 5, 100)  # Keep within realistic test score range

df = pd.DataFrame({"Test Score": values})

# Peak annotations to highlight bimodal distribution storytelling
peaks = pd.DataFrame(
    {"Test Score": [38, 72], "density": [0.032, 0.021], "label": ["Foundational Course", "Advanced Course"]}
)

# Nearest-point selection for interactive density readout (HTML export)
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["Test Score"], empty=False)

# Density curve with filled area
density = (
    alt.Chart(df)
    .transform_density("Test Score", as_=["Test Score", "density"], bandwidth=4)
    .mark_area(opacity=0.45, color="#306998", line={"color": "#1e4d6e", "strokeWidth": 2.5})
    .encode(
        x=alt.X(
            "Test Score:Q",
            title="Test Score (points)",
            scale=alt.Scale(domain=[15, 100]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, tickCount=10, grid=False),
        ),
        y=alt.Y(
            "density:Q", title="Probability Density", axis=alt.Axis(labelFontSize=18, titleFontSize=22, format=".3f")
        ),
        tooltip=[
            alt.Tooltip("Test Score:Q", title="Score", format=".1f"),
            alt.Tooltip("density:Q", title="Density", format=".4f"),
        ],
    )
)

# Invisible points on density curve driving nearest-point selection
hover_points = (
    alt.Chart(df)
    .transform_density("Test Score", as_=["Test Score", "density"], bandwidth=4)
    .mark_point(opacity=0)
    .encode(x="Test Score:Q", y="density:Q")
    .add_params(nearest)
)

# Hover dot — conditionally visible point at cursor position
hover_dot = (
    alt.Chart(df)
    .transform_density("Test Score", as_=["Test Score", "density"], bandwidth=4)
    .mark_point(size=80, filled=True, color="#1e4d6e")
    .encode(x="Test Score:Q", y="density:Q", opacity=alt.condition(nearest, alt.value(1), alt.value(0)))
)

# Peak annotations — label the two distribution modes
annotations = (
    alt.Chart(peaks)
    .mark_text(fontSize=16, fontWeight="bold", color="#1e4d6e", dy=-18)
    .encode(x="Test Score:Q", y="density:Q", text="label:N")
)

# Rug plot — tick marks showing individual observations at density=0
rug = (
    alt.Chart(df)
    .mark_tick(color="#306998", opacity=0.4, thickness=1.5, size=18)
    .encode(x=alt.X("Test Score:Q"), y=alt.Y(datum=0))
)

# Combine layers
chart = (
    alt.layer(density, rug, annotations, hover_points, hover_dot)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            text="density-basic · altair · pyplots.ai",
            subtitle="Kernel density estimation of test scores across two course levels",
            fontSize=28,
            subtitleFontSize=16,
            subtitleColor="#666666",
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_axis(gridColor="#e0e0e0", gridOpacity=0.15, gridDash=[4, 4], domainColor="#888888")
)

# Save as PNG (1600 * 3 = 4800, 900 * 3 = 2700)
chart.save("plot.png", scale_factor=3.0)

# Save as interactive HTML with selection-driven hover readout
chart.save("plot.html")
