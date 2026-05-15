""" anyplot.ai
pdp-basic: Partial Dependence Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import plotly.graph_objects as go
from sklearn.datasets import load_diabetes
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"  # Okabe-Ito position 1

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
pdp_result = partial_dependence(model, X, features=[feature_idx], kind="average", grid_resolution=100)
feature_values = pdp_result["grid_values"][0]
pd_values = pdp_result["average"][0]

# Compute individual conditional expectation (ICE) for uncertainty visualization
ice_result = partial_dependence(model, X, features=[feature_idx], kind="individual", grid_resolution=100)
ice_lines = ice_result["individual"][0]

# Calculate confidence intervals (mean ± 1 std for variability band)
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

# Add confidence band (±1 std)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([feature_values, feature_values[::-1]]),
        y=np.concatenate([ci_upper_centered, ci_lower_centered[::-1]]),
        fill="toself",
        fillcolor=f"rgba({int(BRAND[1:3], 16)}, {int(BRAND[3:5], 16)}, {int(BRAND[5:7], 16)}, 0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="±1 Std Deviation",
        showlegend=True,
        hoverinfo="skip",
    )
)

# Add partial dependence line
fig.add_trace(
    go.Scatter(
        x=feature_values, y=pd_centered, mode="lines", line=dict(color=BRAND, width=4), name="Partial Dependence"
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
        marker=dict(symbol="line-ns", size=16, color=INK_SOFT, opacity=0.5, line=dict(width=2)),
        name="Data Distribution",
        hoverinfo="skip",
    )
)

# Add zero reference line
fig.add_hline(y=0, line_dash="dash", line_color=INK_SOFT, line_width=2)

# Layout
fig.update_layout(
    title=dict(text="pdp-basic · plotly · anyplot.ai", font=dict(size=28, color=INK)),
    xaxis=dict(
        title=dict(text="BMI (Body Mass Index, standardized)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Partial Dependence (centered)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend=dict(
        font=dict(size=16, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=100, r=80, t=120, b=100),
)

# Save as PNG (4800 x 2700 px) and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
