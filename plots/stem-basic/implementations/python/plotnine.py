"""anyplot.ai
stem-basic: Basic Stem Plot
Library: plotnine 0.15.7 | Python 3.13.12
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    geom_segment,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"

# Data - Damped sinusoidal discrete signal (signal processing example)
np.random.seed(42)
n = 30
t = np.arange(n)
decay = np.exp(-t / 12.0)
signal = decay * np.cos(0.55 * t)

df = pd.DataFrame({"t": t, "signal": signal, "zero": 0.0})

# Fine-resolution decay envelope, plotted as a reference curve so the
# amplitude decay is visually explicit rather than only implied by the stems.
t_env = np.linspace(0, n - 1, 200)
envelope = pd.DataFrame({"t": t_env, "upper": np.exp(-t_env / 12.0), "lower": -np.exp(-t_env / 12.0)})

# Plot
plot = (
    ggplot(df, aes(x="t"))
    + geom_line(envelope, aes(x="t", y="upper"), color=INK_SOFT, alpha=0.5, linetype="dashed", size=0.6)
    + geom_line(envelope, aes(x="t", y="lower"), color=INK_SOFT, alpha=0.5, linetype="dashed", size=0.6)
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.5)
    + geom_segment(aes(x="t", xend="t", y="zero", yend="signal"), color=BRAND, size=1.0)
    + geom_point(aes(y="signal"), color=BRAND, size=3.0, stroke=0.5)
    + labs(x="Sample Index", y="Amplitude (normalized)", title="stem-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_major_x=element_line(color=INK, size=0.0, alpha=0.0),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        axis_line=element_line(color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
