""" anyplot.ai
bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 87/100 | Created: 2026-06-14
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_x_discrete,
    scale_y_continuous,
    theme,
    theme_classic,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Zone colors — semantic exception: conventional fitness platform zone palette
# mapped to nearest Imprint palette members (Z1→muted grey, Z2→blue, Z3→green, Z4→ochre, Z5→red)
ZONE_COLORS = [INK_MUTED, "#4467A3", "#009E73", "#BD8233", "#AE3030"]

# Data — 60-minute tempo run session
zones = ["Z1", "Z2", "Z3", "Z4", "Z5"]
minutes = [8, 22, 15, 12, 3]
zone_names = ["Recovery", "Endurance", "Aerobic", "Threshold", "Maximum"]
hr_ranges = ["< 114 bpm", "114–133 bpm", "134–151 bpm", "152–171 bpm", "> 171 bpm"]
total = sum(minutes)  # 60

df = pd.DataFrame(
    {
        "zone": zones,
        "minutes": [float(m) for m in minutes],
        "zone_name": zone_names,
        "hr_range": hr_ranges,
        "duration_label": [f"{m} min" for m in minutes],
        "pct_label": [f"{round(m / total * 100)}%" for m in minutes],
        "bar_label": [f"{m} min  ·  {round(m / total * 100)}%" for m in minutes],
    }
)
df["zone"] = pd.Categorical(df["zone"], categories=zones, ordered=True)

# X-axis labels: zone code, zone name, and HR boundary
zone_axis_labels = {
    "Z1": "Z1  Recovery\n< 114 bpm",
    "Z2": "Z2  Endurance\n114–133 bpm",
    "Z3": "Z3  Aerobic\n134–151 bpm",
    "Z4": "Z4  Threshold\n152–171 bpm",
    "Z5": "Z5  Maximum\n> 171 bpm",
}

title = "bar-heart-rate-zones · python · letsplot · anyplot.ai"
n_chars = len(title)
title_size = round(16 * 67 / n_chars) if n_chars > 67 else 16

# lets-plot distinctive feature: formatted interactive tooltip specification
tooltips = (
    layer_tooltips()
    .title("@zone_name")
    .line("Duration|@duration_label")
    .line("Share|@pct_label")
    .line("Heart rate|@hr_range")
)

plot = (
    ggplot(df, aes(x="zone", y="minutes", fill="zone"))
    + geom_bar(stat="identity", width=0.6, color=INK_SOFT, size=0.3, tooltips=tooltips)
    + geom_text(aes(label="bar_label"), vjust=-0.5, size=4, color=INK)
    + scale_fill_manual(values=ZONE_COLORS, name="")
    + scale_x_discrete(labels=zone_axis_labels)
    + scale_y_continuous(limits=[0, 27])
    + labs(x="", y="Time (minutes)", title=title, subtitle="60-minute tempo run  ·  training intensity distribution")
    + ggsize(800, 450)
    + theme_classic()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=RULE, size=0.5),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title_y=element_text(color=INK, size=12),
        axis_title_x=element_blank(),
        axis_text=element_text(color=INK_SOFT, size=10),
        axis_line=element_line(color=INK_SOFT),
        axis_ticks=element_line(color=INK_SOFT),
        plot_title=element_text(color=INK, size=title_size),
        plot_subtitle=element_text(color=INK_SOFT, size=10),
        legend_position="none",
    )
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
