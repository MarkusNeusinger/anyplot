"""pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Logistic map: x(n+1) = r * x(n) * (1 - x(n))
r_values = np.linspace(2.5, 4.0, 1500)
transient = 200
iterations = 80

r_all = []
x_all = []

for r in r_values:
    x = 0.5
    for _ in range(transient):
        x = r * x * (1.0 - x)
    for _ in range(iterations):
        x = r * x * (1.0 - x)
        r_all.append(r)
        x_all.append(x)

df = pd.DataFrame({"r": np.array(r_all), "x": np.array(x_all)})

# Key bifurcation points
bif_r = [3.0, 3.449, 3.544, 3.5699]
segments_df = pd.DataFrame({"r": bif_r, "ymin": [0.0] * 4, "ymax": [1.0] * 4})
labels_df = pd.DataFrame(
    {"r": bif_r, "x": [0.04, 0.04, 0.04, 0.04], "label": ["Period-2", "Period-4", "Period-8", "Chaos"]}
)

# Plot
plot = (
    ggplot(df, aes(x="r", y="x"))  # noqa: F405
    + geom_point(  # noqa: F405
        color="#306998", size=0.1, alpha=0.12, tooltips="none"
    )
    + geom_segment(  # noqa: F405
        aes(x="r", y="ymin", xend="r", yend="ymax"),  # noqa: F405
        data=segments_df,
        color="#CCCCCC",
        size=0.5,
        linetype="dashed",
    )
    + geom_text(  # noqa: F405
        aes(x="r", y="x", label="label"),  # noqa: F405
        data=labels_df,
        size=9,
        color="#888888",
        angle=90,
        hjust=0,
    )
    + labs(  # noqa: F405
        x="Growth Rate (r)",
        y="Population (x)",
        title="bifurcation-basic · letsplot · pyplots.ai",
        caption="Logistic map: x(n+1) = r · x(n) · (1 − x(n))",
    )
    + scale_x_continuous(  # noqa: F405
        breaks=[2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0], expand=[0.02, 0]
    )
    + scale_y_continuous(  # noqa: F405
        breaks=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0], expand=[0.02, 0]
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16, color="#555555"),  # noqa: F405
        axis_title=element_text(size=20, color="#333333"),  # noqa: F405
        plot_title=element_text(size=24, color="#222222", face="bold"),  # noqa: F405
        plot_caption=element_text(size=13, color="#999999", face="italic"),  # noqa: F405
        panel_grid_major=element_line(color="#EEEEEE", size=0.3),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),  # noqa: F405
        panel_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),  # noqa: F405
        axis_ticks=element_line(color="#CCCCCC", size=0.3),  # noqa: F405
        plot_margin=[30, 40, 20, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
