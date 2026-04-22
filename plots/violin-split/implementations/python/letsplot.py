""" pyplots.ai
violin-split: Split Violin Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Employee satisfaction scores before and after office redesign across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Design"]
data = []

# Generate realistic distributions showing varied effects of office redesign
distributions = {
    "Engineering": {
        "Before": {"mean": 65, "std": 12},  # Moderate satisfaction
        "After": {"mean": 78, "std": 10},  # Clear improvement
    },
    "Marketing": {
        "Before": {"mean": 58, "std": 15},  # Lower satisfaction with high variance
        "After": {"mean": 72, "std": 11},  # Improvement with less variance
    },
    "Sales": {
        "Before": {"mean": 70, "std": 14},  # Already decent
        "After": {"mean": 75, "std": 12},  # Modest improvement
    },
    "Design": {
        "Before": {"mean": 55, "std": 18},  # Low satisfaction
        "After": {"mean": 82, "std": 8},  # Dramatic improvement, tight distribution
    },
}

for dept in departments:
    for period in ["Before", "After"]:
        params = distributions[dept][period]
        n_samples = np.random.randint(80, 150)
        values = np.random.normal(params["mean"], params["std"], n_samples)
        values = np.clip(values, 20, 100)  # Satisfaction score bounds
        for v in values:
            data.append({"Department": dept, "Satisfaction": v, "Period": period})

df = pd.DataFrame(data)

# Split violin: use show_half=-1 for "Before" (left side) and show_half=1 for "After" (right side)
df_before = df[df["Period"] == "Before"].copy()
df_after = df[df["Period"] == "After"].copy()

# Create split violin plot  # noqa: F405
plot = (
    ggplot()  # noqa: F405
    # Left half: Before (show_half=-1)
    + geom_violin(  # noqa: F405
        aes(x="Department", y="Satisfaction", fill="Period"),  # noqa: F405
        data=df_before,
        show_half=-1,  # Left half
        trim=False,
        size=1.0,
        alpha=0.75,
        color="#306998",
        tooltips=layer_tooltips()  # noqa: F405
        .title("@Department - Before")
        .line("Satisfaction: @Satisfaction")
        .format("@Satisfaction", ".0f"),
    )
    # Right half: After (show_half=1)
    + geom_violin(  # noqa: F405
        aes(x="Department", y="Satisfaction", fill="Period"),  # noqa: F405
        data=df_after,
        show_half=1,  # Right half
        trim=False,
        size=1.0,
        alpha=0.75,
        color="#FFD43B",
        tooltips=layer_tooltips()  # noqa: F405
        .title("@Department - After")
        .line("Satisfaction: @Satisfaction")
        .format("@Satisfaction", ".0f"),
    )
    # Add inner quartile lines for better distribution visualization
    + geom_boxplot(  # noqa: F405
        aes(x="Department", y="Satisfaction", fill="Period"),  # noqa: F405
        data=df_before,
        width=0.08,
        outlier_shape=None,
        position=position_nudge(x=-0.05),  # noqa: F405
        alpha=0.9,
        size=0.8,
        show_legend=False,
    )
    + geom_boxplot(  # noqa: F405
        aes(x="Department", y="Satisfaction", fill="Period"),  # noqa: F405
        data=df_after,
        width=0.08,
        outlier_shape=None,
        position=position_nudge(x=0.05),  # noqa: F405
        alpha=0.9,
        size=0.8,
        show_legend=False,
    )
    # Color scale: Python Blue for Before, Python Yellow for After
    + scale_fill_manual(values=["#FFD43B", "#306998"], name="Period")  # noqa: F405
    # Set y-axis limits to match data range (satisfaction scores 0-100)
    + scale_y_continuous(limits=[15, 105])  # noqa: F405
    # Labels
    + labs(  # noqa: F405
        x="Department", y="Satisfaction Score (0-100)", title="violin-split · letsplot · pyplots.ai"
    )
    # Theme
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, face="bold"),  # noqa: F405
        axis_title_x=element_text(size=20),  # noqa: F405
        axis_title_y=element_text(size=20),  # noqa: F405
        axis_text_x=element_text(size=16),  # noqa: F405
        axis_text_y=element_text(size=16),  # noqa: F405
        legend_title=element_text(size=18),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
        legend_position="right",
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color="rgba(0, 0, 0, 0.3)", size=0.5),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
