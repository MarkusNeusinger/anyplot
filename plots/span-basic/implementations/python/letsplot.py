""" pyplots.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_line,
    geom_point,
    geom_rect,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Simulated economic indicator over time (2006-2011)
np.random.seed(42)
months = pd.date_range("2006-01", periods=72, freq="ME")
# Economic cycle: growth -> recession dip -> recovery
base = np.linspace(105, 90, 24).tolist() + np.linspace(90, 75, 18).tolist() + np.linspace(75, 115, 30).tolist()
noise = np.random.randn(72) * 2.5
values = np.array(base) + noise

df = pd.DataFrame({"date": months, "index": values})
df["date_num"] = np.arange(len(df))

# Create year labels for x-axis
year_positions = [0, 12, 24, 36, 48, 60]
year_labels = ["2006", "2007", "2008", "2009", "2010", "2011"]

# Span regions - recession period (Dec 2007 to Jun 2009)
recession_start = 24  # Jan 2008
recession_end = 42  # Jun 2009

spans = pd.DataFrame(
    {
        "xmin": [recession_start],
        "xmax": [recession_end],
        "ymin": [df["index"].min() - 8],
        "ymax": [df["index"].max() + 8],
        "label": ["Recession Period"],
    }
)

# Label position for span annotation
span_label = pd.DataFrame(
    {"x": [(recession_start + recession_end) / 2], "y": [df["index"].max() + 4], "text": ["Recession 2008-2009"]}
)

# Plot
plot = (
    ggplot()
    # Vertical span for recession period (highlight with yellow)
    + geom_rect(data=spans, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="label"), alpha=0.25)
    # Economic indicator line
    + geom_line(data=df, mapping=aes(x="date_num", y="index"), color="#306998", size=1.8)
    + geom_point(data=df, mapping=aes(x="date_num", y="index"), color="#306998", size=3.5, alpha=0.7)
    # Span label annotation
    + geom_text(data=span_label, mapping=aes(x="x", y="y", label="text"), size=14, color="#8B6914")
    # Labels and styling
    + labs(x="Year", y="Economic Index", title="span-basic · letsplot · pyplots.ai")
    + scale_fill_manual(values=["#FFD43B"], name="Highlighted Region")
    + scale_x_continuous(breaks=year_positions, labels=year_labels)
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x gives 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
