""" pyplots.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Titanic-like survival data cross-tabulated by class and survival status
# This shows clear association patterns between passenger class and survival
categories_1 = ["First Class", "Second Class", "Third Class", "Crew"]
categories_2 = ["Survived", "Did Not Survive"]

# Frequencies for each combination (rows: category_1, cols: category_2)
# Data shows higher survival rates for upper classes
frequencies = {
    "First Class": [202, 123],  # 62% survival rate
    "Second Class": [118, 167],  # 41% survival rate
    "Third Class": [178, 528],  # 25% survival rate
    "Crew": [212, 673],  # 24% survival rate
}

# Calculate totals for each category_1 (determines column width)
cat1_totals = {cat: sum(freqs) for cat, freqs in frequencies.items()}
grand_total = sum(cat1_totals.values())

# Calculate proportional widths (sum to 100%)
cat1_widths = {cat: total / grand_total * 100 for cat, total in cat1_totals.items()}

# Build rectangle coordinates for mosaic plot
# xmin, xmax define horizontal position (proportional to category_1 marginal)
# ymin, ymax define vertical position (proportional to category_2 conditional)
rects = []
x_pos = 0
gap = 0.8  # Gap between columns

for cat1 in categories_1:
    col_width = cat1_widths[cat1] - gap
    col_freqs = frequencies[cat1]
    col_total = cat1_totals[cat1]

    y_pos = 0
    for i, cat2 in enumerate(categories_2):
        freq = col_freqs[i]
        segment_height = (freq / col_total) * 100  # Height as percentage

        rects.append(
            {
                "category_1": cat1,
                "category_2": cat2,
                "frequency": freq,
                "xmin": x_pos + gap / 2,
                "xmax": x_pos + col_width + gap / 2,
                "ymin": y_pos + 0.3,  # Small gap between segments
                "ymax": y_pos + segment_height - 0.3,
                "x_center": x_pos + cat1_widths[cat1] / 2,
                "y_center": y_pos + segment_height / 2,
            }
        )
        y_pos += segment_height

    x_pos += cat1_widths[cat1]

df = pd.DataFrame(rects)

# Colors: Python Blue for Survived, Python Yellow for Did Not Survive
colors = ["#306998", "#FFD43B"]

# Create x-axis breaks at center of each column
x_breaks = []
x_pos = 0
for cat1 in categories_1:
    x_breaks.append(x_pos + cat1_widths[cat1] / 2)
    x_pos += cat1_widths[cat1]

# Create mosaic plot using geom_rect
plot = (
    ggplot(df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="category_2"), color="white", size=0.3)
    # Add frequency labels on each segment
    + geom_text(aes(x="x_center", y="y_center", label="frequency"), size=14, color="white", fontface="bold")
    + scale_fill_manual(values=colors, name="Survival Status")
    + scale_x_continuous(
        name="Passenger Class (width proportional to count)", breaks=x_breaks, labels=categories_1, limits=[0, 100]
    )
    + scale_y_continuous(name="Survival Rate (%)", limits=[0, 100], breaks=[0, 25, 50, 75, 100])
    + labs(title="mosaic-categorical · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        axis_title=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scaled 3x for 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
