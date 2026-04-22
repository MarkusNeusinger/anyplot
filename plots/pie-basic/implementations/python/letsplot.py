""" pyplots.ai
pie-basic: Basic Pie Chart
Library: letsplot 4.8.2 | Python 3.14.0
Quality: 82/100 | Created: 2025-12-23
"""

from lets_plot import *  # noqa: F403
from lets_plot import ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Global smartphone market share (2024)
data = {
    "company": ["Apple", "Samsung", "Xiaomi", "OPPO", "Others"],
    "share": [23.1, 19.4, 13.7, 8.8, 35.0],
    "explode": [0.0, 0.0, 0.0, 0.12, 0.0],
}

# Colors - Python Blue first, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#4CAF50", "#AB47BC", "#90A4AE"]

# Plot — square canvas fills space evenly for circular pie charts
plot = (
    ggplot(data)  # noqa: F405
    + geom_pie(  # noqa: F405
        aes(slice="share", fill="company", explode="explode"),  # noqa: F405
        stat="identity",
        size=75,
        hole=0,
        stroke=2,
        stroke_side="both",
        color="white",
        spacer_width=1.5,
        spacer_color="white",
        labels=layer_labels()  # noqa: F405
        .line("@{share}")
        .format("share", "{.1f}%")
        .size(18),
    )
    + scale_fill_manual(values=colors)  # noqa: F405
    + labs(  # noqa: F405
        title="Global Smartphone Market Share · pie-basic · letsplot · pyplots.ai",
        subtitle="OPPO's 8.8% slice is the smallest — 'Others' dominate at 35%",
        fill="Brand",
    )
    + ggsize(1200, 1200)  # noqa: F405
    + theme_void()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=26, hjust=0.5, face="bold"),  # noqa: F405
        plot_subtitle=element_text(size=16, hjust=0.5, color="#555555"),  # noqa: F405
        legend_title=element_text(size=20),  # noqa: F405
        legend_text=element_text(size=18),  # noqa: F405
        plot_margin=[30, 20, 30, 20],
        legend_position="bottom",
        legend_direction="horizontal",
    )
)

# Save
ggsave(plot, filename="plot.png", path=".", scale=3)
ggsave(plot, filename="plot.html", path=".")
