"""anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: altair | Python 3.13
Quality: pending | Created: 2025-12-26
"""

import os
import sys
from pathlib import Path


current_dir = Path(__file__).parent
sys.path = [p for p in sys.path if p != str(current_dir)]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"

# Data - bivariate distribution with correlation
np.random.seed(42)
n = 150
x = np.random.randn(n) * 15 + 50
y = 0.7 * x + np.random.randn(n) * 10 + 20

df = pd.DataFrame({"X Value": x, "Y Value": y})

# Shared axis domains for proper alignment
x_domain = [df["X Value"].min() - 2, df["X Value"].max() + 2]
y_domain = [df["Y Value"].min() - 2, df["Y Value"].max() + 2]

# Base chart
base = alt.Chart(df)

# Main scatter plot with grid
scatter = (
    base.mark_circle(size=120, opacity=0.65, color=BRAND)
    .encode(
        x=alt.X("X Value:Q", title="X Value (units)", scale=alt.Scale(domain=x_domain)),
        y=alt.Y("Y Value:Q", title="Y Value (units)", scale=alt.Scale(domain=y_domain)),
        tooltip=["X Value:Q", "Y Value:Q"],
    )
    .properties(width=1000, height=600)
)

# Top marginal histogram with matching X scale
top_hist = (
    base.mark_bar(color=BRAND, opacity=0.5)
    .encode(
        x=alt.X(
            "X Value:Q",
            bin=alt.Bin(maxbins=25),
            title=None,
            scale=alt.Scale(domain=x_domain),
            axis=alt.Axis(labels=False, ticks=False),
        ),
        y=alt.Y("count()", title=None, axis=alt.Axis(labels=False, ticks=False)),
    )
    .properties(width=1000, height=120)
)

# Right marginal histogram with matching Y scale
right_hist = (
    base.mark_bar(color=BRAND, opacity=0.5)
    .encode(
        y=alt.Y(
            "Y Value:Q",
            bin=alt.Bin(maxbins=25),
            title=None,
            scale=alt.Scale(domain=y_domain),
            axis=alt.Axis(labels=False, ticks=False),
        ),
        x=alt.X("count()", title=None, axis=alt.Axis(labels=False, ticks=False)),
    )
    .properties(width=120, height=600)
)

# Combine: top histogram above, scatter with right histogram below
combined = (
    alt.vconcat(top_hist, alt.hconcat(scatter, right_hist, spacing=5), spacing=5)
    .properties(
        background=PAGE_BG,
        title=alt.Title(text="scatter-marginal · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=16,
        titleColor=INK,
        titleFontSize=20,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=1)
    .configure_concat(spacing=5)
)

# Save outputs
combined.save(f"plot-{THEME}.png", scale_factor=3.0)
combined.save(f"plot-{THEME}.html")
