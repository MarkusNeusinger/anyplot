""" anyplot.ai
pdp-basic: Partial Dependence Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito colors
BRAND = "#009E73"
ACCENT = "#C475FD"

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
rug_height = (avg_pd.max() - avg_pd.min()) * 0.08
y_min = avg_pd.min() - rug_height / 2
y_max = avg_pd.min() + rug_height / 2
df_rug = pd.DataFrame(
    {"x": rug_sample, "y_start": np.full(len(rug_sample), y_min), "y_end": np.full(len(rug_sample), y_max)}
)

# Custom theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.2),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=24, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=16),
)

# Create the partial dependence plot
plot = (
    ggplot()
    + geom_ribbon(aes(x="feature_value", ymin="lower", ymax="upper", fill="Confidence Band"), data=df_pdp, alpha=0.25)
    + geom_line(
        aes(x="feature_value", y="ice_value", group="line_id", color="Individual"), data=df_ice, alpha=0.2, size=0.5
    )
    + geom_line(aes(x="feature_value", y="partial_dependence", color="Main PDP"), data=df_pdp, size=2.5)
    + geom_segment(
        aes(x="x", y="y_start", xend="x", yend="y_end", color="Data Distribution"), data=df_rug, alpha=0.6, size=1.2
    )
    + scale_color_manual(values={"Main PDP": BRAND, "Individual": ACCENT, "Data Distribution": ACCENT})
    + scale_fill_manual(values={"Confidence Band": ACCENT})
    + labs(
        x=f"{feature_name} (standardized)",
        y="Partial Dependence (predicted outcome)",
        title="pdp-basic · letsplot · anyplot.ai",
        color="Elements",
        fill="",
    )
    + anyplot_theme
    + ggsize(1600, 900)
    + theme(legend_position="top", legend_direction="horizontal")
)

# Save as PNG and HTML
ggsave(plot, f"plot-{THEME}.png", w=4800, h=2700, unit="px", path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
