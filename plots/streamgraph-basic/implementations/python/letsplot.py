""" anyplot.ai
streamgraph-basic: Basic Stream Graph
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-05
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave
from scipy.interpolate import make_interp_spline


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Data — monthly streaming hours by music genre over two years
np.random.seed(42)
n_months = 24
genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz"]

raw_values = {}
months_orig = np.arange(n_months, dtype=float)
for i, genre in enumerate(genres):
    base = 100 + 50 * np.sin(np.linspace(0, 4 * np.pi, n_months) + i * 0.7)
    trend = np.linspace(0, 25, n_months) * (1 if i % 2 == 0 else -0.6)
    noise = np.random.randn(n_months) * 8
    raw_values[genre] = np.clip(base + trend + noise, 25, None)

# Smooth each series with a cubic spline for flowing curves
n_interp = n_months * 8
months_smooth = np.linspace(0, n_months - 1, n_interp)
values_smooth = {}
for genre in genres:
    spline = make_interp_spline(months_orig, raw_values[genre], k=3)
    values_smooth[genre] = np.clip(spline(months_smooth), 10, None)

# Compute streamgraph positions (symmetric baseline around zero)
values_matrix = np.array([values_smooth[g] for g in genres])
total_per_point = values_matrix.sum(axis=0)
baseline_offset = -total_per_point / 2

data = []
for t_idx, t in enumerate(months_smooth):
    cumulative = baseline_offset[t_idx]
    for genre_idx, genre in enumerate(genres):
        ymin = cumulative
        ymax = cumulative + values_matrix[genre_idx, t_idx]
        data.append({"month": t, "genre": genre, "ymin": ymin, "ymax": ymax})
        cumulative = ymax

df = pd.DataFrame(data)

# Plot
anyplot_theme = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
    panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
    panel_grid_major_x=element_line(color=INK_SOFT, size=0.3, linetype="dashed"),  # noqa: F405
    panel_grid_major_y=element_blank(),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
    axis_title=element_text(color=INK, size=20),  # noqa: F405
    axis_text=element_text(color=INK_SOFT, size=16),  # noqa: F405
    axis_text_y=element_blank(),  # noqa: F405
    axis_ticks_y=element_blank(),  # noqa: F405
    axis_line=element_line(color=INK_SOFT),  # noqa: F405
    plot_title=element_text(color=INK, size=24),  # noqa: F405
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
    legend_text=element_text(color=INK_SOFT, size=16),  # noqa: F405
    legend_title=element_text(color=INK, size=18),  # noqa: F405
)

plot = (
    ggplot(df, aes(x="month", fill="genre"))  # noqa: F405
    + geom_ribbon(aes(ymin="ymin", ymax="ymax"), alpha=0.9)  # noqa: F405
    + scale_fill_manual(values=OKABE_ITO)  # noqa: F405
    + scale_x_continuous(  # noqa: F405
        breaks=[0, 6, 12, 18, 23], labels=["Jan '23", "Jul '23", "Jan '24", "Jul '24", "Dec '24"]
    )
    + labs(  # noqa: F405
        x="Month", y="", fill="Genre", title="streamgraph-basic · letsplot · anyplot.ai"
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + anyplot_theme
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
