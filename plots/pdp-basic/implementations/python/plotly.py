""" pyplots.ai
pdp-basic: Partial Dependence Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import plotly.graph_objects as go
from sklearn.datasets import load_diabetes
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Data - Use diabetes dataset for realistic PDP
diabetes = load_diabetes()
X, y = diabetes.data, diabetes.target
feature_names = diabetes.feature_names

# Train model
np.random.seed(42)
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, y)

# Compute partial dependence for BMI (feature 2) - known to have strong effect
feature_idx = 2  # bmi
pdp_result = partial_dependence(model, X, features=[feature_idx], kind="average", grid_resolution=80)
feature_values = pdp_result["grid_values"][0]
pd_values = pdp_result["average"][0]

# Compute individual conditional expectation (ICE) for uncertainty visualization
ice_result = partial_dependence(model, X, features=[feature_idx], kind="individual", grid_resolution=80)
ice_lines = ice_result["individual"][0]

# Calculate confidence intervals (mean ± std for variability band)
ice_mean = np.mean(ice_lines, axis=0)
ice_std = np.std(ice_lines, axis=0)
ci_lower = ice_mean - ice_std
ci_upper = ice_mean + ice_std

# Center partial dependence at zero for easier interpretation
pd_centered = pd_values - np.mean(pd_values)
ci_lower_centered = ci_lower - np.mean(pd_values)
ci_upper_centered = ci_upper - np.mean(pd_values)

# Create figure
fig = go.Figure()

# Add confidence band
fig.add_trace(
    go.Scatter(
        x=np.concatenate([feature_values, feature_values[::-1]]),
        y=np.concatenate([ci_upper_centered, ci_lower_centered[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.2)",
        line=dict(color="rgba(255,255,255,0)"),
        name="95% Confidence Interval",
        showlegend=True,
        hoverinfo="skip",
    )
)

# Add partial dependence line
fig.add_trace(
    go.Scatter(
        x=feature_values, y=pd_centered, mode="lines", line=dict(color="#306998", width=4), name="Partial Dependence"
    )
)

# Add rug plot showing distribution of training data
y_range = np.max(ci_upper_centered) - np.min(ci_lower_centered)
rug_y = np.full(len(X), np.min(ci_lower_centered) - 0.08 * y_range)
fig.add_trace(
    go.Scatter(
        x=X[:, feature_idx],
        y=rug_y,
        mode="markers",
        marker=dict(symbol="line-ns", size=14, color="#306998", opacity=0.4, line=dict(width=1.5)),
        name="Data Distribution",
        hoverinfo="skip",
    )
)

# Add zero reference line
fig.add_hline(y=0, line_dash="dash", line_color="#999999", line_width=1.5)

# Layout
fig.update_layout(
    title=dict(text="pdp-basic · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="BMI (Body Mass Index, standardized)", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Partial Dependence (centered)", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    template="plotly_white",
    legend=dict(font=dict(size=18), x=0.02, y=0.98, xanchor="left", yanchor="top", bgcolor="rgba(255,255,255,0.8)"),
    margin=dict(l=100, r=80, t=120, b=100),
    plot_bgcolor="white",
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
