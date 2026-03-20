""" pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-20
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

# Stagger labels at different y positions to avoid overlap
labels_df = pd.DataFrame(
    {"r": bif_r, "x": [0.92, 0.82, 0.72, 0.62], "label": ["Period-2", "Period-4", "Period-8", "Chaos"]}
)

# Plot with color-mapped r values for visual differentiation
plot = (
    ggplot(df, aes(x="r", y="x", color="r"))  # noqa: F405
    + geom_point(  # noqa: F405
        size=0.5, alpha=0.25, tooltips="none"
    )
    + scale_color_gradient2(  # noqa: F405
        low="#306998", mid="#7B68AE", high="#E8555B", midpoint=3.45, name="r"
    )
    + geom_segment(  # noqa: F405
        aes(x="r", y="ymin", xend="r", yend="ymax"),  # noqa: F405
        data=segments_df,
        color="#BBBBBB",
        size=0.4,
        linetype="dashed",
        inherit_aes=False,
    )
    + geom_text(  # noqa: F405
        aes(x="r", y="x", label="label"),  # noqa: F405
        data=labels_df,
        size=10,
        color="#666666",
        hjust=0.5,
        vjust=0,
        inherit_aes=False,
    )
    + guides(color="none")  # noqa: F405
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
    + coord_cartesian(ylim=[0, 1])  # noqa: F405
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
