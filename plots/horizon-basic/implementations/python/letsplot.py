""" anyplot.ai
horizon-basic: Horizon Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-08
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

# Imprint palette (first series ALWAYS #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data - Server metrics over 7 days for multiple servers
np.random.seed(42)

n_points = 168  # 7 days of hourly data
n_series = 6
series_names = ["Server A", "Server B", "Server C", "Server D", "Server E", "Server F"]

# Create time series data
hours = np.arange(n_points)

# Generate realistic CPU usage deviation data with different patterns per server
data_records = []
for i, name in enumerate(series_names):
    # Base sinusoidal pattern with phase shift per server (daily cycle)
    base = 18 * np.sin(2 * np.pi * hours / 24 + i * np.pi / 3)
    # Add weekly pattern
    weekly = 10 * np.sin(2 * np.pi * hours / 168 + i * 0.5)
    # Add noise
    noise = np.random.randn(n_points) * 1.5
    # Add occasional spikes
    spikes = np.zeros(n_points)
    spike_indices = np.random.choice(n_points, size=4, replace=False)
    spikes[spike_indices] = np.random.choice([-1, 1], size=4) * np.random.uniform(12, 20, size=4)
    raw = base + weekly + noise + spikes
    # Light rolling smoothing so folded bands read as clean intensity
    # mountains instead of a jagged sawtooth
    values = pd.Series(raw).rolling(window=5, center=True, min_periods=1).mean().to_numpy()

    for h, val in zip(hours, values, strict=True):
        data_records.append({"hour": h, "value": val, "series": name})

df = pd.DataFrame(data_records)

# Order facets by descending volatility so the most erratic server leads the grid
series_order = df.groupby("series")["value"].std().sort_values(ascending=False).index.tolist()

# Horizon chart parameters - fold values into bands of equal range
n_bands = 3
max_val = df["value"].abs().max()
band_size = max_val / n_bands
# Band edges on both sides of the zero baseline
levels = band_size * np.arange(-(n_bands - 1), n_bands)

# Legend label per sign and band, with the band's value range
signs = {"pos": (1, "+"), "neg": (-1, "−")}
band_labels = {}
for key, (_, mark) in signs.items():
    for band in range(n_bands):
        low = f"{mark}{band * band_size:.0f}" if band else "0"
        band_labels[f"{key}{band}"] = f"{low} to {mark}{(band + 1) * band_size:.0f}"

# Fold every series: each band covers the whole week, zero where the band is not
# reached, so no polygon bridges a gap. The exact points where a series crosses
# the baseline or a band edge are added first, so each band starts and ends on its
# edge and every hour shows one sign only.
horizon_frames = []
for series in series_order:
    series_data = df[df["series"] == series].sort_values("hour")
    t = series_data["hour"].to_numpy(dtype=float)
    v = series_data["value"].to_numpy()
    crossings = [t]
    for level in levels:
        s = v - level
        k = np.flatnonzero(s[:-1] * s[1:] < 0)
        crossings.append(t[k] + s[k] / (s[k] - s[k + 1]) * (t[k + 1] - t[k]))
    tt = np.unique(np.concatenate(crossings))
    vv = np.interp(tt, t, v)

    for band in range(n_bands):
        for key, (sign, _) in signs.items():
            # Values below the baseline are mirrored upward and drawn in the second hue
            folded = np.clip(np.maximum(sign * vv, 0) - band * band_size, 0, band_size)
            horizon_frames.append(
                pd.DataFrame(
                    {
                        "hour": tt,
                        "value": folded,
                        "deviation": vv,
                        "series": series,
                        "level": band,
                        "band": band_labels[f"{key}{band}"],
                    }
                )
            )

horizon_df = pd.concat(horizon_frames, ignore_index=True)
horizon_df["series"] = pd.Categorical(horizon_df["series"], categories=series_order, ordered=True)

# Band intensity colors: tints interpolated from the Imprint semantic anchors
# (brand green = positive/gain, brand blue = negative/loss) toward white, so
# band colors stay theme-independent while intensity still reads clearly.
# Blue is used instead of red for the negative direction to avoid a
# red-green color-vision-deficiency pairing against the brand-green positive.
brand_rgb = tuple(int(IMPRINT[0][i : i + 2], 16) for i in (1, 3, 5))
loss_rgb = tuple(int(IMPRINT[2][i : i + 2], 16) for i in (1, 3, 5))

colors = {}
for band_idx in range(n_bands):
    frac = (band_idx + 1) / n_bands
    pos_rgb = tuple(round(255 + (brand_rgb[c] - 255) * frac) for c in range(3))
    neg_rgb = tuple(round(255 + (loss_rgb[c] - 255) * frac) for c in range(3))
    colors[band_labels[f"pos{band_idx}"]] = "#{:02X}{:02X}{:02X}".format(*pos_rgb)
    colors[band_labels[f"neg{band_idx}"]] = "#{:02X}{:02X}{:02X}".format(*neg_rgb)

# Legend from the strongest positive band down to the strongest negative one
legend_order = [band_labels[f"pos{b}"] for b in reversed(range(n_bands))] + [
    band_labels[f"neg{b}"] for b in range(n_bands)
]

# Distinctive lets-plot feature: custom tooltip content (unavailable in plotnine)
horizon_tooltips = (
    layer_tooltips()
    .title("@series")
    .format("@deviation", ".1f")
    .line("Band (%)|@band")
    .line("Deviation (%)|@deviation")
)

# Create the horizon chart: one opaque layer per band, the lowest band first, so
# a higher band is always drawn over the lower ones in its more intense color
plot = ggplot(horizon_df, aes(x="hour", y="value", fill="band", color="band"))
for band in range(n_bands):
    plot += geom_area(
        data=horizon_df[horizon_df["level"] == band], position="identity", size=0, tooltips=horizon_tooltips
    )
plot = (
    plot
    + scale_fill_manual(values=colors, breaks=legend_order)
    # Outline in the fill color, so the legend keys match the borderless bands
    + scale_color_manual(values=colors, breaks=legend_order)
    # Stack every series as a single, full-width, thin horizontal strip
    # (one row per series) rather than a large multi-column grid — this is
    # the defining "minimize vertical space" trait of a horizon chart.
    + facet_grid(y="series", y_order=0)
    # Only the meaningful zero baseline is labeled per row — with six thin
    # stacked strips, a top+bottom tick on every row would collide with the
    # neighboring row's ticks.
    + scale_y_continuous(breaks=[0], labels=["0"], limits=[0, band_size])
    + scale_x_continuous(breaks=[0, 24, 48, 72, 96, 120, 144], labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    + labs(
        title="horizon-basic · python · letsplot · anyplot.ai",
        x="Day of Week",
        y="CPU deviation from baseline (%)",
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
