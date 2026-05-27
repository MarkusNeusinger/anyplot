""" anyplot.ai
scatter-brush-zoom: Interactive Scatter Plot with Brush Selection and Zoom
Library: altair 6.1.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-16
"""

import os
import sys


# Work around module name conflict: ensure altair library is imported, not this file
if (
    "altair" in sys.modules
    and hasattr(sys.modules["altair"], "__file__")
    and "scatter-brush-zoom" in sys.modules["altair"].__file__
):
    del sys.modules["altair"]
sys.path = [p for p in sys.path if "scatter-brush-zoom" not in p]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Generate clustered data for brush selection demonstration
np.random.seed(42)

n_points = 200
clusters = []

# Cluster 1: Top-right (high performance sensors)
c1 = pd.DataFrame({"x": np.random.normal(75, 8, 50), "y": np.random.normal(80, 10, 50), "category": "Sensor A"})
clusters.append(c1)

# Cluster 2: Bottom-left (low performance sensors)
c2 = pd.DataFrame({"x": np.random.normal(25, 10, 50), "y": np.random.normal(30, 8, 50), "category": "Sensor B"})
clusters.append(c2)

# Cluster 3: Center (moderate performance)
c3 = pd.DataFrame({"x": np.random.normal(50, 12, 60), "y": np.random.normal(55, 12, 60), "category": "Sensor C"})
clusters.append(c3)

# Cluster 4: Scattered outliers
c4 = pd.DataFrame({"x": np.random.uniform(10, 90, 40), "y": np.random.uniform(10, 90, 40), "category": "Sensor D"})
clusters.append(c4)

df = pd.concat(clusters, ignore_index=True)
df["id"] = range(len(df))

# Define interval selection for brush (click-drag to select region)
brush = alt.selection_interval()

# Define color scale using Okabe-Ito palette
color_scale = alt.Scale(domain=["Sensor A", "Sensor B", "Sensor C", "Sensor D"], range=IMPRINT)

# Create the scatter plot with brush selection
points = (
    alt.Chart(df)
    .mark_circle(size=120, strokeWidth=2)
    .encode(
        x=alt.X("x:Q", title="Efficiency Score (%)", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y("y:Q", title="Reliability Index", scale=alt.Scale(domain=[0, 100])),
        color=alt.condition(brush, alt.Color("category:N", scale=color_scale, title="Category"), alt.value(INK_SOFT)),
        opacity=alt.condition(brush, alt.value(0.85), alt.value(0.3)),
        stroke=alt.condition(brush, alt.value(INK), alt.value("transparent")),
        tooltip=[
            alt.Tooltip("id:O", title="Point ID"),
            alt.Tooltip("category:N", title="Category"),
            alt.Tooltip("x:Q", title="Efficiency", format=".1f"),
            alt.Tooltip("y:Q", title="Reliability", format=".1f"),
        ],
    )
    .add_params(brush)
)

# Create a dummy layer for the legend (always shows full legend)
legend_layer = (
    alt.Chart(df)
    .mark_circle(size=0, opacity=0)
    .encode(color=alt.Color("category:N", scale=color_scale, title="Category"))
)

scatter = alt.layer(points, legend_layer).properties(
    width=1600,
    height=900,
    title=alt.Title(
        text="scatter-brush-zoom · altair · anyplot.ai",
        fontSize=28,
        anchor="middle",
        subtitle="Click and drag to select a region | Scroll to zoom | Shift+drag to pan",
        subtitleFontSize=18,
        subtitleColor=INK_SOFT,
    ),
)

# Create a bar chart showing count of selected points per category
bars = (
    alt.Chart(df)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X(
            "category:N",
            title="Category",
            axis=alt.Axis(labelFontSize=16, titleFontSize=18, labelAngle=0, labelPadding=15),
        ),
        y=alt.Y("count():Q", title="Selected Count", axis=alt.Axis(labelFontSize=16, titleFontSize=18)),
        color=alt.Color("category:N", scale=color_scale, legend=None),
    )
    .transform_filter(brush)
    .properties(width=1600, height=200, title=alt.Title(text="Selected Points by Category", fontSize=22))
)

# Combine charts vertically
chart = (
    alt.vconcat(scatter.interactive(), bars)
    .properties(background=PAGE_BG)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        labelFontSize=16,
        titleFontSize=20,
        gridColor=INK,
        gridOpacity=0.10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK, fontSize=28)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=18,
        labelFontSize=16,
        symbolSize=200,
    )
    .resolve_scale(color="shared")
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
