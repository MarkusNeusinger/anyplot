"""anyplot.ai
pdp-basic: Partial Dependence Plot
Library: altair | Python 3.13
Quality: pending | Created: 2025-05-15
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

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

# Create DataFrame for main line
df_line = pd.DataFrame({"Feature Value": feature_values, "Partial Dependence": pd_values})

# Create DataFrame for confidence band
df_band = pd.DataFrame({"Feature Value": feature_values, "CI Lower": ci_lower, "CI Upper": ci_upper})

# Create rug plot data (sample of training data distribution)
rug_sample = np.random.choice(X[:, feature_idx], size=min(100, len(X)), replace=False)
df_rug = pd.DataFrame(
    {"Feature Value": rug_sample, "y": [pd_values.min() - (pd_values.max() - pd_values.min()) * 0.05] * len(rug_sample)}
)

# Confidence band
band = (
    alt.Chart(df_band)
    .mark_area(opacity=0.2, color=BRAND)
    .encode(
        x=alt.X("Feature Value:Q", title=f"{feature_names[feature_idx]} (standardized units)"),
        y=alt.Y("CI Lower:Q", title="Partial Dependence (predicted outcome)"),
        y2="CI Upper:Q",
    )
)

# Main PDP line
line = (
    alt.Chart(df_line)
    .mark_line(strokeWidth=4, color=BRAND)
    .encode(
        x=alt.X("Feature Value:Q"),
        y=alt.Y("Partial Dependence:Q"),
        tooltip=[alt.Tooltip("Feature Value:Q", format=".2f"), alt.Tooltip("Partial Dependence:Q", format=".2f")],
    )
)

# Rug plot for data distribution
rug = alt.Chart(df_rug).mark_tick(thickness=2, size=20, color=BRAND, opacity=0.4).encode(x=alt.X("Feature Value:Q"))

# Combine layers
chart = (
    alt.layer(band, line, rug)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(text="pdp-basic · altair · anyplot.ai", fontSize=28, anchor="middle"),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
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
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
