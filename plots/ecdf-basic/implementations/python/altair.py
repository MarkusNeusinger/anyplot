""" anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: altair 6.1.0 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-24
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data: API response latency from a production web service
np.random.seed(42)
response_times_ms = np.random.normal(loc=120, scale=35, size=250)
response_times_ms = np.clip(response_times_ms, 20, None)

sorted_latency = np.sort(response_times_ms)
cumulative_proportion = np.arange(1, len(sorted_latency) + 1) / len(sorted_latency)

df = pd.DataFrame({"latency_ms": sorted_latency, "cumulative": cumulative_proportion})

# Chart
chart = (
    alt.Chart(df)
    .mark_line(interpolate="step-after", strokeWidth=3.5, color=BRAND)
    .encode(
        x=alt.X("latency_ms:Q", title="API Response Time (ms)", scale=alt.Scale(nice=True)),
        y=alt.Y(
            "cumulative:Q",
            title="Cumulative Proportion",
            scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(format=".0%", tickCount=11),
        ),
        tooltip=[
            alt.Tooltip("latency_ms:Q", title="Latency (ms)", format=".1f"),
            alt.Tooltip("cumulative:Q", title="Proportion", format=".3f"),
        ],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("ecdf-basic · altair · anyplot.ai", fontSize=28, color=INK),
    )
    .interactive()
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
    )
    .configure_title(color=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
