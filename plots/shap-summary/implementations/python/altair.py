""" pyplots.ai
shap-summary: SHAP Summary Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Generate synthetic SHAP values for a model explanation visualization
np.random.seed(42)
n_samples = 300
n_features = 10

# Feature names representing typical ML model inputs
feature_names = [
    "Account Age (months)",
    "Transaction Count",
    "Avg Transaction ($)",
    "Credit Score",
    "Income ($K)",
    "Debt Ratio",
    "Payment History",
    "Account Balance ($)",
    "Login Frequency",
    "Support Tickets",
]

# Create synthetic feature values (normalized to 0-1 for color mapping)
feature_values = np.random.rand(n_samples, n_features)

# Create synthetic SHAP values with varying importances per feature
# Higher importance = wider spread of SHAP values
feature_importances = np.array([0.25, 0.20, 0.15, 0.12, 0.10, 0.07, 0.05, 0.03, 0.02, 0.01])
shap_values = np.zeros((n_samples, n_features))

for i in range(n_features):
    # Create SHAP-like values: correlation with feature value + noise
    # More important features have larger SHAP value spreads
    base_effect = (feature_values[:, i] - 0.5) * feature_importances[i] * 4
    noise = np.random.randn(n_samples) * feature_importances[i] * 0.5
    shap_values[:, i] = base_effect + noise

# Sort features by importance (already ordered, but calculate mean abs for verification)
mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
feature_order = np.argsort(mean_abs_shap)[::-1]
feature_order_names = [feature_names[i] for i in feature_order]

# Build dataframe for Altair
rows = []
for feat_idx in feature_order:
    for sample_idx in range(n_samples):
        rows.append(
            {
                "Feature": feature_names[feat_idx],
                "SHAP Value": shap_values[sample_idx, feat_idx],
                "Feature Value": feature_values[sample_idx, feat_idx],
                "Importance": mean_abs_shap[feat_idx],
            }
        )

df = pd.DataFrame(rows)

# Create the SHAP summary plot
scatter = (
    alt.Chart(df)
    .mark_circle(opacity=0.7, stroke="#333333", strokeWidth=0.3)
    .encode(
        x=alt.X(
            "SHAP Value:Q",
            title="SHAP Value (Impact on Model Output)",
            axis=alt.Axis(titleFontSize=22, labelFontSize=18, grid=True, gridOpacity=0.3),
        ),
        y=alt.Y("Feature:N", title=None, sort=feature_order_names, axis=alt.Axis(labelFontSize=18)),
        color=alt.Color(
            "Feature Value:Q",
            scale=alt.Scale(scheme="blueorange", domain=[0, 1]),
            legend=alt.Legend(
                title="Feature Value", titleFontSize=18, labelFontSize=16, orient="right", gradientLength=200
            ),
        ),
        size=alt.value(80),
        yOffset=alt.YOffset("jitter:Q", scale=alt.Scale(domain=[-1, 1], range=[-15, 15])),
    )
    .transform_calculate(jitter="random() * 2 - 1")
)

# Add vertical line at x=0
zero_line = (
    alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#333333", strokeWidth=2, strokeDash=[5, 3]).encode(x="x:Q")
)

# Combine scatter and zero line
chart = (
    (zero_line + scatter)
    .properties(
        width=1400, height=850, title=alt.Title("shap-summary · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=18, labelFontSize=16)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
