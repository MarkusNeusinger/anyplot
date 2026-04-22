""" pyplots.ai
pdp-basic: Partial Dependence Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import *
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


LetsPlot.setup_html()

# Train a model for partial dependence
np.random.seed(42)
X, y = make_regression(n_samples=500, n_features=5, noise=20, random_state=42)
feature_names = ["Temperature", "Humidity", "Pressure", "WindSpeed", "Altitude"]

model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, y)

# Compute partial dependence for Temperature (feature 0)
feature_idx = 0
feature_name = feature_names[feature_idx]
pdp_result = partial_dependence(model, X, features=[feature_idx], kind="both", grid_resolution=80)

feature_values = pdp_result["grid_values"][0]
avg_pd = pdp_result["average"][0]

# Get individual conditional expectations (ICE) for uncertainty
ice_lines = pdp_result["individual"][0]
lower_bound = np.percentile(ice_lines, 10, axis=0)
upper_bound = np.percentile(ice_lines, 90, axis=0)

# Create DataFrame for plotting
df_pdp = pd.DataFrame(
    {"feature_value": feature_values, "partial_dependence": avg_pd, "lower": lower_bound, "upper": upper_bound}
)

# Sample ICE lines for visualization (show a subset)
n_ice_lines = 50
ice_indices = np.random.choice(ice_lines.shape[0], n_ice_lines, replace=False)
ice_data = []
for i, idx in enumerate(ice_indices):
    for j, fv in enumerate(feature_values):
        ice_data.append({"feature_value": fv, "ice_value": ice_lines[idx, j], "line_id": i})
df_ice = pd.DataFrame(ice_data)

# Get rug data (sample of training feature values for distribution)
rug_sample = np.random.choice(X[:, feature_idx], size=100, replace=False)
y_min = avg_pd.min() - (avg_pd.max() - avg_pd.min()) * 0.02
y_max = avg_pd.min() + (avg_pd.max() - avg_pd.min()) * 0.02
df_rug = pd.DataFrame(
    {"x": rug_sample, "y_start": np.full(len(rug_sample), y_min), "y_end": np.full(len(rug_sample), y_max)}
)

# Create the partial dependence plot
plot = (
    ggplot()
    # Confidence band (80% interval from ICE lines)
    + geom_ribbon(aes(x="feature_value", ymin="lower", ymax="upper"), data=df_pdp, fill="#306998", alpha=0.2)
    # ICE lines (individual conditional expectations)
    + geom_line(
        aes(x="feature_value", y="ice_value", group="line_id"), data=df_ice, color="#306998", alpha=0.15, size=0.5
    )
    # Main PDP line
    + geom_line(aes(x="feature_value", y="partial_dependence"), data=df_pdp, color="#FFD43B", size=2.5)
    # Rug plot showing data distribution (vertical segments at bottom)
    + geom_segment(aes(x="x", y="y_start", xend="x", yend="y_end"), data=df_rug, color="#306998", alpha=0.4, size=0.8)
    # Labels and title
    + labs(
        x=f"{feature_name} (standardized)",
        y="Partial Dependence (predicted outcome)",
        title="pdp-basic · letsplot · pyplots.ai",
    )
    # Theme for readability
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#CCCCCC", size=0.3),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG and HTML
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
