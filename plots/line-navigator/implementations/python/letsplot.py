""" pyplots.ai
line-navigator: Line Chart with Mini Navigator
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Generate 3 years of daily sensor readings (1000+ data points)
np.random.seed(42)
n_days = 1095  # 3 years of daily data
dates = pd.date_range(start="2023-01-01", periods=n_days, freq="D")

# Generate realistic sensor data with trend, seasonality, and noise
trend = np.linspace(20, 35, n_days)  # Gradual temperature increase
seasonality = 10 * np.sin(2 * np.pi * np.arange(n_days) / 365)  # Annual cycle
noise = np.random.normal(0, 2, n_days)  # Random variation
values = trend + seasonality + noise

# Create main DataFrame with full data
df_full = pd.DataFrame({"date": dates, "value": values})

# Define selected range - show most recent 6 months in detail
selected_days = 180
range_start_idx = len(df_full) - selected_days
df_selected = df_full.iloc[range_start_idx:].copy()

# Y-axis limits for main chart with padding
main_y_min = df_selected["value"].min()
main_y_max = df_selected["value"].max()
main_y_range = main_y_max - main_y_min
main_y_lower = main_y_min - main_y_range * 0.05
main_y_upper = main_y_max + main_y_range * 0.1

# Navigator Y-axis limits (full data range)
nav_y_min = df_full["value"].min() - 2
nav_y_max = df_full["value"].max() + 2

# Tooltips for main chart
main_tooltips = (
    layer_tooltips()  # noqa: F405
    .title("Sensor Reading")
    .line("Date: @date")
    .line("Value: @{value}")
    .format("value", ".1f")
)

# Selection rectangle data for navigator
select_xmin = df_full["date"].iloc[range_start_idx]
select_xmax = df_full["date"].iloc[-1]
selection_rect = pd.DataFrame({"xmin": [select_xmin], "xmax": [select_xmax], "ymin": [nav_y_min], "ymax": [nav_y_max]})

# Date range labels for display
start_label = select_xmin.strftime("%b %d, %Y")
end_label = select_xmax.strftime("%b %d, %Y")
range_label_df = pd.DataFrame(
    {
        "x": [(select_xmin + (select_xmax - select_xmin) / 2)],
        "y": [main_y_upper - main_y_range * 0.05],
        "label": [f"Selected Range: {start_label} - {end_label}"],
    }
)

# Main chart - detailed view of selected range
main_chart = (
    ggplot(df_selected, aes(x="date", y="value"))  # noqa: F405
    + geom_area(fill="#306998", alpha=0.15)  # noqa: F405
    + geom_line(color="#306998", size=1.5, tooltips=main_tooltips)  # noqa: F405
    # Date range annotation
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=range_label_df,
        inherit_aes=False,
        size=14,
        color="#306998",
        fontface="bold",
    )
    + labs(x="", y="Value")  # noqa: F405
    + scale_x_datetime(format="%b %Y")  # noqa: F405
    + scale_y_continuous(limits=[main_y_lower, main_y_upper])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        panel_grid_major=element_line(color="#D8D8D8", size=0.4),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
    )
    + ggsize(1600, 650)  # noqa: F405
)

# Navigator/mini chart - full data overview with selection window
navigator = (
    ggplot(df_full, aes(x="date", y="value"))  # noqa: F405
    # Selection rectangle (highlights the visible range)
    + geom_rect(  # noqa: F405
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),  # noqa: F405
        data=selection_rect,
        inherit_aes=False,
        fill="#306998",
        alpha=0.2,
        color="#306998",
        linetype="solid",
        size=1.5,
    )
    # Full data line
    + geom_area(fill="#306998", alpha=0.15, tooltips="none")  # noqa: F405
    + geom_line(color="#306998", size=0.8, tooltips="none")  # noqa: F405
    + labs(x="Date", y="")  # noqa: F405
    + scale_x_datetime(format="%Y")  # noqa: F405
    + scale_y_continuous(limits=[nav_y_min, nav_y_max])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=14),  # noqa: F405
        axis_text=element_text(size=12),  # noqa: F405
        panel_grid=element_line(color="#E8E8E8", size=0.3),  # noqa: F405
    )
    + ggsize(1600, 150)  # noqa: F405
)

# Combine main chart and navigator using gggrid
# Navigator height is ~18% of main chart height (proportionally smaller as specified)
combined = gggrid(  # noqa: F405
    [main_chart, navigator], ncol=1, heights=[5.5, 1], align=True
)

# Add overall title
combined = (
    combined
    + ggtitle("line-navigator · letsplot · pyplots.ai")  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme(plot_title=element_text(size=26, face="bold"))  # noqa: F405
)

# Save PNG (scale 3x for 4800x2700 px output)
ggsave(combined, "plot.png", path=".", scale=3)

# Save interactive HTML (pan, zoom, tooltips available)
ggsave(combined, "plot.html", path=".")
