""" anyplot.ai
violin-split: Split Violin Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-08
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave

LetsPlot.setup_html()  # noqa: F405

# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_LINE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series always #009E73)
COLOR_BEFORE = "#009E73"  # Okabe-Ito position 1
COLOR_AFTER = "#C475FD"  # Okabe-Ito position 2

# Data - Employee satisfaction scores before and after office redesign across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Design"]
data = []

# Generate realistic distributions showing varied effects of office redesign
distributions = {
    "Engineering": {"Before": {"mean": 65, "std": 12}, "After": {"mean": 78, "std": 10}},
    "Marketing": {"Before": {"mean": 58, "std": 15}, "After": {"mean": 72, "std": 11}},
    "Sales": {"Before": {"mean": 70, "std": 14}, "After": {"mean": 75, "std": 12}},
    "Design": {"Before": {"mean": 55, "std": 18}, "After": {"mean": 82, "std": 8}},
}

for dept in departments:
    for period in ["Before", "After"]:
        params = distributions[dept][period]
        n_samples = np.random.randint(80, 150)
        values = np.random.normal(params["mean"], params["std"], n_samples)
        values = np.clip(values, 20, 100)
        for v in values:
            data.append({"Department": dept, "Satisfaction": v, "Period": period})

df = pd.DataFrame(data)

# Prepare data for split violin
df_before = df[df["Period"] == "Before"].copy()
df_after = df[df["Period"] == "After"].copy()

# Create split violin plot
plot = (
    ggplot()  # noqa: F405
    # Left half: Before (show_half=-1)
    + geom_violin(  # noqa: F405
        aes(x="Department", y="Satisfaction", fill="Period"),  # noqa: F405
        data=df_before,
        show_half=-1,
        trim=False,
        size=0.8,
        alpha=0.75,
    )
    # Right half: After (show_half=1)
    + geom_violin(  # noqa: F405
        aes(x="Department", y="Satisfaction", fill="Period"),  # noqa: F405
        data=df_after,
        show_half=1,
        trim=False,
        size=0.8,
        alpha=0.75,
    )
    # Inner quartile lines for distribution visualization
    + geom_boxplot(  # noqa: F405
        aes(x="Department", y="Satisfaction", fill="Period"),  # noqa: F405
        data=df_before,
        width=0.08,
        outlier_shape=None,
        position=position_nudge(x=-0.05),  # noqa: F405
        alpha=0.9,
        size=0.6,
        show_legend=False,
    )
    + geom_boxplot(  # noqa: F405
        aes(x="Department", y="Satisfaction", fill="Period"),  # noqa: F405
        data=df_after,
        width=0.08,
        outlier_shape=None,
        position=position_nudge(x=0.05),  # noqa: F405
        alpha=0.9,
        size=0.6,
        show_legend=False,
    )
    # Okabe-Ito colors (Before=#009E73, After=#C475FD)
    + scale_fill_manual(values=[COLOR_AFTER, COLOR_BEFORE], name="Period")  # noqa: F405
    + scale_y_continuous(limits=[15, 105])  # noqa: F405
    # Labels
    + labs(x="Department", y="Satisfaction Score (0-100)", title="violin-split · letsplot · anyplot.ai")  # noqa: F405
    # Theme-adaptive styling
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color=GRID_LINE, size=0.4),  # noqa: F405
        plot_title=element_text(size=24, face="bold", color=INK),  # noqa: F405
        axis_title_x=element_text(size=20, color=INK),  # noqa: F405
        axis_title_y=element_text(size=20, color=INK),  # noqa: F405
        axis_text_x=element_text(size=16, color=INK_SOFT),  # noqa: F405
        axis_text_y=element_text(size=16, color=INK_SOFT),  # noqa: F405
        axis_line=element_line(color=INK_SOFT, size=0.4),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
        legend_title=element_text(size=18, color=INK),  # noqa: F405
        legend_text=element_text(size=16, color=INK_SOFT),  # noqa: F405
        legend_position="right",
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save outputs (scale 3x to get 4800 x 2700 px)
ggsave(plot, f"plot-{THEME}.png", scale=3)
ggsave(plot, f"plot-{THEME}.html")
