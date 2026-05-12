""" anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 86/100 | Created: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data: Plant growth by treatment type
np.random.seed(42)
treatment_a = np.random.normal(loc=45, scale=8, size=40)
growth_a = treatment_a * 1.1 + np.random.normal(loc=5, scale=6, size=40)

treatment_b = np.random.normal(loc=52, scale=9, size=35)
growth_b = treatment_b * 0.95 + np.random.normal(loc=3, scale=7, size=35)

treatment_c = np.random.normal(loc=38, scale=7, size=38)
growth_c = treatment_c * 1.25 + np.random.normal(loc=8, scale=5, size=38)

treatment_d = np.random.normal(loc=55, scale=10, size=37)
growth_d = treatment_d * 0.85 + np.random.normal(loc=2, scale=8, size=37)

df = pd.DataFrame(
    {
        "Temperature (°C)": np.concatenate([treatment_a, treatment_b, treatment_c, treatment_d]),
        "Growth Rate (%)": np.concatenate([growth_a, growth_b, growth_c, growth_d]),
        "Treatment": (["Treatment A"] * 40 + ["Treatment B"] * 35 + ["Treatment C"] * 38 + ["Treatment D"] * 37),
    }
)

# Plot
plot = (
    ggplot(df, aes(x="Temperature (°C)", y="Growth Rate (%)", color="Treatment"))
    + geom_point(size=3, alpha=0.75)
    + scale_color_manual(values=OKABE_ITO[:4])
    + labs(
        x="Temperature (°C)",
        y="Growth Rate (%)",
        title="scatter-categorical · letsplot · anyplot.ai",
        color="Treatment",
    )
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=None),
        panel_grid_major=element_line(color=INK, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
    )
)

# Save
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
