"""pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: altair | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data — Logistic map: x(n+1) = r * x(n) * (1 - x(n))
np.random.seed(42)
r_values = np.linspace(2.5, 4.0, 2000)
transient = 200
iterations = 100

r_all = []
x_all = []
for r in r_values:
    x = 0.5
    for _ in range(transient):
        x = r * x * (1.0 - x)
    for _ in range(iterations):
        x = r * x * (1.0 - x)
        r_all.append(r)
        x_all.append(x)

df = pd.DataFrame({"r": r_all, "x": x_all})

# Key bifurcation points
bifurcation_points = pd.DataFrame(
    {
        "r": [3.0, 3.449, 3.544, 3.5699],
        "label": ["r≈3.0 · Period 2", "r≈3.45 · Period 4", "r≈3.54 · Period 8", "r≈3.57 · Chaos"],
        "y": [0.05, 0.05, 0.05, 0.05],
    }
)

# Plot
points = (
    alt.Chart(df)
    .mark_circle(size=1, opacity=0.15, color="#306998")
    .encode(
        x=alt.X(
            "r:Q",
            title="Growth Rate (r)",
            scale=alt.Scale(domain=[2.5, 4.0], nice=False),
            axis=alt.Axis(tickCount=7, titleColor="#333333", labelColor="#555555", domain=False),
        ),
        y=alt.Y(
            "x:Q",
            title="Steady-State Population (x)",
            scale=alt.Scale(domain=[0, 1.02], nice=False),
            axis=alt.Axis(tickCount=6, titleColor="#333333", labelColor="#555555", domain=False),
        ),
        tooltip=[alt.Tooltip("r:Q", title="r", format=".4f"), alt.Tooltip("x:Q", title="x", format=".4f")],
    )
)

# Bifurcation point markers
rules = (
    alt.Chart(bifurcation_points)
    .mark_rule(strokeDash=[6, 4], strokeWidth=1.2, opacity=0.4, color="#888888")
    .encode(x="r:Q")
)

labels = (
    alt.Chart(bifurcation_points)
    .mark_text(fontSize=13, fontWeight="bold", color="#555555", angle=270, align="left", dx=0, dy=-6)
    .encode(x="r:Q", y="y:Q", text="label:N")
)

# Compose
chart = (
    (points + rules + labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "bifurcation-basic · altair · pyplots.ai",
            fontSize=28,
            color="#222222",
            subtitle="Logistic map period-doubling cascade from stability to chaos",
            subtitleFontSize=16,
            subtitleColor="#777777",
            subtitlePadding=6,
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titlePadding=12,
        grid=True,
        gridOpacity=0.15,
        gridColor="#cccccc",
        gridDash=[3, 3],
    )
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
