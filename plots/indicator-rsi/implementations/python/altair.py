""" anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-16
"""

import os
import sys
from importlib.machinery import SourceFileLoader

import numpy as np
import pandas as pd


venv_path = sys.executable
site_packages = os.path.join(os.path.dirname(venv_path), "..", "lib", "python3.13", "site-packages")
altair_init = os.path.join(site_packages, "altair", "__init__.py")

loader = SourceFileLoader("altair", altair_init)
alt = loader.load_module()


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

np.random.seed(42)
n_periods = 140
dates = pd.date_range(start="2024-01-01", periods=n_periods, freq="D")

price_changes = np.random.randn(n_periods) * 4

lookback = 14
gains = np.zeros(n_periods)
losses = np.zeros(n_periods)

for i in range(1, n_periods):
    change = price_changes[i]
    if change > 0:
        gains[i] = change
    else:
        losses[i] = abs(change)

avg_gain = np.zeros(n_periods)
avg_loss = np.zeros(n_periods)
avg_gain[lookback] = np.mean(gains[1 : lookback + 1])
avg_loss[lookback] = np.mean(losses[1 : lookback + 1])

for i in range(lookback + 1, n_periods):
    avg_gain[i] = (avg_gain[i - 1] * (lookback - 1) + gains[i]) / lookback
    avg_loss[i] = (avg_loss[i - 1] * (lookback - 1) + losses[i]) / lookback

with np.errstate(divide="ignore", invalid="ignore"):
    rs = np.where(avg_loss != 0, avg_gain / avg_loss, 0)
    rsi = np.where(avg_loss != 0, 100 - (100 / (1 + rs)), 100)
rsi[:lookback] = 50

df = pd.DataFrame({"date": dates, "rsi": rsi})

overbought_df = pd.DataFrame({"y": [70], "y2": [100]})
oversold_df = pd.DataFrame({"y": [0], "y2": [30]})

overbought_zone = (
    alt.Chart(overbought_df)
    .mark_rect(opacity=0.12, color="#E74C3C")
    .encode(y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 100])), y2=alt.Y2("y2:Q"))
)

oversold_zone = (
    alt.Chart(oversold_df)
    .mark_rect(opacity=0.12, color="#27AE60")
    .encode(y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 100])), y2=alt.Y2("y2:Q"))
)

threshold_df = pd.DataFrame({"y": [30, 50, 70], "label": ["Oversold (30)", "Neutral (50)", "Overbought (70)"]})

threshold_lines = (
    alt.Chart(threshold_df)
    .mark_rule(strokeDash=[8, 4], strokeWidth=2)
    .encode(
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color(
            "label:N",
            scale=alt.Scale(
                domain=["Oversold (30)", "Neutral (50)", "Overbought (70)"], range=["#27AE60", INK_SOFT, "#E74C3C"]
            ),
            legend=alt.Legend(
                title="Thresholds",
                orient="bottom-left",
                titleFontSize=16,
                labelFontSize=14,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
            ),
        ),
    )
)

rsi_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=3, color="#4467A3")
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y")),
        y=alt.Y("rsi:Q", title="RSI Value", scale=alt.Scale(domain=[0, 100])),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("rsi:Q", title="RSI", format=".1f"),
        ],
    )
)

chart = (
    alt.layer(overbought_zone, oversold_zone, threshold_lines, rsi_line)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "indicator-rsi · altair · anyplot.ai",
            fontSize=28,
            anchor="middle",
            subtitle="14-Period RSI with Overbought/Oversold Zones",
            subtitleFontSize=18,
        ),
        background=PAGE_BG,
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        gridOpacity=0.10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
