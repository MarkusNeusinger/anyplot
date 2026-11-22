"""anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close Price"  # role: close
EMA_SHORT = "EMA 12"  # role: ema_short
EMA_LONG = "EMA 26"  # role: ema_long

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
rng = np.random.default_rng(42)
returns = rng.normal(0.001, 0.015, 120)
close = 100 * np.cumprod(1 + returns)
df = pd.DataFrame({DATE: pd.date_range("2024-01-02", periods=120, freq="B"), CLOSE: close})
df[EMA_SHORT] = df[CLOSE].ewm(span=12, adjust=False).mean()
df[EMA_LONG] = df[CLOSE].ewm(span=26, adjust=False).mean()

# Plot: reads only df and the constants above
series = [CLOSE, EMA_SHORT, EMA_LONG]
colors = dict(zip(series, IMPRINT_PALETTE, strict=False))
long_df = df.melt(id_vars=DATE, value_vars=series, var_name="Series", value_name="Price (USD)")
long_df["Series"] = pd.Categorical(long_df["Series"], categories=series, ordered=True)

# Crossovers of the short EMA over/under the long EMA, found from the sign of their gap
gap = (df[EMA_SHORT] - df[EMA_LONG]).to_numpy()
flips = np.where(np.diff(np.sign(gap)) != 0)[0] + 1
bullish = df.iloc[[i for i in flips if gap[i] > 0]][[DATE]]
bearish = df.iloc[[i for i in flips if gap[i] < 0]][[DATE]]

anyplot_theme = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
    panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
    panel_grid_major_y=element_line(color=RULE, size=0.4),  # noqa: F405
    panel_grid_major_x=element_blank(),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
    axis_title=element_text(size=12, color=INK),  # noqa: F405
    axis_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
    axis_line=element_line(color=INK_SOFT),  # noqa: F405
    plot_title=element_text(size=16, color=INK),  # noqa: F405
    plot_subtitle=element_text(size=11, color=INK_SOFT),  # noqa: F405
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
    legend_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
    legend_title=element_text(size=11, color=INK),  # noqa: F405
    legend_position="right",
)

plot = (
    ggplot(long_df, aes(x=DATE, y="Price (USD)", color="Series"))  # noqa: F405
    + geom_vline(  # noqa: F405
        aes(xintercept=DATE),  # noqa: F405
        data=bullish,
        inherit_aes=False,
        color=IMPRINT_PALETTE[0],
        linetype="dashed",
        size=0.5,
        alpha=0.5,
    )
    + geom_vline(  # noqa: F405
        aes(xintercept=DATE),  # noqa: F405
        data=bearish,
        inherit_aes=False,
        color=IMPRINT_PALETTE[4],
        linetype="dashed",
        size=0.5,
        alpha=0.5,
    )
    + geom_line(  # noqa: F405
        data=long_df[long_df["Series"] == CLOSE],
        size=1.2,
        alpha=0.9,
        tooltips=layer_tooltips().title("@Series").line("$@{Price (USD)}"),  # noqa: F405
    )
    + geom_line(  # noqa: F405
        data=long_df[long_df["Series"] != CLOSE],
        size=0.8,
        tooltips=layer_tooltips().title("@Series").line("$@{Price (USD)}"),  # noqa: F405
    )
    + scale_color_manual(values=colors, name="Series")  # noqa: F405
    + scale_x_datetime(format="%b %d")  # noqa: F405
    + labs(  # noqa: F405
        x=DATE,
        y="Price (USD)",
        title="indicator-ema · python · letsplot · anyplot.ai",
        subtitle="Dashed lines mark EMA crossovers: green bullish (short crosses above), red bearish (short crosses below)",
    )
    + theme_minimal()  # noqa: F405
    + anyplot_theme
    + ggsize(800, 450)  # noqa: F405
)

# Save
export_ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
export_ggsave(plot, f"plot-{THEME}.html", path=".")
