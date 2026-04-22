""" pyplots.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_x_log10,
    scale_y_log10,
    theme,
    theme_minimal,
)


# Data - S-N curve for steel specimen fatigue testing
np.random.seed(42)

# Material properties (MPa)
ultimate_strength = 550
yield_strength = 350
endurance_limit = 250

# Generate realistic S-N curve data with scatter
# Using Basquin equation: S = A * N^b (linearized: log(S) = log(A) + b*log(N))
# For steel: typical b ~ -0.1 to -0.15
A = 1200  # Fatigue strength coefficient
b = -0.12  # Fatigue strength exponent

# Generate test data at various stress levels
stress_levels = np.array([500, 450, 400, 375, 350, 325, 300, 280, 270, 260, 255])

cycles = []
stress = []

for s in stress_levels:
    # Calculate expected cycles from Basquin equation (S = A * N^b => N = (S/A)^(1/b))
    n_expected = (s / A) ** (1 / b)
    # Add scatter (multiple specimens at each stress level)
    n_tests = np.random.randint(3, 6)
    scatter = np.random.lognormal(0, 0.3, n_tests)
    n_values = n_expected * scatter
    cycles.extend(n_values)
    stress.extend([s] * n_tests)

# Add runout data points (did not fail, typically marked at endurance limit)
runout_cycles = [1e7, 2e7, 5e7]
runout_stress = [endurance_limit - 10, endurance_limit - 5, endurance_limit + 5]
cycles.extend(runout_cycles)
stress.extend(runout_stress)

df = pd.DataFrame({"cycles": cycles, "stress": stress})

# Create curve fit line for plotting
fit_cycles = np.logspace(2, 7, 100)
fit_stress = A * fit_cycles**b

df_fit = pd.DataFrame({"cycles": fit_cycles, "stress": fit_stress})

# Create plot
plot = (
    ggplot()
    # Fitted S-N curve line
    + geom_line(df_fit, aes(x="cycles", y="stress"), color="#306998", size=1.5, alpha=0.8)
    # Data points
    + geom_point(df, aes(x="cycles", y="stress"), color="#306998", size=4, alpha=0.7)
    # Reference lines
    + geom_hline(yintercept=ultimate_strength, linetype="dashed", color="#e74c3c", size=1, alpha=0.8)
    + geom_hline(yintercept=yield_strength, linetype="dashed", color="#f39c12", size=1, alpha=0.8)
    + geom_hline(yintercept=endurance_limit, linetype="dashed", color="#27ae60", size=1, alpha=0.8)
    # Reference line labels
    + annotate("text", x=1e2, y=ultimate_strength + 15, label="Ultimate Strength", size=12, color="#e74c3c", ha="left")
    + annotate("text", x=1e2, y=yield_strength + 15, label="Yield Strength", size=12, color="#f39c12", ha="left")
    + annotate("text", x=1e2, y=endurance_limit - 20, label="Endurance Limit", size=12, color="#27ae60", ha="left")
    # Logarithmic scales
    + scale_x_log10()
    + scale_y_log10()
    # Labels
    + labs(
        x="Number of Cycles to Failure (N)", y="Stress Amplitude (MPa)", title="sn-curve-basic · plotnine · pyplots.ai"
    )
    # Theme with proper sizing for 4800x2700
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major_x=element_text(alpha=0.3),
        panel_grid_minor_x=element_text(alpha=0.15),
        panel_grid_major_y=element_text(alpha=0.3),
        panel_grid_minor_y=element_text(alpha=0.15),
    )
)

# Save
plot.save("plot.png", dpi=300)
