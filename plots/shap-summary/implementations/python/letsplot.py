""" pyplots.ai
shap-summary: SHAP Summary Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Simulate SHAP values for a regression model
np.random.seed(42)
n_samples = 200
n_features = 12

feature_names = [
    "Age",
    "Income",
    "Credit Score",
    "Loan Amount",
    "Employment Years",
    "Debt Ratio",
    "Num Accounts",
    "Payment History",
    "Education Level",
    "Property Value",
    "Monthly Balance",
    "Inquiry Count",
]

# Generate feature values with realistic ranges
feature_values = np.column_stack(
    [
        np.random.uniform(22, 65, n_samples),  # Age
        np.random.lognormal(10.5, 0.5, n_samples),  # Income
        np.random.uniform(550, 850, n_samples),  # Credit Score
        np.random.lognormal(11, 0.8, n_samples),  # Loan Amount
        np.random.uniform(0, 30, n_samples),  # Employment Years
        np.random.uniform(0.1, 0.6, n_samples),  # Debt Ratio
        np.random.randint(1, 15, n_samples),  # Num Accounts
        np.random.uniform(0.5, 1.0, n_samples),  # Payment History
        np.random.randint(1, 5, n_samples),  # Education Level
        np.random.lognormal(12, 0.6, n_samples),  # Property Value
        np.random.normal(5000, 2000, n_samples),  # Monthly Balance
        np.random.randint(0, 8, n_samples),  # Inquiry Count
    ]
)

# Generate SHAP values with feature-dependent effects
shap_values = np.zeros((n_samples, n_features))

# Age: moderate positive effect
shap_values[:, 0] = (feature_values[:, 0] - 45) * 0.02 + np.random.normal(0, 0.15, n_samples)

# Income: strong positive effect (higher income = higher prediction)
income_normalized = (np.log(feature_values[:, 1]) - 10.5) / 0.5
shap_values[:, 1] = income_normalized * 0.8 + np.random.normal(0, 0.2, n_samples)

# Credit Score: very strong positive effect
score_normalized = (feature_values[:, 2] - 700) / 100
shap_values[:, 2] = score_normalized * 1.0 + np.random.normal(0, 0.15, n_samples)

# Loan Amount: negative effect (higher loan = lower prediction)
loan_normalized = (np.log(feature_values[:, 3]) - 11) / 0.8
shap_values[:, 3] = -loan_normalized * 0.6 + np.random.normal(0, 0.2, n_samples)

# Employment Years: positive effect
shap_values[:, 4] = (feature_values[:, 4] - 15) * 0.03 + np.random.normal(0, 0.12, n_samples)

# Debt Ratio: strong negative effect
shap_values[:, 5] = -(feature_values[:, 5] - 0.35) * 3.0 + np.random.normal(0, 0.25, n_samples)

# Num Accounts: weak positive effect
shap_values[:, 6] = (feature_values[:, 6] - 7) * 0.03 + np.random.normal(0, 0.1, n_samples)

# Payment History: positive effect
shap_values[:, 7] = (feature_values[:, 7] - 0.75) * 2.0 + np.random.normal(0, 0.15, n_samples)

# Education Level: weak positive
shap_values[:, 8] = (feature_values[:, 8] - 2.5) * 0.08 + np.random.normal(0, 0.08, n_samples)

# Property Value: moderate positive
prop_normalized = (np.log(feature_values[:, 9]) - 12) / 0.6
shap_values[:, 9] = prop_normalized * 0.35 + np.random.normal(0, 0.12, n_samples)

# Monthly Balance: weak effect
shap_values[:, 10] = (feature_values[:, 10] - 5000) / 10000 + np.random.normal(0, 0.08, n_samples)

# Inquiry Count: negative effect
shap_values[:, 11] = -feature_values[:, 11] * 0.04 + np.random.normal(0, 0.06, n_samples)

# Calculate mean absolute SHAP value for feature importance
mean_abs_shap = np.abs(shap_values).mean(axis=0)
feature_order = np.argsort(mean_abs_shap)[::-1]

# Select top 10 features
top_k = 10
top_indices = feature_order[:top_k]

# Create long-form DataFrame for plotting
data_records = []
for rank, feat_idx in enumerate(top_indices):
    feat_name = feature_names[feat_idx]
    feat_shap = shap_values[:, feat_idx]
    feat_val = feature_values[:, feat_idx]
    # Normalize feature values to 0-1 for consistent coloring
    feat_val_norm = (feat_val - feat_val.min()) / (feat_val.max() - feat_val.min() + 1e-8)
    # Add vertical jitter for visibility
    jitter = np.random.uniform(-0.25, 0.25, n_samples)

    for i in range(n_samples):
        data_records.append(
            {
                "Feature": feat_name,
                "SHAP Value": feat_shap[i],
                "Feature Value": feat_val_norm[i],
                "y_position": (top_k - 1 - rank) + jitter[i],
                "importance_rank": rank,
            }
        )

df = pd.DataFrame(data_records)

# Create ordered feature list (most important at top)
ordered_features = [feature_names[i] for i in top_indices]

# Plot
plot = (
    ggplot(df, aes(x="SHAP Value", y="y_position", color="Feature Value"))
    + geom_point(size=3, alpha=0.7)
    + geom_vline(xintercept=0, color="#666666", size=0.8, linetype="dashed")
    + scale_color_gradient(low="#306998", high="#DC2626", name="Feature\nValue")
    + scale_y_continuous(breaks=list(range(top_k)), labels=ordered_features[::-1])
    + labs(x="SHAP Value (impact on model output)", y="", title="shap-summary · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=18),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, "plot.html")
