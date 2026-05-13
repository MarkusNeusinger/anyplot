""" anyplot.ai
line-stepwise: Step Line Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-13
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

# Data - Server Response Time Monitor (discrete state changes)
np.random.seed(42)
hours = np.arange(0, 24)

# Response time that changes in steps (server performance states)
base_response = 50
response_times = [base_response]

for i in range(1, 24):
    if i in [6, 9, 12, 15, 18, 21]:
        change = np.random.choice([-20, -10, 10, 20, 30])
        new_val = max(20, min(150, response_times[-1] + change))
        response_times.append(new_val)
    else:
        response_times.append(response_times[-1])

response_times = np.array(response_times)
df = pd.DataFrame({"hour": hours, "response_time": response_times})

# Theme-adaptive plot styling
anyplot_theme = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=24, color=INK),
)

# Plot
plot = (
    ggplot(df, aes(x="hour", y="response_time"))  # noqa: F405
    + geom_step(color=BRAND, size=2, direction="hv")  # noqa: F405
    + geom_point(  # noqa: F405
        data=df[df["hour"].isin([6, 9, 12, 15, 18, 21])], color=BRAND, size=5, shape=21, fill=BRAND, stroke=1.5
    )
    + labs(  # noqa: F405
        x="Hour of Day", y="Response Time (ms)", title="line-stepwise · letsplot · anyplot.ai"
    )
    + scale_x_continuous(breaks=list(range(0, 25, 3)))  # noqa: F405
    + scale_y_continuous(expand=[0.05, 0.05])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + anyplot_theme
    + theme(legend_position="none")  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG and HTML with theme suffix
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
