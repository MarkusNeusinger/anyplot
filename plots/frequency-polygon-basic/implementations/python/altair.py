""" pyplots.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import altair as alt
import numpy as np
import pandas as pd


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

# Colors: Python Blue, Python Yellow, and a third colorblind-safe color
colors = ["#306998", "#FFD43B", "#E377C2"]

# Create frequency polygon chart
chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("Response Time (ms):Q", title="Response Time (ms)"),
        y=alt.Y("Frequency:Q", title="Frequency"),
        color=alt.Color(
            "Condition:N",
            scale=alt.Scale(domain=["Control", "Treatment A", "Treatment B"], range=colors),
            legend=alt.Legend(title="Condition", titleFontSize=20, labelFontSize=18),
        ),
        strokeDash=alt.StrokeDash(
            "Condition:N",
            scale=alt.Scale(domain=["Control", "Treatment A", "Treatment B"], range=[[1, 0], [8, 4], [4, 4]]),
            legend=None,
        ),
    )
    .properties(width=1600, height=900, title="frequency-polygon-basic · altair · pyplots.ai")
    .configure_title(fontSize=28, anchor="middle")
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_legend(orient="right", padding=20)
)

# Save as PNG (4800 x 2700 px) and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
