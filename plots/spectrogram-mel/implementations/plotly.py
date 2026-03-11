"""pyplots.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-11
"""

import numpy as np
import plotly.graph_objects as go


# Data - Synthesize audio with multiple frequency components (melody-like)
np.random.seed(42)
sample_rate = 22050
duration = 4.0
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Create a rich audio signal: melody with harmonics and chirp
signal = (
    0.5 * np.sin(2 * np.pi * 440 * t)
    + 0.3 * np.sin(2 * np.pi * 880 * t)
    + 0.2 * np.sin(2 * np.pi * 1320 * t)
    + 0.4 * np.sin(2 * np.pi * (200 + 600 * t / duration) * t)
    + 0.15 * np.sin(2 * np.pi * 3000 * t) * np.exp(-t / 2)
    + 0.1 * np.random.randn(n_samples)
)
# Add amplitude envelope to simulate natural audio
envelope = np.ones(n_samples)
envelope[: int(0.05 * sample_rate)] = np.linspace(0, 1, int(0.05 * sample_rate))
envelope[-int(0.3 * sample_rate) :] = np.linspace(1, 0, int(0.3 * sample_rate))
signal *= envelope

# STFT computation
n_fft = 2048
hop_length = 512
window = np.hanning(n_fft)
n_frames = 1 + (n_samples - n_fft) // hop_length
stft_matrix = np.zeros((n_fft // 2 + 1, n_frames))
for i in range(n_frames):
    start = i * hop_length
    frame = signal[start : start + n_fft] * window
    spectrum = np.fft.rfft(frame)
    stft_matrix[:, i] = np.abs(spectrum) ** 2

# Mel filterbank
n_mels = 128
f_min = 0.0
f_max = sample_rate / 2.0


mel_min = 2595.0 * np.log10(1.0 + f_min / 700.0)
mel_max = 2595.0 * np.log10(1.0 + f_max / 700.0)
mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)
freq_bins = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

filterbank = np.zeros((n_mels, n_fft // 2 + 1))
for m in range(1, n_mels + 1):
    f_left = freq_bins[m - 1]
    f_center = freq_bins[m]
    f_right = freq_bins[m + 1]
    for k in range(f_left, f_center):
        if f_center != f_left:
            filterbank[m - 1, k] = (k - f_left) / (f_center - f_left)
    for k in range(f_center, f_right):
        if f_right != f_center:
            filterbank[m - 1, k] = (f_right - k) / (f_right - f_center)

# Apply mel filterbank and convert to dB
mel_spec = filterbank @ stft_matrix
mel_spec = np.maximum(mel_spec, 1e-10)
mel_spec_db = 10.0 * np.log10(mel_spec)
ref_db = mel_spec_db.max()
mel_spec_db = mel_spec_db - ref_db

# Time and frequency axes
time_axis = np.arange(n_frames) * hop_length / sample_rate
mel_freq_points = np.linspace(mel_min, mel_max, n_mels)
mel_freqs = 700.0 * (10.0 ** (mel_freq_points / 2595.0) - 1.0)

# Plot
fig = go.Figure(
    data=go.Heatmap(
        z=mel_spec_db,
        x=time_axis,
        y=mel_freqs,
        colorscale="Inferno",
        colorbar={
            "title": {"text": "dB", "font": {"size": 20}},
            "tickfont": {"size": 16},
            "thickness": 18,
            "len": 0.85,
        },
        zmin=-80,
        zmax=0,
        hovertemplate="Time: %{x:.2f}s<br>Freq: %{y:.0f} Hz<br>Power: %{z:.1f} dB<extra></extra>",
    )
)

# Style
fig.update_layout(
    title={"text": "spectrogram-mel · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={"title": {"text": "Time (s)", "font": {"size": 22}}, "tickfont": {"size": 18}},
    yaxis={
        "title": {"text": "Frequency (Hz)", "font": {"size": 22}},
        "tickfont": {"size": 16},
        "type": "log",
        "tickvals": [50, 100, 200, 500, 1000, 2000, 4000, 8000],
        "ticktext": ["50", "100", "200", "500", "1k", "2k", "4k", "8k"],
    },
    template="plotly_white",
    plot_bgcolor="rgba(0,0,0,0)",
    width=1600,
    height=900,
    margin={"l": 80, "r": 30, "t": 70, "b": 60},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
