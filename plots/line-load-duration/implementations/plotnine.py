"""pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_text,
    geom_hline,
    geom_line,
    geom_ribbon,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data
np.random.seed(42)
hours_in_year = 8760

base_load = 400
peak_load = 1200

hourly_load = np.zeros(hours_in_year)
for i in range(hours_in_year):
    hour_of_day = i % 24
    day_of_year = i // 24
    seasonal = 80 * np.sin(2 * np.pi * (day_of_year - 30) / 365)
    daily = 120 * np.sin(np.pi * (hour_of_day - 6) / 18) if 6 <= hour_of_day <= 24 else -60
    noise = np.random.normal(0, 30)
    hourly_load[i] = 700 + seasonal + daily + noise

hourly_load = np.clip(hourly_load, base_load, peak_load)
load_sorted = np.sort(hourly_load)[::-1]

base_capacity = 500
intermediate_capacity = 850

df = pd.DataFrame({"hour": np.arange(hours_in_year), "load_mw": load_sorted})

total_energy_gwh = np.trapezoid(load_sorted) / 1000
peak_hours = int((load_sorted > intermediate_capacity).sum())
intermediate_hours = int(((load_sorted > base_capacity) & (load_sorted <= intermediate_capacity)).sum())

# Region shading: three ribbons stacked
df["base_top"] = np.minimum(df["load_mw"], base_capacity)
df["inter_top"] = np.clip(df["load_mw"], base_capacity, intermediate_capacity)
df["peak_top"] = np.where(df["load_mw"] > intermediate_capacity, df["load_mw"], intermediate_capacity)

# Label positions
peak_label_x = peak_hours / 2
inter_label_x = peak_hours + intermediate_hours / 2
base_label_x = hours_in_year / 2

# Plot
plot = (
    ggplot(df, aes(x="hour"))
    + geom_ribbon(aes(ymin=0, ymax="base_top"), fill="#306998", alpha=0.4)
    + geom_ribbon(aes(ymin=base_capacity, ymax="inter_top"), fill="#4A90C4", alpha=0.4)
    + geom_ribbon(aes(ymin=intermediate_capacity, ymax="peak_top"), fill="#E8734A", alpha=0.4)
    + geom_line(aes(y="load_mw"), color="#1a1a1a", size=0.8)
    + geom_hline(yintercept=base_capacity, linetype="dashed", color="#306998", size=0.7, alpha=0.8)
    + geom_hline(yintercept=intermediate_capacity, linetype="dashed", color="#4A90C4", size=0.7, alpha=0.8)
    + annotate(
        "text",
        x=hours_in_year - 200,
        y=base_capacity + 25,
        label=f"Base Capacity ({base_capacity} MW)",
        size=11,
        ha="right",
        color="#306998",
        fontweight="bold",
    )
    + annotate(
        "text",
        x=hours_in_year - 200,
        y=intermediate_capacity + 25,
        label=f"Intermediate Capacity ({intermediate_capacity} MW)",
        size=11,
        ha="right",
        color="#4A90C4",
        fontweight="bold",
    )
    + annotate(
        "text",
        x=peak_label_x,
        y=intermediate_capacity + 80,
        label="Peak",
        size=14,
        ha="center",
        color="#C0552E",
        fontweight="bold",
    )
    + annotate(
        "text",
        x=inter_label_x,
        y=(base_capacity + intermediate_capacity) / 2,
        label="Intermediate",
        size=14,
        ha="center",
        color="#3570A0",
        fontweight="bold",
    )
    + annotate(
        "text",
        x=base_label_x,
        y=base_capacity / 2,
        label="Base Load",
        size=14,
        ha="center",
        color="#1E4060",
        fontweight="bold",
    )
    + annotate(
        "text",
        x=hours_in_year * 0.75,
        y=peak_load - 40,
        label=f"Total Energy: {total_energy_gwh:,.0f} GWh",
        size=12,
        ha="center",
        color="#333333",
        fontweight="bold",
    )
    + scale_x_continuous(breaks=[0, 2000, 4000, 6000, 8000], labels=["0", "2,000", "4,000", "6,000", "8,000"])
    + scale_y_continuous(breaks=[0, 200, 400, 600, 800, 1000, 1200], limits=[0, peak_load + 100])
    + labs(x="Hours", y="Load (MW)", title="line-load-duration · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, weight="bold"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(alpha=0.2, size=0.5),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
