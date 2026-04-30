"""anyplot.ai
rug-basic: Basic Rug Plot
Library: letsplot | Python 3.13
Quality: pending | Updated: 2026-04-30
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Simulated response times with clusters and gaps (realistic scenario)
np.random.seed(42)
cluster1 = np.random.normal(120, 15, 45)  # Fast responses ~120ms
cluster2 = np.random.normal(250, 30, 35)  # Medium responses ~250ms
cluster3 = np.random.normal(400, 40, 15)  # Slow responses ~400ms
outliers = np.array([550, 620, 700, 780])  # Edge outliers
values = np.concatenate([cluster1, cluster2, cluster3, outliers])

df = pd.DataFrame({"response_time": values})

rug_y_max = 0.0005
df_rug = pd.DataFrame(
    {"x": values, "xend": values, "y": np.zeros(len(values)), "yend": np.full(len(values), rug_y_max)}
)

# Plot - Density curve with rug marks along x-axis
plot = (
    ggplot(df, aes(x="response_time"))  # noqa: F405
    + geom_density(fill=BRAND, alpha=0.25, size=1.5, color=BRAND)  # noqa: F405
    + geom_segment(  # noqa: F405
        aes(x="x", xend="xend", y="y", yend="yend"),  # noqa: F405
        data=df_rug,
        color=BRAND,
        alpha=0.7,
        size=1.5,
    )
    + labs(  # noqa: F405
        x="Response Time (ms)", y="Density", title="rug-basic · letsplot · anyplot.ai"
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        axis_title=element_text(size=20, color=INK),  # noqa: F405
        axis_text=element_text(size=16, color=INK_SOFT),  # noqa: F405
        plot_title=element_text(size=24, color=INK),  # noqa: F405
        panel_grid_major=element_line(color=INK_SOFT, size=0.2),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_line=element_line(color=INK_SOFT),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x for 4800x2700) and HTML
export_ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
export_ggsave(plot, f"plot-{THEME}.html", path=".")
