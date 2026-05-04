"""anyplot.ai
strip-basic: Basic Strip Plot
Library: plotnine | Python 3.13
Quality: pending | Updated: 2026-05-04
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_point,
    ggplot,
    labs,
    position_jitter,
    scale_color_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Patient response times (seconds) across different drug treatments
np.random.seed(42)

distributions = {
    "Placebo": {"mean": 45, "std": 12, "n": 40},
    "Drug A": {"mean": 32, "std": 8, "n": 45},
    "Drug B": {"mean": 28, "std": 10, "n": 42},
    "Drug C": {"mean": 25, "std": 6, "n": 38},
}

data = []
for treatment, params in distributions.items():
    times = np.random.normal(params["mean"], params["std"], params["n"])
    times = np.clip(times, 5, 80)
    data.extend([(treatment, time) for time in times])

df = pd.DataFrame(data, columns=["treatment", "response_time"])

# Plot
plot = (
    ggplot(df, aes(x="treatment", y="response_time", color="treatment"))
    + geom_point(position=position_jitter(width=0.25, height=0, random_state=42), size=4, alpha=0.65)
    + scale_color_manual(values=OKABE_ITO)
    + labs(x="Treatment Group", y="Response Time (seconds)", title="strip-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.20),
        panel_grid_minor=element_line(color=INK, size=0.15, alpha=0.08),
        axis_title=element_text(color=INK, size=20),
        axis_text=element_text(color=INK_SOFT, size=16),
        plot_title=element_text(color=INK, size=24),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
