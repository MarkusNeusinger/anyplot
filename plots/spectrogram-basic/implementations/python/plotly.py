""" pyplots.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-31
"""

import numpy as np
import plotly.graph_objects as go
from scipy import signal


# Data - Create a chirp signal with increasing frequency
np.random.seed(42)
sample_rate = 4000  # Hz
duration = 2.0  # seconds
t = np.linspace(0, duration, int(sample_rate * duration))

# Chirp signal: frequency sweeps from 100 Hz to 800 Hz
f0, f1 = 100, 800
chirp_signal = signal.chirp(t, f0=f0, f1=f1, t1=duration, method="linear")

# Add some noise for realism
noise = np.random.randn(len(t)) * 0.1
audio_signal = chirp_signal + noise

# Compute spectrogram
nperseg = 256  # Window size
noverlap = 200  # Overlap for smooth visualization
frequencies, times, Sxx = signal.spectrogram(audio_signal, fs=sample_rate, nperseg=nperseg, noverlap=noverlap)

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
            "title": {"text": "Power (dB)", "font": {"size": 20}},
            "tickfont": {"size": 16},
            "len": 0.85,
            "thickness": 25,
        },
        hovertemplate="Time: %{x:.3f}s<br>Frequency: %{y:.0f}Hz<br>Power: %{z:.1f}dB<extra></extra>",
    )
)

# Layout
fig.update_layout(
    title={"text": "spectrogram-basic · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={"title": {"text": "Time (seconds)", "font": {"size": 22}}, "tickfont": {"size": 18}},
    yaxis={"title": {"text": "Frequency (Hz)", "font": {"size": 22}}, "tickfont": {"size": 18}},
    template="plotly_white",
    margin={"l": 100, "r": 120, "t": 100, "b": 100},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
