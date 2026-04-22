""" pyplots.ai
spectrum-basic: Frequency Spectrum Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data: Generate synthetic signal with multiple frequency components
np.random.seed(42)
sample_rate = 8192  # Hz
duration = 1.0  # seconds
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Create composite signal: 50 Hz base, 150 Hz harmonic, 400 Hz component, plus noise
signal = (
    1.0 * np.sin(2 * np.pi * 50 * t)  # Fundamental at 50 Hz
    + 0.5 * np.sin(2 * np.pi * 150 * t)  # Harmonic at 150 Hz
    + 0.3 * np.sin(2 * np.pi * 400 * t)  # Component at 400 Hz
    + 0.1 * np.random.randn(n_samples)  # Noise
)

# Compute FFT
fft_result = np.fft.rfft(signal)
frequencies = np.fft.rfftfreq(n_samples, 1 / sample_rate)
amplitude = np.abs(fft_result) / n_samples  # Normalize amplitude

# Convert to dB scale (with floor to avoid log(0))
amplitude_db = 20 * np.log10(np.maximum(amplitude, 1e-10))

# Limit to 500 Hz for better visualization
mask = frequencies <= 500
frequencies = frequencies[mask]
amplitude_db = amplitude_db[mask]

# Create data source
source = ColumnDataSource(data={"frequency": frequencies, "amplitude": amplitude_db})

# Create figure (4800 x 2700 px for 16:9)
p = figure(
    width=4800,
    height=2700,
    title="spectrum-basic · bokeh · pyplots.ai",
    x_axis_label="Frequency (Hz)",
    y_axis_label="Amplitude (dB)",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Plot spectrum as line with area fill
p.line(x="frequency", y="amplitude", source=source, line_width=4, line_color="#306998", legend_label="Signal Spectrum")

# Add subtle fill under the curve
p.varea(x="frequency", y1="amplitude", y2=-80, source=source, fill_color="#306998", fill_alpha=0.2)

# Mark peak frequencies with vertical lines and circles
peak_freqs = [50, 150, 400]
peak_labels = ["50 Hz", "150 Hz", "400 Hz"]
for freq, label in zip(peak_freqs, peak_labels, strict=True):
    idx = np.argmin(np.abs(frequencies - freq))
    peak_amp = amplitude_db[idx]

    # Vertical line at peak
    p.line(x=[freq, freq], y=[-80, peak_amp], line_width=3, line_dash="dashed", line_color="#FFD43B", line_alpha=0.8)

    # Circle marker at peak
    p.scatter(
        x=[freq],
        y=[peak_amp],
        size=25,
        color="#FFD43B",
        line_color="#306998",
        line_width=3,
        legend_label=f"Peak: {label}",
    )

# Styling - text sizes for large canvas (4800x2700)
p.title.text_font_size = "36pt"
p.title.text_color = "#333333"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.label_text_font_size = "20pt"
p.legend.location = "top_right"
p.legend.background_fill_alpha = 0.8
p.legend.border_line_color = "#cccccc"
p.legend.padding = 10
p.legend.spacing = 5

# Background
p.background_fill_color = "#fafafa"

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="spectrum-basic · bokeh · pyplots.ai")
