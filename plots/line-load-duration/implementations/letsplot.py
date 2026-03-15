""" pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-15
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
    geom_area,
    geom_hline,
    geom_line,
    geom_text,
    ggplot,
    ggsize,
    labs,
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
seasonal_component = 250 * np.sin(2 * np.pi * (day_of_year - 30) / 365) ** 2
daily_pattern = 150 * np.sin(np.pi * (hour_of_day - 6) / 16) ** 2
daily_pattern[hour_of_day < 6] = 0
noise = np.random.normal(0, 30, 8760)

hourly_load = base_load + seasonal_component + daily_pattern + noise
hourly_load = np.clip(hourly_load, 350, 1250)

# Sort descending to create load duration curve
load_sorted = np.sort(hourly_load)[::-1]
rank_hours = np.arange(8760)

# Define load regions
peak_threshold = 850
intermediate_threshold = 550

# Total energy (area under curve) in GWh
total_energy_gwh = np.sum(load_sorted) / 1000

# Create main dataframe for shaded regions
peak_load = np.where(load_sorted > peak_threshold, load_sorted, peak_threshold)
intermediate_load = np.where(
    load_sorted > intermediate_threshold, np.minimum(load_sorted, peak_threshold), intermediate_threshold
)
base_load_fill = np.minimum(load_sorted, intermediate_threshold)

df = pd.DataFrame(
    {
        "hour": list(rank_hours) * 3,
        "load_mw": np.concatenate([peak_load, intermediate_load, base_load_fill]),
        "region": ["Peak"] * 8760 + ["Intermediate"] * 8760 + ["Base"] * 8760,
    }
)

df["region"] = pd.Categorical(df["region"], categories=["Peak", "Intermediate", "Base"], ordered=True)

# Dataframe for the main curve line
df_line = pd.DataFrame({"hour": rank_hours, "load_mw": load_sorted})

# Label positions for region annotations
peak_hours = np.sum(load_sorted > peak_threshold)
intermediate_hours = np.sum(load_sorted > intermediate_threshold)

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

# Energy annotation
df_energy = pd.DataFrame(
    {"hour": [6500], "load_mw": [1100], "label": [f"Total Energy: {total_energy_gwh:,.0f} GWh/year"]}
)

# Capacity tier lines
df_tiers = pd.DataFrame(
    {
        "yintercept": [peak_threshold, intermediate_threshold],
        "label": [f"Intermediate Capacity: {peak_threshold} MW", f"Base Capacity: {intermediate_threshold} MW"],
    }
)

# Plot
plot = (
    ggplot()
    + geom_area(data=df[df["region"] == "Peak"], mapping=aes(x="hour", y="load_mw"), fill="#E74C3C", alpha=0.35)
    + geom_area(data=df[df["region"] == "Intermediate"], mapping=aes(x="hour", y="load_mw"), fill="#F39C12", alpha=0.35)
    + geom_area(data=df[df["region"] == "Base"], mapping=aes(x="hour", y="load_mw"), fill="#306998", alpha=0.4)
    + geom_line(data=df_line, mapping=aes(x="hour", y="load_mw"), color="#1a1a1a", size=1.2)
    + geom_hline(yintercept=peak_threshold, linetype="dashed", color="#C0392B", size=0.8)
    + geom_hline(yintercept=intermediate_threshold, linetype="dashed", color="#D68910", size=0.8)
    + geom_text(
        data=df_labels, mapping=aes(x="hour", y="load_mw", label="label"), size=14, color="#2c3e50", fontface="bold"
    )
    + geom_text(
        data=df_energy, mapping=aes(x="hour", y="load_mw", label="label"), size=12, color="#2c3e50", fontface="italic"
    )
    + geom_text(
        data=pd.DataFrame({"hour": [8400], "load_mw": [peak_threshold + 30], "label": [f"{peak_threshold} MW"]}),
        mapping=aes(x="hour", y="load_mw", label="label"),
        size=11,
        color="#C0392B",
    )
    + geom_text(
        data=pd.DataFrame(
            {"hour": [8400], "load_mw": [intermediate_threshold + 30], "label": [f"{intermediate_threshold} MW"]}
        ),
        mapping=aes(x="hour", y="load_mw", label="label"),
        size=11,
        color="#D68910",
    )
    + scale_x_continuous(
        name="Hours of Year (Ranked by Demand)",
        breaks=[0, 2000, 4000, 6000, 8000],
        labels=["0", "2,000", "4,000", "6,000", "8,000"],
    )
    + scale_y_continuous(name="Power Demand (MW)", breaks=[0, 200, 400, 600, 800, 1000, 1200])
    + labs(title="line-load-duration · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#e0e0e0", size=0.3),
        legend_position="none",
        plot_background=element_rect(fill="white", color="white"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
