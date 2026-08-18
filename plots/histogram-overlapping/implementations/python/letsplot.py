""" anyplot.ai
histogram-overlapping: Overlapping Histograms
Library: letsplot 4.11.0 | Python 3.13.15
Quality: 84/100 | Updated: 2026-08-18
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
    geom_histogram,
    geom_text,
    geom_vline,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    theme,
)


LetsPlot.setup_html()

# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette (first series always #009E73)
COLORS = ["#009E73", "#C475FD"]

# Data - comparing response times between two experimental conditions
np.random.seed(42)

# Control group - baseline response times (ms)
control = np.random.normal(loc=450, scale=80, size=200)

# Treatment group - faster response times with intervention
treatment = np.random.normal(loc=380, scale=70, size=200)

# Create DataFrame
df = pd.DataFrame(
    {"response_time": np.concatenate([control, treatment]), "group": ["Control"] * 200 + ["Treatment"] * 200}
)

mean_control = control.mean()
mean_treatment = treatment.mean()

# Explicit bin width + shared boundary so both distributions align on identical edges
bin_width = 20
bin_start = np.floor(df["response_time"].min() / bin_width) * bin_width
edges = np.arange(bin_start, df["response_time"].max() + bin_width, bin_width)
peak_count = max(np.histogram(control, bins=edges)[0].max(), np.histogram(treatment, bins=edges)[0].max())

# Mean-line callouts, anchored just above the tallest bar for a clear focal point
annotations = pd.DataFrame(
    {
        "x": [mean_control, mean_treatment],
        "y": [peak_count * 1.12] * 2,
        "label": [f"Control  {mean_control:.0f} ms", f"Treatment  {mean_treatment:.0f} ms"],
    }
)

# Distinctive lets-plot touch: custom tooltip content for the interactive HTML export
bar_tooltips = layer_tooltips().line("@group").line("Response time|^x ms").line("Count|^y")

# Theme-adaptive styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=RULE, size=0.3),
    panel_grid_minor_y=element_blank(),
    panel_grid_major_x=element_blank(),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.3),
    plot_title=element_text(size=16, color=INK),
    plot_subtitle=element_text(size=11, color=INK_SOFT),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_title=element_text(size=11, color=INK),
    legend_position="top",
)

# Overlapping histograms with aligned bins, mean reference lines, and mean-value callouts
plot = (
    ggplot(df, aes(x="response_time", fill="group"))
    + geom_histogram(
        alpha=0.55,
        binwidth=bin_width,
        boundary=bin_start,
        position="identity",
        color=PAGE_BG,
        size=0.3,
        tooltips=bar_tooltips,
    )
    + geom_vline(xintercept=mean_control, color=COLORS[0], linetype="dashed", size=1.1, alpha=0.9)
    + geom_vline(xintercept=mean_treatment, color=COLORS[1], linetype="dashed", size=1.1, alpha=0.9)
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=annotations.iloc[[0]],
        color=COLORS[0],
        size=3.2,
        hjust=0,
        nudge_x=8,
        fontface="bold",
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=annotations.iloc[[1]],
        color=COLORS[1],
        size=3.2,
        hjust=1,
        nudge_x=-8,
        fontface="bold",
    )
    + scale_fill_manual(values=COLORS)
    + labs(
        x="Response Time (ms)",
        y="Count",
        title="histogram-overlapping · letsplot · anyplot.ai",
        subtitle=f"Intervention shifts the mean left by {mean_control - mean_treatment:.0f} ms",
        fill="Condition",
    )
    + ggsize(800, 450)
    + anyplot_theme
)

# Save as PNG (scale 4x to get 3200 × 1800 px)
ggsave(plot, filename=f"plot-{THEME}.png", scale=4)

# Save as HTML for interactivity
ggsave(plot, filename=f"plot-{THEME}.html")

# Move files from lets-plot-images subdirectory to current directory
if os.path.exists("lets-plot-images"):
    for file in os.listdir("lets-plot-images"):
        src = os.path.join("lets-plot-images", file)
        if os.path.isfile(src):
            shutil.move(src, file)
    shutil.rmtree("lets-plot-images")
