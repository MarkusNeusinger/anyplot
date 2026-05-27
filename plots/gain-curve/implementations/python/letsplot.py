""" anyplot.ai
gain-curve: Cumulative Gains Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from lets_plot import element_blank, element_line, element_rect, element_text, theme
from scipy.interpolate import make_interp_spline


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Data
np.random.seed(42)
n_samples = 1000

# Generate realistic customer response data
customer_score = np.random.beta(2, 5, n_samples)
y_true = (np.random.random(n_samples) < customer_score * 0.6 + 0.05).astype(int)
y_score = customer_score + np.random.normal(0, 0.1, n_samples)
y_score = np.clip(y_score, 0, 1)

# Sort by predicted score descending
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative gains
total_positives = y_true.sum()
cumulative_positives = np.cumsum(y_true_sorted)
gains = cumulative_positives / total_positives * 100
population_pct = np.arange(1, n_samples + 1) / n_samples * 100

# Add origin point (0, 0)
gains = np.insert(gains, 0, 0)
population_pct = np.insert(population_pct, 0, 0)

# Smooth the model curve using spline interpolation
spl = make_interp_spline(population_pct, gains, k=3)
population_smooth = np.linspace(0, 100, 300)
gains_smooth = spl(population_smooth)
gains_smooth = np.clip(gains_smooth, 0, 100)

# Perfect model curve
positive_rate = total_positives / n_samples
perfect_gains = np.minimum(population_pct / (positive_rate * 100), 1) * 100

# Random baseline
random_gains = population_pct

# Create DataFrames for plotting
df_model = pd.DataFrame({"Population": population_smooth, "Gain": gains_smooth, "Type": "Model"})
df_random = pd.DataFrame({"Population": population_pct, "Gain": random_gains, "Type": "Random"})
df_perfect = pd.DataFrame({"Population": population_pct, "Gain": perfect_gains, "Type": "Perfect"})
df_long = pd.concat([df_model, df_random, df_perfect], ignore_index=True)

# Colors: Okabe-Ito palette
colors = {
    "Model": "#009E73",  # Okabe-Ito position 1 (brand green)
    "Random": "#888888",  # Neutral gray for reference line
    "Perfect": "#4467A3",  # Okabe-Ito position 3 (blue)
}

# Plot
plot = (
    ggplot(df_long, aes(x="Population", y="Gain", color="Type"))
    + geom_line(size=1.5)
    + scale_color_manual(values=colors, name="Curve")
    + scale_x_continuous(limits=[0, 100])
    + scale_y_continuous(limits=[0, 100])
    + labs(x="Population Targeted (%)", y="Positive Cases Captured (%)", title="gain-curve · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_position=[0.85, 0.25],
    )
    + ggsize(1600, 900)
)

# Save
output_dir = os.getcwd()
ggsave(plot, os.path.join(output_dir, f"plot-{THEME}.png"), scale=3)
ggsave(plot, os.path.join(output_dir, f"plot-{THEME}.html"))
