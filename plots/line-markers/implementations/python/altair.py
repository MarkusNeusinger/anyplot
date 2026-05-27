""" anyplot.ai
line-markers: Line Plot with Markers
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-12
"""

import os
import sys

import numpy as np
import pandas as pd


# Handle import shadowing: remove current dir from path temporarily
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != current_dir]

import altair as alt  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Quality control measurements over time (sparse dataset where each point matters)
np.random.seed(42)
times = np.array([1, 3, 6, 9, 12, 15, 18, 22, 26, 30])
batch_a = 99.2 + np.random.normal(0, 1.5, len(times))
batch_b = 98.8 + np.random.normal(0, 1.8, len(times))
batch_c = 99.5 + np.random.normal(0, 1.2, len(times))

df = pd.DataFrame(
    {
        "Time (hours)": np.concatenate([times, times, times]),
        "Quality (%)": np.concatenate([batch_a, batch_b, batch_c]),
        "Batch": np.repeat(["Batch A", "Batch B", "Batch C"], len(times)),
    }
)

# Plot
base_chart = alt.Chart(df).encode(
    x=alt.X("Time (hours):Q", title="Time (hours)"),
    y=alt.Y("Quality (%):Q", title="Quality (%)"),
    color=alt.Color("Batch:N", scale=alt.Scale(range=IMPRINT[:3])),
    strokeDash=alt.StrokeDash(
        "Batch:N", scale=alt.Scale(domain=["Batch A", "Batch B", "Batch C"], range=[[], [5, 5], [2, 2]])
    ),
)

line_chart = base_chart.mark_line(size=3) + base_chart.mark_point(size=150)

chart = (
    line_chart.properties(
        width=1600, height=900, background=PAGE_BG, title=alt.Title("line-markers · altair · anyplot.ai", fontSize=28)
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
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
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=16,
        titleFontSize=18,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
