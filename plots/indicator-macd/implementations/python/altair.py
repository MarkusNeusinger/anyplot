""" pyplots.ai
indicator-macd: MACD Technical Indicator Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate realistic stock price data and calculate MACD
np.random.seed(42)
n_days = 150

# Generate a random walk with trend for closing prices
returns = np.random.normal(0.0005, 0.02, n_days)
price = 100 * np.cumprod(1 + returns)


# Calculate EMAs using pandas
ema_12 = pd.Series(price).ewm(span=12, adjust=False).mean().values
ema_26 = pd.Series(price).ewm(span=26, adjust=False).mean().values
macd_line = ema_12 - ema_26
signal_line = pd.Series(macd_line).ewm(span=9, adjust=False).mean().values
histogram = macd_line - signal_line

# Create DataFrame with dates (skip first 26 days for meaningful MACD values)
start_idx = 26
dates = pd.date_range("2025-06-01", periods=n_days - start_idx, freq="D")

df = pd.DataFrame(
    {
        "date": dates,
        "macd": macd_line[start_idx:],
        "signal": signal_line[start_idx:],
        "histogram": histogram[start_idx:],
    }
)

# Add color column for histogram
df["hist_color"] = df["histogram"].apply(lambda x: "Positive" if x >= 0 else "Negative")

# Melt dataframe for line chart
df_lines = df.melt(id_vars=["date"], value_vars=["macd", "signal"], var_name="line_type", value_name="value")

# Map line types to labels
line_labels = {"macd": "MACD (12, 26)", "signal": "Signal (9)"}
df_lines["line_label"] = df_lines["line_type"].map(line_labels)

# Create histogram chart with green/red coloring
histogram_chart = (
    alt.Chart(df)
    .mark_bar(size=8)
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(labelFontSize=16, titleFontSize=20)),
        y=alt.Y("histogram:Q", title="Histogram", axis=alt.Axis(labelFontSize=16, titleFontSize=20)),
        color=alt.Color(
            "hist_color:N",
            scale=alt.Scale(domain=["Positive", "Negative"], range=["#2E7D32", "#C62828"]),
            legend=alt.Legend(title="Histogram", labelFontSize=14, titleFontSize=16),
        ),
        tooltip=[alt.Tooltip("date:T", title="Date"), alt.Tooltip("histogram:Q", title="Histogram", format=".4f")],
    )
)

# Create MACD and Signal line chart
line_chart = (
    alt.Chart(df_lines)
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("value:Q", title="MACD Value"),
        color=alt.Color(
            "line_label:N",
            scale=alt.Scale(domain=["MACD (12, 26)", "Signal (9)"], range=["#306998", "#FFD43B"]),
            legend=alt.Legend(title="Lines", labelFontSize=14, titleFontSize=16),
        ),
        strokeDash=alt.StrokeDash(
            "line_label:N", scale=alt.Scale(domain=["MACD (12, 26)", "Signal (9)"], range=[[0], [8, 4]]), legend=None
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date"),
            alt.Tooltip("line_label:N", title="Line"),
            alt.Tooltip("value:Q", title="Value", format=".4f"),
        ],
    )
)

# Create zero reference line
zero_line = (
    alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#666666", strokeWidth=1.5, strokeDash=[4, 4]).encode(y="y:Q")
)

# Combine charts: histogram + lines + zero line
chart = (
    alt.layer(histogram_chart, line_chart, zero_line)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "indicator-macd · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            subtitle="MACD (12, 26, 9) - Moving Average Convergence Divergence",
            subtitleFontSize=18,
            subtitleColor="#666666",
        ),
    )
    .configure_axis(labelFontSize=16, titleFontSize=20, gridColor="#E0E0E0", gridOpacity=0.5)
    .configure_view(strokeWidth=0)
    .configure_legend(labelFontSize=14, titleFontSize=16, orient="right")
    .resolve_scale(color="independent")
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
