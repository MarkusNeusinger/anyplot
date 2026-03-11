"""pyplots.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-11
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, FixedTicker, HoverTool, LinearColorMapper
from bokeh.palettes import Magma256
from bokeh.plotting import figure
from scipy import signal


# Data - Synthesize a melody-like audio signal with multiple frequency components
np.random.seed(42)
sample_rate = 22050
duration = 4.0
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Create a rich audio signal: melody with harmonics and transients
audio_signal = np.zeros(n_samples)

# Melody notes (fundamental frequencies in Hz with harmonics)
notes = [
    (0.0, 1.0, 261.63),  # C4
    (0.5, 1.5, 329.63),  # E4
    (1.0, 2.0, 392.00),  # G4
    (1.5, 2.5, 523.25),  # C5
    (2.0, 3.0, 440.00),  # A4
    (2.5, 3.5, 349.23),  # F4
    (3.0, 4.0, 293.66),  # D4
]

for start, end, freq in notes:
    mask = (t >= start) & (t < end)
    envelope = np.zeros(n_samples)
    note_len = np.sum(mask)
    # ADSR-like envelope
    attack = int(0.05 * sample_rate)
    release = int(0.1 * sample_rate)
    if note_len > attack + release:
        env = np.ones(note_len)
        env[:attack] = np.linspace(0, 1, attack)
        env[-release:] = np.linspace(1, 0, release)
        envelope[mask] = env
    # Fundamental + harmonics
    audio_signal += envelope * (
        0.6 * np.sin(2 * np.pi * freq * t)
        + 0.25 * np.sin(2 * np.pi * 2 * freq * t)
        + 0.1 * np.sin(2 * np.pi * 3 * freq * t)
        + 0.05 * np.sin(2 * np.pi * 4 * freq * t)
    )

# Add subtle background noise
audio_signal += 0.02 * np.random.randn(n_samples)

# Normalize
audio_signal = audio_signal / np.max(np.abs(audio_signal))

# Compute STFT
n_fft = 2048
hop_length = 512
frequencies, times, Zxx = signal.stft(audio_signal, fs=sample_rate, nperseg=n_fft, noverlap=n_fft - hop_length)
power_spectrum = np.abs(Zxx) ** 2


# Mel filterbank construction
n_mels = 128
f_min = 0.0
f_max = sample_rate / 2.0

# Mel points evenly spaced on mel scale (Hz-to-mel: 2595 * log10(1 + f/700))
mel_min = 2595.0 * np.log10(1.0 + f_min / 700.0)
mel_max = 2595.0 * np.log10(1.0 + f_max / 700.0)
mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)

# Convert Hz points to FFT bin indices
bin_points = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

# Build triangular filterbank
n_freqs = len(frequencies)
filterbank = np.zeros((n_mels, n_freqs))
for m in range(n_mels):
    f_left = bin_points[m]
    f_center = bin_points[m + 1]
    f_right = bin_points[m + 2]
    for k in range(f_left, f_center):
        if f_center != f_left:
            filterbank[m, k] = (k - f_left) / (f_center - f_left)
    for k in range(f_center, f_right):
        if f_right != f_center:
            filterbank[m, k] = (f_right - k) / (f_right - f_center)

# Apply mel filterbank to power spectrum
mel_spectrogram = filterbank @ power_spectrum

# Convert to decibel scale
mel_spectrogram_db = 10.0 * np.log10(mel_spectrogram + 1e-10)

# Mel band edge frequencies (for positioning rectangles correctly on log scale)
mel_edge_freqs = hz_points  # n_mels + 2 edges
# Clamp to positive values for log scale
mel_edge_freqs = np.maximum(mel_edge_freqs, 1.0)

# Build quad data for each mel band x time frame
n_times = len(times)
time_step = times[1] - times[0] if n_times > 1 else hop_length / sample_rate

quad_left = []
quad_right = []
quad_bottom = []
quad_top = []
quad_power = []
quad_time_label = []
quad_freq_label = []

for ti in range(n_times):
    for mi in range(n_mels):
        quad_left.append(times[ti] - time_step / 2)
        quad_right.append(times[ti] + time_step / 2)
        quad_bottom.append(mel_edge_freqs[mi + 1])
        quad_top.append(mel_edge_freqs[mi + 2])
        quad_power.append(mel_spectrogram_db[mi, ti])
        quad_time_label.append(round(times[ti], 3))
        quad_freq_label.append(round((mel_edge_freqs[mi + 1] + mel_edge_freqs[mi + 2]) / 2, 1))

quad_power_arr = np.array(quad_power)
vmin = float(np.percentile(mel_spectrogram_db, 5))
vmax = float(mel_spectrogram_db.max())

# Map power to palette indices for fill_color
normalized = (quad_power_arr - vmin) / (vmax - vmin)
normalized = np.clip(normalized, 0, 1)
color_indices = (normalized * 255).astype(int)
colors = [Magma256[i] for i in color_indices]

source = ColumnDataSource(
    data={
        "left": quad_left,
        "right": quad_right,
        "bottom": quad_bottom,
        "top": quad_top,
        "power": quad_power,
        "color": colors,
        "time_s": quad_time_label,
        "freq_hz": quad_freq_label,
    }
)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="spectrogram-mel \u00b7 bokeh \u00b7 pyplots.ai",
    x_axis_label="Time (seconds)",
    y_axis_label="Frequency (Hz)",
    x_range=(times.min() - time_step / 2, times.max() + time_step / 2),
    y_range=(mel_edge_freqs[1], mel_edge_freqs[-1]),
    y_axis_type="log",
    tools="",
    toolbar_location=None,
)

# Render mel bands as quads for correct log-scale positioning
p.quad(
    left="left",
    right="right",
    bottom="bottom",
    top="top",
    fill_color="color",
    line_color=None,
    source=source,
    level="image",
)

# HoverTool for interactive readout
hover = HoverTool(
    tooltips=[("Time", "@time_s{0.000} s"), ("Frequency", "@freq_hz{0.0} Hz"), ("Power", "@power{0.0} dB")],
    point_policy="follow_mouse",
)
p.add_tools(hover)

# Color mapper for the colorbar
color_mapper = LinearColorMapper(palette=Magma256, low=vmin, high=vmax)

# Colorbar labeled in dB
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(desired_num_ticks=8),
    label_standoff=20,
    border_line_color=None,
    location=(0, 0),
    title="Power (dB)",
    title_text_font_size="32pt",
    major_label_text_font_size="24pt",
    width=70,
    padding=40,
    title_standoff=20,
)
p.add_layout(color_bar, "right")

# Y-axis tick labels at key mel band frequencies
mel_tick_freqs = [50, 100, 200, 500, 1000, 2000, 4000, 8000]
mel_tick_freqs = [f for f in mel_tick_freqs if mel_edge_freqs[1] <= f <= mel_edge_freqs[-1]]
p.yaxis.ticker = FixedTicker(ticks=mel_tick_freqs)

# Style for 4800x2700 canvas
p.title.text_font_size = "40pt"
p.title.text_font_style = "bold"
p.title.text_color = "#222222"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"

# Axis styling
p.xaxis.axis_line_width = 3
p.yaxis.axis_line_width = 3
p.xaxis.major_tick_line_width = 3
p.yaxis.major_tick_line_width = 3
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid - subtle styling
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]
p.xgrid.grid_line_color = "#aaaaaa"
p.ygrid.grid_line_color = "#aaaaaa"

# Background
p.background_fill_color = "#000004"
p.border_fill_color = "white"
p.outline_line_color = "#333333"
p.outline_line_width = 2
p.min_border_right = 140
p.min_border_left = 120
p.min_border_bottom = 100

# Save
export_png(p, filename="plot.png")

output_file("plot.html", title="spectrogram-mel \u00b7 bokeh \u00b7 pyplots.ai")
save(p)
