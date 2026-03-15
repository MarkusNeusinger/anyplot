""" pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: altair 6.0.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-15
"""

from statistics import NormalDist

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)
observed = np.concatenate([np.random.normal(50, 10, 160), np.random.exponential(5, 40) + 55])
observed_sorted = np.sort(observed)
n = len(observed_sorted)

mu = float(observed_sorted.mean())
sigma = float(observed_sorted.std())
dist = NormalDist(mu, sigma)
empirical_cdf = np.arange(1, n + 1) / (n + 1)
theoretical_cdf = np.array([dist.cdf(x) for x in observed_sorted])

df = pd.DataFrame({"Theoretical CDF": theoretical_cdf, "Empirical CDF": empirical_cdf})

ref_df = pd.DataFrame({"x": [0, 1], "y": [0, 1]})

# Plot
reference_line = alt.Chart(ref_df).mark_line(strokeDash=[8, 6], strokeWidth=2, color="#AAAAAA").encode(x="x:Q", y="y:Q")

points = (
    alt.Chart(df)
    .mark_circle(size=120, color="#306998", opacity=0.7, stroke="white", strokeWidth=0.5)
    .encode(
        x=alt.X("Theoretical CDF:Q", scale=alt.Scale(domain=[0, 1]), title="Theoretical CDF (Normal)"),
        y=alt.Y("Empirical CDF:Q", scale=alt.Scale(domain=[0, 1]), title="Empirical CDF"),
        tooltip=["Theoretical CDF:Q", "Empirical CDF:Q"],
    )
)

chart = (
    (reference_line + points)
    .properties(
        width=1200, height=1200, title=alt.Title("pp-basic · altair · pyplots.ai", fontSize=28, fontWeight="bold")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.2, domainColor="#333333")
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
