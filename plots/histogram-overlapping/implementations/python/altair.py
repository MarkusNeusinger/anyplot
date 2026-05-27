""" anyplot.ai
histogram-overlapping: Overlapping Histograms
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-08
"""

import os
import sys


sys.path.insert(0, os.path.dirname(sys.executable) + "/../lib/python3.13/site-packages")

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is ALWAYS #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data: Employee response times (ms) by department
np.random.seed(42)

engineering = np.random.normal(loc=350, scale=80, size=150)
sales = np.random.normal(loc=420, scale=100, size=150)
support = np.random.normal(loc=280, scale=60, size=150)

df = pd.DataFrame(
    {
        "Response Time (ms)": np.concatenate([engineering, sales, support]),
        "Department": ["Engineering"] * 150 + ["Sales"] * 150 + ["Support"] * 150,
    }
)

# Plot - overlapping histograms with semi-transparent bars
chart = (
    alt.Chart(df)
    .mark_bar(opacity=0.5, binSpacing=0)
    .encode(
        x=alt.X(
            "Response Time (ms):Q",
            bin=alt.Bin(maxbins=25),
            title="Response Time (ms)",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        y=alt.Y("count():Q", title="Frequency", stack=None, axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        color=alt.Color(
            "Department:N",
            scale=alt.Scale(domain=["Engineering", "Sales", "Support"], range=IMPRINT[:3]),
            legend=alt.Legend(
                title="Department",
                titleFontSize=20,
                labelFontSize=18,
                orient="right",
                symbolSize=300,
                symbolStrokeWidth=0,
            ),
        ),
        tooltip=[alt.Tooltip("Department:N"), alt.Tooltip("count():Q", title="Count")],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("histogram-overlapping · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.1, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
