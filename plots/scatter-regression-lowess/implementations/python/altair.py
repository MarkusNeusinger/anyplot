"""anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import os
import sys

import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess


# Handle module name conflict by removing current directory from import path
original_path = sys.path[:]
sys.path = [p for p in sys.path if p not in ("", ".")]
import altair as alt  # noqa: E402


sys.path = original_path


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - complex non-linear relationship
np.random.seed(42)
n = 200
x = np.linspace(0, 10, n)
# Non-linear pattern: sine wave with trend and noise
y = 2 * np.sin(x * 0.8) + 0.5 * x + np.random.normal(0, 0.8, n)

# Create DataFrame for scatter points
df = pd.DataFrame({"x": x, "y": y})

# Compute LOWESS smoothed values
lowess_result = lowess(y, x, frac=0.3, return_sorted=True)
df_lowess = pd.DataFrame({"x": lowess_result[:, 0], "y_lowess": lowess_result[:, 1]})

# Scatter points layer with filled markers and tooltips
scatter = (
    alt.Chart(df)
    .mark_circle(size=100, opacity=0.6, color="#009E73")
    .encode(
        x=alt.X("x:Q", title="Independent Variable (meters)"),
        y=alt.Y("y:Q", title="Dependent Variable (kg)"),
        tooltip=["x:Q", "y:Q"],
    )
)

# LOWESS curve layer
lowess_line = (
    alt.Chart(df_lowess).mark_line(strokeWidth=4, color="#FFD43B").encode(x=alt.X("x:Q"), y=alt.Y("y_lowess:Q"))
)

# Combine layers and apply theme-adaptive styling
chart = (
    (scatter + lowess_line)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("scatter-regression-lowess · altair · anyplot.ai", fontSize=28),
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
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_title(color=INK)
)

# Save with theme-suffixed filenames
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
