""" anyplot.ai
count-basic: Basic Count Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-07
"""

import os
import sys


sys.path = [p for p in sys.path if not p.endswith("implementations/python")]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1

# Data: Survey responses with varying frequencies
np.random.seed(42)
responses = np.random.choice(
    ["Excellent", "Good", "Average", "Poor", "Very Poor"], size=200, p=[0.25, 0.35, 0.20, 0.12, 0.08]
)
df = pd.DataFrame({"Response": responses})

# Create chart using Altair's native count() aggregation
chart = (
    alt.Chart(df)
    .mark_bar(color=BRAND, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X("Response:N", sort="-y", title="Survey Response"), y=alt.Y("count():Q", title="Number of Responses")
    )
)

# Add count labels on top of bars
text = chart.mark_text(align="center", baseline="bottom", dy=-8, fontSize=18, fontWeight="bold").encode(
    text="count():Q"
)

# Combine bar and text
final_chart = (
    (chart + text)
    .properties(
        width=1600, height=900, background=PAGE_BG, title=alt.Title("count-basic · altair · anyplot.ai", fontSize=28)
    )
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
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
final_chart.save(f"plot-{THEME}.png", scale_factor=3.0)
final_chart.save(f"plot-{THEME}.html")
