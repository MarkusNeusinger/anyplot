""" pyplots.ai
ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
Library: altair 6.0.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-02-17
"""

import altair as alt
import numpy as np
import pandas as pd
from scipy import stats


# Data - Credit scoring: Good vs Bad customer score distributions
np.random.seed(42)
good_scores = np.random.normal(loc=620, scale=80, size=300)
bad_scores = np.random.normal(loc=480, scale=90, size=300)

# K-S test
ks_stat, p_value = stats.ks_2samp(good_scores, bad_scores)

# Compute ECDFs using sorted arrays and normalized ranks
good_sorted = np.sort(good_scores)
bad_sorted = np.sort(bad_scores)
good_ecdf = np.arange(1, len(good_sorted) + 1) / len(good_sorted)
bad_ecdf = np.arange(1, len(bad_sorted) + 1) / len(bad_sorted)

# Find max divergence point by evaluating both ECDFs on combined grid
all_values = np.union1d(good_sorted, bad_sorted)
good_at_all = np.searchsorted(good_sorted, all_values, side="right") / len(good_sorted)
bad_at_all = np.searchsorted(bad_sorted, all_values, side="right") / len(bad_sorted)
max_idx = np.argmax(np.abs(good_at_all - bad_at_all))
ks_x = all_values[max_idx]
ks_y_good = good_at_all[max_idx]
ks_y_bad = bad_at_all[max_idx]

# Assemble DataFrames
good_df = pd.DataFrame({"Score": good_sorted, "ECDF": good_ecdf, "Group": "Good Customers"})
bad_df = pd.DataFrame({"Score": bad_sorted, "ECDF": bad_ecdf, "Group": "Bad Customers"})
ecdf_df = pd.concat([good_df, bad_df], ignore_index=True)

# Shaded region between ECDFs at max divergence (storytelling: highlight the gap)
n_shade = 40
shade_y = np.linspace(ks_y_bad, ks_y_good, n_shade)
shade_df = pd.DataFrame({"Score": ks_x, "y": shade_y})

# K-S distance vertical line endpoints
ks_line_df = pd.DataFrame({"Score": [ks_x, ks_x], "ECDF": [ks_y_bad, ks_y_good]})

# Annotation label at midpoint of distance line
ks_mid_y = (ks_y_good + ks_y_bad) / 2
ks_label_df = pd.DataFrame({"Score": [ks_x], "ECDF": [ks_mid_y], "label": [f"  D = {ks_stat:.3f}"]})

# Endpoint markers for the distance line
ks_endpoints_df = pd.DataFrame({"Score": [ks_x, ks_x], "ECDF": [ks_y_bad, ks_y_good]})

# Colors
BLUE = "#306998"
ORANGE = "#E8833A"
PURPLE = "#7B2D8E"  # distinct from both ECDF colors for annotations
BG_COLOR = "#FAFAFA"

color_scale = alt.Scale(domain=["Good Customers", "Bad Customers"], range=[BLUE, ORANGE])

# --- Layers ---

# ECDF step lines with distinct widths for visual hierarchy
ecdf_lines = (
    alt.Chart(ecdf_df)
    .mark_line(interpolate="step-after", strokeWidth=3.5)
    .encode(
        x=alt.X(
            "Score:Q",
            title="Credit Score",
            scale=alt.Scale(nice=True),
            axis=alt.Axis(values=list(range(200, 1001, 100))),
        ),
        y=alt.Y(
            "ECDF:Q",
            title="Cumulative Proportion",
            scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(values=[0, 0.2, 0.4, 0.6, 0.8, 1.0], format=".1f"),
        ),
        color=alt.Color("Group:N", scale=color_scale, legend=alt.Legend(title=None)),
        strokeDash=alt.StrokeDash(
            "Group:N", scale=alt.Scale(domain=["Good Customers", "Bad Customers"], range=[[1, 0], [8, 4]]), legend=None
        ),
        tooltip=["Group:N", alt.Tooltip("Score:Q", format=".0f"), alt.Tooltip("ECDF:Q", format=".3f")],
    )
)

# Shaded band at max divergence — visual storytelling element
shade_band = (
    alt.Chart(shade_df).mark_point(size=18, opacity=0.18, color=PURPLE, filled=True).encode(x="Score:Q", y="y:Q")
)

# K-S distance vertical line
ks_distance = (
    alt.Chart(ks_line_df).mark_line(color=PURPLE, strokeWidth=3, strokeDash=[8, 5]).encode(x="Score:Q", y="ECDF:Q")
)

# Endpoint dots on the distance line
ks_dots = (
    alt.Chart(ks_endpoints_df)
    .mark_point(color=PURPLE, size=120, filled=True, stroke="white", strokeWidth=1.5)
    .encode(x="Score:Q", y="ECDF:Q")
)

# K-S statistic label
ks_label = (
    alt.Chart(ks_label_df)
    .mark_text(align="left", fontSize=22, fontWeight="bold", color=PURPLE, font="monospace")
    .encode(x="Score:Q", y="ECDF:Q", text="label:N")
)

# Subtitle with statistical summary
p_text = "p < 0.001" if p_value < 0.001 else f"p = {p_value:.4f}"
subtitle_text = f"K-S Statistic: {ks_stat:.3f}  ·  {p_text}  ·  Distributions are significantly different"

# Combine layers with refined styling
chart = (
    alt.layer(shade_band, ecdf_lines, ks_distance, ks_dots, ks_label)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "ks-test-comparison · altair · pyplots.ai",
            subtitle=subtitle_text,
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#666666",
            anchor="start",
            offset=12,
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titleColor="#333333",
        labelColor="#555555",
        gridColor="#E0E0E0",
        gridOpacity=0.5,
        domainColor="#AAAAAA",
        tickColor="#AAAAAA",
    )
    .configure_legend(
        titleFontSize=18,
        labelFontSize=18,
        symbolSize=400,
        symbolStrokeWidth=3.5,
        orient="top-right",
        padding=12,
        cornerRadius=4,
        strokeColor="#CCCCCC",
        fillColor="white",
    )
    .configure_view(strokeWidth=0, fill=BG_COLOR)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
