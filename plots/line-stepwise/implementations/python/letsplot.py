"""anyplot.ai
line-stepwise: Step Line Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401
from lets_plot import element_blank, element_line, element_rect, element_text, theme
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"

# Column constants
HOUR = "Hour of Day"  # role: x
RESPONSE = "Response Time (ms)"  # role: y

# Data: server response time monitor (discrete state changes); replace with your own table
np.random.seed(42)
levels = [50]
for hour in range(1, 24):
    if hour in [6, 9, 12, 15, 18, 21]:
        change = np.random.choice([-20, -10, 10, 20, 30])
        levels.append(max(20, min(150, levels[-1] + change)))
    else:
        levels.append(levels[-1])
df = pd.DataFrame({HOUR: np.arange(0, 24), RESPONSE: levels})

# Plot
anyplot_theme = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=16, color=INK),
)

# Mark the points where the level changes
changes = df[df[RESPONSE].diff().fillna(0) != 0]

plot = (
    ggplot(df, aes(x=HOUR, y=RESPONSE))  # noqa: F405
    + geom_step(color=BRAND, size=1.0, direction="hv")  # noqa: F405
    + geom_point(data=changes, color=BRAND, size=2.5, shape=21, fill=BRAND, stroke=0.8)  # noqa: F405
    + labs(title="line-stepwise · python · letsplot · anyplot.ai")  # noqa: F405
    + scale_x_continuous(breaks=list(range(0, int(df[HOUR].max()) + 2, 3)))  # noqa: F405
    + scale_y_continuous(expand=[0.05, 0.05])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + anyplot_theme
    + theme(legend_position="none")  # noqa: F405
    + ggsize(800, 450)  # noqa: F405
)

# Save PNG and HTML with theme suffix
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
