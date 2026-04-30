""" anyplot.ai
ridgeline-basic: Basic Ridgeline Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-04-30
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

# Data
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

data = []
base_temps = [2, 4, 8, 14, 18, 22, 25, 24, 20, 14, 8, 4]
temp_stds = [4, 5, 5, 4, 4, 3, 3, 3, 4, 5, 5, 4]

for i, month in enumerate(months):
    temps = np.random.normal(base_temps[i], temp_stds[i], 200)
    for t in temps:
        data.append({"month": month, "temperature": t, "month_order": i})

df = pd.DataFrame(data)

# Plot - ridgeline via row faceting with negative spacing for overlap
chart = (
    alt.Chart(df)
    .transform_density(
        density="temperature",
        as_=["temperature", "density"],
        groupby=["month", "month_order"],
        extent=[-15, 40],
        bandwidth=2,
    )
    .mark_area(fillOpacity=0.8, stroke="#306998", strokeWidth=2, interpolate="monotone")
    .encode(
        x=alt.X(
            "temperature:Q",
            title="Temperature (°C)",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, grid=False),
            scale=alt.Scale(domain=[-15, 40]),
        ),
        y=alt.Y("density:Q", title=None, axis=None, scale=alt.Scale(domain=[0, 0.15])),
        fill=alt.Fill(
            "month_order:O", scale=alt.Scale(scheme="blues", domain=list(range(12)), reverse=True), legend=None
        ),
        row=alt.Row(
            "month:N",
            sort=months,
            header=alt.Header(
                labelFontSize=18, labelAngle=0, labelAlign="right", labelPadding=10, title=None, labelColor=INK_SOFT
            ),
        ),
    )
    .properties(
        width=1400,
        height=55,
        background=PAGE_BG,
        title=alt.Title(
            text="Monthly Temperature Distribution · ridgeline-basic · altair · anyplot.ai",
            fontSize=28,
            anchor="middle",
        ),
    )
    .configure_facet(spacing=-25)
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        labelFontSize=16,
        titleFontSize=20,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
    )
    .configure_title(color=INK)
    .configure_header(labelColor=INK_SOFT)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
