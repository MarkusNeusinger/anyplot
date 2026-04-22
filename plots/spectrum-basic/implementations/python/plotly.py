""" pyplots.ai
spectrum-basic: Frequency Spectrum Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-31
"""

import numpy as np
import plotly.graph_objects as go


# Data - Generate synthetic signal with multiple frequency components
np.random.seed(42)

# Signal parameters
sample_rate = 1000  # Hz
duration = 1.0  # seconds
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Create synthetic signal: sum of sinusoids at 50, 120, and 300 Hz
signal = (
    1.0 * np.sin(2 * np.pi * 50 * t)  # 50 Hz fundamental
    + 0.5 * np.sin(2 * np.pi * 120 * t)  # 120 Hz component
    + 0.3 * np.sin(2 * np.pi * 300 * t)  # 300 Hz component
    + 0.1 * np.random.randn(n_samples)  # Noise
)

# Compute FFT
fft_result = np.fft.rfft(signal)
frequency = np.fft.rfftfreq(n_samples, 1 / sample_rate)
amplitude_db = 20 * np.log10(np.abs(fft_result) / n_samples + 1e-10)  # Convert to dB

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=frequency,
        y=amplitude_db,
        mode="lines",
        line=dict(color="#306998", width=2),
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.3)",
        name="Spectrum",
    )
)

# Layout
fig.update_layout(
    title=dict(text="spectrum-basic · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Frequency (Hz)", font=dict(size=22)),
        tickfont=dict(size=18),
        range=[0, 500],
        gridcolor="rgba(128, 128, 128, 0.3)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Amplitude (dB)", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.3)",
        gridwidth=1,
    ),
    template="plotly_white",
    showlegend=False,
    margin=dict(l=80, r=40, t=80, b=60),
)

# Add annotations for peak frequencies
peak_freqs = [50, 120, 300]
for freq in peak_freqs:
    idx = np.argmin(np.abs(frequency - freq))
    fig.add_annotation(
        x=frequency[idx],
        y=amplitude_db[idx],
        text=f"{freq} Hz",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#FFD43B",
        font=dict(size=16, color="#306998"),
        ax=0,
        ay=-40,
    )

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
