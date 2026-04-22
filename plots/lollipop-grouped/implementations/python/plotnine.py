""" pyplots.ai
lollipop-grouped: Grouped Lollipop Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    ggplot,
    labs,
    position_dodge,
    scale_color_manual,
    theme,
)


# Data - Quarterly revenue by product line across regions
np.random.seed(42)

categories = ["North America", "Europe", "Asia Pacific", "Latin America"]
series = ["Software", "Hardware", "Services"]

data = []
for cat in categories:
    for ser in series:
        # Create realistic revenue patterns
        base = {"Software": 85, "Hardware": 65, "Services": 50}[ser]
        region_factor = {"North America": 1.2, "Europe": 1.0, "Asia Pacific": 0.9, "Latin America": 0.7}[cat]
        value = base * region_factor + np.random.uniform(-8, 8)
        data.append({"Category": cat, "Series": ser, "Revenue": value})

df = pd.DataFrame(data)

# Colors - Python blue plus complementary colors
colors = ["#306998", "#FFD43B", "#E85D04"]

# Create grouped lollipop chart
plot = (
    ggplot(df, aes(x="Category", y="Revenue", color="Series"))
    # Stems (segments from 0 to value)
    + geom_segment(
        aes(x="Category", xend="Category", y=0, yend="Revenue"), position=position_dodge(width=0.6), size=1.5
    )
    # Markers (dots at the top)
    + geom_point(position=position_dodge(width=0.6), size=6)
    # Custom colors
    + scale_color_manual(values=colors)
    # Labels
    + labs(
        title="lollipop-grouped · plotnine · pyplots.ai", x="Region", y="Revenue (Million USD)", color="Product Line"
    )
    # Theme
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(size=14),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_background=element_rect(fill="white"),
        panel_grid_major_y=element_line(color="#CCCCCC", size=0.5, alpha=0.3),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color="#333333", size=0.8),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
