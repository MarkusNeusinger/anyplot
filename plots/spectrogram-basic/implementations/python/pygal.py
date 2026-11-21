"""anyplot.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from pygal.graph.graph import Graph
from pygal.style import Style
from scipy import signal


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def lerp_hex(c0, c1, t):
    """Linear blend between two hex colors."""
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    r, g, bl = (round(x + (y - x) * t) for x, y in zip(a, b, strict=True))
    return f"#{r:02X}{g:02X}{bl:02X}"


# imprint_seq: single-polarity continuous colormap, Imprint green -> blue
IMPRINT_SEQ = [lerp_hex("#009E73", "#4467A3", i / 9) for i in range(10)]

# Constants
WINDOWS_PER_SIGNAL = 31  # signal length / this = analysis window; sets the time/frequency resolution trade-off
OVERLAP = 0.78  # fraction of each window shared with the next
DB_FLOOR = 1e-10  # added before the log so silent cells stay finite
DB_RANGE_PERCENTILES = (5, 99.9)  # color range; keeps a few deep-noise cells from flattening the contrast

# Columns: set these to your table's column names
TIME = "Time (s)"  # role: extra
SIGNAL = "Amplitude"  # role: signal
SAMPLE_RATE = "Sample rate (Hz)"  # role: sample_rate

# Data: replace this block with your own table, for example df = pd.read_csv("recording.csv")
rng = np.random.default_rng(42)
rate = 4000  # Hz
duration = 2.0  # seconds
t = np.arange(int(rate * duration)) / rate
wave = signal.chirp(t, f0=100, f1=800, t1=duration, method="linear")
wave += 0.3 * signal.chirp(t, f0=200, f1=1200, t1=duration, method="linear")
wave += 0.1 * rng.standard_normal(len(t))
df = pd.DataFrame({TIME: t, SIGNAL: wave, SAMPLE_RATE: rate})

# Plot: reads only df and the constants above
samples = df[SIGNAL].interpolate().bfill().ffill().to_numpy()
fs = float(df[SAMPLE_RATE].iloc[0])
nperseg = max(8, len(samples) // WINDOWS_PER_SIGNAL)
frequencies, times, power = signal.spectrogram(samples, fs=fs, nperseg=nperseg, noverlap=int(nperseg * OVERLAP))
power_db = 10 * np.log10(power + DB_FLOOR)
times = times + df[TIME].iloc[0]
cells = power_db.tolist()
n_freq, n_time = power_db.shape
min_val, max_val = (float(v) for v in np.percentile(power_db, DB_RANGE_PERCENTILES))
time_ticks = times.tolist()
freq_ticks = frequencies.tolist()


def color_at(value):
    """Color of the imprint_seq colormap for a power value."""
    if max_val == min_val:
        return IMPRINT_SEQ[-1]
    pos = min(1.0, max(0.0, (value - min_val) / (max_val - min_val))) * (len(IMPRINT_SEQ) - 1)
    idx = min(int(pos), len(IMPRINT_SEQ) - 2)
    return lerp_hex(IMPRINT_SEQ[idx], IMPRINT_SEQ[idx + 1], pos - idx)


def add_text(chart, parent, x, y, text, size, anchor="middle", bold=False, rotate=False):
    node = chart.svg.node(parent, "text", x=x, y=y)
    if rotate:
        node.set("transform", f"rotate(-90, {x}, {y})")
    node.set("text-anchor", anchor)
    node.set("fill", INK)
    weight = "font-weight:bold;" if bold else ""
    node.set("style", f"font-size:{size}px;{weight}font-family:sans-serif")
    node.text = text


def add_line(chart, parent, x1, y1, x2, y2):
    line = chart.svg.node(parent, "line", x1=x1, y1=y1, x2=x2, y2=y2)
    line.set("stroke", INK)
    line.set("stroke-width", "2")


def draw_spectrogram(chart):
    """Draw cells, axes, ticks and the color bar into the chart's plot group."""
    margin_left, margin_right, margin_top, margin_bottom = 250, 340, 40, 190
    avail_w = chart.view.width - margin_left - margin_right
    avail_h = chart.view.height - margin_top - margin_bottom
    cell_w = avail_w / n_time
    cell_h = avail_h / n_freq
    x0 = chart.view.x(0) + margin_left
    y0 = chart.view.y(n_freq) + margin_top
    group = chart.svg.node(chart.nodes["plot"], class_="spectrogram-heatmap")

    # Cells: highest frequency at the top
    for i in range(n_freq):
        row = cells[n_freq - 1 - i]
        for j in range(n_time):
            rect = chart.svg.node(
                group, "rect", x=x0 + j * cell_w, y=y0 + i * cell_h, width=cell_w + 0.5, height=cell_h + 0.5
            )
            rect.set("fill", color_at(row[j]))
            rect.set("stroke", "none")

    frame = chart.svg.node(group, "rect", x=x0, y=y0, width=avail_w, height=avail_h)
    frame.set("fill", "none")
    frame.set("stroke", INK)
    frame.set("stroke-width", "2")

    add_text(chart, group, x0 + avail_w / 2, y0 + avail_h + 135, TIME, 56, bold=True)
    add_text(chart, group, x0 - 175, y0 + avail_h / 2, "Frequency (Hz)", 56, bold=True, rotate=True)

    n_ticks = 6
    for i in range(n_ticks):
        frac = i / (n_ticks - 1)
        tx = x0 + frac * avail_w
        add_line(chart, group, tx, y0 + avail_h, tx, y0 + avail_h + 12)
        value = time_ticks[round(frac * (len(time_ticks) - 1))]
        add_text(chart, group, tx, y0 + avail_h + 62, f"{value:.1f}", 44)

        ty = y0 + frac * avail_h
        add_line(chart, group, x0 - 12, ty, x0, ty)
        value = freq_ticks[round((1 - frac) * (len(freq_ticks) - 1))]
        add_text(chart, group, x0 - 24, ty + 15, f"{value:.0f}", 44, anchor="end")

    # Color bar
    bar_w = 44
    bar_h = avail_h * 0.8
    bar_x = x0 + avail_w + 50
    bar_y = y0 + (avail_h - bar_h) / 2
    n_seg = 80
    seg_h = bar_h / n_seg
    for i in range(n_seg):
        level = min_val + (max_val - min_val) * (n_seg - 1 - i) / (n_seg - 1)
        chart.svg.node(group, "rect", x=bar_x, y=bar_y + i * seg_h, width=bar_w, height=seg_h + 1, fill=color_at(level))
    chart.svg.node(group, "rect", x=bar_x, y=bar_y, width=bar_w, height=bar_h, fill="none", stroke=INK)
    n_cb = 6
    for i in range(n_cb):
        pos = i / (n_cb - 1)
        cy = bar_y + pos * bar_h
        add_line(chart, group, bar_x + bar_w, cy, bar_x + bar_w + 10, cy)
        label = f"{max_val - (max_val - min_val) * pos:.0f}"
        add_text(chart, group, bar_x + bar_w + 20, cy + 14, label, 40, anchor="start")
    add_text(chart, group, bar_x + bar_w / 2, bar_y - 35, "Power (dB)", 46, bold=True)


def set_cell_box(chart):
    """Set the data box to the cell grid."""
    chart._box.xmin, chart._box.xmax = 0, n_time
    chart._box.ymin, chart._box.ymax = 0, n_freq


custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    legend_font_size=44,
    label_font_size=44,
    value_font_size=36,
    font_family="sans-serif",
)

chart = Graph(
    width=3200,
    height=1800,
    style=custom_style,
    title="spectrogram-basic · python · pygal · anyplot.ai",
    show_legend=False,
    margin=50,
    margin_top=130,
    show_x_labels=False,
    show_y_labels=False,
)
chart.add("", [0])  # pygal needs a series to call the plot hook
chart._compute = lambda: set_cell_box(chart)
chart._plot = lambda: draw_spectrogram(chart)

chart.render_to_file(f"plot-{THEME}.svg")
chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>spectrogram-basic - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: {PAGE_BG}; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {chart.render(is_unicode=True)}
    </figure>
</body>
</html>
"""
    )
