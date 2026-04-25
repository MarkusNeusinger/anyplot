""" anyplot.ai
errorbar-basic: Basic Error Bar Plot
Library: plotnine 0.15.3 | Python 3.14.4
Quality: 85/100 | Updated: 2026-04-25
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_errorbar,
    geom_point,
    ggplot,
    labs,
    position_dodge,
    scale_color_manual,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]

# Data — three lab methods measured across six samples
data = pd.DataFrame(
    {
        "sample": [
            "Sample A",
            "Sample B",
            "Sample C",
            "Sample D",
            "Sample E",
            "Sample F",
            "Sample A",
            "Sample B",
            "Sample C",
            "Sample D",
            "Sample E",
            "Sample F",
            "Sample A",
            "Sample B",
            "Sample C",
            "Sample D",
            "Sample E",
            "Sample F",
        ],
        "method": (["Method A"] * 6 + ["Method B"] * 6 + ["Method C"] * 6),
        "measurement": [
            42.5,
            38.2,
            55.1,
            47.8,
            33.6,
            51.3,
            44.8,
            40.1,
            53.6,
            49.2,
            35.9,
            52.7,
            41.2,
            39.5,
            56.3,
            46.4,
            34.8,
            50.1,
        ],
        "error": [3.2, 4.1, 2.8, 5.5, 3.8, 4.2, 2.6, 3.4, 3.1, 4.2, 3.0, 3.6, 3.9, 4.5, 2.5, 5.1, 4.3, 4.0],
    }
)

data["ymin"] = data["measurement"] - data["error"]
data["ymax"] = data["measurement"] + data["error"]

# Order samples by mean measurement to create visual hierarchy
sample_order = data.groupby("sample")["measurement"].mean().sort_values().index.tolist()
data["sample"] = pd.Categorical(data["sample"], categories=sample_order, ordered=True)

dodge = position_dodge(width=0.55)

plot = (
    ggplot(data, aes(x="sample", y="measurement", color="method", group="method"))
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.35, size=1.4, position=dodge)
    + geom_point(size=5, position=dodge)
    + scale_color_manual(values=OKABE_ITO, name="Method")
    + labs(x="Experimental Sample", y="Measurement Value (mg/L)", title="errorbar-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.10),
        axis_line_x=element_line(color=INK_SOFT, size=0.6),
        axis_line_y=element_blank(),
        axis_ticks=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK, weight="bold"),
        legend_background=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_key=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
        legend_position="right",
    )
)

plot.save(f"plot-{THEME}.png", dpi=300, width=16, height=9, verbose=False)
