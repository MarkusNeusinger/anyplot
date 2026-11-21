""" anyplot.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import BasicTicker, ColorBar, LinearColorMapper
from bokeh.plotting import figure
from scipy import signal
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def lerp_hex(c0, c1, t):
    r0, g0, b0 = (int(c0[i : i + 2], 16) for i in (1, 3, 5))
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(a + (z - a) * t) for a, z in ((r0, r1), (g0, g1), (b0, b1)))
    return f"#{r:02X}{g:02X}{b:02X}"


# Imprint sequential ramp (single polarity): green to blue
IMPRINT_SEQ256 = [lerp_hex("#009E73", "#4467A3", i / 255) for i in range(256)]

# Columns: set these to your table's column names
TIME = "Time (seconds)"  # role: extra
SIGNAL = "Amplitude"  # role: signal
SAMPLE_RATE = "Sample rate (Hz)"  # role: sample_rate

# Constants
NPERSEG = 256  # window length in samples
OVERLAP = 0.75  # fraction of the window shared by neighbouring segments

# Data: replace this block with your own table, for example df = pd.read_csv("signal.csv")
np.random.seed(42)
sample_rate = 8000
duration = 2.0
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
chirp = signal.chirp(t, 200, duration, 2000, method="linear")
chirp += 0.1 * np.random.randn(len(chirp))
df = pd.DataFrame({TIME: t, SIGNAL: chirp, SAMPLE_RATE: sample_rate})

# Plot: reads only df and the constants above
fs = df[SAMPLE_RATE].iloc[0]
frequencies, times, Sxx = signal.spectrogram(
    df[SIGNAL].to_numpy(), fs=fs, nperseg=NPERSEG, noverlap=int(NPERSEG * OVERLAP), scaling="density"
)
Sxx_db = 10 * np.log10(Sxx + 1e-10)

p = figure(
    width=3200,
    height=1800,
    title="spectrogram-basic · python · bokeh · anyplot.ai",
    x_axis_label=TIME,
    y_axis_label="Frequency (Hz)",
    x_range=(times.min(), times.max()),
    y_range=(frequencies.min(), frequencies.max()),
    tools="",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

color_mapper = LinearColorMapper(palette=IMPRINT_SEQ256, low=Sxx_db.min(), high=Sxx_db.max())

p.image(
    image=[Sxx_db],
    x=times.min(),
    y=frequencies.min(),
    dw=times.max() - times.min(),
    dh=frequencies.max() - frequencies.min(),
    color_mapper=color_mapper,
    level="image",
)

color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(),
    label_standoff=20,
    border_line_color=INK_SOFT,
    title="Power (dB)",
    title_text_font_size="34pt",
    title_text_color=INK,
    major_label_text_font_size="34pt",
    major_label_text_color=INK_SOFT,
    major_tick_line_color=INK_SOFT,
    bar_line_color=INK_SOFT,
    background_fill_color=PAGE_BG,
    width=70,
    padding=30,
)
p.add_layout(color_bar, "right")

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with Selenium
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
