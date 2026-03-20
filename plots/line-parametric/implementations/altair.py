""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: altair 6.0.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Lissajous figure and Archimedean spiral
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

# Shared axis configuration
axis_config = alt.Axis(
    labelFontSize=18, titleFontSize=22, domainColor="#888", domainWidth=0.5, tickColor="#888", tickSize=4
)
scale_xy = alt.Scale(domain=[-1.15, 1.15])


def make_curve_chart(df, subtitle, end_label, sel_name, label_offsets=None):
    """Build a single parametric curve panel with markers and tooltips."""
    nearest = alt.selection_point(name=sel_name, nearest=True, on="pointerover", fields=["order"], empty=False)

    base = alt.Chart(df).encode(
        x=alt.X("x:Q", title="x(t)", scale=scale_xy, axis=axis_config),
        y=alt.Y("y:Q", title="y(t)", scale=scale_xy, axis=axis_config),
    )

    curve = base.mark_circle(size=18, opacity=0.9).encode(
        color=alt.Color(
            "t:Q",
            title="Parameter t",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(titleFontSize=18, labelFontSize=16, gradientLength=300, gradientThickness=20),
        ),
        order="order:Q",
        tooltip=[
            alt.Tooltip("t:Q", title="t", format=".3f"),
            alt.Tooltip("x:Q", title="x(t)", format=".4f"),
            alt.Tooltip("y:Q", title="y(t)", format=".4f"),
        ],
    )

    # Voronoi-based selection for interactive crosshair highlight
    selectors = (
        base.mark_point(size=0, opacity=0)
        .encode(opacity=alt.condition(nearest, alt.value(1), alt.value(0)))
        .add_params(nearest)
    )

    highlight = base.mark_point(size=200, color="#E84855", strokeWidth=2, filled=False).encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Start/end markers with offset control for overlapping points
    dy_start, dy_end = label_offsets or (-18, -18)
    start_pt = pd.DataFrame({"x": [df["x"].iloc[0]], "y": [df["y"].iloc[0]]})
    end_pt = pd.DataFrame({"x": [df["x"].iloc[-1]], "y": [df["y"].iloc[-1]]})

    start_marker = (
        alt.Chart(start_pt)
        .mark_point(size=300, shape="circle", filled=True, color="#306998", stroke="white", strokeWidth=2)
        .encode(x="x:Q", y="y:Q")
    )

    end_marker = (
        alt.Chart(end_pt)
        .mark_point(size=300, shape="diamond", filled=True, color="#E84855", stroke="white", strokeWidth=2)
        .encode(x="x:Q", y="y:Q")
    )

    start_label = (
        alt.Chart(start_pt)
        .mark_text(fontSize=16, fontWeight="bold", dy=dy_start, color="#306998")
        .encode(x="x:Q", y="y:Q", text=alt.value("t = 0"))
    )

    end_label_mark = (
        alt.Chart(end_pt)
        .mark_text(fontSize=16, fontWeight="bold", dy=dy_end, color="#E84855")
        .encode(x="x:Q", y="y:Q", text=alt.value(end_label))
    )

    return (curve + selectors + highlight + start_marker + end_marker + start_label + end_label_mark).properties(
        width=750, height=750, title=alt.Title(subtitle, fontSize=22)
    )


# Build both panels — Lissajous start/end overlap, so offset labels vertically
lissajous_chart = make_curve_chart(
    df_lissajous, "Lissajous · x = sin(3t), y = sin(2t)", "t = 2π", sel_name="nearest_liss", label_offsets=(-18, 22)
)
spiral_chart = make_curve_chart(
    df_spiral, "Archimedean Spiral · x = t·cos(t), y = t·sin(t)", "t = 6π", sel_name="nearest_spiral"
)

# Combine side by side with independent color scales for full gradient range per curve
chart = (
    alt.hconcat(lissajous_chart, spiral_chart)
    .resolve_scale(color="independent")
    .properties(title=alt.Title("line-parametric · altair · pyplots.ai", fontSize=28, anchor="middle"))
    .configure_axis(gridColor="#E0E0E0", gridOpacity=0.2)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
