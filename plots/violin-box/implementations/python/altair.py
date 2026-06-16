""" anyplot.ai
violin-box: Violin Plot with Embedded Box Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
"""

import os

import altair as alt
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Generate realistic response time data for different server tiers
np.random.seed(42)

groups = ["Basic", "Standard", "Premium", "Enterprise"]
n_per_group = 80

data = []
# Basic tier - higher latency, more variance
data.extend([(np.random.exponential(120) + 80, "Basic") for _ in range(n_per_group)])
# Standard tier - moderate latency
data.extend([(np.random.normal(100, 25), "Standard") for _ in range(n_per_group)])
# Premium tier - lower latency, tighter distribution
data.extend([(np.random.normal(60, 15), "Premium") for _ in range(n_per_group)])
# Enterprise tier - lowest latency, bimodal (some cached, some not)
enterprise_cached = np.random.normal(25, 8, n_per_group // 2)
enterprise_uncached = np.random.normal(55, 12, n_per_group // 2)
data.extend([(v, "Enterprise") for v in np.concatenate([enterprise_cached, enterprise_uncached])])

df = pd.DataFrame(data, columns=["Response Time (ms)", "Server Tier"])
df["Response Time (ms)"] = df["Response Time (ms)"].clip(lower=5)

# Create violin plot layer using transform_density
violin = (
    alt.Chart(df)
    .transform_density("Response Time (ms)", as_=["Response Time (ms)", "density"], groupby=["Server Tier"])
    .mark_area(orient="horizontal", opacity=0.6)
    .encode(
        y=alt.Y("Response Time (ms):Q"),
        x=alt.X(
            "density:Q",
            stack="center",
            impute=None,
            title=None,
            axis=alt.Axis(labels=False, values=[0], grid=False, ticks=False),
        ),
        color=alt.Color("Server Tier:N", scale=alt.Scale(domain=groups, range=IMPRINT)),
    )
)

# Create box plot layer
boxplot = (
    alt.Chart(df)
    .mark_boxplot(
        extent="min-max",
        size=25,
        median={"stroke": INK_SOFT, "strokeWidth": 2},
        box={"fill": INK_SOFT, "fillOpacity": 0.3},
        outliers={"size": 60, "strokeWidth": 2, "stroke": INK_SOFT},
    )
    .encode(y=alt.Y("Response Time (ms):Q", title="Response Time (ms)"), x=alt.value(0), color=alt.value(INK_SOFT))
)

# Layer violin and box plots first, then facet
layered = alt.layer(violin, boxplot).properties(width=280, height=600)

# Apply faceting after layering
chart = (
    layered.facet(
        column=alt.Column(
            "Server Tier:N",
            header=alt.Header(titleFontSize=20, labelFontSize=18, labelOrient="bottom"),
            title=None,
            sort=groups,
        )
    )
    .properties(
        title=alt.Title("violin-box · altair · anyplot.ai", fontSize=28, anchor="middle", offset=20), background=PAGE_BG
    )
    .configure_axis(
        labelFontSize=16,
        titleFontSize=20,
        gridOpacity=0.0,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_view(stroke=None, fill=PAGE_BG)
    .configure_legend(
        titleFontSize=18, labelFontSize=16, symbolSize=200, orient="right", titleColor=INK, labelColor=INK_SOFT
    )
    .configure_title(color=INK)
    .resolve_scale(x="independent")
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
