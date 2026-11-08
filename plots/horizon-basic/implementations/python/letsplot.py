""" anyplot.ai
horizon-basic: Horizon Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 88/100 | Updated: 2026-11-08
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BANDS = 3  # equal-range bands folded on each side of the baseline

# Columns: set these to your table's column names
TIME = "Time"  # role: date
CPU = "CPU deviation from baseline (%)"  # role: value
HOST = "Host"  # role: series

# Data: replace this block with your own table, for example df = pd.read_csv("cpu.csv")
np.random.seed(42)
timestamps = pd.date_range("2026-03-02", periods=168, freq="h")  # one week, hourly
hours = np.arange(len(timestamps))
records = []
for i, host in enumerate(["web-01", "web-02", "api-01", "api-02", "db-primary", "cache-01"]):
    daily = 18 * np.sin(2 * np.pi * hours / 24 + i * np.pi / 3)
    weekly = 10 * np.sin(2 * np.pi * hours / 168 + i * 0.5)
    noise = np.random.randn(len(hours)) * 1.5
    spikes = np.zeros(len(hours))
    spike_idx = np.random.choice(len(hours), size=4, replace=False)
    spikes[spike_idx] = np.random.choice([-1, 1], size=4) * np.random.uniform(12, 20, size=4)
    # Light rolling smoothing so folded bands read as clean intensity mountains
    values = pd.Series(daily + weekly + noise + spikes).rolling(5, center=True, min_periods=1).mean()
    records.append(pd.DataFrame({TIME: timestamps, CPU: values.to_numpy(), HOST: host}))
df = pd.concat(records, ignore_index=True)

# Plot: reads only df and the constants above
# Order rows by descending volatility so the most erratic host leads the grid
series_order = df.groupby(HOST, sort=False)[CPU].std().sort_values(ascending=False).index.tolist()

# Fold values into bands of equal range on both sides of the zero baseline
band_size = df[CPU].abs().max() / N_BANDS
levels = band_size * np.arange(-(N_BANDS - 1), N_BANDS)

# Legend label per sign and band, with the band's value range
signs = {"pos": (1, "+"), "neg": (-1, "−")}
band_labels = {}
for key, (_, mark) in signs.items():
    for band in range(N_BANDS):
        low = f"{mark}{band * band_size:.0f}" if band else "0"
        band_labels[f"{key}{band}"] = f"{low} to {mark}{(band + 1) * band_size:.0f}"

# Fold every series: each band covers the whole span, zero where the band is not
# reached, so no polygon bridges a gap. The exact points where a series crosses
# the baseline or a band edge are added first, so each band starts and ends on its
# edge and every time point shows one sign only.
start = df[TIME].min()
horizon_frames = []
for series in series_order:
    series_data = df[(df[HOST] == series) & df[CPU].notna()].sort_values(TIME)
    t = ((series_data[TIME] - start) / pd.Timedelta(hours=1)).to_numpy(dtype=float)
    v = series_data[CPU].to_numpy(dtype=float)
    crossings = [t]
    for level in levels:
        s = v - level
        k = np.flatnonzero(s[:-1] * s[1:] < 0)
        crossings.append(t[k] + s[k] / (s[k] - s[k + 1]) * (t[k + 1] - t[k]))
    tt = np.unique(np.concatenate(crossings))
    vv = np.interp(tt, t, v)

    for band in range(N_BANDS):
        for key, (sign, _) in signs.items():
            # Values below the baseline are mirrored upward and drawn in the second hue
            folded = np.clip(np.maximum(sign * vv, 0) - band * band_size, 0, band_size)
            horizon_frames.append(
                pd.DataFrame(
                    {
                        TIME: start + pd.to_timedelta(tt, unit="h"),
                        "folded": folded,
                        "deviation": vv,
                        HOST: series,
                        "level": band,
                        "band": band_labels[f"{key}{band}"],
                    }
                )
            )

horizon_df = pd.concat(horizon_frames, ignore_index=True)
horizon_df[HOST] = pd.Categorical(horizon_df[HOST], categories=series_order, ordered=True)

# Band intensity colors: steps of the Imprint diverging ramp (imprint_div),
# blue above the baseline and matte red below, tinted toward white so band
# colors stay theme-independent while a darker fill means a larger magnitude.
above_rgb = tuple(int(IMPRINT[2][i : i + 2], 16) for i in (1, 3, 5))
below_rgb = tuple(int(IMPRINT[4][i : i + 2], 16) for i in (1, 3, 5))

colors = {}
for band_idx in range(N_BANDS):
    frac = (band_idx + 1) / N_BANDS
    pos_rgb = tuple(round(255 + (above_rgb[c] - 255) * frac) for c in range(3))
    neg_rgb = tuple(round(255 + (below_rgb[c] - 255) * frac) for c in range(3))
    colors[band_labels[f"pos{band_idx}"]] = "#{:02X}{:02X}{:02X}".format(*pos_rgb)
    colors[band_labels[f"neg{band_idx}"]] = "#{:02X}{:02X}{:02X}".format(*neg_rgb)

# Legend from the strongest positive band down to the strongest negative one
legend_order = [band_labels[f"pos{b}"] for b in reversed(range(N_BANDS))] + [
    band_labels[f"neg{b}"] for b in range(N_BANDS)
]

# Distinctive lets-plot feature: custom tooltip content (unavailable in plotnine)
horizon_tooltips = (
    layer_tooltips()
    .title(f"@{{{HOST}}}")
    .format("@deviation", ".1f")
    .line("Band (%)|@band")
    .line("Deviation (%)|@deviation")
)

# Create the horizon chart: one opaque layer per band, the lowest band first, so
# a higher band is always drawn over the lower ones in its more intense color
plot = ggplot(horizon_df, aes(x=TIME, y="folded", fill="band", color="band"))
for band in range(N_BANDS):
    plot += geom_area(
        data=horizon_df[horizon_df["level"] == band], position="identity", size=0, tooltips=horizon_tooltips
    )
plot = (
    plot
    + scale_fill_manual(values=colors, breaks=legend_order)
    # Outline in the fill color, so the legend keys match the borderless bands
    + scale_color_manual(values=colors, breaks=legend_order)
    # Stack every series as a single, full-width, thin horizontal strip
    # (one row per series) — the defining "minimize vertical space" trait.
    + facet_grid(y=HOST, y_order=0)
    # Only the meaningful zero baseline is labeled per row — with thin stacked
    # strips, a top+bottom tick on every row would collide with the neighbors.
    + scale_y_continuous(breaks=[0], labels=["0"], limits=[0, band_size])
    + scale_x_datetime(format="%a")
    + labs(
        title="horizon-basic · python · letsplot · anyplot.ai",
        x=TIME,
        y=CPU,
        fill="Deviation band (%)",
        color="Deviation band (%)",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_blank(),
        panel_border=element_blank(),
        panel_grid_major=element_line(color=INK_SOFT, size=0.2),
        panel_grid_minor=element_blank(),
        panel_spacing_y=3,
        strip_spacing_y=3,
        plot_title=element_text(size=20, face="bold", color=INK),
        axis_title=element_text(size=14, color=INK),
        axis_text_x=element_text(size=11, color=INK_SOFT),
        axis_text_y=element_text(size=11, color=INK_SOFT),
        axis_line=element_blank(),
        strip_text=element_text(size=10, face="bold", color=INK),
        legend_position="right",
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        legend_title=element_text(size=12, face="bold", color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_key_size=12,
    )
    + ggsize(800, 450)
)

# Save as PNG (scale 4x for 3200x1800)
ggsave(plot, f"plot-{THEME}.png", scale=4)

# Save as HTML for interactive version
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images subdirectory to current directory
if os.path.exists("lets-plot-images"):
    for filename in [f"plot-{THEME}.png", f"plot-{THEME}.html"]:
        src = os.path.join("lets-plot-images", filename)
        if os.path.exists(src):
            shutil.move(src, filename)
    if not os.listdir("lets-plot-images"):
        shutil.rmtree("lets-plot-images")
