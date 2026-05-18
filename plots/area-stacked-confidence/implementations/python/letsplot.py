"""anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]

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

# Theme-adaptive plot styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=INK, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.4),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    legend_position="right",
)

# Create plot with stacked areas and confidence ribbons
plot = (
    ggplot()
    + geom_ribbon(aes(x="x", ymin="y_lower", ymax="y_upper", fill="source"), data=df_conf, alpha=0.25)
    + geom_ribbon(aes(x="x", ymin="y_min", ymax="y_max", fill="source"), data=df_areas, alpha=0.7)
    + geom_line(aes(x="x", y="y", color="source"), data=df_lines, size=1.5)
    + scale_fill_manual(values=OKABE_ITO, name="Energy Source")
    + scale_color_manual(values=OKABE_ITO, guide="none")
    + scale_x_continuous(breaks=list(range(0, n, 4)), labels=[x_labels[i] for i in range(0, n, 4)])
    + labs(
        title="area-stacked-confidence · Python · letsplot · anyplot.ai",
        x="Quarter",
        y="Energy Consumption (TWh)",
        caption="Shaded bands show 90% prediction intervals",
    )
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800x2700)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactive viewing
ggsave(plot, f"plot-{THEME}.html", path=".")
