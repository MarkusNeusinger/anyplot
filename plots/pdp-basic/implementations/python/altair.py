""" pyplots.ai
pdp-basic: Partial Dependence Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Data - Train a model and compute partial dependence
np.random.seed(42)
X, y = make_regression(n_samples=500, n_features=5, noise=10, random_state=42)
feature_names = ["Temperature", "Pressure", "Humidity", "Flow Rate", "Duration"]

# Train gradient boosting model
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, y)

# Compute partial dependence for feature 0 (Temperature)
feature_idx = 0
grid_resolution = 80
pd_result = partial_dependence(model, X, features=[feature_idx], grid_resolution=grid_resolution, kind="average")

# Extract data
feature_values = pd_result["grid_values"][0]
pd_values = pd_result["average"][0]

# Bootstrap for confidence intervals
n_bootstrap = 50
bootstrap_pds = []
for _ in range(n_bootstrap):
    indices = np.random.choice(len(X), size=len(X), replace=True)
    X_boot = X[indices]
    pd_boot = partial_dependence(model, X_boot, features=[feature_idx], grid_resolution=grid_resolution, kind="average")
    bootstrap_pds.append(pd_boot["average"][0])

bootstrap_pds = np.array(bootstrap_pds)
ci_lower = np.percentile(bootstrap_pds, 2.5, axis=0)
ci_upper = np.percentile(bootstrap_pds, 97.5, axis=0)

# Create DataFrame for main line and confidence band
df_line = pd.DataFrame({"Feature Value": feature_values, "Partial Dependence": pd_values})

df_band = pd.DataFrame({"Feature Value": feature_values, "CI Lower": ci_lower, "CI Upper": ci_upper})

# Create rug plot data (sample of training data distribution)
rug_sample = np.random.choice(X[:, feature_idx], size=min(100, len(X)), replace=False)
df_rug = pd.DataFrame(
    {"Feature Value": rug_sample, "y": [pd_values.min() - (pd_values.max() - pd_values.min()) * 0.05] * len(rug_sample)}
)

# Confidence band
band = (
    alt.Chart(df_band)
    .mark_area(opacity=0.3, color="#306998")
    .encode(
        x=alt.X("Feature Value:Q", title=f"{feature_names[feature_idx]} (standardized units)"),
        y=alt.Y("CI Lower:Q", title="Partial Dependence (predicted outcome)"),
        y2="CI Upper:Q",
    )
)

# Main PDP line
line = (
    alt.Chart(df_line)
    .mark_line(strokeWidth=4, color="#306998")
    .encode(
        x=alt.X("Feature Value:Q"),
        y=alt.Y("Partial Dependence:Q"),
        tooltip=[alt.Tooltip("Feature Value:Q", format=".2f"), alt.Tooltip("Partial Dependence:Q", format=".2f")],
    )
)

# Rug plot for data distribution
rug = alt.Chart(df_rug).mark_tick(thickness=2, size=20, color="#306998", opacity=0.5).encode(x=alt.X("Feature Value:Q"))

# Combine layers
chart = (
    alt.layer(band, line, rug)
    .properties(
        width=1600, height=900, title=alt.Title(text="pdp-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
