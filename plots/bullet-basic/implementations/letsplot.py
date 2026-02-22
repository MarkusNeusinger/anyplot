"""pyplots.ai
bullet-basic: Basic Bullet Chart
Library: letsplot 4.8.2 | Python 3.14.3
Quality: /100 | Updated: 2026-02-22
"""
# ruff: noqa: F405

import os
import shutil

import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Data - KPI dashboard with varied performance levels
metrics = ["Revenue ($K)", "Profit Margin (%)", "Satisfaction", "New Customers"]
actual = [275, 88, 3.8, 42]
target = [300, 85, 4.5, 40]
poor = [100, 40, 2.5, 15]
satisfactory = [200, 70, 3.5, 30]
good = [350, 100, 5.0, 50]

n = len(metrics)

# Normalize to percentage of maximum range
actual_pct = [actual[i] / good[i] * 100 for i in range(n)]
target_pct = [target[i] / good[i] * 100 for i in range(n)]
poor_pct = [poor[i] / good[i] * 100 for i in range(n)]
sat_pct = [satisfactory[i] / good[i] * 100 for i in range(n)]

# Reversed y positions (top to bottom)
y_pos = list(range(n - 1, -1, -1))
bar_h = 0.35
narrow_h = 0.14
marker_h = 0.28

# Build all rects into one DataFrame with a layer column for ordering
rows = []
for i in range(n):
    y = y_pos[i]
    # Good range (lightest, full width background)
    rows.append({"xmin": 0.0, "xmax": 100.0, "ymin": y - bar_h, "ymax": y + bar_h, "layer": "1_good"})
    # Satisfactory range
    rows.append({"xmin": 0.0, "xmax": sat_pct[i], "ymin": y - bar_h, "ymax": y + bar_h, "layer": "2_sat"})
    # Poor range (darkest)
    rows.append({"xmin": 0.0, "xmax": poor_pct[i], "ymin": y - bar_h, "ymax": y + bar_h, "layer": "3_poor"})
    # Actual value (narrow)
    rows.append({"xmin": 0.0, "xmax": actual_pct[i], "ymin": y - narrow_h, "ymax": y + narrow_h, "layer": "4_actual"})
    # Target marker (thin vertical)
    rows.append(
        {
            "xmin": target_pct[i] - 0.3,
            "xmax": target_pct[i] + 0.3,
            "ymin": y - marker_h,
            "ymax": y + marker_h,
            "layer": "5_target",
        }
    )

df = pd.DataFrame(rows)

# Plot using fill mapped to layer, drawn in layer order
plot = (
    ggplot(df, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="layer"))
    + geom_rect()
    + scale_fill_manual(
        values={
            "1_good": "#CCCCCC",
            "2_sat": "#999999",
            "3_poor": "#555555",
            "4_actual": "#306998",
            "5_target": "#1a1a1a",
        }
    )
    + scale_x_continuous(name="Performance (%)", limits=[0, 105])
    + scale_y_continuous(breaks=y_pos, labels=metrics, limits=[-0.7, n - 0.3])
    + labs(title="bullet-basic · letsplot · pyplots.ai", y="")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title_x=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=18),
        legend_position="none",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(size=0.3, color="#E0E0E0"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")

# Move files from lets-plot-images subfolder to current directory
if os.path.exists("lets-plot-images/plot.png"):
    shutil.move("lets-plot-images/plot.png", "plot.png")
if os.path.exists("lets-plot-images/plot.html"):
    shutil.move("lets-plot-images/plot.html", "plot.html")
if os.path.exists("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
