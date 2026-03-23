""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: altair 6.0.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-20
"""

import altair as alt
import numpy as np
import pandas as pd


# --- Data ---
t_lissajous = np.linspace(0, 2 * np.pi, 1000)
t_spiral = np.linspace(0, 6 * np.pi, 1000)

df_lissajous = pd.DataFrame(
    {"x": np.sin(3 * t_lissajous), "y": np.sin(2 * t_lissajous), "t": t_lissajous, "order": range(len(t_lissajous))}
)

df_spiral = pd.DataFrame(
    {
        "x": t_spiral * np.cos(t_spiral) / (6 * np.pi),
        "y": t_spiral * np.sin(t_spiral) / (6 * np.pi),
        "t": t_spiral,
        "order": range(len(t_spiral)),
    }
)

# --- Shared configuration ---
scale_xy = alt.Scale(domain=[-1.15, 1.15])
color_legend = alt.Legend(titleFontSize=18, labelFontSize=16, gradientLength=300, gradientThickness=20, orient="right")
axis_cfg = alt.Axis(labelFontSize=18, titleFontSize=22, domain=False, ticks=False)
x_enc = alt.X("x:Q", title="x(t)", scale=scale_xy, axis=axis_cfg)
y_enc = alt.Y("y:Q", title="y(t)", scale=scale_xy, axis=axis_cfg)

# --- Lissajous panel ---
liss_curve = (
    alt.Chart(df_lissajous)
    .mark_circle(size=18, opacity=0.9)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color("t:Q", title="Parameter t", scale=alt.Scale(scheme="viridis"), legend=color_legend),
        order="order:Q",
    )
)

liss_start = pd.DataFrame({"x": [df_lissajous["x"].iloc[0]], "y": [df_lissajous["y"].iloc[0]]})
liss_end = pd.DataFrame({"x": [df_lissajous["x"].iloc[-1]], "y": [df_lissajous["y"].iloc[-1]]})

liss_start_marker = (
    alt.Chart(liss_start)
    .mark_point(size=300, shape="circle", filled=True, color="#306998", stroke="white", strokeWidth=2)
    .encode(x="x:Q", y="y:Q")
)
liss_end_marker = (
    alt.Chart(liss_end)
    .mark_point(size=300, shape="diamond", filled=True, color="#E84855", stroke="white", strokeWidth=2)
    .encode(x="x:Q", y="y:Q")
)
liss_start_label = (
    alt.Chart(liss_start)
    .mark_text(fontSize=16, fontWeight="bold", dy=-18, color="#306998")
    .encode(x="x:Q", y="y:Q", text=alt.value("t = 0"))
)
liss_end_label = (
    alt.Chart(liss_end)
    .mark_text(fontSize=16, fontWeight="bold", dy=22, color="#E84855")
    .encode(x="x:Q", y="y:Q", text=alt.value("t = 2\u03c0"))
)

lissajous_panel = (liss_curve + liss_start_marker + liss_end_marker + liss_start_label + liss_end_label).properties(
    width=750, height=750, title=alt.Title("Lissajous \u00b7 x = sin(3t), y = sin(2t)", fontSize=22, color="#444")
)

# --- Spiral panel ---
spiral_curve = (
    alt.Chart(df_spiral)
    .mark_circle(size=18, opacity=0.9)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color("t:Q", title="Parameter t", scale=alt.Scale(scheme="viridis"), legend=color_legend),
        order="order:Q",
    )
)

spiral_start = pd.DataFrame({"x": [df_spiral["x"].iloc[0]], "y": [df_spiral["y"].iloc[0]]})
spiral_end = pd.DataFrame({"x": [df_spiral["x"].iloc[-1]], "y": [df_spiral["y"].iloc[-1]]})

spiral_start_marker = (
    alt.Chart(spiral_start)
    .mark_point(size=300, shape="circle", filled=True, color="#306998", stroke="white", strokeWidth=2)
    .encode(x="x:Q", y="y:Q")
)
spiral_end_marker = (
    alt.Chart(spiral_end)
    .mark_point(size=300, shape="diamond", filled=True, color="#E84855", stroke="white", strokeWidth=2)
    .encode(x="x:Q", y="y:Q")
)
spiral_start_label = (
    alt.Chart(spiral_start)
    .mark_text(fontSize=16, fontWeight="bold", dy=-18, color="#306998")
    .encode(x="x:Q", y="y:Q", text=alt.value("t = 0"))
)
spiral_end_label = (
    alt.Chart(spiral_end)
    .mark_text(fontSize=16, fontWeight="bold", dy=-18, color="#E84855")
    .encode(x="x:Q", y="y:Q", text=alt.value("t = 6\u03c0"))
)

spiral_panel = (
    spiral_curve + spiral_start_marker + spiral_end_marker + spiral_start_label + spiral_end_label
).properties(
    width=750,
    height=750,
    title=alt.Title("Archimedean Spiral \u00b7 x = t\u00b7cos(t), y = t\u00b7sin(t)", fontSize=22, color="#444"),
)

# --- Combine panels ---
chart = (
    alt.hconcat(lissajous_panel, spiral_panel, spacing=40)
    .resolve_scale(color="independent")
    .properties(
        title=alt.Title(
            "line-parametric \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            anchor="middle",
            color="#333",
            subtitle="Tracing curves in 2D space through parametric equations x(t) and y(t)",
            subtitleFontSize=18,
            subtitleColor="#777",
        )
    )
    .configure_axis(gridColor="#E0E0E0", gridOpacity=0.15, gridDash=[3, 3])
    .configure_view(strokeWidth=0)
)

# --- Save ---
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
