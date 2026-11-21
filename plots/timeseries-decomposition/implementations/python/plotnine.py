"""anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_line,
    ggplot,
    labs,
    scale_x_datetime,
    theme,
    theme_minimal,
)
from statsmodels.tsa.seasonal import seasonal_decompose


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, first series is always brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SEASONAL_PERIOD = 7  # weekly cycle in daily data
COMPONENTS = ["Original", "Trend", "Seasonal", "Residual"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
SESSIONS = "Daily website sessions"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("sessions.csv")
rng = np.random.default_rng(42)
n_days = 273  # 39 full weeks
days = np.arange(n_days)
growth = 4000 + 9 * days + 350 * np.sin(2 * np.pi * days / 273)  # slow, slightly wavy audience growth
weekday_effect = np.array([620, 540, 480, 430, 260, -820, -1010])  # busy Mon-Fri, quiet weekend
noise = rng.normal(0, 230, n_days)
noise[[40, 135, 210]] += [900, -800, 1100]  # a campaign spike, an outage, a viral post
df = pd.DataFrame(
    {DATE: pd.date_range("2024-01-01", periods=n_days, freq="D"), SESSIONS: growth + weekday_effect[days % 7] + noise}
)

# Plot: reads only df and the constants above
decomposition = seasonal_decompose(
    df[SESSIONS].interpolate(limit_area="inside").bfill().ffill().to_numpy(), model="additive", period=SEASONAL_PERIOD
)
series = [df[SESSIONS].to_numpy(), decomposition.trend, decomposition.seasonal, decomposition.resid]

df_plot = pd.DataFrame(
    {
        DATE: np.tile(df[DATE].to_numpy(), len(COMPONENTS)),
        SESSIONS: np.concatenate(series),
        "Component": pd.Categorical(np.repeat(COMPONENTS, len(df)), categories=COMPONENTS, ordered=True),
    }
).dropna()  # the centered moving average leaves the series edges unestimated

plot = (
    ggplot(df_plot, aes(x=DATE, y=SESSIONS))
    + geom_line(color=IMPRINT_PALETTE[0], size=0.7)
    + facet_wrap("Component", ncol=1, scales="free_y")
    + scale_x_datetime(date_labels="%b %Y", date_breaks="2 months")
    + labs(title="timeseries-decomposition · python · plotnine · anyplot.ai", x=DATE, y=SESSIONS)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK),
        axis_title_x=element_text(size=10, margin={"t": 6}, color=INK),
        axis_title_y=element_text(size=10, margin={"r": 6}, color=INK),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        axis_text_y=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        strip_text=element_text(size=9, weight="bold", color=INK),
        strip_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_spacing_y=0.04,
        panel_grid_major=element_line(color=INK, size=0.25, alpha=0.15),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
