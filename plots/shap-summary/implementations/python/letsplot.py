"""anyplot.ai
shap-summary: SHAP Summary Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
TOP_K = 10  # the Notes ask for the 10-20 most important features

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature_names
SHAP_VALUE = "SHAP value (impact on model output)"  # role: shap_values
FEATURE_VALUE = "Feature value"  # role: feature_values

# Data: replace this block with your own long table, for example df = pd.read_csv("shap_long.csv")
np.random.seed(42)
n_samples = 250
n_features = 12

feature_names = [
    "BMI",
    "Blood Pressure",
    "Glucose Level",
    "Cholesterol",
    "Heart Rate",
    "Sleep Hours",
    "Exercise Days",
    "Stress Score",
    "Age",
    "Triglycerides",
    "HDL Cholesterol",
    "LDL Cholesterol",
]

# Generate realistic medical feature values
feature_values = np.column_stack(
    [
        np.random.normal(26, 5, n_samples),  # BMI
        np.random.normal(130, 15, n_samples),  # Blood Pressure (systolic)
        np.random.normal(110, 25, n_samples),  # Glucose Level
        np.random.normal(200, 40, n_samples),  # Cholesterol
        np.random.normal(75, 12, n_samples),  # Heart Rate
        np.random.normal(7, 1.5, n_samples),  # Sleep Hours
        np.random.normal(4, 2, n_samples),  # Exercise Days/week
        np.random.normal(50, 20, n_samples),  # Stress Score (0-100)
        np.random.normal(55, 15, n_samples),  # Age
        np.random.normal(150, 50, n_samples),  # Triglycerides
        np.random.normal(50, 12, n_samples),  # HDL Cholesterol
        np.random.normal(130, 30, n_samples),  # LDL Cholesterol
    ]
)

# Generate SHAP values with realistic medical relationships
shap_values = np.zeros((n_samples, n_features))

# BMI: positive effect on risk (higher BMI = worse outcome)
bmi_norm = (feature_values[:, 0] - 25) / 5
shap_values[:, 0] = bmi_norm * 0.8 + np.random.normal(0, 0.15, n_samples)

# Blood Pressure: positive effect
bp_norm = (feature_values[:, 1] - 120) / 20
shap_values[:, 1] = bp_norm * 0.9 + np.random.normal(0, 0.14, n_samples)

# Glucose Level: strong positive effect
glucose_norm = (feature_values[:, 2] - 100) / 30
shap_values[:, 2] = glucose_norm * 1.2 + np.random.normal(0, 0.18, n_samples)

# Cholesterol: positive effect
chol_norm = (feature_values[:, 3] - 200) / 50
shap_values[:, 3] = chol_norm * 0.7 + np.random.normal(0, 0.16, n_samples)

# Heart Rate: U-shaped effect (too low or too high is bad)
hr_centered = np.abs(feature_values[:, 4] - 72)
shap_values[:, 4] = (hr_centered / 15) * 0.5 + np.random.normal(0, 0.12, n_samples)

# Sleep Hours: negative effect (more sleep = better)
shap_values[:, 5] = -(feature_values[:, 5] - 7) * 0.15 + np.random.normal(0, 0.1, n_samples)

# Exercise Days: strong negative effect (protective)
shap_values[:, 6] = -(feature_values[:, 6] - 3.5) * 0.2 + np.random.normal(0, 0.12, n_samples)

# Stress Score: positive effect
stress_norm = (feature_values[:, 7] - 40) / 25
shap_values[:, 7] = stress_norm * 0.6 + np.random.normal(0, 0.13, n_samples)

# Age: positive effect
age_norm = (feature_values[:, 8] - 50) / 20
shap_values[:, 8] = age_norm * 0.7 + np.random.normal(0, 0.14, n_samples)

# Triglycerides: moderate positive effect
trig_norm = (feature_values[:, 9] - 150) / 60
shap_values[:, 9] = trig_norm * 0.45 + np.random.normal(0, 0.11, n_samples)

# HDL Cholesterol: negative effect (protective)
hdl_norm = (feature_values[:, 10] - 50) / 15
shap_values[:, 10] = -hdl_norm * 0.35 + np.random.normal(0, 0.09, n_samples)

# LDL Cholesterol: positive effect
ldl_norm = (feature_values[:, 11] - 130) / 40
shap_values[:, 11] = ldl_norm * 0.55 + np.random.normal(0, 0.13, n_samples)

df = pd.DataFrame(
    {FEATURE: np.tile(feature_names, n_samples), SHAP_VALUE: shap_values.ravel(), FEATURE_VALUE: feature_values.ravel()}
)

# Plot: reads only df and the constants above
# Rank features by mean absolute SHAP value and keep the top ones
importance = df.groupby(FEATURE)[SHAP_VALUE].agg(lambda v: v.abs().mean()).sort_values(ascending=False)
top = importance.index[:TOP_K]
plot_df = df[df[FEATURE].isin(top)].copy()

# Scale each feature's values to 0-1 so one color bar serves every row
by_feature = plot_df.groupby(FEATURE)[FEATURE_VALUE]
plot_df["scaled"] = (plot_df[FEATURE_VALUE] - by_feature.transform("min")) / (
    by_feature.transform("max") - by_feature.transform("min")
)

# Imprint diverging scale: blue (low) - page-colored midpoint - red (high)
MID = "#FAF8F1" if THEME == "light" else "#1A1A17"

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_line(color=INK_MUTED, size=0.3),
    panel_grid_major_y=element_blank(),
    panel_grid_minor=element_blank(),
    axis_line=element_blank(),
    axis_ticks=element_blank(),
    axis_title=element_text(color=INK, size=13),
    axis_text=element_text(color=INK_SOFT, size=11),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_title=element_text(color=INK, size=12),
    legend_text=element_text(color=INK_SOFT, size=11),
)

plot = (
    ggplot(plot_df, aes(x=SHAP_VALUE, y=FEATURE, fill="scaled"))
    + geom_vline(xintercept=0, color=INK_SOFT, size=0.5, linetype="dashed")
    + geom_point(
        shape=21,
        size=2.2,
        stroke=0.25,
        color=INK_SOFT,
        alpha=0.8,
        position=position_jitter(width=0, height=0.25, seed=42),
    )
    + scale_fill_gradient2(
        low="#4467A3", mid=MID, high="#AE3030", midpoint=0.5, name=FEATURE_VALUE, breaks=[0, 1], labels=["Low", "High"]
    )
    + scale_y_discrete(limits=list(top[::-1]))
    + labs(y="", title="shap-summary · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
    + anyplot_theme
)

# Save as PNG and HTML
_plot_dir = os.path.dirname(os.path.abspath(__file__))
ggsave(plot, f"{_plot_dir}/plot-{THEME}.png", scale=4)
ggsave(plot, f"{_plot_dir}/plot-{THEME}.html")
