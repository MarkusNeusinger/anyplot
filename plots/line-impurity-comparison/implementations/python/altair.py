""" pyplots.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: altair 6.0.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-02-17
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
p = np.linspace(0, 1, 200)
gini = 2 * p * (1 - p)

# Entropy with safe log computation (0 at boundaries)
with np.errstate(divide="ignore", invalid="ignore"):
    entropy_raw = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
entropy_raw = np.nan_to_num(entropy_raw, nan=0.0)
entropy = entropy_raw / np.max(entropy_raw)

df = pd.DataFrame(
    {
        "p": np.tile(p, 2),
        "Impurity": np.concatenate([gini, entropy]),
        "Measure": ["Gini: 2p(1−p)"] * len(p) + ["Entropy (scaled)"] * len(p),
    }
)

# Annotation at p = 0.5 where both measures peak
annotation_df = pd.DataFrame({"p": [0.5, 0.5], "Impurity": [0.5, 1.0], "label": ["Gini max = 0.5", "Entropy max"]})

# Plot
color_scale = alt.Scale(domain=["Gini: 2p(1−p)", "Entropy (scaled)"], range=["#306998", "#E8833A"])

lines = (
    alt.Chart(df)
    .mark_line(strokeWidth=4)
    .encode(
        x=alt.X(
            "p:Q",
            title="Probability (p)",
            scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        y=alt.Y(
            "Impurity:Q",
            title="Impurity Measure (normalized)",
            scale=alt.Scale(domain=[0, 1.05]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        color=alt.Color(
            "Measure:N",
            scale=color_scale,
            legend=alt.Legend(
                title=None, labelFontSize=16, orient="top-right", offset=10, symbolStrokeWidth=4, symbolSize=300
            ),
        ),
    )
)

annotation_point = (
    alt.Chart(annotation_df).mark_point(size=200, filled=True, color="#333333").encode(x="p:Q", y="Impurity:Q")
)

annotation_text = (
    alt.Chart(annotation_df)
    .mark_text(fontSize=15, dx=70, fontWeight="bold", color="#333333", align="left")
    .encode(x="p:Q", y="Impurity:Q", text="label:N")
)

# Vertical rule at p = 0.5
rule_df = pd.DataFrame({"p": [0.5]})
vertical_rule = alt.Chart(rule_df).mark_rule(strokeDash=[6, 4], strokeWidth=1.5, color="#999999").encode(x="p:Q")

# Combine layers
chart = (
    (lines + vertical_rule + annotation_point + annotation_text)
    .properties(width=1600, height=900, title=alt.Title("line-impurity-comparison · altair · pyplots.ai", fontSize=28))
    .configure_axis(gridColor="#E0E0E0", gridOpacity=0.2)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
