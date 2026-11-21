"""anyplot.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential colormap (imprint_seq): brand green to blue
IMPRINT_SEQ = ["#009E73", "#4467A3"]

# Constants
WINDOW = 256  # STFT window length in samples
HOP = 32  # step between windows (high overlap for a smooth track)
MAX_FREQ = 1000  # upper edge of the displayed frequency range in Hz
POWER_FLOOR = 1e-10  # keeps log10 finite for empty bins

# Columns: set these to your table's column names
TIME = "Time (s)"  # role: sample_rate
SIGNAL = "Signal (a.u.)"  # role: signal
FREQUENCY = "Frequency (Hz)"  # role: extra
POWER = "Power (dB)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("signal.csv")
rng = np.random.default_rng(42)
sample_rate = 4000  # Hz
duration = 2.0  # seconds
t = np.arange(int(sample_rate * duration)) / sample_rate
# Linear chirp sweeping 100 Hz to 800 Hz, plus noise
f0, f1 = 100, 800
phase = 2 * np.pi * (f0 * t + (f1 - f0) / (2 * duration) * t**2)
df = pd.DataFrame({TIME: t, SIGNAL: np.sin(phase) + rng.normal(0, 0.1, len(t))})

# Plot: reads only df and the constants above
fs = 1 / np.median(np.diff(df[TIME]))
window = np.hanning(WINDOW)
signal = df[SIGNAL].to_numpy()
n_frames = (len(signal) - WINDOW) // HOP + 1

# Short-time Fourier transform: power per frequency bin and frame
frames = np.stack([signal[i * HOP : i * HOP + WINDOW] * window for i in range(n_frames)], axis=1)
power_db = 10 * np.log10(np.abs(np.fft.rfft(frames, axis=0)) ** 2 + POWER_FLOOR)
freqs = np.fft.rfftfreq(WINDOW, 1 / fs)
times = df[TIME].iloc[0] + (np.arange(n_frames) * HOP + WINDOW / 2) / fs

keep = freqs <= MAX_FREQ
time_grid, freq_grid = np.meshgrid(times, freqs[keep])
spec = pd.DataFrame({TIME: time_grid.ravel(), FREQUENCY: freq_grid.ravel(), POWER: power_db[keep].ravel()})

# Cell edges: each rectangle spans its own bin, widened by 2 % so no seams show
time_step = times[1] - times[0]
freq_step = freqs[1] - freqs[0]
spec["t0"] = spec[TIME] - time_step * 0.51
spec["t1"] = spec[TIME] + time_step * 0.51
spec["f0"] = spec[FREQUENCY] - freq_step * 0.51
spec["f1"] = spec[FREQUENCY] + freq_step * 0.51

low = spec[POWER].quantile(0.02)  # clip the extreme low tail so weak structure shows
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
chart = (
    alt.Chart(spec)
    .mark_rect()
    .encode(
        x=alt.X("t0", type="quantitative", title=TIME, scale=alt.Scale(nice=False)),
        x2=alt.X2("t1"),
        y=alt.Y("f0", type="quantitative", title=FREQUENCY, scale=alt.Scale(nice=False)),
        y2=alt.Y2("f1"),
        color=alt.Color(
            POWER.translate(ESCAPE),
            type="quantitative",
            title=POWER,
            scale=alt.Scale(range=IMPRINT_SEQ, domain=[float(low), float(spec[POWER].max())], clamp=True),
            legend=alt.Legend(type="gradient", gradientLength=220, gradientThickness=14),
        ),
        tooltip=[
            alt.Tooltip(TIME.translate(ESCAPE), type="quantitative", format=".3f", title=TIME),
            alt.Tooltip(FREQUENCY.translate(ESCAPE), type="quantitative", format=".1f", title=FREQUENCY),
            alt.Tooltip(POWER.translate(ESCAPE), type="quantitative", format=".1f", title=POWER),
        ],
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("spectrogram-basic · python · altair · anyplot.ai", fontSize=16),
    )
    .configure_title(anchor="middle", color=INK)
    .configure_axis(
        labelFontSize=11,
        titleFontSize=13,
        tickSize=6,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_legend(
        labelFontSize=11,
        titleFontSize=13,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        padding=8,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) the PNG to the 3200 x 1800 landscape target
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair rendered {img.width}x{img.height}, larger than {TARGET_W}x{TARGET_H}")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
