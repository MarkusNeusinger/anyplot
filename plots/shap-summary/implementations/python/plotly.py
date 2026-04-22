""" pyplots.ai
shap-summary: SHAP Summary Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import plotly.graph_objects as go


# Data - Generate synthetic SHAP values for ML model interpretability demo
np.random.seed(42)

# Simulated feature data (like from a gradient boosting model on tabular data)
n_samples = 200
feature_names = [
    "mean radius",
    "mean texture",
    "mean perimeter",
    "mean area",
    "mean smoothness",
    "mean compactness",
    "mean concavity",
    "mean concave points",
    "mean symmetry",
    "mean fractal dimension",
    "radius error",
    "texture error",
    "perimeter error",
    "area error",
    "smoothness error",
]
n_features = len(feature_names)

# Generate realistic feature values (simulating measurement data)
X = np.zeros((n_samples, n_features))
X[:, 0] = np.random.normal(14, 3.5, n_samples)  # mean radius
X[:, 1] = np.random.normal(19, 4, n_samples)  # mean texture
X[:, 2] = np.random.normal(92, 24, n_samples)  # mean perimeter
X[:, 3] = np.random.normal(655, 350, n_samples)  # mean area
X[:, 4] = np.random.normal(0.096, 0.014, n_samples)  # mean smoothness
X[:, 5] = np.random.normal(0.104, 0.053, n_samples)  # mean compactness
X[:, 6] = np.random.normal(0.089, 0.08, n_samples)  # mean concavity
X[:, 7] = np.random.normal(0.049, 0.039, n_samples)  # mean concave points
X[:, 8] = np.random.normal(0.181, 0.027, n_samples)  # mean symmetry
X[:, 9] = np.random.normal(0.063, 0.007, n_samples)  # mean fractal dimension
X[:, 10] = np.random.normal(0.41, 0.28, n_samples)  # radius error
X[:, 11] = np.random.normal(1.22, 0.55, n_samples)  # texture error
X[:, 12] = np.random.normal(2.87, 2.02, n_samples)  # perimeter error
X[:, 13] = np.random.normal(40, 45, n_samples)  # area error
X[:, 14] = np.random.normal(0.007, 0.003, n_samples)  # smoothness error

# Simulated feature importances (as from a tree-based model)
importances = np.array([0.25, 0.08, 0.12, 0.18, 0.03, 0.06, 0.10, 0.09, 0.02, 0.01, 0.02, 0.01, 0.01, 0.01, 0.01])

# Generate SHAP values that correlate with feature values (simulating real SHAP behavior)
shap_values = np.zeros((n_samples, n_features))
for i in range(n_features):
    feat_min, feat_max = X[:, i].min(), X[:, i].max()
    feat_normalized = (X[:, i] - feat_min) / (feat_max - feat_min + 1e-10)

    # SHAP values correlate with feature values, scaled by importance
    base_effect = (feat_normalized - 0.5) * importances[i] * 2
    noise = np.random.randn(n_samples) * importances[i] * 0.3
    shap_values[:, i] = base_effect + noise

# Sort features by mean absolute SHAP value (most important first)
mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
sorted_idx = np.argsort(mean_abs_shap)[::-1]

# Show top 15 features for clarity
top_n = 15
sorted_idx = sorted_idx[:top_n]

# Create figure
fig = go.Figure()

# Add traces for each feature (from bottom to top for proper y-axis ordering)
for rank, feat_idx in enumerate(reversed(sorted_idx)):
    feat_shap = shap_values[:, feat_idx]
    feat_vals = X[:, feat_idx]

    # Normalize feature values for coloring (0 to 1)
    feat_min, feat_max = feat_vals.min(), feat_vals.max()
    feat_normalized = (feat_vals - feat_min) / (feat_max - feat_min + 1e-10)

    # Add jitter to y-position
    y_base = rank
    jitter = np.random.uniform(-0.3, 0.3, n_samples)
    y_positions = y_base + jitter

    # Create color array based on feature values (blue=low, red=high)
    colors = feat_normalized

    fig.add_trace(
        go.Scatter(
            x=feat_shap,
            y=y_positions,
            mode="markers",
            marker={
                "size": 8,
                "color": colors,
                "colorscale": "RdBu_r",
                "cmin": 0,
                "cmax": 1,
                "opacity": 0.7,
                "line": {"width": 0},
            },
            name=feature_names[feat_idx][:25],
            hovertemplate=(
                f"<b>{feature_names[feat_idx]}</b><br>"
                "SHAP: %{x:.3f}<br>"
                "Feature value: %{marker.color:.2f}<extra></extra>"
            ),
            showlegend=False,
        )
    )

# Add vertical line at x=0
fig.add_vline(x=0, line_width=2, line_color="#333333", line_dash="solid")

# Create y-axis labels (feature names in order from bottom to top)
y_labels = [feature_names[idx][:25] for idx in reversed(sorted_idx)]

# Add colorbar as a separate trace
colorbar_trace = go.Scatter(
    x=[None],
    y=[None],
    mode="markers",
    marker={
        "size": 0.1,
        "color": [0, 1],
        "colorscale": "RdBu_r",
        "cmin": 0,
        "cmax": 1,
        "colorbar": {
            "title": {"text": "Feature Value", "font": {"size": 20}, "side": "right"},
            "tickfont": {"size": 16},
            "tickvals": [0, 0.5, 1],
            "ticktext": ["Low", "Medium", "High"],
            "len": 0.5,
            "thickness": 25,
            "x": 1.02,
            "y": 0.5,
        },
        "showscale": True,
    },
    showlegend=False,
    hoverinfo="skip",
)
fig.add_trace(colorbar_trace)

# Update layout
fig.update_layout(
    title={
        "text": "shap-summary · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "SHAP Value (Impact on Model Output)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 2,
        "zerolinecolor": "#333333",
        "gridcolor": "rgba(128, 128, 128, 0.2)",
        "showgrid": True,
    },
    yaxis={
        "title": {"text": "Feature", "font": {"size": 22}},
        "tickfont": {"size": 16},
        "tickmode": "array",
        "tickvals": list(range(top_n)),
        "ticktext": y_labels,
        "showgrid": False,
    },
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 200, "r": 120, "t": 80, "b": 80},
    showlegend=False,
)

# Save as PNG (4800 x 2700)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
