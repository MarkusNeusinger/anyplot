"""anyplot.ai
ridgeline-basic: Basic Ridgeline Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-07-25
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Monthly temperature distributions (realistic weather data)
np.random.seed(42)

months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# Temperature parameters (mean, std) for each month - Northern hemisphere pattern
temp_params = {
    "January": (2, 5),
    "February": (4, 5),
    "March": (8, 5),
    "April": (13, 4),
    "May": (17, 4),
    "June": (21, 3),
    "July": (24, 3),
    "August": (23, 3),
    "September": (19, 4),
    "October": (14, 4),
    "November": (8, 5),
    "December": (4, 5),
}

# Generate temperature observations for each month
data = []
for month in months:
    mean, std = temp_params[month]
    temps = np.random.normal(mean, std, 150)
    for t in temps:
        data.append({"Month": month, "Temperature": t})

df = pd.DataFrame(data)

# Convert month to categorical with correct order (reversed for ridgeline bottom-to-top)
df["Month"] = pd.Categorical(df["Month"], categories=months[::-1], ordered=True)

# Imprint sequential gradient per month (single-polarity: chronological Jan -> Dec),
# interpolated as discrete per-group fills since geom_area_ridges renders one solid
# fill per ridge (a continuous scale collapses to a single blended color here).
n_months = len(months)
month_colors = {
    month: "#{:02X}{:02X}{:02X}".format(
        *(round(a + (b - a) * i / (n_months - 1)) for a, b in zip((0x00, 0x9E, 0x73), (0x44, 0x67, 0xA3), strict=True))
    )
    for i, month in enumerate(months)
}

plot = (
    ggplot(df, aes(x="Temperature", y="Month", fill="Month"))  # noqa: F405
    + geom_area_ridges(  # noqa: F405
        scale=1.2,  # Overlap amount (>1 means overlap)
        alpha=0.85,
        size=1.0,  # Border thickness
        color=PAGE_BG,  # Border matches page background for clean ridge separation
    )
    + scale_fill_manual(values=month_colors)  # noqa: F405
    + labs(  # noqa: F405
        x="Temperature (°C)",
        y="",
        title="Monthly Temperature Distribution · ridgeline-basic · python · letsplot · anyplot.ai",
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        axis_title=element_text(size=12, color=INK),  # noqa: F405
        axis_text_x=element_text(size=10, color=INK_SOFT),  # noqa: F405
        axis_text_y=element_text(size=10, color=INK_SOFT),  # noqa: F405
        axis_line=element_line(color=INK_SOFT),  # noqa: F405
        plot_title=element_text(size=13, color=INK),  # noqa: F405
        legend_position="none",  # Y-axis labels are sufficient; fill is chronological, not a separate metric
        panel_grid_major_y=element_blank(),  # noqa: F405
        panel_grid_major_x=element_line(color=INK, size=0.3),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
    )
    + ggsize(800, 450)  # noqa: F405
)

# Save PNG (scale 4x for 3200x1800) and HTML
export_ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
export_ggsave(plot, f"plot-{THEME}.html", path=".")
