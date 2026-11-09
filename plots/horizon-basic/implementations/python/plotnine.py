"""anyplot.ai
horizon-basic: Horizon Chart
Library: plotnine 0.15.8 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
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
    synoptic = 3 * np.sin(2 * np.pi * hours / 168 * 1.5 + i * 0.9)  # passing warm and cold air masses
    drift = np.zeros(n_points)
    for h in hours[1:]:
        drift[h] = 0.85 * drift[h - 1] + np.random.randn() * 0.6  # hour-to-hour persistence
    events = np.zeros(n_points)
    for _ in range(3):  # heat or cold spells lasting several hours
        center, width = np.random.uniform(10, n_points - 10), np.random.uniform(4, 9)
        events += np.random.choice([-1, 1]) * np.random.uniform(4, 8) * np.exp(-0.5 * ((hours - center) / width) ** 2)
    values = synoptic + drift + events
    frames.append(pd.DataFrame({TIME: timestamps, ANOMALY: values, STATION: name}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
band_size = df[ANOMALY].abs().quantile(BAND_QUANTILE) / N_BANDS
page_rgb = np.array([int(PAGE_BG[k : k + 2], 16) for k in (1, 3, 5)])

bands = []
colors = {}
labels = {}
for sign, pole, prefix in [(1, WARM, "+"), (-1, COLD, "−")]:
    pole_rgb = np.array([int(pole[k : k + 2], 16) for k in (1, 3, 5)])
    for b in range(N_BANDS):
        key = f"{prefix}{b}"
        # discrete imprint_div steps: the pole blended into the page color
        rgb = np.round(page_rgb + (pole_rgb - page_rgb) * BAND_STRENGTH[b]).astype(int)
        colors[key] = "#{:02X}{:02X}{:02X}".format(*rgb)
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
        legend_margin=8,
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
