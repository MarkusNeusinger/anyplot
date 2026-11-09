"""anyplot.ai
horizon-basic: Horizon Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-07
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
    facet_grid,
    geom_area,
    ggplot,
    labs,
    scale_fill_manual,
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

# Imprint palette; the horizon bands use the imprint_div poles (warm = matte red, cold = blue)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
WARM = IMPRINT_PALETTE[4]
COLD = IMPRINT_PALETTE[2]

# Constants
N_BANDS = 3  # equal-range bands per sign
BAND_STRENGTH = [0.4, 0.7, 1.0]  # share of the pole color per band, palest first
BAND_QUANTILE = 0.98  # the bands span this quantile of |value|; rarer peaks are cut flat in the top band

# Columns: set these to your table's column names
TIME = "Time"  # role: date
ANOMALY = "Temperature anomaly (°C)"  # role: value
STATION = "Station"  # role: series

# Data: replace this block with your own table, for example df = pd.read_csv("stations.csv")
np.random.seed(42)
n_points = 168  # one week of hourly readings
station_names = ["Northern Ridge", "Coastal Bay", "Highland Peak", "Valley Floor", "Forest Edge", "Desert Plain"]
hours = np.arange(n_points)
timestamps = pd.date_range("2026-07-06", periods=n_points, freq="h")
frames = []
for i, name in enumerate(station_names):
    daily_cycle = 8 * np.sin(2 * np.pi * hours / 24 + i * np.pi / 6)
    weekly_pattern = 5 * np.sin(2 * np.pi * hours / 168 + i * 0.3)
    noise = np.random.randn(n_points) * 2
    extremes = np.zeros(n_points)
    event_indices = np.random.choice(n_points, size=4, replace=False)
    extremes[event_indices] = np.random.choice([-1, 1], size=4) * np.random.uniform(12, 18, size=4)
    values = daily_cycle + weekly_pattern + noise + extremes
    frames.append(pd.DataFrame({TIME: timestamps, ANOMALY: values, STATION: name}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
band_size = df[ANOMALY].abs().quantile(BAND_QUANTILE) / N_BANDS


def mix(hex_color, share):
    """Blend a pole color into the page background — discrete steps of imprint_div."""
    pole = np.array([int(hex_color[k : k + 2], 16) for k in (1, 3, 5)])
    page = np.array([int(PAGE_BG[k : k + 2], 16) for k in (1, 3, 5)])
    rgb = np.round(page + (pole - page) * share).astype(int)
    return "#{:02X}{:02X}{:02X}".format(*rgb)


bands = []
colors = {}
labels = {}
for sign, pole, prefix in [(1, WARM, "+"), (-1, COLD, "−")]:
    for b in range(N_BANDS):
        key = f"{prefix}{b}"
        colors[key] = mix(pole, BAND_STRENGTH[b])
        low, high = b * band_size, (b + 1) * band_size
        start = f"{prefix}{low:.1f}" if b else "0"
        labels[key] = f"{start} to {prefix}{high:.1f}" if b < N_BANDS - 1 else f"{prefix}{low:.1f} and beyond"
        folded = (df[ANOMALY] * sign).clip(lower=0) - low
        bands.append(df[[TIME, STATION]].assign(height=folded.clip(0, band_size), band=key))

horizon_df = pd.concat(bands, ignore_index=True)
band_order = list(colors)  # pale → dark per sign, so a darker band is drawn over a paler one
horizon_df["band"] = pd.Categorical(horizon_df["band"], categories=band_order, ordered=True)
horizon_df[STATION] = pd.Categorical(horizon_df[STATION], categories=df[STATION].dropna().unique().tolist())
legend_breaks = band_order[N_BANDS - 1 :: -1] + band_order[N_BANDS:]

plot = (
    ggplot(horizon_df, aes(x=TIME, y="height", fill="band"))
    + geom_area(position="identity")
    + facet_grid(f"{STATION} ~ .")
    + scale_fill_manual(values=colors, labels=labels, breaks=legend_breaks)
    + scale_x_datetime(date_breaks="1 day", date_labels="%a %d %b", expand=(0, 0))
    + scale_y_continuous(limits=(0, band_size), expand=(0, 0))
    + labs(title="horizon-basic · python · plotnine · anyplot.ai", x=TIME, y=None, fill=ANOMALY)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=None),
        plot_title=element_text(size=12, weight="bold", color=INK),
        axis_title_x=element_text(size=10, color=INK),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        axis_title_y=element_blank(),
        axis_text_y=element_blank(),
        axis_ticks=element_blank(),
        strip_text_y=element_text(size=8, color=INK, angle=0, ha="left"),
        strip_background=element_blank(),
        panel_spacing_y=0.012,
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
