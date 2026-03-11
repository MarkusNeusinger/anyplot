"""pyplots.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-11
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import BasicTicker, ColorBar, FixedTicker, LinearColorMapper
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

# Mel frequency axis - center frequencies for each mel band (mel-to-Hz conversion)
mel_center_points = np.linspace(mel_min, mel_max, n_mels + 2)[1:-1]
mel_center_freqs = 700.0 * (10.0 ** (mel_center_points / 2595.0) - 1.0)

# Magma palette for mel spectrogram
magma = [
    "#000004",
    "#010005",
    "#010106",
    "#010108",
    "#020109",
    "#02020b",
    "#02020d",
    "#03030f",
    "#030312",
    "#040414",
    "#050416",
    "#060518",
    "#07051a",
    "#08061c",
    "#09071e",
    "#0a0720",
    "#0b0822",
    "#0c0926",
    "#0d0a28",
    "#0e0b2a",
    "#0f0b2c",
    "#100c2f",
    "#110d31",
    "#120d33",
    "#130e36",
    "#140e38",
    "#160f3b",
    "#170f3d",
    "#181040",
    "#1a1042",
    "#1b1044",
    "#1c1147",
    "#1e1149",
    "#1f114b",
    "#20114e",
    "#221150",
    "#231152",
    "#251155",
    "#261157",
    "#281159",
    "#29115b",
    "#2b105d",
    "#2d1060",
    "#2e1062",
    "#301064",
    "#311066",
    "#331068",
    "#34106a",
    "#36106b",
    "#38106d",
    "#39106f",
    "#3b1070",
    "#3d1072",
    "#3e0f73",
    "#400f75",
    "#420f76",
    "#430f77",
    "#450e78",
    "#470e79",
    "#480e7a",
    "#4a0e7b",
    "#4c0e7c",
    "#4d0d7c",
    "#4f0d7d",
    "#510d7d",
    "#520d7e",
    "#540d7e",
    "#560c7e",
    "#570c7f",
    "#590c7f",
    "#5b0c7f",
    "#5c0b7f",
    "#5e0b7f",
    "#600b7f",
    "#610a7f",
    "#630a7f",
    "#650a7f",
    "#66097f",
    "#68097e",
    "#6a097e",
    "#6b097e",
    "#6d087d",
    "#6f087d",
    "#70087d",
    "#72077c",
    "#74077c",
    "#75077b",
    "#77067b",
    "#79067a",
    "#7a067a",
    "#7c0679",
    "#7e0578",
    "#7f0578",
    "#810577",
    "#830476",
    "#840476",
    "#860475",
    "#880474",
    "#890374",
    "#8b0373",
    "#8d0372",
    "#8e0271",
    "#900270",
    "#920270",
    "#93026f",
    "#95026e",
    "#97016d",
    "#98016c",
    "#9a016b",
    "#9c016b",
    "#9d016a",
    "#9f0169",
    "#a10168",
    "#a20167",
    "#a40166",
    "#a60165",
    "#a70164",
    "#a90163",
    "#ab0162",
    "#ac0161",
    "#ae0160",
    "#b00160",
    "#b1015f",
    "#b3015e",
    "#b4015d",
    "#b6015c",
    "#b8015b",
    "#b9015a",
    "#bb0159",
    "#bc0158",
    "#be0157",
    "#c00256",
    "#c10255",
    "#c30354",
    "#c40453",
    "#c60552",
    "#c70651",
    "#c90750",
    "#ca084f",
    "#cc094e",
    "#cd0a4d",
    "#cf0b4d",
    "#d00d4c",
    "#d10e4b",
    "#d3104a",
    "#d41149",
    "#d51349",
    "#d71448",
    "#d81647",
    "#d91847",
    "#da1946",
    "#dc1b46",
    "#dd1d45",
    "#de1f45",
    "#df2044",
    "#e02244",
    "#e12444",
    "#e22643",
    "#e32843",
    "#e42a43",
    "#e52c43",
    "#e62e43",
    "#e73043",
    "#e83243",
    "#e93443",
    "#ea3643",
    "#eb3843",
    "#eb3a43",
    "#ec3c43",
    "#ed3e44",
    "#ee4044",
    "#ef4344",
    "#ef4545",
    "#f04745",
    "#f14946",
    "#f14b46",
    "#f24d47",
    "#f34f48",
    "#f35148",
    "#f45349",
    "#f5554a",
    "#f5574b",
    "#f6594c",
    "#f65b4d",
    "#f75d4e",
    "#f75f4f",
    "#f86250",
    "#f86451",
    "#f96653",
    "#f96854",
    "#f96a55",
    "#fa6c57",
    "#fa6e58",
    "#fa705a",
    "#fb725b",
    "#fb745d",
    "#fb765e",
    "#fb7860",
    "#fc7a62",
    "#fc7c63",
    "#fc7e65",
    "#fc8067",
    "#fc8269",
    "#fc846b",
    "#fd866d",
    "#fd886f",
    "#fd8a71",
    "#fd8c73",
    "#fd8e75",
    "#fd9078",
    "#fd927a",
    "#fd947c",
    "#fd967e",
    "#fd9880",
    "#fe9a83",
    "#fe9c85",
    "#fe9e87",
    "#fea08a",
    "#fea28c",
    "#fea48e",
    "#fea690",
    "#fea893",
    "#feaa95",
    "#feac98",
    "#feae9a",
    "#feb09c",
    "#feb29f",
    "#feb4a1",
    "#feb6a4",
    "#feb8a6",
    "#febaa8",
    "#febcab",
    "#fdbead",
    "#fdc0b0",
    "#fdc2b2",
    "#fdc4b5",
    "#fdc6b7",
    "#fdc8ba",
    "#fdcabc",
    "#fdccbf",
    "#fdcec1",
    "#fdd0c4",
    "#fdd2c6",
    "#fdd4c9",
    "#fdd5cb",
    "#fdd7ce",
    "#fdd9d1",
    "#fddbd3",
    "#fdddd6",
    "#fddfd8",
    "#fde1db",
    "#fde3dd",
    "#fde5e0",
    "#fee7e3",
    "#fee9e5",
    "#feebe8",
    "#fcedea",
    "#fcefed",
]

# Plot
p = figure(
    width=4800,
    height=2700,
    title="spectrogram-mel · bokeh · pyplots.ai",
    x_axis_label="Time (seconds)",
    y_axis_label="Frequency (Hz)",
    x_range=(times.min(), times.max()),
    y_range=(mel_center_freqs[0], mel_center_freqs[-1]),
    y_axis_type="log",
    tools="",
    toolbar_location=None,
)

# Color mapper
vmin = np.percentile(mel_spectrogram_db, 5)
vmax = mel_spectrogram_db.max()
color_mapper = LinearColorMapper(palette=magma, low=vmin, high=vmax)

# Render mel spectrogram as image
p.image(
    image=[mel_spectrogram_db],
    x=times.min(),
    y=mel_center_freqs[0],
    dw=times.max() - times.min(),
    dh=mel_center_freqs[-1] - mel_center_freqs[0],
    color_mapper=color_mapper,
    level="image",
)

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
mel_tick_freqs = [f for f in mel_tick_freqs if mel_center_freqs[0] <= f <= mel_center_freqs[-1]]
p.yaxis.ticker = FixedTicker(ticks=mel_tick_freqs)

# Style for 4800x2700 canvas
p.title.text_font_size = "40pt"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"

# Axis styling
p.xaxis.axis_line_width = 3
p.yaxis.axis_line_width = 3
p.xaxis.major_tick_line_width = 3
p.yaxis.major_tick_line_width = 3

# Grid - subtle dashed lines
p.xgrid.grid_line_alpha = 0.2
p.ygrid.grid_line_alpha = 0.2
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = None
p.border_fill_color = "white"
p.outline_line_color = "#333333"
p.outline_line_width = 2
p.min_border_right = 100

# Save
export_png(p, filename="plot.png")

output_file("plot.html", title="spectrogram-mel · bokeh · pyplots.ai")
save(p)
