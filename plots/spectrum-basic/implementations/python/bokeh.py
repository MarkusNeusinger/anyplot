"""anyplot.ai
spectrum-basic: Frequency Spectrum Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-14
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_PEAKS = 3  # the dominant components that get a highlight

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
AMPLITUDE = "Amplitude (dB)"  # role: amplitude

# Data: replace this block with your own table, for example df = pd.read_csv("spectrum.csv")
np.random.seed(42)
sample_rate = 8192  # Hz
n_samples = 8192
t = np.arange(n_samples) / sample_rate
signal = (
    1.0 * np.sin(2 * np.pi * 50 * t)  # fundamental
    + 0.5 * np.sin(2 * np.pi * 150 * t)  # harmonic
    + 0.3 * np.sin(2 * np.pi * 400 * t)  # further component
    + 0.1 * np.random.randn(n_samples)  # noise
)
magnitude = np.abs(np.fft.rfft(signal)) / n_samples
freqs = np.fft.rfftfreq(n_samples, 1 / sample_rate)
keep = (freqs > 0) & (freqs <= 500)  # drop the DC bin (no place on a log axis), limit to 500 Hz
df = pd.DataFrame({FREQUENCY: freqs[keep], AMPLITUDE: 20 * np.log10(np.maximum(magnitude[keep], 1e-10))})

# Plot: reads only df and the constants above
freq = df[FREQUENCY].to_numpy()
amp = df[AMPLITUDE].to_numpy()
floor = amp.min() - 5
ceiling = amp.max() + 8

# Dominant components: the highest local maxima of the spectrum
is_peak = np.r_[False, (amp[1:-1] > amp[:-2]) & (amp[1:-1] > amp[2:]), False]
peak_idx = np.flatnonzero(is_peak)
peak_idx = np.sort(peak_idx[np.argsort(amp[peak_idx])[::-1][:N_PEAKS]])

source = ColumnDataSource(df)

p = figure(
    width=3200,
    height=1800,
    title="spectrum-basic · python · bokeh · anyplot.ai",
    x_axis_label=FREQUENCY,
    y_axis_label=AMPLITUDE,
    x_axis_type="log",
    y_range=Range1d(floor, ceiling),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

p.varea(x=FREQUENCY, y1=AMPLITUDE, y2=floor, source=source, fill_color=IMPRINT_PALETTE[0], fill_alpha=0.15)
p.line(x=FREQUENCY, y=AMPLITUDE, source=source, line_width=4, line_color=IMPRINT_PALETTE[0], legend_label="Spectrum")

for i, idx in enumerate(peak_idx):
    p.scatter(
        x=[freq[idx]],
        y=[amp[idx]],
        size=30,
        color=IMPRINT_PALETTE[i + 1],
        line_color=INK_SOFT,
        line_width=2,
        legend_label=f"Peak: {freq[idx]:.0f} Hz",
    )

hover = HoverTool(tooltips=[(FREQUENCY, f"@{{{FREQUENCY}}}{{0.0}}"), (AMPLITUDE, f"@{{{AMPLITUDE}}}{{0.0}}")])
p.add_tools(hover)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.location = "top_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.padding = 18
p.legend.spacing = 8

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save the interactive HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
