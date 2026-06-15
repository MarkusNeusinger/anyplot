""" anyplot.ai
climograph-walter-lieth: Walter-Lieth Climate Diagram
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 83/100 | Created: 2026-06-15
"""

import os

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
    geom_point,
    geom_ribbon,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — semantic mapping: temperature=red, precipitation=blue
TEMP_COLOR = "#AE3030"  # matte red (pos 5) — heat/temperature semantic
PRECIP_COLOR = "#4467A3"  # blue (pos 3) — water/precipitation semantic

# Athens, Greece — classic Mediterranean climate, 1991-2020 normals
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
month_num = np.arange(1, 13)
temp_c = np.array([9.3, 10.2, 12.5, 16.4, 21.4, 26.1, 29.0, 28.8, 24.4, 19.3, 14.4, 10.7])
precip_mm = np.array([57, 37, 37, 23, 15, 7, 6, 7, 15, 51, 56, 71])

# Walter-Lieth 1:2 convention: 20 mm precipitation ↔ 10°C (precip_scaled = precip / 2)
precip_scaled = precip_mm / 2.0

# Fill regions — zero-height ribbons are invisible, so no masking needed
humid_top = np.maximum(temp_c, precip_scaled)  # = precip_scaled where humid, else = temp_c
arid_bottom = np.minimum(temp_c, precip_scaled)  # = precip_scaled where arid, else = temp_c

df = pd.DataFrame(
    {
        "month": month_num,
        "temp": temp_c,
        "precip_scaled": precip_scaled,
        "humid_top": humid_top,
        "arid_bottom": arid_bottom,
    }
)

# Long-format data for legend-mapped lines and points
df_lines = pd.concat(
    [
        pd.DataFrame({"month": month_num, "y": temp_c, "series": "Temperature"}),
        pd.DataFrame({"month": month_num, "y": precip_scaled, "series": "Precipitation"}),
    ],
    ignore_index=True,
)

# Manual right y-axis (precipitation scale) — sec_axis not available in lets-plot 4.x
x_rax = 12.55  # right axis vertical line
x_rtick = 12.72  # tick mark end and label start
right_y = [0, 10, 20, 30, 40]
right_labels = ["0", "20", "40", "60", "80"]  # mm values (= 2 × temp-scale positions)

df_rax_line = pd.DataFrame({"x": [x_rax], "xend": [x_rax], "y": [-4], "yend": [41]})
df_rtick_marks = pd.DataFrame({"x": [x_rax] * 5, "xend": [x_rax + 0.13] * 5, "y": right_y, "yend": right_y})
df_rtick_labels = pd.DataFrame({"x": [x_rtick] * 5, "y": right_y, "label": right_labels})
df_rax_title = pd.DataFrame({"x": [14.2], "y": [20.0], "label": ["Precipitation (mm)"]})

# Title fontsize: scaled for long title string
title_text = "Athens, Greece · climograph-walter-lieth · python · letsplot · anyplot.ai"
title_fs = max(11, round(16 * 67 / len(title_text)))

subtitle_text = "107 m a.s.l. │ Tmean = 18.5°C │ P = 383 mm yr⁻¹ │  1991–2020 normals"

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.2),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=title_fs),
    plot_subtitle=element_text(color=INK_SOFT, size=9),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=PAGE_BG, size=1),
    legend_position="bottom",
)

plot = (
    ggplot(df, aes(x="month"))
    # Humid fill (blue): precipitation curve above temperature curve (Jan-Mar, Oct-Dec)
    + geom_ribbon(aes(ymin="temp", ymax="humid_top"), fill=PRECIP_COLOR, alpha=0.28)
    # Arid fill (red): temperature curve above precipitation curve (Apr-Sep)
    + geom_ribbon(aes(ymin="arid_bottom", ymax="temp"), fill=TEMP_COLOR, alpha=0.28)
    # Freezing-point reference
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.5, linetype="dashed")
    # Temperature and precipitation curves (mapped color → legend)
    + geom_line(data=df_lines, mapping=aes(x="month", y="y", color="series"), size=1.2)
    + geom_point(data=df_lines, mapping=aes(x="month", y="y", color="series"), size=2.2)
    + scale_color_manual(values={"Temperature": TEMP_COLOR, "Precipitation": PRECIP_COLOR}, name=" ")
    # X-axis: month labels; extended range accommodates manual right axis
    + scale_x_continuous(breaks=list(range(1, 13)), labels=month_labels, limits=(0.4, 15.5))
    # Left y-axis: temperature (°C)
    + scale_y_continuous(name="Temperature (°C)", breaks=right_y, limits=(-5, 42))
    # Manual right y-axis — precipitation (mm), color-coded blue
    + geom_segment(data=df_rax_line, mapping=aes(x="x", xend="xend", y="y", yend="yend"), color=INK_SOFT, size=0.4)
    + geom_segment(data=df_rtick_marks, mapping=aes(x="x", xend="xend", y="y", yend="yend"), color=INK_SOFT, size=0.4)
    + geom_text(data=df_rtick_labels, mapping=aes(x="x", y="y", label="label"), color=PRECIP_COLOR, size=3.0, hjust=0)
    + geom_text(
        data=df_rax_title, mapping=aes(x="x", y="y", label="label"), color=PRECIP_COLOR, size=3.5, angle=270, hjust=0.5
    )
    + labs(x="", title=title_text, subtitle=subtitle_text)
    + anyplot_theme
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
