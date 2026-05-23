""" anyplot.ai
drawdown-basic: Drawdown Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-23
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

DRAWDOWN_COLOR = "#B71D27"  # anyplot red — semantic: losses / drawdown
RECOVERY_COLOR = "#009E73"  # anyplot green — semantic: recovery / new high

# Data — synthetic portfolio with realistic drawdown patterns
np.random.seed(42)
n_days = 500
dates = pd.date_range(start="2022-01-01", periods=n_days, freq="D")

returns = np.random.normal(0.0005, 0.011, n_days)
returns[60:85] = np.random.normal(-0.004, 0.015, 25)
returns[180:230] = np.random.normal(-0.006, 0.016, 50)
returns[230:300] = np.random.normal(0.002, 0.012, 70)
returns[300:320] = np.random.normal(-0.003, 0.012, 20)
returns[400:500] = np.random.normal(0.001, 0.010, 100)

price = 100 * np.cumprod(1 + returns)

df = pd.DataFrame({"date": dates, "price": price})
df["running_max"] = df["price"].cummax()
df["drawdown"] = (df["price"] - df["running_max"]) / df["running_max"] * 100
df["zero"] = 0.0

# Maximum drawdown statistics
max_dd_idx = df["drawdown"].idxmin()
max_dd_value = df.loc[max_dd_idx, "drawdown"]
max_dd_date = df.loc[max_dd_idx, "date"]
max_drawdown = df["drawdown"].min()

# Max drawdown duration
df["in_drawdown"] = df["drawdown"] < -0.5
drawdown_groups = (df["in_drawdown"] != df["in_drawdown"].shift()).cumsum()
drawdown_durations = df[df["in_drawdown"]].groupby(drawdown_groups).size()
max_duration = int(drawdown_durations.max()) if len(drawdown_durations) > 0 else 0

# Recovery points: where drawdown transitions back to 0 (new all-time highs)
prev_drawdown = df["drawdown"].shift(1, fill_value=0.0)
recovery_mask = (df["drawdown"] >= -0.01) & (prev_drawdown < -1.0)
recovery_df = df[recovery_mask].copy()

# Single-row DataFrame for max drawdown marker
max_dd_df = df.iloc[[max_dd_idx]].copy()

stats_label = f"Max Drawdown: {max_drawdown:.1f}%  |  Max Duration: {max_duration} days"

# Plot
plot = (
    ggplot(df, aes(x="date", y="drawdown"))
    + geom_ribbon(aes(ymin="drawdown", ymax="zero"), fill=DRAWDOWN_COLOR, alpha=0.30)
    + geom_line(color=DRAWDOWN_COLOR, size=1.0)
    + geom_hline(yintercept=0, linetype="dashed", color=INK_SOFT, size=0.7)
    + geom_point(
        aes(x="date", y="drawdown"), data=max_dd_df, color=PAGE_BG, fill=DRAWDOWN_COLOR, size=6, shape="o", stroke=1.5
    )
    + annotate(
        geom="text",
        x=max_dd_date + pd.Timedelta(days=22),
        y=max_dd_value + 4,
        label=f"Max Drawdown: {max_drawdown:.1f}%",
        size=9,
        color=INK,
        ha="left",
    )
    + labs(x="Date", y="Drawdown (%)", title="drawdown-basic · python · plotnine · anyplot.ai", caption=stats_label)
    + scale_x_datetime(date_breaks="3 months", date_labels="%b %Y")
    + scale_y_continuous(breaks=list(range(-50, 5, 5)))
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

# Mark recovery points (new all-time highs after drawdown) with green diamonds
if len(recovery_df) > 0:
    plot = plot + geom_point(
        aes(x="date", y="zero"), data=recovery_df, color=PAGE_BG, fill=RECOVERY_COLOR, size=5, shape="D", stroke=1.0
    )

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
