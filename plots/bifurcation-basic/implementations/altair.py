"""pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: altair 6.0.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-20
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

# Classify regions for conditional coloring
df["region"] = np.where(df["r"] < 3.0, "Stable", np.where(df["r"] < 3.57, "Period-doubling", "Chaotic"))

# Key bifurcation points — staggered y positions to avoid overlap
bifurcation_points = pd.DataFrame(
    {
        "r": [3.0, 3.449, 3.544, 3.5699],
        "label": ["Period 2 (r≈3.0)", "Period 4 (r≈3.45)", "Period 8 (r≈3.54)", "Chaos (r≈3.57)"],
        "y": [0.92, 0.92, 0.85, 0.92],
    }
)

# Selection for interactive highlight on nearest point
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["r"], empty=False)

# Color scale by dynamical regime
region_color = alt.Scale(domain=["Stable", "Period-doubling", "Chaotic"], range=["#306998", "#5A9BD5", "#D94F4F"])

# Base scatter layer
points = (
    alt.Chart(df)
    .mark_circle(size=1.5, opacity=0.18)
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
            scale=alt.Scale(domain=[0, 1.0], nice=False),
            axis=alt.Axis(tickCount=6, titleColor="#333333", labelColor="#555555", domain=False),
        ),
        color=alt.Color(
            "region:N",
            scale=region_color,
            legend=alt.Legend(
                title="Regime",
                titleFontSize=16,
                labelFontSize=14,
                orient="top-right",
                offset=-10,
                fillColor="white",
                strokeColor="#dddddd",
                padding=8,
                cornerRadius=4,
            ),
        ),
        tooltip=[alt.Tooltip("r:Q", title="r", format=".4f"), alt.Tooltip("x:Q", title="x", format=".4f"), "region:N"],
    )
)

# Transparent voronoi layer for nearest-point selection
voronoi = (
    alt.Chart(df.sample(n=5000, random_state=42))
    .mark_point(size=1, opacity=0)
    .encode(x="r:Q", y="x:Q")
    .add_params(nearest)
)

# Vertical crosshair following pointer
crosshair = (
    alt.Chart(df.sample(n=5000, random_state=42))
    .mark_rule(color="#306998", strokeWidth=1.5, opacity=0.5)
    .encode(x="r:Q")
    .transform_filter(nearest)
)

# Bifurcation point markers
rules = (
    alt.Chart(bifurcation_points)
    .mark_rule(strokeDash=[6, 4], strokeWidth=1.2, opacity=0.35, color="#888888")
    .encode(x="r:Q")
)

labels = (
    alt.Chart(bifurcation_points)
    .mark_text(fontSize=14, fontWeight="bold", color="#444444", angle=270, align="left", dx=0, dy=-8)
    .encode(x="r:Q", y="y:Q", text="label:N")
)

# Compose
chart = (
    (points + voronoi + crosshair + rules + labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "bifurcation-basic · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            color="#1a1a2e",
            subtitle="Logistic map period-doubling cascade from stability to chaos",
            subtitleFontSize=16,
            subtitleColor="#666666",
            subtitlePadding=8,
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titlePadding=14,
        grid=True,
        gridOpacity=0.12,
        gridColor="#cccccc",
        gridDash=[3, 3],
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
