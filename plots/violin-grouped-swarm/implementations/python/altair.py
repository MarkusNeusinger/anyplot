""" pyplots.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: altair 6.0.0 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-09
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Response times across task types and expertise levels
np.random.seed(42)

categories = ["Simple", "Moderate", "Complex"]
groups = ["Novice", "Expert"]
n_per_group = 40

data = []
for cat in categories:
    for grp in groups:
        # Base response time varies by task complexity
        base = {"Simple": 2.0, "Moderate": 4.5, "Complex": 8.0}[cat]
        # Experts are faster with less variance
        if grp == "Expert":
            base *= 0.6
            spread = 0.8
        else:
            spread = 1.5

        values = np.random.normal(base, spread, n_per_group)
        values = np.clip(values, 0.5, 15)  # Realistic bounds

        for v in values:
            data.append({"Task Type": cat, "Expertise": grp, "Response Time (s)": v})

df = pd.DataFrame(data)

# Color palette - Python colors
colors = ["#306998", "#FFD43B"]

# Create base chart with legend title matching data column
base = alt.Chart(df).encode(
    color=alt.Color(
        "Expertise:N",
        scale=alt.Scale(domain=["Novice", "Expert"], range=colors),
        legend=alt.Legend(
            title="Expertise", titleFontSize=22, labelFontSize=20, orient="right", symbolSize=400, offset=20
        ),
    )
)

# Violin plot using density transform with horizontal orientation
violin = (
    base.transform_density(
        "Response Time (s)", as_=["Response Time (s)", "density"], groupby=["Task Type", "Expertise"]
    )
    .mark_area(orient="horizontal", opacity=0.5)
    .encode(
        x=alt.X(
            "density:Q",
            stack="center",
            impute=None,
            title=None,
            axis=alt.Axis(labels=False, values=[0], grid=False, ticks=False),
        ),
        y=alt.Y("Response Time (s):Q", title="Response Time (s)", axis=alt.Axis(grid=True, gridOpacity=0.3)),
    )
)

# Swarm points with jitter transform - better aligned with violin positions
# Using narrower jitter range and more precise offset to center points within violins
swarm = (
    base.mark_circle(opacity=0.85, size=120)
    .encode(
        x=alt.X(
            "jitter:Q",
            title=None,
            axis=alt.Axis(labels=False, values=[0], grid=False, ticks=False),
            scale=alt.Scale(domain=[-1, 1]),
        ),
        y=alt.Y("Response Time (s):Q"),
        color=alt.Color("Expertise:N", scale=alt.Scale(domain=["Novice", "Expert"], range=colors), legend=None),
    )
    .transform_calculate(jitter='(random() - 0.5) * 0.15 + (datum.Expertise === "Novice" ? -0.3 : 0.3)')
)

# Layer and then facet
# Width and height sized to achieve ~4800x2700 at scale 3
# 1600 x 3 = 4800, but faceted so each facet is smaller
chart = (
    alt.layer(violin, swarm)
    .facet(
        column=alt.Column(
            "Task Type:N",
            sort=categories,
            header=alt.Header(title="Task Type", titleFontSize=24, labelFontSize=22, labelOrient="bottom"),
        )
    )
    .resolve_scale(x="independent")
    .properties(title=alt.Title("violin-grouped-swarm · altair · pyplots.ai", fontSize=32, anchor="middle", offset=20))
    .configure_axis(labelFontSize=20, titleFontSize=24)
    .configure_view(strokeWidth=0, continuousWidth=400, continuousHeight=700)
    .configure_facet(spacing=40)
)

# Save as PNG and HTML
# Target ~4800x2700: using scale_factor to achieve this
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
