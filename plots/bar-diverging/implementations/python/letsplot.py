""" anyplot.ai
bar-diverging: Diverging Bar Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-08
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

# Okabe-Ito brand colors for diverging bars
POSITIVE_COLOR = "#009E73"  # Brand green
NEGATIVE_COLOR = "#AE3030"  # imprint red — negative

# Data - Customer satisfaction survey (Net Promoter Score style)
categories = [
    "Product Quality",
    "Customer Service",
    "Pricing",
    "Delivery Speed",
    "Website Usability",
    "Return Policy",
    "Product Selection",
    "Payment Options",
    "Mobile App",
    "Packaging",
    "Technical Support",
    "Loyalty Program",
]

# More balanced scores: 6 negative, 6 positive
scores = [62, 48, -22, 35, -15, 52, 28, 68, -38, 42, -8, 38]

df = pd.DataFrame(
    {"Category": categories, "Score": scores, "Sentiment": ["Positive" if s >= 0 else "Negative" for s in scores]}
)

# Sort by score for better pattern recognition
df = df.sort_values("Score", ascending=True).reset_index(drop=True)

# Preserve category order after sorting
df["Category"] = pd.Categorical(df["Category"], categories=df["Category"].tolist(), ordered=True)

# Create horizontal diverging bar chart with theme-adaptive styling
plot = (
    ggplot(df, aes(x="Score", y="Category", fill="Sentiment"))  # noqa: F405
    + geom_bar(stat="identity", width=0.75, alpha=0.95)  # noqa: F405
    + geom_vline(xintercept=0, color=INK_SOFT, size=1.5)  # noqa: F405
    + scale_fill_manual(  # noqa: F405
        values={
            "Positive": POSITIVE_COLOR,
            "Negative": NEGATIVE_COLOR,
        }
    )
    + labs(  # noqa: F405
        x="Net Promoter Score (-100 to +100)", y="Category", title="bar-diverging · letsplot · anyplot.ai"
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        panel_grid_major_x=element_line(color=INK, size=0.3),  # noqa: F405
        panel_grid_major_y=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_title=element_text(size=28, face="bold", color=INK, hjust=0.5),  # noqa: F405
        axis_title_x=element_text(size=22, color=INK),  # noqa: F405
        axis_title_y=element_text(size=22, color=INK),  # noqa: F405
        axis_text_x=element_text(size=18, color=INK_SOFT),  # noqa: F405
        axis_text_y=element_text(size=18, color=INK_SOFT),  # noqa: F405
        axis_line_x=element_line(color=INK_SOFT),  # noqa: F405
        axis_line_y=element_line(color=INK_SOFT),  # noqa: F405
        legend_title=element_text(size=18, color=INK),  # noqa: F405
        legend_text=element_text(size=16, color=INK_SOFT),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
        legend_position="right",
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG with scale 3x to get 4800 × 2700 px
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
