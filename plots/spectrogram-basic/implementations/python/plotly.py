"""anyplot.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93 | Updated: 2025-05-15
"""

import os

import numpy as np
import plotly.graph_objects as go
from scipy import signal


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - EEG biomedical signal with alpha-beta oscillations
np.random.seed(42)
sample_rate = 256  # Hz (standard EEG sampling rate)
duration = 4.0  # seconds
t = np.linspace(0, duration, int(sample_rate * duration))

# Simulate EEG with multiple frequency components
# Alpha waves (8-12 Hz), beta waves (12-30 Hz), and muscle artifact (50 Hz)
alpha = 2.0 * np.sin(2 * np.pi * 10 * t)  # 10 Hz alpha waves
beta = 1.5 * np.sin(2 * np.pi * 20 * t + np.pi / 4)  # 20 Hz beta waves
muscle_artifact = 0.8 * np.sin(2 * np.pi * 50 * t)  # 50 Hz artifact

# Add realistic noise and transient bursts
noise = np.random.randn(len(t)) * 0.5
transient = np.zeros_like(t)
transient[int(1.5 * sample_rate) : int(2.2 * sample_rate)] += 3.0 * np.sin(
    2 * np.pi * 15 * t[int(1.5 * sample_rate) : int(2.2 * sample_rate)]
)

eeg_signal = alpha + beta + muscle_artifact + noise + transient

# Compute spectrogram
nperseg = 128  # Window size for better frequency resolution
noverlap = 96  # Overlap (75% overlap for smooth visualization)
frequencies, times, Sxx = signal.spectrogram(eeg_signal, fs=sample_rate, nperseg=nperseg, noverlap=noverlap)

# Limit frequency range to 0-60 Hz (typical EEG band of interest)
freq_mask = frequencies <= 60
frequencies = frequencies[freq_mask]
Sxx = Sxx[freq_mask, :]

# Convert to dB scale for better visualization
Sxx_db = 10 * np.log10(Sxx + 1e-10)

# Create spectrogram heatmap
fig = go.Figure()

fig.add_trace(
    go.Heatmap(
        x=times,
        y=frequencies,
        z=Sxx_db,
        colorscale="Viridis",
        colorbar={
            "title": {"text": "Power (dB)", "font": {"size": 20, "color": INK}},
            "tickfont": {"size": 16, "color": INK_SOFT},
            "len": 0.85,
            "thickness": 25,
            "outlinecolor": INK_SOFT,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
        },
        hovertemplate="Time: %{x:.2f}s<br>Frequency: %{y:.1f}Hz<br>Power: %{z:.1f}dB<extra></extra>",
    )
)

# Layout
fig.update_layout(
    title={
        "text": "spectrogram-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Time (seconds)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "Frequency (Hz)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "showgrid": False,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 100, "r": 120, "t": 100, "b": 100},
    height=None,
    width=None,
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
