""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: altair 6.1.0 | Python 3.14.4
Quality: 88/100 | Created: 2026-04-23
"""

import importlib
import os
import sys


# Drop script directory from sys.path so the `altair` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data
np.random.seed(42)
n = 180
study_hours = np.random.uniform(1, 12, n)
exam_scores = np.clip(40 + study_hours * 4.8 + np.random.randn(n) * 7.5, 30, 100)
df = pd.DataFrame({"hours": study_hours, "score": exam_scores})

# Plot
points = (
    alt.Chart(df)
    .mark_circle(size=180, opacity=0.7, color=BRAND, stroke=PAGE_BG, strokeWidth=0.8)
    .encode(
        x=alt.X("hours:Q", title="Study Hours per Week", scale=alt.Scale(domain=[0, 13], nice=False)),
        y=alt.Y("score:Q", title="Exam Score (%)", scale=alt.Scale(domain=[25, 105], nice=False)),
    )
)

chart = (
    points.properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(
            "scatter-basic · altair · anyplot.ai",
            fontSize=28,
            fontWeight="normal",
            color=INK,
            anchor="start",
            offset=16,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titlePadding=14,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        gridWidth=0.8,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
