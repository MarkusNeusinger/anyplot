"""anyplot.ai
band-basic: Basic Band Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — first series is always #009E73
BRAND = "#009E73"

# Column constants
TIME = "Time (days)"  # role: x
LOWER = "Lower 95% bound (°C)"  # role: y_lower
UPPER = "Upper 95% bound (°C)"  # role: y_upper
CENTER = "Temperature (°C)"  # role: y_center

# Data: replace this block with your own table, for example df = pd.read_csv("sensor.csv")
np.random.seed(42)
n_points = 60
days = np.linspace(0, 30, n_points)

# Central trend: temperature rising then stabilizing (realistic sensor pattern)
temperature = 18 + 4 * (1 - np.exp(-0.15 * days)) + 1.5 * np.sin(0.4 * days)
temperature = temperature + np.random.normal(0, 0.3, n_points)

# Uncertainty narrows as model calibrates, then widens for extrapolation
uncertainty = 1.8 * np.exp(-0.08 * days) + 0.3 + 0.04 * np.maximum(days - 20, 0)

df = pd.DataFrame(
    {TIME: days, LOWER: temperature - 1.96 * uncertainty, UPPER: temperature + 1.96 * uncertainty, CENTER: temperature}
)

# Plot
# Title length ~73 chars → scale down: round(12 × 67 / 73) = 11
plot = (
    ggplot(df, aes(x=TIME))
    + geom_ribbon(aes(ymin=LOWER, ymax=UPPER), fill=BRAND, alpha=0.35)
    + geom_line(aes(y=CENTER), color=INK, size=1.0)
    + labs(
        x=TIME,
        y=CENTER,
        title="Sensor Calibration Forecast · band-basic · python · plotnine · anyplot.ai",
        subtitle="Shaded region shows 95% confidence interval — narrowing during calibration, widening for extrapolation",
    )
    + scale_x_continuous(breaks=np.arange(0, df[TIME].max() + 1, 5))
    + scale_y_continuous(labels=lambda lst: [f"{v:.0f}°C" for v in lst])
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=11, color=INK),
        plot_subtitle=element_text(size=8, color=INK_SOFT),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
