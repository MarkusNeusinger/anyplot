"""anyplot.ai
donut-basic: Basic Donut Chart
Library: letsplot | Python 3.13
Quality: pending | Updated: 2026-06-25
"""

import os

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — 5 slots for 5 department categories
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — annual budget allocation by department ($M)
categories = ["Marketing", "Operations", "R&D", "Sales", "HR"]
values = [28, 22, 25, 18, 7]

df = pd.DataFrame({"category": categories, "value": values})
total = sum(values)
df["pct"] = df["value"] / total * 100
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)
# Explode the dominant segment to give it visual emphasis
df["explode"] = [0.12 if c == "Marketing" else 0.0 for c in df["category"]]

center_df = pd.DataFrame({"x": [0.0], "y": [0.0], "label": [f"Total\n${total}M"]})

# Title: 46 chars < 67-char baseline → keep default size=16
TITLE = "donut-basic · python · letsplot · anyplot.ai"

plot = (
    ggplot(df)  # noqa: F405
    + geom_pie(  # noqa: F405
        aes(slice="value", fill="category", explode="explode"),  # noqa: F405
        stat="identity",
        size=40,
        hole=0.5,
        labels=layer_labels()  # noqa: F405
        .line("@pct")
        .format("pct", "{.1f}%")
        .size(11),
    )
    + geom_label(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=center_df,
        size=10,
        color=INK,
        fill=ELEVATED_BG,
        label_padding=0.6,
        label_r=0.2,
    )
    + scale_fill_manual(values=IMPRINT)  # noqa: F405
    + labs(title=TITLE, fill="Department")  # noqa: F405
    + ggsize(600, 600)  # noqa: F405  → scale=4 → 2400×2400 PNG
    + theme_void()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        plot_title=element_text(size=16, hjust=0.5, color=INK),  # noqa: F405
        legend_title=element_text(size=12, color=INK),  # noqa: F405
        legend_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),  # noqa: F405
        legend_position=[0.85, 0.5],
    )
)

export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
