""" anyplot.ai
gain-curve: Cumulative Gains Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-11
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"  # Model curve
SECONDARY = "#C475FD"  # Baseline reference

# Data - Simulated model predictions for fraud detection
np.random.seed(42)
n_samples = 1500

# Generate model scores with strong discrimination
base_score = np.random.beta(2, 5, n_samples)
noise = np.random.normal(0, 0.1, n_samples)
y_score = np.clip(base_score + noise, 0, 1)

# Generate actual fraud outcomes - strong correlation with scores
fraud_prob = 0.5 * y_score + 0.02
y_true = (np.random.random(n_samples) < fraud_prob).astype(int)

# Calculate cumulative gains curve
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

cumulative_positives = np.cumsum(y_true_sorted)
total_positives = y_true_sorted.sum()
pct_population = np.arange(1, n_samples + 1) / n_samples * 100
pct_gain = cumulative_positives / total_positives * 100

# Add origin point
pct_population = np.insert(pct_population, 0, 0)
pct_gain = np.insert(pct_gain, 0, 0)

# Subsample for smooth visual
sample_idx = np.concatenate([[0], np.arange(15, len(pct_population) - 1, 15), [len(pct_population) - 1]])
pct_population_smooth = pct_population[sample_idx]
pct_gain_smooth = pct_gain[sample_idx]

# Create DataFrame
df_gains = pd.DataFrame({"population": pct_population_smooth, "gain": pct_gain_smooth, "Type": "Model"})
df_baseline = pd.DataFrame({"population": [0, 100], "gain": [0, 100], "Type": "Baseline"})
df_combined = pd.concat([df_gains, df_baseline], ignore_index=True)

# Shaded area under model curve
area_model = (
    alt.Chart(df_combined[df_combined["Type"] == "Model"])
    .mark_area(opacity=0.15, color=BRAND, interpolate="monotone")
    .encode(x="population:Q", y="gain:Q")
)

# Model curve line
model_curve = (
    alt.Chart(df_combined[df_combined["Type"] == "Model"])
    .mark_line(strokeWidth=4, color=BRAND, interpolate="monotone")
    .encode(
        x=alt.X(
            "population:Q",
            title="Population Targeted (%)",
            scale=alt.Scale(domain=[0, 100]),
            axis=alt.Axis(titleFontSize=22, labelFontSize=18, tickCount=10, labelColor=INK_SOFT, titleColor=INK),
        ),
        y=alt.Y(
            "gain:Q",
            title="Positive Cases Captured (%)",
            scale=alt.Scale(domain=[0, 100]),
            axis=alt.Axis(titleFontSize=22, labelFontSize=18, tickCount=10, labelColor=INK_SOFT, titleColor=INK),
        ),
    )
)

# Baseline diagonal line
baseline_line = (
    alt.Chart(df_combined[df_combined["Type"] == "Baseline"])
    .mark_line(strokeWidth=3, strokeDash=[8, 4], color=INK_SOFT)
    .encode(x="population:Q", y="gain:Q")
)

# Legend in lower-right area (out of data overlap)
legend_model_line = (
    alt.Chart(pd.DataFrame({"x": [68, 68], "y": [15, 20]}))
    .mark_line(strokeWidth=4, color=BRAND)
    .encode(x=alt.X("x:Q", scale=alt.Scale(domain=[0, 100])), y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 100])))
)

legend_model_text = (
    alt.Chart(pd.DataFrame({"x": [72], "y": [17.5], "text": ["Model"]}))
    .mark_text(align="left", fontSize=18, color=INK)
    .encode(x="x:Q", y="y:Q", text="text:N")
)

legend_baseline_line = (
    alt.Chart(pd.DataFrame({"x": [68, 68], "y": [8, 13]}))
    .mark_line(strokeWidth=3, strokeDash=[8, 4], color=INK_SOFT)
    .encode(x=alt.X("x:Q", scale=alt.Scale(domain=[0, 100])), y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 100])))
)

legend_baseline_text = (
    alt.Chart(pd.DataFrame({"x": [72], "y": [10.5], "text": ["Baseline"]}))
    .mark_text(align="left", fontSize=18, color=INK)
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Combine all layers
chart = (
    alt.layer(
        area_model,
        baseline_line,
        model_curve,
        legend_model_line,
        legend_model_text,
        legend_baseline_line,
        legend_baseline_text,
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("gain-curve · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_axis(gridColor=INK_SOFT, gridOpacity=0.10, gridDash=[2, 2], domainColor=INK_SOFT, tickColor=INK_SOFT)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK)
)

# Save output
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
