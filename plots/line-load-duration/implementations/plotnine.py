""" pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 94/100 | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    geom_segment,
    ggplot,
    guide_legend,
    labs,
    scale_fill_manual,
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
intermediate_capacity = 800

total_energy_gwh = np.trapezoid(load_sorted) / 1000
peak_hours = int((load_sorted > intermediate_capacity).sum())

# Long-format data for grammar-of-graphics fill mapping
hours = np.arange(hours_in_year)
df_regions = pd.concat(
    [
        pd.DataFrame(
            {"hour": hours, "ymin": 0.0, "ymax": np.minimum(load_sorted, base_capacity), "region": "Base Load"}
        ),
        pd.DataFrame(
            {
                "hour": hours,
                "ymin": float(base_capacity),
                "ymax": np.clip(load_sorted, base_capacity, intermediate_capacity),
                "region": "Intermediate",
            }
        ),
        pd.DataFrame(
            {
                "hour": hours,
                "ymin": float(intermediate_capacity),
                "ymax": np.where(load_sorted > intermediate_capacity, load_sorted, float(intermediate_capacity)),
                "region": "Peak",
            }
        ),
    ],
    ignore_index=True,
)
df_regions["region"] = pd.Categorical(
    df_regions["region"], categories=["Peak", "Intermediate", "Base Load"], ordered=True
)

df_line = pd.DataFrame({"hour": hours, "load_mw": load_sorted})

# Color palette — warm-to-cool semantic encoding with strong contrast
region_colors = {"Peak": "#C0392B", "Intermediate": "#6CA6CD", "Base Load": "#1B4F72"}

# Capacity line segment data for geom_segment (plotnine-idiomatic)
df_segments = pd.DataFrame(
    {
        "x": [0, 0],
        "xend": [hours_in_year, hours_in_year],
        "y": [base_capacity, intermediate_capacity],
        "yend": [base_capacity, intermediate_capacity],
        "label": [f"Base Capacity ({base_capacity} MW)", f"Intermediate Capacity ({intermediate_capacity} MW)"],
        "color": ["#2C5F88", "#5B8DB8"],
    }
)

# Plot
plot = (
    ggplot()
    # Filled regions using mapped fill aesthetic (grammar-of-graphics approach)
    + geom_ribbon(data=df_regions, mapping=aes(x="hour", ymin="ymin", ymax="ymax", fill="region"), alpha=0.5)
    # Capacity threshold lines using geom_segment
    + geom_segment(
        data=df_segments,
        mapping=aes(x="x", xend="xend", y="y", yend="yend"),
        linetype="dashed",
        color="#4A6A8A",
        size=0.6,
        alpha=0.7,
    )
    # Main load curve
    + geom_line(data=df_line, mapping=aes(x="hour", y="load_mw"), color="#0D1B2A", size=1.0)
    # Capacity labels — positioned away from right edge
    + annotate(
        "label",
        x=hours_in_year * 0.82,
        y=base_capacity,
        label=f"Base Capacity — {base_capacity} MW",
        size=10,
        ha="center",
        color="#2C5F88",
        fill="#FFFFFF",
        alpha=0.85,
        fontweight="bold",
        label_padding=0.4,
    )
    + annotate(
        "label",
        x=hours_in_year * 0.82,
        y=intermediate_capacity,
        label=f"Intermediate Capacity — {intermediate_capacity} MW",
        size=10,
        ha="center",
        color="#5B8DB8",
        fill="#FFFFFF",
        alpha=0.85,
        fontweight="bold",
        label_padding=0.4,
    )
    # Region labels
    + annotate(
        "text",
        x=peak_hours * 0.45,
        y=intermediate_capacity + 100,
        label="Peak",
        size=15,
        ha="center",
        color="#9E3322",
        fontweight="bold",
        fontstyle="italic",
    )
    + annotate(
        "text",
        x=hours_in_year * 0.35,
        y=(base_capacity + intermediate_capacity) / 2,
        label="Intermediate",
        size=15,
        ha="center",
        color="#3D6D94",
        fontweight="bold",
        fontstyle="italic",
    )
    + annotate(
        "text",
        x=hours_in_year * 0.55,
        y=base_capacity * 0.45,
        label="Base Load",
        size=15,
        ha="center",
        color="#1A3D5C",
        fontweight="bold",
        fontstyle="italic",
    )
    # Total energy annotation with background box
    + annotate(
        "label",
        x=hours_in_year * 0.72,
        y=peak_load - 60,
        label=f"Total Energy: {total_energy_gwh:,.0f} GWh",
        size=12,
        ha="center",
        color="#1a1a1a",
        fill="#F0F4F8",
        alpha=0.9,
        fontweight="bold",
        label_padding=0.5,
    )
    # Scales with plotnine-specific fill mapping
    + scale_fill_manual(
        values=region_colors, guide=guide_legend(title="Load Region", override_aes={"alpha": 0.7}, nrow=1)
    )
    + scale_x_continuous(
        breaks=[0, 2000, 4000, 6000, 8000], labels=["0", "2,000", "4,000", "6,000", "8,000"], expand=(0.02, 0)
    )
    + scale_y_continuous(breaks=[0, 200, 400, 600, 800, 1000, 1200], expand=(0.02, 0))
    + coord_cartesian(ylim=(0, peak_load + 120))
    + labs(x="Hours", y="Load (MW)", title="line-load-duration · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#2D3436"),
        axis_title=element_text(size=20, weight="bold"),
        axis_text=element_text(size=16, color="#636E72"),
        plot_title=element_text(size=24, weight="bold", color="#0D1B2A"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(alpha=0.15, size=0.4, color="#B2BEC3"),
        panel_background=element_rect(fill="#FAFBFC", alpha=1),
        plot_background=element_rect(fill="#FFFFFF"),
        legend_position="bottom",
        legend_title=element_text(size=14, weight="bold"),
        legend_text=element_text(size=13),
        legend_background=element_rect(fill="#FAFBFC", color="#DFE6E9", size=0.5),
        legend_key_size=18,
        plot_margin=0.04,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
