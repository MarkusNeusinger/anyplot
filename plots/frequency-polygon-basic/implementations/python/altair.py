""" anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-17
"""

import os
import site
import sys


# Workaround for script name shadowing the altair package
sys.path = (
    site.getsitepackages()
    + [site.getusersitepackages()]
    + [p for p in sys.path if p not in site.getsitepackages() + [site.getusersitepackages()]]
)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens (Okabe-Ito palette + theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (colorblind-safe)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Response times (ms) by experimental condition
np.random.seed(42)

# Three groups with different distributions
control = np.random.normal(loc=450, scale=80, size=200)
treatment_a = np.random.normal(loc=380, scale=60, size=200)
treatment_b = np.random.normal(loc=420, scale=100, size=200)

# Compute histogram bins aligned across all groups
all_data = np.concatenate([control, treatment_a, treatment_b])
bin_edges = np.histogram_bin_edges(all_data, bins=20)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Compute frequencies for each group and build polygon data
data_rows = []
for data, group_name in [(control, "Control"), (treatment_a, "Treatment A"), (treatment_b, "Treatment B")]:
    counts, _ = np.histogram(data, bins=bin_edges)
    # Extend to zero at both ends to close the polygon shape
    x = np.concatenate([[bin_edges[0]], bin_centers, [bin_edges[-1]]])
    y = np.concatenate([[0], counts, [0]])
    for xi, yi in zip(x, y, strict=True):
        data_rows.append({"Response Time (ms)": xi, "Frequency": yi, "Condition": group_name})

df = pd.DataFrame(data_rows)

# Create frequency polygon chart
chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("Response Time (ms):Q", title="Response Time (ms)"),
        y=alt.Y("Frequency:Q", title="Frequency"),
        color=alt.Color(
            "Condition:N",
            scale=alt.Scale(domain=["Control", "Treatment A", "Treatment B"], range=IMPRINT),
            legend=alt.Legend(title="Condition", titleFontSize=20, labelFontSize=18),
        ),
        strokeDash=alt.StrokeDash(
            "Condition:N",
            scale=alt.Scale(domain=["Control", "Treatment A", "Treatment B"], range=[[1, 0], [8, 4], [4, 4]]),
            legend=None,
        ),
    )
    .properties(width=1600, height=900, background=PAGE_BG)
    .configure_title(fontSize=28, anchor="middle", color=INK)
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridOpacity=0.10,
        gridColor=INK,
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, titleColor=INK, labelColor=INK_SOFT)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
)

# Add title with format: spec-id · library · anyplot.ai
chart = chart.properties(title="frequency-polygon-basic · altair · anyplot.ai")

# Save as PNG (4800 x 2700 px) and HTML
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
