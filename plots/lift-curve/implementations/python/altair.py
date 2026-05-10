""" anyplot.ai
lift-curve: Model Lift Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-10
"""

import os
import sys


_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)
if "" in sys.path:
    sys.path.remove("")

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"  # First series (lift curve)
REFERENCE_COLOR = "#999999"  # Reference line (adaptive neutral)

# Data - Simulate customer churn prediction model results
np.random.seed(42)
n_samples = 1000

# Create realistic churn prediction scenario
# True positives have higher scores, some overlap for realism
y_true = np.concatenate([np.ones(200), np.zeros(800)])  # 20% churn rate
y_score = np.concatenate(
    [
        np.clip(np.random.beta(5, 2, 200), 0, 1),  # Churners: higher scores
        np.clip(np.random.beta(2, 5, 800), 0, 1),  # Non-churners: lower scores
    ]
)

# Calculate lift curve
sorted_indices = np.argsort(y_score)[::-1]  # Sort by score descending
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative lift at each percentage
percentages = np.arange(1, 101)
n_total = len(y_true)
n_positives = y_true.sum()
baseline_rate = n_positives / n_total

lift_values = []
for pct in percentages:
    n_selected = int(np.ceil(n_total * pct / 100))
    n_captured = y_true_sorted[:n_selected].sum()
    model_rate = n_captured / n_selected
    lift = model_rate / baseline_rate
    lift_values.append(lift)

# Create DataFrame for Altair
df = pd.DataFrame({"Population (%)": percentages, "Cumulative Lift": lift_values})

# Reference line at y=1 (random selection)
df_reference = pd.DataFrame({"Population (%)": [0, 100], "Reference": [1.0, 1.0]})

# Create lift curve chart
lift_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=4, color=BRAND)
    .encode(
        x=alt.X("Population (%):Q", scale=alt.Scale(domain=[0, 100]), title="Population Targeted (%)"),
        y=alt.Y("Cumulative Lift:Q", scale=alt.Scale(domain=[0, 5]), title="Cumulative Lift"),
        tooltip=[alt.Tooltip("Population (%):Q", format=".0f"), alt.Tooltip("Cumulative Lift:Q", format=".2f")],
    )
)

# Reference line at lift = 1
reference_line = (
    alt.Chart(df_reference)
    .mark_line(strokeWidth=2, strokeDash=[8, 4], color=REFERENCE_COLOR)
    .encode(x="Population (%):Q", y="Reference:Q")
)

# Add decile markers
decile_df = df[df["Population (%)"].isin([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])]
decile_points = (
    alt.Chart(decile_df)
    .mark_point(size=200, color=BRAND, filled=True)
    .encode(
        x="Population (%):Q",
        y="Cumulative Lift:Q",
        tooltip=[
            alt.Tooltip("Population (%):Q", format=".0f", title="Decile %"),
            alt.Tooltip("Cumulative Lift:Q", format=".2f", title="Lift"),
        ],
    )
)

# Combine all layers
chart = (
    alt.layer(reference_line, lift_line, decile_points)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(text="lift-curve · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_title(color=INK)
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
