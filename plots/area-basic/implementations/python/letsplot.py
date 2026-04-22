""" pyplots.ai
area-basic: Basic Area Chart
Library: letsplot 4.8.2 | Python 3.14.2
Quality: 93/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data — daily website visitors over a month
np.random.seed(42)
days = pd.date_range(start="2024-01-01", periods=30, freq="D")
base_visitors = 5000
trend = np.linspace(0, 2000, 30)
weekly_pattern = 1000 * np.sin(np.arange(30) * 2 * np.pi / 7)
noise = np.random.randn(30) * 300
visitors = base_visitors + trend + weekly_pattern + noise
visitors = np.clip(visitors, 2000, None).astype(int)

df = pd.DataFrame({"date": days, "visitors": visitors})

# Key data points for storytelling
peak_idx = int(df["visitors"].idxmax())
dip_idx = int(df["visitors"].idxmin())
dip_val = df.loc[dip_idx, "visitors"]
peak_val = df.loc[peak_idx, "visitors"]
growth_pct = (df["visitors"].iloc[-5:].mean() / df["visitors"].iloc[:5].mean() - 1) * 100

subtitle = f"+{growth_pct:.0f}% average growth over January \u2014 weekly cycles with steady upward trend"

# Annotation data for peak and dip markers
ann_peak = df.iloc[[peak_idx]].copy()
ann_dip = df.iloc[[dip_idx]].copy()

# Y-axis range: generous padding for area fill weight below, headroom above for annotations
y_min = max(int(dip_val * 0.82), 0)
y_max = int(peak_val * 1.12)

# Gradient fill: layer multiple area geoms with decreasing alpha to simulate a vertical gradient
plot = (
    ggplot(df, aes(x="date", y="visitors"))  # noqa: F405
    + geom_area(fill="#306998", alpha=0.15)  # noqa: F405
    + geom_area(  # noqa: F405
        fill="#306998",
        alpha=0.35,
        tooltips=layer_tooltips()  # noqa: F405
        .line("@visitors visitors")
        .format("date", "%b %d, %Y")
        .line("@date"),
    )
    + geom_line(color="#306998", size=2.2)  # noqa: F405
    + geom_smooth(  # noqa: F405
        color="#1a3a5c", size=1.2, se=False, method="loess", linetype="dashed"
    )
    # Annotations — peak and dip markers
    + geom_point(  # noqa: F405
        data=ann_peak,
        mapping=aes(x="date", y="visitors"),  # noqa: F405
        size=8,
        color="#306998",
        fill="white",
        shape=21,
        stroke=2.5,
    )
    + geom_point(  # noqa: F405
        data=ann_dip,
        mapping=aes(x="date", y="visitors"),  # noqa: F405
        size=8,
        color="#c0392b",
        fill="white",
        shape=21,
        stroke=2.5,
    )
    # Annotations — peak and dip labels (peak placed below-left, dip placed below)
    + geom_text(  # noqa: F405
        data=ann_peak,
        mapping=aes(x="date", y="visitors", label="visitors"),  # noqa: F405
        nudge_y=-500,
        size=13,
        color="#1a3a5c",
        hjust=1,
        label_format="\u25b2 {,d} peak",
    )
    + geom_text(  # noqa: F405
        data=ann_dip,
        mapping=aes(x="date", y="visitors", label="visitors"),  # noqa: F405
        nudge_y=-400,
        size=13,
        color="#c0392b",
        label_format="\u25bc {,d} dip",
    )
    + scale_x_datetime(format="%b %d")  # noqa: F405
    + scale_y_continuous(limits=[y_min, y_max])  # noqa: F405
    + labs(  # noqa: F405
        x="Date", y="Daily Visitors", title="area-basic \u00b7 letsplot \u00b7 pyplots.ai", subtitle=subtitle
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        plot_subtitle=element_text(size=16, color="#555555"),  # noqa: F405
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_margin=[40, 60, 20, 20],  # top, right, bottom, left — extra right margin
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename="plot.html", path=".")
