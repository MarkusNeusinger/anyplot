"""pyplots.ai
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
# Higher resolution in chaotic regime for denser visualization
r_stable = np.linspace(2.5, 3.45, 600)
r_chaotic = np.linspace(3.45, 4.0, 1600)
r_values = np.concatenate([r_stable, r_chaotic])
transient = 250
iterations = 100

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
    {"r": bif_r, "x": [0.93, 0.83, 0.73, 0.63], "label": ["Period-2", "Period-4", "Period-8", "Chaos"]}
)

# Feigenbaum point annotation
feigen_df = pd.DataFrame({"r": [3.5699], "x": [0.05], "label": ["δ ≈ 4.669 (Feigenbaum)"]})

# Plot with perceptually uniform viridis-based gradient
plot = (
    ggplot(df, aes(x="r", y="x", color="r"))  # noqa: F405
    + geom_point(  # noqa: F405
        size=0.4,
        alpha=0.35,
        tooltips="none",
        show_legend=False,
        sampling=sampling_pick(n=220000),  # noqa: F405
    )
    + scale_color_gradientn(  # noqa: F405
        colors=["#440154", "#414487", "#2A788E", "#22A884", "#7AD151"], name="r"
    )
    + geom_segment(  # noqa: F405
        aes(x="r", y="ymin", xend="r", yend="ymax"),  # noqa: F405
        data=segments_df,
        color="#AAAAAA",
        size=0.3,
        linetype="dashed",
        inherit_aes=False,
        tooltips="none",
    )
    + geom_text(  # noqa: F405
        aes(x="r", y="x", label="label"),  # noqa: F405
        data=labels_df,
        size=13,
        color="#555555",
        hjust=0.5,
        vjust=0,
        inherit_aes=False,
    )
    + geom_text(  # noqa: F405
        aes(x="r", y="x", label="label"),  # noqa: F405
        data=feigen_df,
        size=11,
        color="#777777",
        hjust=0,
        vjust=1,
        fontface="italic",
        nudge_x=0.02,
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
        breaks=[2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0], expand=[0.02, 0], format=".2f"
    )
    + scale_y_continuous(  # noqa: F405
        breaks=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0], expand=[0.02, 0], format=".1f"
    )
    + coord_cartesian(ylim=[0, 1])  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16, color="#555555"),  # noqa: F405
        axis_title=element_text(size=20, color="#333333"),  # noqa: F405
        plot_title=element_text(size=24, color="#222222", face="bold"),  # noqa: F405
        plot_caption=element_text(size=13, color="#888888", face="italic"),  # noqa: F405
        panel_grid_major_x=element_line(color="#E8E8E8", size=0.3),  # noqa: F405
        panel_grid_major_y=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),  # noqa: F405
        panel_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),  # noqa: F405
        axis_ticks=element_line(color="#CCCCCC", size=0.3),  # noqa: F405
        axis_line=element_line(color="#CCCCCC", size=0.4),  # noqa: F405
        plot_margin=[30, 40, 20, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
