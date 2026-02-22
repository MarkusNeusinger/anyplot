""" pyplots.ai
bullet-basic: Basic Bullet Chart
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 89/100 | Updated: 2026-02-22
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

# Above/below target for color differentiation
status = ["Above Target" if actual[i] >= target[i] else "Below Target" for i in range(n)]

# Y positions (reversed for top-to-bottom reading, compact spacing)
y_spacing = 0.90
y_pos = [i * y_spacing for i in range(n - 1, -1, -1)]
bar_h = 0.38
narrow_h = 0.17
marker_h = 0.33

# Qualitative range bands (grayscale per Stephen Few convention)
range_rows = []
for i in range(n):
    y = y_pos[i]
    range_rows.append({"xmin": 0, "xmax": 100, "ymin": y - bar_h, "ymax": y + bar_h, "band": "Good"})
    range_rows.append({"xmin": 0, "xmax": sat_pct[i], "ymin": y - bar_h, "ymax": y + bar_h, "band": "Satisfactory"})
    range_rows.append({"xmin": 0, "xmax": poor_pct[i], "ymin": y - bar_h, "ymax": y + bar_h, "band": "Poor"})
df_ranges = pd.DataFrame(range_rows)

# Actual value bars with metadata for interactive tooltips
actual_rows = []
for i in range(n):
    y = y_pos[i]
    actual_rows.append(
        {
            "xmin": 0,
            "xmax": actual_pct[i],
            "ymin": y - narrow_h,
            "ymax": y + narrow_h,
            "status": status[i],
            "metric": metrics[i],
            "actual_val": f"{actual[i]:g}",
            "target_val": f"{target[i]:g}",
            "achievement": f"{actual[i] / target[i] * 100:.0f}%",
        }
    )
df_actual = pd.DataFrame(actual_rows)

# Target markers
target_rows = []
for i in range(n):
    y = y_pos[i]
    target_rows.append({"x": target_pct[i], "y": y - marker_h, "xend": target_pct[i], "yend": y + marker_h})
df_target = pd.DataFrame(target_rows)

# Value annotations for precise reading (in original units)
annot_labels = ["$275K", "88%", "3.8", "42"]
annot_rows = []
for i in range(n):
    annot_rows.append({"x": actual_pct[i] + 2, "y": float(y_pos[i]), "label": annot_labels[i], "status": status[i]})
df_annot = pd.DataFrame(annot_rows)

# Band legend annotation (compact text explaining grayscale ranges)
df_band_note = pd.DataFrame(
    [{"x": 0, "y": -0.55, "label": "Bands:  Dark = Poor  ·  Medium = Satisfactory  ·  Light = Good"}]
)

# Build layered bullet chart
plot = (
    ggplot()
    # Qualitative range bands
    + geom_rect(data=df_ranges, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="band"), size=0)
    # Actual value bars — color-coded by target achievement with letsplot tooltips
    + geom_rect(
        data=df_actual,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="status"),
        size=0,
        tooltips=(
            layer_tooltips()
            .line("@{metric}")
            .line("Actual|@{actual_val}")
            .line("Target|@{target_val}")
            .line("Achievement|@{achievement}")
        ),
    )
    # Target markers (prominent vertical lines)
    + geom_segment(data=df_target, mapping=aes(x="x", y="y", xend="xend", yend="yend"), size=2.5, color="#1a1a1a")
    # Value annotations beside each bar — color-coded by target achievement
    + geom_text(
        data=df_annot,
        mapping=aes(x="x", y="y", label="label", color="status"),
        size=12,
        hjust=0,
        fontface="bold",
        show_legend=False,
    )
    # Band legend (text note explaining grayscale qualitative ranges)
    + geom_text(data=df_band_note, mapping=aes(x="x", y="y", label="label"), size=10, hjust=0, color="#666666")
    # Color scales
    + scale_fill_manual(
        values={
            "Good": "#C8C8C8",
            "Satisfactory": "#969696",
            "Poor": "#525252",
            "Above Target": "#2D6A4F",
            "Below Target": "#C0785A",
        },
        labels={"Above Target": "Above Target", "Below Target": "Below Target"},
        breaks=["Above Target", "Below Target"],
        name="Performance",
    )
    # Color scale for annotations (matches fill colors, no separate legend)
    + scale_color_manual(values={"Above Target": "#2D6A4F", "Below Target": "#C0785A"}, guide="none")
    # Axes
    + scale_x_continuous(name="Performance (%)", limits=[0, 105], expand=[0, 1])
    + scale_y_continuous(breaks=y_pos, labels=metrics, limits=[-0.75, 3.25], expand=[0, 0])
    + labs(
        title="bullet-basic · letsplot · pyplots.ai", subtitle="Q4 2024 Dashboard — Actual vs. Target Performance", y=""
    )
    # Theme — refined styling with subtle background
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_subtitle=element_text(size=16, color="#555555"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=18, face="bold"),
        legend_position="bottom",
        legend_direction="horizontal",
        legend_title=element_text(size=14, face="bold"),
        legend_text=element_text(size=14),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(size=0.3, color="#E0E0E0"),
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")

# Move files from lets-plot-images subfolder
if os.path.exists("lets-plot-images/plot.png"):
    shutil.move("lets-plot-images/plot.png", "plot.png")
if os.path.exists("lets-plot-images/plot.html"):
    shutil.move("lets-plot-images/plot.html", "plot.html")
if os.path.exists("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
