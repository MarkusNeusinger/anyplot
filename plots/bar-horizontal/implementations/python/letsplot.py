""" anyplot.ai
bar-horizontal: Horizontal Bar Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-07
"""

import os

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - Programming language popularity survey results (sorted by value)
data = pd.DataFrame(
    {
        "language": ["JavaScript", "Python", "Java", "TypeScript", "C#", "C++", "PHP", "C", "Go", "Rust"],
        "developers": [65.36, 49.28, 35.35, 34.83, 29.81, 22.55, 20.87, 19.34, 13.24, 11.76],
    }
)

# Sort by value for better comparison (largest to smallest)
data = data.sort_values("developers", ascending=True)
data["language"] = pd.Categorical(data["language"], categories=data["language"].tolist(), ordered=True)

# Create horizontal bar chart
plot = (
    ggplot(data, aes(x="developers", y="language"))
    + geom_bar(stat="identity", fill="#009E73", width=0.65, alpha=0.85)
    + labs(x="Developers (%)", y="Programming Language", title="bar-horizontal · letsplot · anyplot.ai")
    + ggsize(1600, 900)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_x=element_line(color=RULE, size=0.3),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title_x=element_text(size=20, color=INK),
        axis_title_y=element_text(size=20, color=INK),
        axis_text_x=element_text(size=16, color=INK_SOFT),
        axis_text_y=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
    )
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, f"plot-{THEME}.html", path=".")
