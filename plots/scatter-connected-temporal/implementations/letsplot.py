"""pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-13
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data — Unemployment rate vs inflation rate (Phillips curve), 1990-2023
np.random.seed(42)
years = np.arange(1990, 2024)
n = len(years)

# Simulate realistic Phillips curve dynamics with regime shifts
unemployment = np.concatenate(
    [
        np.linspace(5.6, 4.0, 10) + np.random.randn(10) * 0.3,  # 1990s decline
        np.linspace(4.0, 6.3, 4) + np.random.randn(4) * 0.2,  # 2001 recession
        np.linspace(6.3, 4.4, 6) + np.random.randn(6) * 0.2,  # mid-2000s recovery
        np.linspace(4.4, 10.0, 3) + np.random.randn(3) * 0.3,  # 2008 crisis
        np.linspace(10.0, 3.5, 11) + np.random.randn(11) * 0.3,  # long recovery
    ]
)
inflation = np.concatenate(
    [
        np.linspace(5.4, 2.3, 10) + np.random.randn(10) * 0.4,  # 1990s disinflation
        np.linspace(2.3, 1.6, 4) + np.random.randn(4) * 0.3,  # low inflation
        np.linspace(1.6, 3.8, 6) + np.random.randn(6) * 0.3,  # rising
        np.linspace(3.8, -0.4, 3) + np.random.randn(3) * 0.4,  # deflation scare
        np.linspace(-0.4, 6.5, 11) + np.random.randn(11) * 0.5,  # recovery to post-covid
    ]
)

df = pd.DataFrame(
    {
        "unemployment": unemployment,
        "inflation": inflation,
        "year": years,
        "year_label": [str(y) for y in years],
        "time_idx": np.arange(n),
    }
)

# Color gradient: map time index to a normalized value for color encoding
df["time_norm"] = df["time_idx"] / (n - 1)

# Label only key years for annotation
key_years = {1990, 1995, 2000, 2003, 2007, 2009, 2015, 2020, 2023}
df_labels = df[df["year"].isin(key_years)].copy()

# Plot
plot = (
    ggplot(df, aes(x="unemployment", y="inflation"))  # noqa: F405
    + geom_path(  # noqa: F405
        aes(color="time_idx"),  # noqa: F405
        size=1.8,
        alpha=0.7,
        tooltips="none",
    )
    + geom_point(  # noqa: F405
        aes(fill="time_idx"),  # noqa: F405
        color="white",
        size=5,
        stroke=1.0,
        shape=21,
        alpha=0.85,
        tooltips=layer_tooltips()  # noqa: F405
        .line("Year|@year")
        .line("Unemployment|@{unemployment}{.1f}%")
        .line("Inflation|@{inflation}{.1f}%"),
    )
    + geom_text(  # noqa: F405
        data=df_labels,
        mapping=aes(x="unemployment", y="inflation", label="year_label"),  # noqa: F405
        size=11,
        color="#333333",
        nudge_y=0.45,
        family="monospace",
    )
    + scale_color_gradient(  # noqa: F405
        low="#a8d5e2", high="#1a3a5c", name="Year", breaks=[0, (n - 1) / 2, n - 1], labels=["1990", "2006", "2023"]
    )
    + scale_fill_gradient(  # noqa: F405
        low="#a8d5e2", high="#1a3a5c", guide="none"
    )
    + labs(  # noqa: F405
        x="Unemployment Rate (%)",
        y="Inflation Rate (%)",
        title="scatter-connected-temporal · letsplot · pyplots.ai",
        subtitle="Phillips Curve Dynamics — US-style unemployment vs inflation, 1990-2023",
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16, color="#555555"),  # noqa: F405
        axis_title=element_text(size=20, color="#333333"),  # noqa: F405
        plot_title=element_text(size=24, color="#222222"),  # noqa: F405
        plot_subtitle=element_text(size=16, color="#666666"),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
        legend_title=element_text(size=16),  # noqa: F405
        panel_grid_major=element_line(color="#E8E8E8", size=0.35),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_margin=[40, 50, 20, 20],
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename="plot.html", path=".")
