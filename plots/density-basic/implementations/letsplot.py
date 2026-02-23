"""pyplots.ai
density-basic: Basic Density Plot
Library: letsplot 4.8.2 | Python 3.14.3
Quality: repair-2 | Updated: 2026-02-23
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()  # noqa: F405

# Data - Simulated marathon finish times with realistic right skew
np.random.seed(42)
finish_minutes = np.concatenate(
    [
        np.random.normal(240, 25, 350),  # Main pack (~4 hour runners)
        np.random.normal(200, 15, 100),  # Competitive runners (~3:20)
        np.random.normal(300, 20, 50),  # Casual runners (~5 hours)
    ]
)
finish_minutes = np.clip(finish_minutes, 140, 400)

df = pd.DataFrame({"time": finish_minutes})

# Rug data: small vertical ticks at each observation
rug_df = pd.DataFrame({"x": finish_minutes, "y0": 0.0, "y1": 0.0004})

# Runner group centroids for storytelling annotations (staggered y to avoid crowding)
group_labels = pd.DataFrame(
    {
        "x": [195, 243, 300],
        "y": [0.0131, 0.0119, 0.0131],
        "label": ["Competitive (~3:20)", "Main Pack (~4:00)", "Casual (~5:00)"],
    }
)

# Plot
plot = (
    ggplot(df, aes(x="time"))  # noqa: F405
    + geom_density(  # noqa: F405
        fill="#306998",
        color="#1e4263",
        alpha=0.55,
        size=1.8,
        kernel="gaussian",
        adjust=0.85,
        trim=True,
        tooltips=layer_tooltips()  # noqa: F405
        .line("@|@time")
        .line("density|@..density.."),
    )
    + geom_segment(  # noqa: F405
        data=rug_df,
        mapping=aes(x="x", y="y0", xend="x", yend="y1"),  # noqa: F405
        color="#1e4263",
        alpha=0.15,
        size=0.4,
    )
    + geom_vline(xintercept=200, linetype="dashed", color="#1a5276", alpha=0.4, size=0.7)  # noqa: F405
    + geom_vline(xintercept=240, linetype="dashed", color="#306998", alpha=0.4, size=0.7)  # noqa: F405
    + geom_vline(xintercept=300, linetype="dashed", color="#5d8aa8", alpha=0.4, size=0.7)  # noqa: F405
    + geom_text(  # noqa: F405
        data=group_labels,
        mapping=aes(x="x", y="y", label="label"),  # noqa: F405
        size=12,
        color="#444444",
    )
    + labs(  # noqa: F405
        x="Finish Time (minutes)", y="Density (×10⁻³)", title="density-basic · letsplot · pyplots.ai"
    )
    + scale_x_continuous(breaks=list(range(150, 401, 50)))  # noqa: F405
    + scale_y_continuous(  # noqa: F405
        breaks=[0.002, 0.004, 0.006, 0.008, 0.010], labels=["2", "4", "6", "8", "10"], expand=[0.02, 0, 0.38, 0]
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color="#e0e0e0", size=0.4),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x for 4800 x 2700 px) and HTML
ggsave(plot, "plot.png", path=".", scale=3)  # noqa: F405
ggsave(plot, "plot.html", path=".")  # noqa: F405
