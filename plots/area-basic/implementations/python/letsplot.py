""" anyplot.ai
area-basic: Basic Area Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-28
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"
DIP_COLOR = "#AE3030"

# Data — daily website visitors over January
np.random.seed(42)
days = pd.date_range(start="2024-01-01", periods=30, freq="D")
base_visitors = 5000
trend = np.linspace(0, 2000, 30)
weekly_pattern = 1000 * np.sin(np.arange(30) * 2 * np.pi / 7)
noise = np.random.randn(30) * 300
visitors = base_visitors + trend + weekly_pattern + noise
visitors = np.clip(visitors, 2000, None).astype(int)

df = pd.DataFrame({"date": days, "visitors": visitors})

peak_idx = int(df["visitors"].idxmax())
dip_idx = int(df["visitors"].idxmin())
dip_val = df.loc[dip_idx, "visitors"]
peak_val = df.loc[peak_idx, "visitors"]
growth_pct = (df["visitors"].iloc[-5:].mean() / df["visitors"].iloc[:5].mean() - 1) * 100

subtitle = f"+{growth_pct:.0f}% average growth over January — weekly cycles with steady upward trend"

ann_peak = df.iloc[[peak_idx]].copy()
ann_dip = df.iloc[[dip_idx]].copy()

y_min = max(int(dip_val * 0.82), 0)
y_max = int(peak_val * 1.06)

anyplot_chrome = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
    panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
    panel_grid_major_y=element_line(color=INK_SOFT, size=0.15),  # noqa: F405
    panel_grid_major_x=element_blank(),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
    axis_title=element_text(color=INK, size=12),  # noqa: F405
    axis_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
    axis_line=element_line(color=INK_SOFT),  # noqa: F405
    plot_title=element_text(color=INK, size=16),  # noqa: F405
    plot_subtitle=element_text(color=INK_SOFT, size=10),  # noqa: F405
    plot_margin=[40, 60, 20, 20],
)

plot = (
    ggplot(df, aes(x="date", y="visitors"))  # noqa: F405
    + geom_area(fill=BRAND, alpha=0.15)  # noqa: F405
    + geom_area(  # noqa: F405
        fill=BRAND,
        alpha=0.35,
        tooltips=layer_tooltips()  # noqa: F405
        .line("@visitors visitors")
        .format("date", "%b %d, %Y")
        .line("@date"),
    )
    + geom_line(color=BRAND, size=1.0)  # noqa: F405
    + geom_smooth(  # noqa: F405
        color=INK_SOFT, size=0.8, se=False, method="loess", linetype="dashed"
    )
    + geom_point(  # noqa: F405
        data=ann_peak,
        mapping=aes(x="date", y="visitors"),  # noqa: F405
        size=5,
        color=BRAND,
        fill=PAGE_BG,
        shape=21,
        stroke=2.0,
    )
    + geom_point(  # noqa: F405
        data=ann_dip,
        mapping=aes(x="date", y="visitors"),  # noqa: F405
        size=5,
        color=DIP_COLOR,
        fill=PAGE_BG,
        shape=21,
        stroke=2.0,
    )
    + geom_text(  # noqa: F405
        data=ann_peak,
        mapping=aes(x="date", y="visitors", label="visitors"),  # noqa: F405
        nudge_y=-500,
        size=4,
        color=BRAND,
        hjust=1,
        label_format="▲ {,d} peak",
    )
    + geom_text(  # noqa: F405
        data=ann_dip,
        mapping=aes(x="date", y="visitors", label="visitors"),  # noqa: F405
        nudge_y=-400,
        size=4,
        color=DIP_COLOR,
        label_format="▼ {,d} dip",
    )
    + scale_x_datetime(format="%b %d")  # noqa: F405
    + scale_y_continuous(limits=[y_min, y_max])  # noqa: F405
    + labs(  # noqa: F405
        x="Date", y="Daily Visitors", title="area-basic · python · letsplot · anyplot.ai", subtitle=subtitle
    )
    + ggsize(800, 450)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + anyplot_chrome
)

ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
