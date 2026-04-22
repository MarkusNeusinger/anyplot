""" pyplots.ai
bar-feature-importance: Feature Importance Bar Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go


# Data - Feature importances from a typical ML model
np.random.seed(42)

features = [
    "age",
    "income",
    "credit_score",
    "employment_years",
    "debt_ratio",
    "num_accounts",
    "payment_history",
    "loan_amount",
    "property_value",
    "monthly_expenses",
    "education_level",
    "marital_status",
    "num_dependents",
    "savings_balance",
    "investment_portfolio",
]

# Generate realistic importance values (decreasing with some variation)
base_importance = np.array(
    [0.18, 0.15, 0.14, 0.11, 0.09, 0.07, 0.06, 0.05, 0.04, 0.03, 0.025, 0.02, 0.015, 0.012, 0.008]
)
importance = base_importance + np.random.uniform(-0.005, 0.005, len(base_importance))
importance = np.clip(importance, 0.001, None)

# Standard deviation for error bars (ensemble uncertainty)
std = importance * np.random.uniform(0.1, 0.3, len(importance))

# Sort by importance (descending)
sorted_idx = np.argsort(importance)[::-1]
features_sorted = [features[i] for i in sorted_idx]
importance_sorted = importance[sorted_idx]
std_sorted = std[sorted_idx]

# Create color gradient based on importance (light to dark blue)
colors = [f"rgba(48, 105, 152, {0.4 + 0.6 * (imp / max(importance_sorted))})" for imp in importance_sorted]

# Create figure
fig = go.Figure()

fig.add_trace(
    go.Bar(
        y=features_sorted,
        x=importance_sorted,
        orientation="h",
        marker=dict(color=colors, line=dict(color="#306998", width=1)),
        error_x=dict(type="data", array=std_sorted, color="#306998", thickness=2, width=6),
    )
)

# Add text annotations positioned after error bars
for feat, imp, std_val in zip(features_sorted, importance_sorted, std_sorted, strict=True):
    fig.add_annotation(
        x=imp + std_val + 0.008,
        y=feat,
        text=f"{imp:.3f}",
        showarrow=False,
        font=dict(size=16, color="#333333"),
        xanchor="left",
    )

# Layout for 4800x2700 px canvas
fig.update_layout(
    title=dict(
        text="bar-feature-importance · plotly · pyplots.ai",
        font=dict(size=32, color="#333333"),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text="Importance Score", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
        range=[0, max(importance_sorted) + max(std_sorted) + 0.035],
    ),
    yaxis=dict(title=dict(text="Feature", font=dict(size=24)), tickfont=dict(size=18), autorange="reversed"),
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=200, r=100, t=100, b=80),
    showlegend=False,
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
