""" pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_ribbon,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data: Synthetic annual hourly load profile for a mid-sized utility
np.random.seed(42)
hours = np.arange(8760)

# Build realistic hourly load with daily and seasonal patterns
hour_of_day = hours % 24
day_of_year = hours // 24

base_load = 400
seasonal_component = 450 * np.sin(2 * np.pi * (day_of_year - 30) / 365) ** 2
daily_pattern = 250 * np.sin(np.pi * (hour_of_day - 6) / 16) ** 2
daily_pattern[hour_of_day < 6] = 0
noise = np.random.normal(0, 40, 8760)

hourly_load = base_load + seasonal_component + daily_pattern + noise
hourly_load = np.clip(hourly_load, 350, 1250)

# Sort descending to create load duration curve
load_sorted = np.sort(hourly_load)[::-1]
rank_hours = np.arange(8760)

# Define load regions
peak_threshold = 900
intermediate_threshold = 550

# Total energy (area under curve) in GWh
total_energy_gwh = np.sum(load_sorted) / 1000

# Create non-overlapping ribbon regions using ymin/ymax
# Peak region: from peak_threshold up to curve (only where curve > peak_threshold)
# Intermediate region: from intermediate_threshold up to min(curve, peak_threshold)
# Base region: from 0 up to min(curve, intermediate_threshold)
peak_ymin = np.full(8760, peak_threshold, dtype=float)
peak_ymax = np.where(load_sorted > peak_threshold, load_sorted, peak_threshold)

inter_ymin = np.full(8760, intermediate_threshold, dtype=float)
inter_ymax = np.where(
    load_sorted > intermediate_threshold, np.minimum(load_sorted, peak_threshold), intermediate_threshold
)

base_ymin = np.zeros(8760)
base_ymax = np.minimum(load_sorted, intermediate_threshold)

df_peak = pd.DataFrame(
    {"hour": rank_hours, "ymin": peak_ymin, "ymax": peak_ymax, "load_mw": load_sorted, "region": "Peak Load"}
)
df_inter = pd.DataFrame(
    {"hour": rank_hours, "ymin": inter_ymin, "ymax": inter_ymax, "load_mw": load_sorted, "region": "Intermediate Load"}
)
df_base = pd.DataFrame(
    {"hour": rank_hours, "ymin": base_ymin, "ymax": base_ymax, "load_mw": load_sorted, "region": "Base Load"}
)

# Main curve dataframe
df_line = pd.DataFrame({"hour": rank_hours, "load_mw": load_sorted})

# Label positions for region annotations
peak_hours = int(np.sum(load_sorted > peak_threshold))
intermediate_hours = int(np.sum(load_sorted > intermediate_threshold))

df_labels = pd.DataFrame(
    {
        "hour": [peak_hours / 2, (peak_hours + intermediate_hours) / 2, (intermediate_hours + 8760) / 2],
        "load_mw": [
            (np.max(load_sorted) + peak_threshold) / 2,
            (peak_threshold + intermediate_threshold) / 2,
            intermediate_threshold / 2 + 20,
        ],
        "label": ["Peak\nLoad", "Intermediate\nLoad", "Base\nLoad"],
    }
)

# Compute storytelling metrics
peak_load_hours = int(np.sum(load_sorted > peak_threshold))
load_factor = np.mean(load_sorted) / np.max(load_sorted) * 100

# Energy annotation with load factor
df_energy = pd.DataFrame(
    {
        "hour": [5800],
        "load_mw": [1180],
        "label": [f"Total Energy: {total_energy_gwh:,.0f} GWh/year\nLoad Factor: {load_factor:.0f}%"],
    }
)

# Color palette
colors = {"Peak Load": "#D94F4F", "Intermediate Load": "#E8A838", "Base Load": "#306998"}

# Plot with non-overlapping geom_ribbon layers and tooltips
plot = (
    ggplot()
    + geom_ribbon(
        data=df_base,
        mapping=aes(x="hour", ymin="ymin", ymax="ymax", fill="region"),
        alpha=0.75,
        tooltips=layer_tooltips()
        .format("ymax", ".0f")
        .format("@hour", ".0f")
        .line("Hour rank: @hour")
        .line("Load: @ymax MW")
        .line("Region: @region"),
    )
    + geom_ribbon(
        data=df_inter,
        mapping=aes(x="hour", ymin="ymin", ymax="ymax", fill="region"),
        alpha=0.75,
        tooltips=layer_tooltips()
        .format("@load_mw", ".0f")
        .format("@hour", ".0f")
        .line("Hour rank: @hour")
        .line("Load: @load_mw MW")
        .line("Region: @region"),
    )
    + geom_ribbon(
        data=df_peak,
        mapping=aes(x="hour", ymin="ymin", ymax="ymax", fill="region"),
        alpha=0.75,
        tooltips=layer_tooltips()
        .format("@load_mw", ".0f")
        .format("@hour", ".0f")
        .line("Hour rank: @hour")
        .line("Load: @load_mw MW")
        .line("Region: @region"),
    )
    + geom_line(
        data=df_line,
        mapping=aes(x="hour", y="load_mw"),
        color="#1a1a1a",
        size=1.8,
        tooltips=layer_tooltips()
        .format("@load_mw", ".0f")
        .format("@hour", ",d")
        .line("Hour: @hour")
        .line("Demand: @load_mw MW"),
    )
    + geom_hline(yintercept=peak_threshold, linetype="dashed", color="#C0392B", size=1.0)
    + geom_hline(yintercept=intermediate_threshold, linetype="dashed", color="#D68910", size=1.0)
    + geom_text(
        data=df_labels, mapping=aes(x="hour", y="load_mw", label="label"), size=14, color="#2c3e50", fontface="bold"
    )
    + geom_text(
        data=df_energy, mapping=aes(x="hour", y="load_mw", label="label"), size=12, color="#2c3e50", fontface="italic"
    )
    + geom_text(
        data=pd.DataFrame(
            {"hour": [6200], "load_mw": [peak_threshold + 35], "label": [f"Peak Capacity: {peak_threshold} MW"]}
        ),
        mapping=aes(x="hour", y="load_mw", label="label"),
        size=12,
        color="#C0392B",
        fontface="bold",
    )
    + geom_text(
        data=pd.DataFrame(
            {
                "hour": [6200],
                "load_mw": [intermediate_threshold + 35],
                "label": [f"Intermediate Capacity: {intermediate_threshold} MW"],
            }
        ),
        mapping=aes(x="hour", y="load_mw", label="label"),
        size=12,
        color="#D68910",
        fontface="bold",
    )
    + scale_fill_manual(values=colors)
    + scale_x_continuous(
        name="Hours of Year (Ranked by Demand)",
        breaks=[0, 2000, 4000, 6000, 8000],
        labels=["0", "2,000", "4,000", "6,000", "8,000"],
    )
    + scale_y_continuous(name="Power Demand (MW)", breaks=[0, 200, 400, 600, 800, 1000, 1200])
    + labs(
        title="line-load-duration · letsplot · pyplots.ai",
        subtitle=f"Mid-sized utility · Peak demand {np.max(load_sorted):.0f} MW · {peak_load_hours:,} hours above peak threshold",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold", color="#1a1a1a"),
        plot_subtitle=element_text(size=16, color="#5a6d7e"),
        axis_title=element_text(size=20, color="#2c3e50"),
        axis_text=element_text(size=16, color="#4a4a4a"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#e8e8e8", size=0.3),
        legend_position="none",
        plot_background=element_rect(fill="#fafafa", color="#fafafa"),
        panel_background=element_rect(fill="#fafafa", color="#fafafa"),
        plot_margin=[40, 20, 20, 20],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
