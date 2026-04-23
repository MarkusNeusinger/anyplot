"""anyplot.ai
scatter-basic: Basic Scatter Plot
Library: altair | Python 3.14
Quality: pending | Updated: 2026-04-23
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1 — always first series

# Data — study hours vs. exam scores (moderate positive correlation, r~0.7)
np.random.seed(42)
n = 180
study_hours = np.random.uniform(1, 10, n)
exam_scores = np.clip(40 + study_hours * 5 + np.random.normal(0, 7, n), 30, 100)
df = pd.DataFrame({"hours": study_hours, "score": exam_scores})

# Plot
chart = (
    alt.Chart(df)
    .mark_point(filled=True, size=180, opacity=0.7, color=BRAND, stroke=PAGE_BG, strokeWidth=0.8)
    .encode(
        x=alt.X(
            "hours:Q",
            title="Study Hours per Day",
            scale=alt.Scale(domain=[0, 11], nice=False),
            axis=alt.Axis(tickCount=11),
        ),
        y=alt.Y(
            "score:Q", title="Exam Score (%)", scale=alt.Scale(domain=[25, 105], nice=False), axis=alt.Axis(tickCount=8)
        ),
        tooltip=[
            alt.Tooltip("hours:Q", title="Study Hours", format=".1f"),
            alt.Tooltip("score:Q", title="Exam Score (%)", format=".1f"),
        ],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(
            "scatter-basic · altair · anyplot.ai",
            fontSize=28,
            fontWeight="normal",
            color=INK,
            anchor="start",
            offset=18,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titlePadding=12,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .interactive()
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
