""" pyplots.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""
# ruff: noqa: F405

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Data - Quarterly energy consumption forecast by source with uncertainty
np.random.seed(42)
quarters = pd.date_range("2023-Q1", periods=24, freq="QE")
n = len(quarters)

# Base trends for 3 energy sources (TWh)
solar_base = np.linspace(50, 120, n) + np.random.normal(0, 5, n)
wind_base = np.linspace(80, 150, n) + np.random.normal(0, 8, n)
hydro_base = np.linspace(100, 110, n) + np.random.normal(0, 3, n)

# Confidence intervals (uncertainty grows over time for forecasts)
time_factor = np.linspace(1, 2.5, n)
solar_lower = solar_base - 8 * time_factor
solar_upper = solar_base + 8 * time_factor
wind_lower = wind_base - 12 * time_factor
wind_upper = wind_base + 12 * time_factor
hydro_lower = hydro_base - 5 * time_factor
hydro_upper = hydro_base + 5 * time_factor

# Create stacked values (cumulative)
solar_stack = solar_base
wind_stack = solar_base + wind_base
hydro_stack = solar_base + wind_base + hydro_base

# Stacked confidence bounds
solar_lower_stack = solar_lower
solar_upper_stack = solar_upper
wind_lower_stack = solar_base + wind_lower
wind_upper_stack = solar_base + wind_upper
hydro_lower_stack = solar_base + wind_base + hydro_lower
hydro_upper_stack = solar_base + wind_base + hydro_upper

# Convert dates to numeric for lets-plot
x_numeric = np.arange(n)
x_labels = [f"{q.year}-Q{(q.month - 1) // 3 + 1}" for q in quarters]

# Central line data
df_lines = pd.DataFrame(
    {
        "x": np.tile(x_numeric, 3),
        "y": np.concatenate([solar_stack, wind_stack, hydro_stack]),
        "source": np.concatenate([["Solar"] * n, ["Wind"] * n, ["Hydro"] * n]),
    }
)

# Main areas data (for stacked area)
df_areas = pd.DataFrame(
    {
        "x": np.tile(x_numeric, 3),
        "y_min": np.concatenate([np.zeros(n), solar_stack, wind_stack]),
        "y_max": np.concatenate([solar_stack, wind_stack, hydro_stack]),
        "source": np.concatenate([["Solar"] * n, ["Wind"] * n, ["Hydro"] * n]),
    }
)

# Confidence band data
df_conf = pd.DataFrame(
    {
        "x": np.tile(x_numeric, 3),
        "y_lower": np.concatenate([solar_lower_stack, wind_lower_stack, hydro_lower_stack]),
        "y_upper": np.concatenate([solar_upper_stack, wind_upper_stack, hydro_upper_stack]),
        "source": np.concatenate([["Solar"] * n, ["Wind"] * n, ["Hydro"] * n]),
    }
)

# Colors
colors_main = ["#306998", "#FFD43B", "#22C55E"]  # Python Blue, Python Yellow, Green

# Create plot with stacked areas and confidence ribbons
plot = (
    ggplot()
    # Confidence bands (lighter, behind main areas)
    + geom_ribbon(aes(x="x", ymin="y_lower", ymax="y_upper", fill="source"), data=df_conf, alpha=0.25)
    # Main stacked areas
    + geom_ribbon(aes(x="x", ymin="y_min", ymax="y_max", fill="source"), data=df_areas, alpha=0.7)
    # Central lines for clarity
    + geom_line(aes(x="x", y="y", color="source"), data=df_lines, size=1.5)
    # Styling
    + scale_fill_manual(values=colors_main, name="Energy Source")
    + scale_color_manual(values=colors_main, guide="none")
    + scale_x_continuous(breaks=list(range(0, n, 4)), labels=[x_labels[i] for i in range(0, n, 4)])
    + labs(
        title="area-stacked-confidence · letsplot · pyplots.ai",
        x="Quarter",
        y="Energy Consumption (TWh)",
        caption="Shaded bands show 90% prediction intervals",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
