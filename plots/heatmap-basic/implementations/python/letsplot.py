""" pyplots.ai
heatmap-basic: Basic Heatmap
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-15
"""

import numpy as np
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    ggsize,
    guide_colorbar,
    labs,
    layer_tooltips,
    scale_color_identity,
    scale_fill_viridis,
    scale_x_discrete,
    scale_y_discrete,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Monthly energy consumption (kWh) by building zone
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
zones = ["Lobby", "Offices", "Lab", "Server Room", "Cafeteria", "Warehouse"]

# Realistic patterns: seasonal variation + zone-specific baselines
baselines = np.array([120, 280, 350, 520, 180, 90])
seasonal = np.array([1.3, 1.2, 1.0, 0.8, 0.7, 0.75, 0.85, 0.9, 0.8, 0.9, 1.1, 1.25])

values = np.outer(seasonal, baselines)
noise = np.random.normal(0, 15, (len(months), len(zones)))
values = np.round(values + noise, 0).astype(int)

# Build long-form data using vectorized operations
n_months, n_zones = len(months), len(zones)
zone_col = np.tile(zones, n_months).tolist()
month_col = np.repeat(months, n_zones).tolist()
kwh_col = values.flatten().tolist()

# Adaptive text color: white on dark cells, dark on light cells
median_val = int(np.median(kwh_col))
text_color = ["#ffffff" if v > median_val else "#1a1a2e" for v in kwh_col]

data = {"Zone": zone_col, "Month": month_col, "kWh": kwh_col, "label_color": text_color}

# Heatmap with perceptually-uniform viridis colormap and interactive tooltips
plot = (
    ggplot(data, aes(x="Zone", y="Month", fill="kWh"))
    + geom_tile(
        width=0.92,
        height=0.92,
        tooltips=layer_tooltips()
        .line("@Zone | @Month")
        .line("Energy: @kWh kWh")
        .line("Median: " + str(median_val) + " kWh"),
    )
    + geom_text(aes(label="kWh", color="label_color"), size=14, fontface="bold")
    + scale_color_identity()
    + scale_fill_viridis(
        option="viridis", direction=-1, name="Energy (kWh)", guide=guide_colorbar(barwidth=18, barheight=300, nbin=256)
    )
    + scale_x_discrete(limits=zones)
    + scale_y_discrete(limits=months[::-1])
    + labs(x="Building Zone", y="Month", title="heatmap-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=26, face="bold", color="#1a1a2e"),
        axis_title=element_text(size=20, color="#2d2d44"),
        axis_text_x=element_text(size=16, face="bold", color="#2d2d44"),
        axis_text_y=element_text(size=16, color="#2d2d44"),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16, face="bold"),
        panel_grid=element_blank(),
        plot_background=element_rect(fill="#fafafa", color="#fafafa"),
        plot_margin=[40, 20, 20, 20],
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive tooltips (lets-plot distinctive feature)
ggsave(plot, "plot.html", path=".")
