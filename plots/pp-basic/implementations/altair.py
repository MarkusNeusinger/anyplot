""" pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: altair 6.0.0 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-15
"""

from statistics import NormalDist

import altair as alt
import numpy as np
import pandas as pd


# Data — clinical trial: blood pressure measurements vs normal reference
np.random.seed(42)
observed = np.concatenate([np.random.normal(50, 10, 160), np.random.exponential(5, 40) + 55])
observed_sorted = np.sort(observed)
n = len(observed_sorted)

mu = float(observed_sorted.mean())
sigma = float(observed_sorted.std())
dist = NormalDist(mu, sigma)
empirical_cdf = np.arange(1, n + 1) / (n + 1)
theoretical_cdf = np.array([dist.cdf(x) for x in observed_sorted])
deviation = np.abs(empirical_cdf - theoretical_cdf)

# Mark the point of maximum deviation for annotation
max_dev_idx = int(np.argmax(deviation))
is_max_deviation = [i == max_dev_idx for i in range(n)]

df = pd.DataFrame(
    {
        "Theoretical CDF (Normal)": theoretical_cdf,
        "Empirical CDF": empirical_cdf,
        "Deviation": deviation,
        "Max Deviation": is_max_deviation,
    }
)

ref_df = pd.DataFrame({"x": [0, 1], "y": [0, 1]})

# Confidence band around diagonal (± ~1.36/√n Kolmogorov-Smirnov bound)
ks_bound = 1.36 / np.sqrt(n)
band_x = np.linspace(0, 1, 50)
band_df = pd.DataFrame(
    {"x": band_x, "y_lo": np.clip(band_x - ks_bound, 0, 1), "y_hi": np.clip(band_x + ks_bound, 0, 1)}
)

# Max deviation annotation label
max_dev_df = pd.DataFrame(
    {
        "x": [theoretical_cdf[max_dev_idx]],
        "y": [empirical_cdf[max_dev_idx]],
        "label": [f"Max deviation: {deviation[max_dev_idx]:.3f}"],
    }
)

# Interactive selection — hovering highlights nearby points (Altair-distinctive)
hover = alt.selection_point(on="pointerover", nearest=True, empty=False)

# Plot layers
band = (
    alt.Chart(band_df).mark_area(opacity=0.08, color="#306998").encode(x=alt.X("x:Q"), y=alt.Y("y_lo:Q"), y2="y_hi:Q")
)

reference_line = (
    alt.Chart(ref_df).mark_line(strokeDash=[8, 6], strokeWidth=2.5, color="#999999").encode(x="x:Q", y="y:Q")
)

points = (
    alt.Chart(df)
    .mark_circle(stroke="#1a3a5c", strokeWidth=0.8)
    .encode(
        x=alt.X("Theoretical CDF (Normal):Q", scale=alt.Scale(domain=[0, 1]), title="Theoretical CDF (Normal)"),
        y=alt.Y("Empirical CDF:Q", scale=alt.Scale(domain=[0, 1]), title="Empirical CDF"),
        color=alt.Color(
            "Deviation:Q",
            scale=alt.Scale(scheme="blues", domain=[0, float(deviation.max())]),
            legend=alt.Legend(
                title="Deviation",
                titleFontSize=16,
                labelFontSize=14,
                orient="bottom-right",
                direction="vertical",
                gradientLength=150,
            ),
        ),
        size=alt.condition(
            hover, alt.value(280), alt.Size("Deviation:Q", scale=alt.Scale(range=[55, 200]), legend=None)
        ),
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.65)),
        strokeWidth=alt.condition(hover, alt.value(2.0), alt.value(0.8)),
        tooltip=[
            alt.Tooltip("Theoretical CDF (Normal):Q", format=".3f"),
            alt.Tooltip("Empirical CDF:Q", format=".3f"),
            alt.Tooltip("Deviation:Q", format=".4f", title="Abs. Deviation"),
        ],
    )
    .add_params(hover)
)

# Highlight max-deviation point with contrasting ring
max_point = (
    alt.Chart(max_dev_df)
    .mark_circle(size=400, stroke="#d62728", strokeWidth=2.5, filled=False)
    .encode(x="x:Q", y="y:Q")
)

max_label = (
    alt.Chart(max_dev_df)
    .mark_text(align="left", dx=14, dy=-10, fontSize=15, fontWeight="bold", color="#d62728")
    .encode(x="x:Q", y="y:Q", text="label:N")
)

chart = (
    (band + reference_line + points + max_point + max_label)
    .properties(
        width=1200,
        height=1200,
        title=alt.Title(
            "pp-basic · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            subtitle="Blood pressure normality check — points colored by deviation from perfect fit",
            subtitleFontSize=18,
            subtitleColor="#666666",
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titleColor="#333333",
        labelColor="#555555",
        grid=True,
        gridOpacity=0.15,
        gridColor="#cccccc",
        domainColor="#888888",
        tickColor="#888888",
    )
    .configure_view(strokeWidth=0)
    .configure_legend(strokeColor="#dddddd", padding=10, cornerRadius=4, fillColor="#fafafa")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
