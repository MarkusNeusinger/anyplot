""" anyplot.ai
funnel-basic: Basic Funnel Chart
Library: letsplot 4.9.0 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-26
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_identity,
    scale_fill_manual,
    scale_y_reverse,
    theme,
    theme_void,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Okabe-Ito palette — first stage is brand green (#009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]
# Light orange (#AE3030) needs dark text for contrast; others use white.
TEXT_ON_FILL = ["white", "white", "white", "white", INK]

# Data — sales funnel example from specification
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]
n_stages = len(stages)
max_value = values[0]

# Build trapezoid polygon vertices for each stage
gap = 0.06
polygons = []
labels = []
for i, (stage, value) in enumerate(zip(stages, values, strict=True)):
    w_top = value / max_value
    w_bot = (values[i + 1] / max_value) if i + 1 < n_stages else w_top
    y_top = i + gap / 2
    y_bot = (i + 1) - gap / 2
    polygons.extend(
        [
            {"stage": stage, "x": -w_top / 2, "y": y_top, "order": 0},
            {"stage": stage, "x": w_top / 2, "y": y_top, "order": 1},
            {"stage": stage, "x": w_bot / 2, "y": y_bot, "order": 2},
            {"stage": stage, "x": -w_bot / 2, "y": y_bot, "order": 3},
        ]
    )
    pct = value / max_value * 100
    labels.append(
        {
            "stage": stage,
            "x": 0,
            "y": (y_top + y_bot) / 2,
            "label": f"{stage}\n{value:,}  ·  {pct:.0f}%",
            "text_color": TEXT_ON_FILL[i],
        }
    )

df_poly = pd.DataFrame(polygons)
df_poly["stage"] = pd.Categorical(df_poly["stage"], categories=stages, ordered=True)
df_labels = pd.DataFrame(labels)

# Plot
plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", fill="stage", group="stage"), data=df_poly, color=PAGE_BG, size=2)
    + geom_text(aes(x="x", y="y", label="label", color="text_color"), data=df_labels, size=12, fontface="bold")
    + scale_fill_manual(values=IMPRINT[:n_stages], guide="none")
    + scale_color_identity()
    + scale_y_reverse()
    + labs(title="funnel-basic · letsplot · anyplot.ai", x="", y="")
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=24, color=INK, face="bold", hjust=0.5),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_position="none",
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
