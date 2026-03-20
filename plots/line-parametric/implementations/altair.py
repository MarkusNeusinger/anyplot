""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: altair 6.0.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Lissajous figure and Archimedean spiral
t_lissajous = np.linspace(0, 2 * np.pi, 1000)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

t_spiral = np.linspace(0, 6 * np.pi, 1000)
x_spiral = t_spiral * np.cos(t_spiral) / (6 * np.pi)
y_spiral = t_spiral * np.sin(t_spiral) / (6 * np.pi)

df_lissajous = pd.DataFrame({"x": x_lissajous, "y": y_lissajous, "t": t_lissajous, "order": range(len(t_lissajous))})

df_spiral = pd.DataFrame({"x": x_spiral, "y": y_spiral, "t": t_spiral, "order": range(len(t_spiral))})

# Plot - Lissajous curve
lissajous_points = (
    alt.Chart(df_lissajous)
    .mark_circle(size=18, opacity=0.9)
    .encode(
        x=alt.X(
            "x:Q",
            title="x(t)",
            scale=alt.Scale(domain=[-1.15, 1.15]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        y=alt.Y(
            "y:Q",
            title="y(t)",
            scale=alt.Scale(domain=[-1.15, 1.15]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        color=alt.Color(
            "t:Q",
            title="Parameter t",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(titleFontSize=18, labelFontSize=16, gradientLength=300, gradientThickness=20),
        ),
        order="order:Q",
    )
    .properties(width=750, height=750, title=alt.Title("Lissajous · x = sin(3t), y = sin(2t)", fontSize=22))
)

starts_l = df_lissajous.iloc[[0]]
ends_l = df_lissajous.iloc[[-1]]

lissajous_start = (
    alt.Chart(starts_l)
    .mark_point(size=300, shape="circle", filled=True, color="#306998", stroke="white", strokeWidth=2)
    .encode(x="x:Q", y="y:Q")
)
lissajous_end = (
    alt.Chart(ends_l)
    .mark_point(size=300, shape="diamond", filled=True, color="#E84855", stroke="white", strokeWidth=2)
    .encode(x="x:Q", y="y:Q")
)
lissajous_start_label = (
    alt.Chart(starts_l)
    .mark_text(fontSize=16, fontWeight="bold", dy=-18, color="#306998")
    .encode(x="x:Q", y="y:Q", text=alt.value("t = 0"))
)
lissajous_end_label = (
    alt.Chart(ends_l)
    .mark_text(fontSize=16, fontWeight="bold", dy=-18, color="#E84855")
    .encode(x="x:Q", y="y:Q", text=alt.value("t = 2π"))
)

lissajous_chart = lissajous_points + lissajous_start + lissajous_end + lissajous_start_label + lissajous_end_label

# Plot - Archimedean spiral
spiral_points = (
    alt.Chart(df_spiral)
    .mark_circle(size=18, opacity=0.9)
    .encode(
        x=alt.X(
            "x:Q",
            title="x(t)",
            scale=alt.Scale(domain=[-1.15, 1.15]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        y=alt.Y(
            "y:Q",
            title="y(t)",
            scale=alt.Scale(domain=[-1.15, 1.15]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        color=alt.Color(
            "t:Q",
            title="Parameter t",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(titleFontSize=18, labelFontSize=16, gradientLength=300, gradientThickness=20),
        ),
        order="order:Q",
    )
    .properties(width=750, height=750, title=alt.Title("Archimedean Spiral · x = t·cos(t), y = t·sin(t)", fontSize=22))
)

starts_s = df_spiral.iloc[[0]]
ends_s = df_spiral.iloc[[-1]]

spiral_start = (
    alt.Chart(starts_s)
    .mark_point(size=300, shape="circle", filled=True, color="#306998", stroke="white", strokeWidth=2)
    .encode(x="x:Q", y="y:Q")
)
spiral_end = (
    alt.Chart(ends_s)
    .mark_point(size=300, shape="diamond", filled=True, color="#E84855", stroke="white", strokeWidth=2)
    .encode(x="x:Q", y="y:Q")
)
spiral_start_label = (
    alt.Chart(starts_s)
    .mark_text(fontSize=16, fontWeight="bold", dy=-18, color="#306998")
    .encode(x="x:Q", y="y:Q", text=alt.value("t = 0"))
)
spiral_end_label = (
    alt.Chart(ends_s)
    .mark_text(fontSize=16, fontWeight="bold", dy=-18, color="#E84855")
    .encode(x="x:Q", y="y:Q", text=alt.value("t = 6π"))
)

spiral_chart = spiral_points + spiral_start + spiral_end + spiral_start_label + spiral_end_label

# Combine side by side
chart = (
    alt.hconcat(lissajous_chart, spiral_chart)
    .resolve_scale(color="shared")
    .properties(title=alt.Title("line-parametric · altair · pyplots.ai", fontSize=28, anchor="middle"))
    .configure_axis(gridColor="#E0E0E0", gridOpacity=0.2)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
