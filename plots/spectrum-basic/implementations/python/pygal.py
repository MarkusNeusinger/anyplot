""" pyplots.ai
spectrum-basic: Frequency Spectrum Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Generate synthetic signal with multiple frequency components
np.random.seed(42)

# Create a synthetic time-domain signal with known frequency components
fs = 1000  # Sampling frequency (Hz)
t = np.linspace(0, 1, fs)  # 1 second of data

# Signal with 3 frequency components: 50 Hz (strong), 120 Hz (medium), 200 Hz (weak)
signal = (
    3.0 * np.sin(2 * np.pi * 50 * t)  # 50 Hz - dominant frequency
    + 1.5 * np.sin(2 * np.pi * 120 * t)  # 120 Hz - secondary
    + 0.8 * np.sin(2 * np.pi * 200 * t)  # 200 Hz - tertiary
    + 0.3 * np.random.randn(len(t))  # Noise floor
)

# Compute FFT
n = len(signal)
fft_result = np.fft.fft(signal)
frequencies = np.fft.fftfreq(n, 1 / fs)

# Take only positive frequencies
positive_mask = frequencies >= 0
frequencies = frequencies[positive_mask]
amplitude = np.abs(fft_result[positive_mask]) / n * 2  # Normalize

# Convert to dB scale for better visualization
amplitude_db = 20 * np.log10(amplitude + 1e-10)

# Limit to 0-300 Hz for clarity (where our signal components are)
freq_limit_mask = frequencies <= 300
frequencies = frequencies[freq_limit_mask]
amplitude_db = amplitude_db[freq_limit_mask]

# Downsample for pygal (it works better with fewer points)
step = 2
frequencies = frequencies[::step]
amplitude_db = amplitude_db[::step]

# Create custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),  # Python Blue
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=32,
    stroke_width=4,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create XY chart (line chart with custom x values)
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="spectrum-basic · pygal · pyplots.ai",
    x_title="Frequency (Hz)",
    y_title="Amplitude (dB)",
    show_dots=False,
    fill=True,
    stroke_style={"width": 4},
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    show_legend=False,
    range=(-60, 20),  # dB range
    dots_size=0,
    margin=60,
    spacing=40,
)

# Add data as XY points
xy_data = [(float(f), float(a)) for f, a in zip(frequencies, amplitude_db, strict=True)]
chart.add("Amplitude", xy_data)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
