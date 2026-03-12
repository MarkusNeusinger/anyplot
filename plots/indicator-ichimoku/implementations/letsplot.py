""" pyplots.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-12
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()  # noqa: F405

# Data - 200 trading days of simulated stock OHLC with Ichimoku components
np.random.seed(42)
n_days = 200

dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Generate realistic OHLC via random walk
price = 150.0
opens, highs, lows, closes = [], [], [], []
for _ in range(n_days):
    open_price = price
    change = np.random.randn() * 2.5
    close_price = open_price + change
    high_price = max(open_price, close_price) + abs(np.random.randn()) * 1.5
    low_price = min(open_price, close_price) - abs(np.random.randn()) * 1.5
    opens.append(open_price)
    closes.append(close_price)
    highs.append(high_price)
    lows.append(low_price)
    price = close_price

df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes})

# Compute Ichimoku components (9, 26, 52 standard parameters)
high_s = df["high"]
low_s = df["low"]

tenkan_sen = (high_s.rolling(9).max() + low_s.rolling(9).min()) / 2
kijun_sen = (high_s.rolling(26).max() + low_s.rolling(26).min()) / 2
senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
senkou_span_b = ((high_s.rolling(52).max() + low_s.rolling(52).min()) / 2).shift(26)
chikou_span = df["close"].shift(-26)

df["tenkan_sen"] = tenkan_sen
df["kijun_sen"] = kijun_sen
df["senkou_span_a"] = senkou_span_a
df["senkou_span_b"] = senkou_span_b
df["chikou_span"] = chikou_span

# Use numeric x-axis for clean positioning
df["x"] = range(len(df))

# Candlestick columns
df["direction"] = np.where(df["close"] >= df["open"], "Bullish", "Bearish")
df["body_low"] = df[["open", "close"]].min(axis=1)
df["body_high"] = df[["open", "close"]].max(axis=1)
df["xmin"] = df["x"] - 0.35
df["xmax"] = df["x"] + 0.35

# Trim to visible range (skip first 52 rows for lookback, keep rest)
visible_start = 52
df_visible = df.iloc[visible_start:].copy()

# Cloud data - split into bullish and bearish segments for fill coloring
df_cloud = df_visible.dropna(subset=["senkou_span_a", "senkou_span_b"]).copy()
df_cloud_bull = df_cloud[df_cloud["senkou_span_a"] >= df_cloud["senkou_span_b"]].copy()
df_cloud_bear = df_cloud[df_cloud["senkou_span_a"] < df_cloud["senkou_span_b"]].copy()

# Lines data
df_tenkan = df_visible.dropna(subset=["tenkan_sen"]).copy()
df_kijun = df_visible.dropna(subset=["kijun_sen"]).copy()
df_chikou = df_visible.dropna(subset=["chikou_span"]).copy()


# Colors - colorblind-safe palette (teal/amber instead of pure red/green)
bull_color = "#0077BB"  # Blue for bullish candles (colorblind-safe)
bear_color = "#CC6633"  # Orange for bearish candles (colorblind-safe)
tenkan_color = "#306998"
kijun_color = "#B5446E"
chikou_color = "#7B8794"
cloud_bull_color = "#0077BB"
cloud_bear_color = "#CC6633"

# X-axis tick positions (every 20 trading days from visible start)
tick_pos = list(range(visible_start, len(df), 20))
tick_labels = [dates[i].strftime("%b %d") for i in tick_pos if i < len(dates)]
tick_pos = tick_pos[: len(tick_labels)]

# Tooltip for candlesticks with rich formatting
df_visible["date_str"] = df_visible["date"].dt.strftime("%b %d, %Y")

# Identify key Ichimoku signals for visual emphasis
# Find Tenkan/Kijun crossover points
df_visible["tk_cross"] = (df_visible["tenkan_sen"] > df_visible["kijun_sen"]) != (
    df_visible["tenkan_sen"].shift(1) > df_visible["kijun_sen"].shift(1)
)
df_crossovers = df_visible[df_visible["tk_cross"] & df_visible["tenkan_sen"].notna()].copy()
df_visible["change"] = df_visible["close"] - df_visible["open"]
df_visible["change_pct"] = ((df_visible["close"] - df_visible["open"]) / df_visible["open"] * 100).round(2)
tip_fmt = (
    layer_tooltips()  # noqa: F405
    .title("@date_str")
    .line("Open|$@{open}")
    .line("High|$@{high}")
    .line("Low|$@{low}")
    .line("Close|$@{close}")
    .line("Change|@{change_pct}%")
    .format("open", ".2f")
    .format("high", ".2f")
    .format("low", ".2f")
    .format("close", ".2f")
)

# Tooltip for indicator lines
tenkan_tip = (
    layer_tooltips()  # noqa: F405
    .title("Tenkan-sen")
    .line("Value|$@{tenkan_sen}")
    .format("tenkan_sen", ".2f")
)
kijun_tip = (
    layer_tooltips()  # noqa: F405
    .title("Kijun-sen")
    .line("Value|$@{kijun_sen}")
    .format("kijun_sen", ".2f")
)

# Plot
plot = (
    ggplot()  # noqa: F405
    # Kumo cloud - bullish (green/blue fill)
    + geom_ribbon(  # noqa: F405
        aes(x="x", ymin="senkou_span_b", ymax="senkou_span_a"),  # noqa: F405
        data=df_cloud_bull,
        fill=cloud_bull_color,
        alpha=0.2,
        tooltips="none",
    )
    # Kumo cloud - bearish (red/orange fill)
    + geom_ribbon(  # noqa: F405
        aes(x="x", ymin="senkou_span_a", ymax="senkou_span_b"),  # noqa: F405
        data=df_cloud_bear,
        fill=cloud_bear_color,
        alpha=0.2,
        tooltips="none",
    )
    # Senkou Span A line
    + geom_line(  # noqa: F405
        aes(x="x", y="senkou_span_a"),  # noqa: F405
        data=df_cloud,
        color=cloud_bull_color,
        size=0.6,
        alpha=0.5,
        tooltips="none",
    )
    # Senkou Span B line
    + geom_line(  # noqa: F405
        aes(x="x", y="senkou_span_b"),  # noqa: F405
        data=df_cloud,
        color=cloud_bear_color,
        size=0.6,
        alpha=0.5,
        tooltips="none",
    )
    # Candlestick wicks
    + geom_segment(  # noqa: F405
        aes(x="x", xend="x", y="low", yend="high", color="direction"),  # noqa: F405
        data=df_visible,
        size=0.7,
        tooltips=tip_fmt,
    )
    # Candlestick bodies
    + geom_rect(  # noqa: F405
        aes(  # noqa: F405
            xmin="xmin", xmax="xmax", ymin="body_low", ymax="body_high", fill="direction", color="direction"
        ),
        data=df_visible,
        size=0.4,
        tooltips=tip_fmt,
    )
    # Tenkan-sen (conversion line) with legend key
    + geom_line(  # noqa: F405
        aes(x="x", y="tenkan_sen"),  # noqa: F405
        data=df_tenkan,
        color=tenkan_color,
        size=1.2,
        tooltips=tenkan_tip,
        manual_key=layer_key("Tenkan-sen"),  # noqa: F405
    )
    # Kijun-sen (base line) with legend key
    + geom_line(  # noqa: F405
        aes(x="x", y="kijun_sen"),  # noqa: F405
        data=df_kijun,
        color=kijun_color,
        size=1.2,
        tooltips=kijun_tip,
        manual_key=layer_key("Kijun-sen"),  # noqa: F405
    )
    # Chikou Span (lagging line) with legend key
    + geom_line(  # noqa: F405
        aes(x="x", y="chikou_span"),  # noqa: F405
        data=df_chikou,
        color=chikou_color,
        size=0.9,
        alpha=0.6,
        linetype="dashed",
        tooltips="none",
        manual_key=layer_key("Chikou Span"),  # noqa: F405
    )
    # Crossover signal markers
    + geom_point(  # noqa: F405
        aes(x="x", y="tenkan_sen"),  # noqa: F405
        data=df_crossovers,
        color="#FFD700",
        fill="#FFD700",
        size=5,
        shape=23,
        stroke=1.5,
        tooltips=layer_tooltips().title("TK Crossover").line("@date_str"),  # noqa: F405
        manual_key=layer_key("TK Crossover"),  # noqa: F405
    )
    # Scales
    + scale_fill_manual(  # noqa: F405
        values={"Bullish": bull_color, "Bearish": bear_color}
    )
    + scale_color_manual(  # noqa: F405
        values={"Bullish": bull_color, "Bearish": bear_color}
    )
    + scale_x_continuous(breaks=tick_pos, labels=tick_labels, expand=[0.02, 0])  # noqa: F405
    + labs(  # noqa: F405
        x="Trading Day (2024)",
        y="Price ($)",
        title="indicator-ichimoku \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle=(
            "Ichimoku Kinko Hyo \u2014 Cloud shifts from bullish (blue) to bearish (orange) as trend reverses mid-year"
        ),
    )
    + guides(fill="none", color="none")  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20, color="#333333"),  # noqa: F405
        axis_text=element_text(size=16, color="#555555"),  # noqa: F405
        plot_title=element_text(size=24, color="#1a1a1a", face="bold"),  # noqa: F405
        plot_subtitle=element_text(size=16, color="#666666", face="italic"),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color="#e0e0e0", size=0.4),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
        plot_background=element_rect(fill="white", color="white"),  # noqa: F405
        legend_position=[0.88, 0.95],
        legend_justification=[0.5, 1.0],
        legend_title=element_text(size=15, face="bold", color="#333333"),  # noqa: F405
        legend_text=element_text(size=13, color="#555555"),  # noqa: F405
        legend_background=element_rect(fill="white", color="#cccccc", size=0.5),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)  # noqa: F405
ggsave(plot, "plot.html", path=".")  # noqa: F405
