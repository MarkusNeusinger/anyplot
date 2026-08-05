""" anyplot.ai
strip-basic: Basic Strip Plot
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 84/100 | Updated: 2026-08-05
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_rect,
    element_text,
    geom_point,
    ggplot,
    labs,
    position_jitter,
    scale_color_manual,
    stat_summary,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]
NEUTRAL = INK  # Imprint semantic anchor for reference lines / baselines

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
df["treatment"] = pd.Categorical(df["treatment"], categories=list(distributions), ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="treatment", y="response_time", color="treatment"))
    + geom_point(position=position_jitter(width=0.25, height=0, random_state=42), size=2.5, alpha=0.65)
    + stat_summary(
        fun_y=np.mean, fun_ymin=np.mean, fun_ymax=np.mean, geom="crossbar", width=0.4, color=NEUTRAL, size=0.4
    )
    + annotate("text", x="Drug C", y=8, label="Fastest response", color=INK, size=8, fontweight="bold", ha="center")
    + scale_color_manual(values=IMPRINT)
    + labs(x="Treatment Group", y="Response Time (seconds)", title="strip-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.20),
        panel_grid_minor=element_line(color=INK, size=0.15, alpha=0.08),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        plot_title=element_text(color=INK, size=12),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
