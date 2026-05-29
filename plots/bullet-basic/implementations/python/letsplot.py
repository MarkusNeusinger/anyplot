"""anyplot.ai
bullet-basic: Basic Bullet Chart
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 89/100 | Updated: 2026-05-29
"""
# ruff: noqa: F405

import os
import shutil

import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — semantic exception: green = above/success, red = below/failure
ABOVE_COLOR = "#009E73"  # brand green
BELOW_COLOR = "#AE3030"  # matte red

# Grayscale band shades — adjusted per theme so bands are visible on both surfaces
if THEME == "light":
    BAND_GOOD = "#D0D0D0"
    BAND_SAT = "#989898"
    BAND_POOR = "#585858"
else:
    BAND_GOOD = "#3C3C38"
    BAND_SAT = "#565650"
    BAND_POOR = "#707068"

# Data — Q4 2024 KPI dashboard with varied performance levels
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

status = ["Above Target" if actual[i] >= target[i] else "Below Target" for i in range(n)]

# Y positions — reversed for top-to-bottom reading
y_spacing = 0.90
y_pos = [i * y_spacing for i in range(n - 1, -1, -1)]
bar_h = 0.38
narrow_h = 0.17
marker_h = 0.33

# Qualitative range bands (grayscale, Stephen Few convention)
range_rows = []
for i in range(n):
    y = y_pos[i]
    range_rows.append({"xmin": 0, "xmax": 100, "ymin": y - bar_h, "ymax": y + bar_h, "band": "Good"})
    range_rows.append({"xmin": 0, "xmax": sat_pct[i], "ymin": y - bar_h, "ymax": y + bar_h, "band": "Satisfactory"})
    range_rows.append({"xmin": 0, "xmax": poor_pct[i], "ymin": y - bar_h, "ymax": y + bar_h, "band": "Poor"})
df_ranges = pd.DataFrame(range_rows)

# Actual value bars with interactive tooltips
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

# Value annotations (actual units, beside each bar)
annot_labels = ["$275K", "88%", "3.8", "42"]
annot_rows = []
for i in range(n):
    annot_rows.append({"x": actual_pct[i] + 2, "y": float(y_pos[i]), "label": annot_labels[i], "status": status[i]})
df_annot = pd.DataFrame(annot_rows)

# Band legend note
df_band_note = pd.DataFrame(
    [{"x": 0, "y": -0.58, "label": "Bands:  Dark = Poor  ·  Medium = Satisfactory  ·  Light = Good"}]
)

# Build layered bullet chart
plot = (
    ggplot()
    # Qualitative range bands
    + geom_rect(data=df_ranges, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="band"), size=0)
    # Actual value bars
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
    # Target markers — thin vertical lines in INK color
    + geom_segment(data=df_target, mapping=aes(x="x", y="y", xend="xend", yend="yend"), size=2.5, color=INK)
    # Value annotations beside each bar
    + geom_text(
        data=df_annot,
        mapping=aes(x="x", y="y", label="label", color="status"),
        size=5,
        hjust=0,
        fontface="bold",
        show_legend=False,
    )
    # Band legend explanation
    + geom_text(data=df_band_note, mapping=aes(x="x", y="y", label="label"), size=4, hjust=0, color=INK_MUTED)
    # Fill scale — bands (grey) + status (Imprint palette)
    + scale_fill_manual(
        values={
            "Good": BAND_GOOD,
            "Satisfactory": BAND_SAT,
            "Poor": BAND_POOR,
            "Above Target": ABOVE_COLOR,
            "Below Target": BELOW_COLOR,
        },
        labels={"Above Target": "Above Target", "Below Target": "Below Target"},
        breaks=["Above Target", "Below Target"],
        name="Performance",
    )
    + scale_color_manual(values={"Above Target": ABOVE_COLOR, "Below Target": BELOW_COLOR}, guide="none")
    # Axes
    + scale_x_continuous(name="Performance (%)", limits=[0, 108], expand=[0, 1])
    + scale_y_continuous(breaks=y_pos, labels=metrics, limits=[-0.78, 3.25], expand=[0, 0])
    + labs(
        title="bullet-basic · python · letsplot · anyplot.ai",
        subtitle="Q4 2024 Dashboard — Actual vs. Target Performance",
        y="",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=16, face="bold", color=INK),
        plot_subtitle=element_text(size=11, color=INK_SOFT),
        axis_title_x=element_text(size=12, color=INK),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=10, color=INK_SOFT),
        axis_text_y=element_text(size=10, face="bold", color=INK_SOFT),
        legend_position="bottom",
        legend_direction="horizontal",
        legend_title=element_text(size=10, face="bold", color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(size=0.3, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
    + ggsize(800, 450)
)

# Save — theme-suffixed, scale=4 yields 3200×1800 px
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")

# Move from lets-plot-images subfolder if ggsave placed files there
for fname in [f"plot-{THEME}.png", f"plot-{THEME}.html"]:
    src = os.path.join("lets-plot-images", fname)
    if os.path.exists(src):
        shutil.move(src, fname)
if os.path.exists("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
