"""anyplot.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Updated: 2026-05-23
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
    geom_label,
    geom_line,
    geom_point,
    geom_vline,
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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # anyplot palette 1 — data lines
ACCENT = "#B71D27"  # anyplot palette 3 — crosshair marker

# Data — seasonal stock: trend + annual cycle + quarterly earnings ripple + mild noise
np.random.seed(42)
n_points = 200
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

t = np.arange(n_points) / n_points
annual_cycle = 8 * np.sin(2 * np.pi * t - np.pi / 2)  # Q2 trough, Q4 peak
quarterly_cycle = 3 * np.sin(8 * np.pi * t)  # earnings-season ripples
trend = 20 * t
noise = np.random.normal(0, 0.4, n_points).cumsum()
price = 100 + trend + annual_cycle + quarterly_cycle + noise

earnings_effect = 0.5 * np.abs(np.sin(4 * np.pi * t))
vol_noise = np.abs(np.random.normal(0, 0.15, n_points))
volume = 1.0 + earnings_effect + vol_noise  # millions

momentum = np.zeros(n_points)
momentum[14:] = price[14:] - price[:-14]
rsi = 50 + 30 * np.tanh(momentum / (2 * momentum.std() + 1e-8))
rsi = np.clip(rsi, 10, 90)

metric_order = pd.CategoricalDtype(categories=["Price ($)", "Volume (M)", "RSI"], ordered=True)

df = pd.DataFrame(
    {
        "date": np.tile(dates, 3),
        "value": np.concatenate([price, volume, rsi]),
        "metric": ["Price ($)"] * n_points + ["Volume (M)"] * n_points + ["RSI"] * n_points,
    }
)
df["metric"] = df["metric"].astype(metric_order)

# Crosshair at a local seasonal inflection point
crosshair_idx = 100
crosshair_date = dates[crosshair_idx]

annotation_df = pd.DataFrame(
    {
        "date": [crosshair_date] * 3,
        "value": [price[crosshair_idx], volume[crosshair_idx], rsi[crosshair_idx]],
        "metric": ["Price ($)", "Volume (M)", "RSI"],
    }
)
annotation_df["metric"] = annotation_df["metric"].astype(metric_order)

label_df = pd.DataFrame(
    {
        "date": [crosshair_date] * 3,
        "value": [price[crosshair_idx] * 1.05, volume[crosshair_idx] + 0.35, rsi[crosshair_idx] + 5],
        "metric": ["Price ($)", "Volume (M)", "RSI"],
        "label_text": [
            f"${price[crosshair_idx]:.2f}",
            f"{volume[crosshair_idx]:.2f}M",
            f"RSI: {rsi[crosshair_idx]:.1f}",
        ],
    }
)
label_df["metric"] = label_df["metric"].astype(metric_order)

# Plot
plot = (
    ggplot(df, aes(x="date", y="value"))
    + geom_line(color=BRAND, size=1.0, alpha=0.9)
    + geom_vline(xintercept=crosshair_date, color=ACCENT, size=0.8, linetype="dashed")
    + geom_point(data=annotation_df, mapping=aes(x="date", y="value"), color=ACCENT, size=3.0)
    + geom_label(
        data=label_df, mapping=aes(x="date", y="value", label="label_text"), color=ACCENT, fill=ELEVATED_BG, size=8
    )
    + facet_wrap("~metric", ncol=1, scales="free_y")
    + scale_x_datetime(date_breaks="1 month", date_labels="%b %Y")
    + scale_y_continuous()
    + labs(title="dashboard-synchronized-crosshair · python · plotnine · anyplot.ai", x="Date", y="")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=12, weight="bold", ha="center", color=INK),
        axis_title_x=element_text(size=10, color=INK),
        axis_title_y=element_blank(),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(angle=45, ha="right"),
        strip_text=element_text(size=10, weight="bold", color=INK),
        strip_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        panel_spacing=0.15,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
