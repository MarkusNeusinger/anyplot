"""anyplot.ai
drawdown-basic: Drawdown Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-23
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    geom_ribbon,
    ggplot,
    labs,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
DRAWDOWN_COLOR = IMPRINT_PALETTE[4]  # Imprint red, semantic: losses / drawdown
RECOVERY_COLOR = IMPRINT_PALETTE[0]  # Imprint green, semantic: recovery / new high
# Higher alpha in dark mode so ribbon remains visible over near-black background
RIBBON_ALPHA = 0.30 if THEME == "light" else 0.55

# Column constants
DATE = "Date"  # role: date
PRICE = "Price"  # role: price
DRAWDOWN = "Drawdown (%)"  # role: extra
ZERO = "Zero"  # role: extra

# Data: synthetic portfolio with realistic drawdown patterns including one full recovery
np.random.seed(42)
n_days = 500
dates = pd.date_range(start="2022-01-01", periods=n_days, freq="D")

returns = np.random.normal(0.0008, 0.009, n_days)
# First moderate drawdown
returns[40:80] = np.random.normal(-0.004, 0.010, 40)
# Strong recovery to new all-time high
returns[80:160] = np.random.normal(0.005, 0.008, 80)
# Second major drawdown: becomes the maximum drawdown
returns[180:250] = np.random.normal(-0.007, 0.015, 70)
# Partial recovery that does not reach a new high
returns[250:350] = np.random.normal(0.002, 0.012, 100)
# Secondary dip
returns[350:420] = np.random.normal(-0.003, 0.012, 70)
# Slow tail
returns[420:500] = np.random.normal(0.001, 0.010, 80)

df = pd.DataFrame({DATE: dates, PRICE: 100 * np.cumprod(1 + returns)})

# Plot: derived series and statistics
df[DRAWDOWN] = (df[PRICE] - df[PRICE].cummax()) / df[PRICE].cummax() * 100
df[ZERO] = 0.0

max_dd_df = df.loc[[df[DRAWDOWN].idxmin()]]
max_drawdown = max_dd_df[DRAWDOWN].iloc[0]
max_dd_date = max_dd_df[DATE].iloc[0]

# Longest stretch spent more than 0.5% below the running maximum
in_dd = df[DRAWDOWN] < -0.5
stretch = (in_dd != in_dd.shift()).cumsum()
max_duration = int(in_dd.groupby(stretch).sum().max())

# Recovery points: first new high after a drawdown episode deeper than 5%
episode_open = df[DRAWDOWN] < 0
episode = (episode_open != episode_open.shift()).cumsum()
episode_depth = df[DRAWDOWN].groupby(episode).transform("min")
recovered = ~episode_open & episode_open.shift(fill_value=False) & (episode_depth.shift(fill_value=0.0) < -5)
recovery_df = df[recovered]

# Recovery time of the maximum drawdown: trough to the next new high
after_trough = df[(df[DATE] > max_dd_date) & (df[DRAWDOWN] >= 0)]
if len(after_trough) > 0:
    recovery_text = f"{(after_trough[DATE].iloc[0] - max_dd_date).days} days"
else:
    recovery_text = "not yet reached"

stats_label = (
    f"Max Drawdown: {max_drawdown:.1f}%  |  Max Duration: {max_duration} days  |  Recovery Time: {recovery_text}"
)

# Axis breaks every 5 points, from the data's depth up to zero
y_floor = int(np.floor(max_drawdown / 5) * 5) - 5
y_breaks = list(range(y_floor, 5, 5))

plot = (
    ggplot(df, aes(x=DATE, y=DRAWDOWN))
    + geom_ribbon(aes(ymin=DRAWDOWN, ymax=ZERO), fill=DRAWDOWN_COLOR, alpha=RIBBON_ALPHA)
    + geom_line(color=DRAWDOWN_COLOR, size=1.0)
    + geom_hline(yintercept=0, linetype="dashed", color=INK_SOFT, size=0.7)
    + geom_point(
        aes(x=DATE, y=DRAWDOWN), data=max_dd_df, color=PAGE_BG, fill=DRAWDOWN_COLOR, size=6, shape="o", stroke=1.5
    )
    + annotate(
        geom="text",
        x=max_dd_date - pd.Timedelta(days=14),
        y=max_drawdown - 1.0,
        label=f"Max Drawdown: {max_drawdown:.1f}%",
        size=9,
        color=INK,
        ha="right",
    )
    + labs(x=DATE, y=DRAWDOWN, title="drawdown-basic · python · plotnine · anyplot.ai", caption=stats_label)
    + scale_x_datetime(date_breaks="3 months", date_labels="%b %Y")
    + scale_y_continuous(breaks=y_breaks)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(angle=45, ha="right", color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        plot_caption=element_text(size=7, color=INK_MUTED),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        axis_line=element_line(color=INK_SOFT),
    )
)

# Mark recovery points (new highs after a drawdown) with green diamonds
if len(recovery_df) > 0:
    plot = plot + geom_point(
        aes(x=DATE, y=ZERO), data=recovery_df, color=PAGE_BG, fill=RECOVERY_COLOR, size=5, shape="D", stroke=1.0
    )

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
