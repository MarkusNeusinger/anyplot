""" pyplots.ai
bullet-basic: Basic Bullet Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-22
"""

import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_segment,
    geom_text,
    geom_tile,
    ggplot,
    guides,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Multiple KPIs with different performance levels
metrics = [
    {"label": "Revenue ($K)", "actual": 275, "target": 250, "ranges": [150, 225, 300]},
    {"label": "Profit (%)", "actual": 22, "target": 26, "ranges": [15, 22.5, 30]},
    {"label": "New Orders", "actual": 1050, "target": 1100, "ranges": [600, 900, 1200]},
    {"label": "Satisfaction", "actual": 4.5, "target": 4.2, "ranges": [2.5, 3.5, 5.0]},
]

# Build data - normalize all values to 0-100 scale for consistent display
tile_data = []
actual_data = []
target_data = []

for i, m in enumerate(metrics):
    y_pos = len(metrics) - 1 - i  # Reverse order so first metric is at top
    max_val = m["ranges"][-1]

    # Qualitative range bands: compute center + width for geom_tile
    band_bounds = [0, (m["ranges"][0] / max_val) * 100, (m["ranges"][1] / max_val) * 100, 100]
    band_names = ["Poor", "Satisfactory", "Good"]
    for j, band in enumerate(band_names):
        x_center = (band_bounds[j] + band_bounds[j + 1]) / 2
        width = band_bounds[j + 1] - band_bounds[j]
        tile_data.append({"y": y_pos, "x": x_center, "width": width, "band": band})

    # Actual value bar
    actual_pct = (m["actual"] / max_val) * 100
    val = m["actual"]
    val_str = str(int(val)) if val == int(val) else str(val)
    actual_data.append({"y": y_pos, "xmin": 0, "xmax": actual_pct, "label": m["label"], "actual": val_str})

    # Target marker
    target_pct = (m["target"] / max_val) * 100
    target_data.append({"y": y_pos, "target": target_pct})

df_tiles = pd.DataFrame(tile_data)
df_actual = pd.DataFrame(actual_data)
df_target = pd.DataFrame(target_data)

# Intentional grayscale gradient (darker = worse performance zone)
band_colors = {"Poor": "#686868", "Satisfactory": "#9E9E9E", "Good": "#D2D2D2"}

# Band label positions centered in each zone of the bottom metric
sat = metrics[-1]
sat_max = sat["ranges"][-1]
poor_mid = (sat["ranges"][0] / sat_max) * 50
satis_mid = ((sat["ranges"][0] + sat["ranges"][1]) / (2 * sat_max)) * 100
good_mid = ((sat["ranges"][1] + sat_max) / (2 * sat_max)) * 100

# Bar dimensions
range_height = 0.68
actual_height = 0.28

# Plot - horizontal bullet charts using grammar of graphics layering
plot = (
    ggplot()
    # Qualitative range bands via geom_tile (center-based GoG geometry)
    + geom_tile(df_tiles, aes(x="x", y="y", width="width", fill="band"), height=range_height, color="none")
    + scale_fill_manual(values=band_colors, limits=["Good", "Satisfactory", "Poor"])
    + guides(fill=False)
    # Actual value bar with subtle edge for depth
    + geom_rect(
        df_actual,
        aes(xmin="xmin", xmax="xmax", ymin="y - actual_height/2", ymax="y + actual_height/2"),
        fill="#306998",
        color="#24537a",
        size=0.3,
    )
    # Target marker (thin contrasting line perpendicular to the bar)
    + geom_segment(
        df_target,
        aes(x="target", xend="target", y="y - range_height/2.2", yend="y + range_height/2.2"),
        color="#1a1a1a",
        size=2.5,
    )
    # Actual value labels above each bar
    + geom_text(
        df_actual,
        aes(x="xmax", y="y + range_height/2 + 0.04", label="actual"),
        ha="right",
        va="bottom",
        size=10,
        color="#306998",
        fontweight="bold",
    )
    # Band labels via annotate layers (plotnine annotation system)
    + annotate("text", x=poor_mid, y=-0.5, label="Poor", size=8, color="#555555", va="top")
    + annotate("text", x=satis_mid, y=-0.5, label="Satisfactory", size=8, color="#555555", va="top")
    + annotate("text", x=good_mid, y=-0.5, label="Good", size=8, color="#555555", va="top")
    # Scales
    + scale_x_continuous(limits=(0, 100), breaks=[0, 25, 50, 75, 100], expand=(0, 0.02))
    + scale_y_continuous(
        breaks=list(range(len(metrics))), labels=[m["label"] for m in reversed(metrics)], expand=(0.15, 0.08)
    )
    + labs(title="bullet-basic · plotnine · pyplots.ai", x="Performance (%)", y="")
    # Theme - refined styling with plotnine theming system
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=18, ha="right"),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#e0e0e0", size=0.3),
        plot_background=element_rect(fill="white", color="none"),
        panel_background=element_rect(fill="#fafafa", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
