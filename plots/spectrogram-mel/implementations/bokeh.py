""" pyplots.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-11
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import (
    BasicTicker,
    BoxAnnotation,
    ColorBar,
    ColumnDataSource,
    FixedTicker,
    HoverTool,
    Label,
    LinearColorMapper,
    Span,
)
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
    attack = int(0.05 * sample_rate)
    release = int(0.1 * sample_rate)
    if note_len > attack + release:
        env = np.ones(note_len)
        env[:attack] = np.linspace(0, 1, attack)
        env[-release:] = np.linspace(1, 0, release)
        envelope[mask] = env
    audio_signal += envelope * (
        0.6 * np.sin(2 * np.pi * freq * t)
        + 0.25 * np.sin(2 * np.pi * 2 * freq * t)
        + 0.1 * np.sin(2 * np.pi * 3 * freq * t)
        + 0.05 * np.sin(2 * np.pi * 4 * freq * t)
    )

audio_signal += 0.02 * np.random.randn(n_samples)
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

mel_min = 2595.0 * np.log10(1.0 + f_min / 700.0)
mel_max = 2595.0 * np.log10(1.0 + f_max / 700.0)
mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)

bin_points = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

# Build triangular filterbank (vectorized inner loop)
n_freqs = len(frequencies)
filterbank = np.zeros((n_mels, n_freqs))
for m in range(n_mels):
    f_left, f_center, f_right = bin_points[m], bin_points[m + 1], bin_points[m + 2]
    if f_center > f_left:
        rising = np.arange(f_left, f_center)
        filterbank[m, rising] = (rising - f_left) / (f_center - f_left)
    if f_right > f_center:
        falling = np.arange(f_center, f_right)
        filterbank[m, falling] = (f_right - falling) / (f_right - f_center)

mel_spectrogram = filterbank @ power_spectrum
mel_spectrogram_db = 10.0 * np.log10(mel_spectrogram + 1e-10)

# Mel band edge frequencies for quad positioning on log scale
mel_edge_freqs = np.maximum(hz_points, 1.0)

# Build quad data vectorized with np.repeat/np.tile
n_times = len(times)
time_step = times[1] - times[0] if n_times > 1 else hop_length / sample_rate

time_grid = np.repeat(times, n_mels)
bottom_grid = np.tile(mel_edge_freqs[1 : n_mels + 1], n_times)
top_grid = np.tile(mel_edge_freqs[2 : n_mels + 2], n_times)
power_grid = mel_spectrogram_db.T.ravel()

vmin = float(np.percentile(mel_spectrogram_db, 5))
vmax = float(mel_spectrogram_db.max())

# Map power to palette colors
normalized = np.clip((power_grid - vmin) / (vmax - vmin), 0, 1)
color_indices = (normalized * 255).astype(int)
colors = [Magma256[i] for i in color_indices]

source = ColumnDataSource(
    data={
        "left": time_grid - time_step / 2,
        "right": time_grid + time_step / 2,
        "bottom": bottom_grid,
        "top": top_grid,
        "power": power_grid,
        "color": colors,
        "time_s": np.round(time_grid, 3),
        "freq_hz": np.round((bottom_grid + top_grid) / 2, 1),
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

# Render mel bands as quads
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

# Visual storytelling: annotate the C-major arpeggio rising pattern
arpeggio_box = BoxAnnotation(
    left=0.0, right=2.5, fill_alpha=0, line_color="#ffffff", line_alpha=0.45, line_width=3, line_dash="dashed"
)
p.add_layout(arpeggio_box)

arpeggio_label = Label(
    x=0.05,
    y=mel_edge_freqs[-1] * 0.85,
    text="C Major Arpeggio (C4 \u2192 E4 \u2192 G4 \u2192 C5)",
    text_font_size="22pt",
    text_color="#ffffff",
    text_alpha=0.85,
    text_font_style="italic",
)
p.add_layout(arpeggio_label)

# Mark octave fundamentals (C4, C5) with horizontal frequency guides
for freq, name in [(261.63, "C4"), (523.25, "C5")]:
    if mel_edge_freqs[1] <= freq <= mel_edge_freqs[-1]:
        span = Span(
            location=freq, dimension="width", line_color="#ffffff", line_alpha=0.25, line_width=2, line_dash="dotted"
        )
        p.add_layout(span)
        label = Label(
            x=times.max() + time_step * 0.3,
            y=freq,
            text=name,
            text_font_size="20pt",
            text_color="#ffffff",
            text_alpha=0.7,
            text_font_style="bold",
        )
        p.add_layout(label)

# Descending passage label
desc_label = Label(
    x=2.55,
    y=mel_edge_freqs[-1] * 0.85,
    text="Descending (A4 \u2192 F4 \u2192 D4)",
    text_font_size="22pt",
    text_color="#ffffff",
    text_alpha=0.65,
    text_font_style="italic",
)
p.add_layout(desc_label)

# HoverTool for interactive readout
hover = HoverTool(
    tooltips=[("Time", "@time_s{0.000} s"), ("Frequency", "@freq_hz{0.0} Hz"), ("Power", "@power{0.0} dB")],
    point_policy="follow_mouse",
)
p.add_tools(hover)

# Colorbar
color_mapper = LinearColorMapper(palette=Magma256, low=vmin, high=vmax)
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(desired_num_ticks=8),
    label_standoff=24,
    border_line_color=None,
    location=(0, 0),
    title="Power (dB)",
    title_text_font_size="32pt",
    title_text_font_style="italic",
    major_label_text_font_size="24pt",
    major_label_text_color="#444444",
    width=70,
    padding=50,
    title_standoff=24,
)
p.add_layout(color_bar, "right")

# Y-axis tick labels at key mel band frequencies
mel_tick_freqs = [
    f for f in [50, 100, 200, 500, 1000, 2000, 4000, 8000] if mel_edge_freqs[1] <= f <= mel_edge_freqs[-1]
]
p.yaxis.ticker = FixedTicker(ticks=mel_tick_freqs)

# Typography for 4800x2700 canvas
p.title.text_font_size = "42pt"
p.title.text_font_style = "bold"
p.title.text_color = "#333333"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

# Axis styling
p.xaxis.axis_line_width = 3
p.yaxis.axis_line_width = 3
p.xaxis.axis_line_color = "#555555"
p.yaxis.axis_line_color = "#555555"
p.xaxis.major_tick_line_width = 3
p.yaxis.major_tick_line_width = 3
p.xaxis.major_tick_line_color = "#555555"
p.yaxis.major_tick_line_color = "#555555"
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid - subtle styling
p.xgrid.grid_line_alpha = 0.12
p.ygrid.grid_line_alpha = 0.12
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]
p.xgrid.grid_line_color = "#888888"
p.ygrid.grid_line_color = "#888888"

# Background
p.background_fill_color = "#000004"
p.border_fill_color = "#fafafa"
p.outline_line_color = "#333333"
p.outline_line_width = 2
p.min_border_right = 180
p.min_border_left = 130
p.min_border_bottom = 110
p.min_border_top = 80

# Save
export_png(p, filename="plot.png")

output_file("plot.html", title="spectrogram-mel \u00b7 bokeh \u00b7 pyplots.ai")
save(p)
