""" anyplot.ai
donut-basic: Basic Donut Chart
Library: letsplot 4.9.0 | Python 3.14.4
Quality: 84/100 | Updated: 2026-04-24
"""

import os

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

categories = ["Marketing", "Operations", "R&D", "Sales", "HR"]
values = [28, 22, 25, 18, 7]

df = pd.DataFrame({"category": categories, "value": values})
total = sum(values)
df["pct"] = df["value"] / total * 100
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)

center_df = pd.DataFrame({"x": [0.0], "y": [0.0], "label": [f"Total\n${total}M"]})

plot = (
    ggplot(df)  # noqa: F405
    + geom_pie(  # noqa: F405
        aes(slice="value", fill="category"),  # noqa: F405
        stat="identity",
        size=55,
        hole=0.5,
        labels=layer_labels()  # noqa: F405
        .line("@pct")
        .format("pct", "{.1f}%")
        .size(18),
    )
    + geom_label(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=center_df,
        size=20,
        color=INK,
        fill=ELEVATED_BG,
        label_padding=0.6,
        label_r=0.2,
    )
    + scale_fill_manual(values=OKABE_ITO)  # noqa: F405
    + labs(title="donut-basic · letsplot · anyplot.ai", fill="Department")  # noqa: F405
    + ggsize(1200, 1200)  # noqa: F405
    + theme_void()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        plot_title=element_text(size=28, hjust=0.5, color=INK),  # noqa: F405
        legend_title=element_text(size=20, color=INK),  # noqa: F405
        legend_text=element_text(size=18, color=INK_SOFT),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),  # noqa: F405
        legend_position=[0.88, 0.5],
    )
)

export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
