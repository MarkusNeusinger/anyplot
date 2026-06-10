""" anyplot.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-10
"""

import os
import shutil

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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — semantic exception applies for load regions:
# base load (reliable/always-on) → green, intermediate → ochre, peak (costly/intensive) → matte red
COLOR_BASE = "#009E73"  # Imprint position 1 — reliable, continuous generation
COLOR_INTER = "#BD8233"  # Imprint position 4 — variable middle-tier generation
COLOR_PEAK = "#AE3030"  # Imprint position 5 — semantic red for high-cost peak demand

# Data: Synthetic annual hourly load profile for a mid-sized utility
np.random.seed(42)
hours = np.arange(8760)
hour_of_day = hours % 24
day_of_year = hours // 24

base_load = 400
seasonal_component = 450 * np.sin(2 * np.pi * (day_of_year - 30) / 365) ** 2
daily_pattern = 250 * np.sin(np.pi * (hour_of_day - 6) / 16) ** 2
daily_pattern[hour_of_day < 6] = 0
noise = np.random.normal(0, 40, 8760)

hourly_load = base_load + seasonal_component + daily_pattern + noise
hourly_load = np.clip(hourly_load, 350, 1250)

# Sort descending to create the load duration curve
load_sorted = np.sort(hourly_load)[::-1]
rank_hours = np.arange(8760)

peak_threshold = 900
intermediate_threshold = 550

total_energy_gwh = np.sum(load_sorted) / 1000

# Non-overlapping ribbon regions
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
df_line = pd.DataFrame({"hour": rank_hours, "load_mw": load_sorted})

peak_hours_count = int(np.sum(load_sorted > peak_threshold))
intermediate_hours_count = int(np.sum(load_sorted > intermediate_threshold))
load_factor = np.mean(load_sorted) / np.max(load_sorted) * 100

# Region label positions (center of each shaded band)
df_labels = pd.DataFrame(
    {
        "hour": [
            peak_hours_count / 2,
            (peak_hours_count + intermediate_hours_count) / 2,
            (intermediate_hours_count + 8760) / 2,
        ],
        "load_mw": [
            (np.max(load_sorted) + peak_threshold) / 2,
            (peak_threshold + intermediate_threshold) / 2,
            intermediate_threshold / 2 + 20,
        ],
        "label": ["Peak\nLoad", "Intermediate\nLoad", "Base\nLoad"],
    }
)

# Energy summary annotation in upper-right empty space
df_energy = pd.DataFrame(
    {
        "hour": [5800],
        "load_mw": [1170],
        "label": [f"Total energy: {total_energy_gwh:,.0f} GWh/yr\nLoad factor: {load_factor:.0f}%"],
    }
)

# Capacity threshold labels
df_peak_cap = pd.DataFrame(
    {"hour": [6200], "load_mw": [peak_threshold + 38], "label": [f"Peak capacity: {peak_threshold} MW"]}
)
df_inter_cap = pd.DataFrame(
    {
        "hour": [6200],
        "load_mw": [intermediate_threshold + 38],
        "label": [f"Intermediate capacity: {intermediate_threshold} MW"],
    }
)

REGION_COLORS = {"Peak Load": COLOR_PEAK, "Intermediate Load": COLOR_INTER, "Base Load": COLOR_BASE}

title = "line-load-duration · python · letsplot · anyplot.ai"
n = len(title)
title_fontsize = round(16 * 67 / n) if n > 67 else 16

plot = (
    ggplot()
    + geom_ribbon(
        data=df_base,
        mapping=aes(x="hour", ymin="ymin", ymax="ymax", fill="region"),
        alpha=0.72,
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
        alpha=0.72,
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
        alpha=0.72,
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
        color=INK,
        size=1.0,
        tooltips=layer_tooltips()
        .format("@load_mw", ".0f")
        .format("@hour", ",d")
        .line("Hour: @hour")
        .line("Demand: @load_mw MW"),
    )
    + geom_hline(yintercept=peak_threshold, linetype="dashed", color=COLOR_PEAK, size=0.8)
    + geom_hline(yintercept=intermediate_threshold, linetype="dashed", color=COLOR_INTER, size=0.8)
    + geom_text(data=df_labels, mapping=aes(x="hour", y="load_mw", label="label"), size=4, color=INK, fontface="bold")
    + geom_text(
        data=df_energy, mapping=aes(x="hour", y="load_mw", label="label"), size=3.5, color=INK_MUTED, fontface="italic"
    )
    + geom_text(
        data=df_peak_cap, mapping=aes(x="hour", y="load_mw", label="label"), size=3.5, color=COLOR_PEAK, fontface="bold"
    )
    + geom_text(
        data=df_inter_cap,
        mapping=aes(x="hour", y="load_mw", label="label"),
        size=3.5,
        color=COLOR_INTER,
        fontface="bold",
    )
    + scale_fill_manual(values=REGION_COLORS)
    + scale_x_continuous(
        name="Hours of Year (Ranked by Demand)",
        breaks=[0, 2000, 4000, 6000, 8000],
        labels=["0", "2,000", "4,000", "6,000", "8,000"],
    )
    + scale_y_continuous(name="Power Demand (MW)", breaks=[0, 200, 400, 600, 800, 1000, 1200])
    + labs(
        title=title,
        subtitle=f"Mid-sized utility · Peak {np.max(load_sorted):.0f} MW · {peak_hours_count:,} hours above peak threshold",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=title_fontsize, face="bold", color=INK),
        plot_subtitle=element_text(size=10, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.15),
        legend_position="none",
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT),
    )
    + ggsize(800, 450)
)

# Save PNG and HTML for both themes
# ggsave writes into lets-plot-images/ by default; move to the working directory
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")
for _ext in ("png", "html"):
    _src = os.path.join("lets-plot-images", f"plot-{THEME}.{_ext}")
    if os.path.exists(_src):
        shutil.move(_src, f"plot-{THEME}.{_ext}")
