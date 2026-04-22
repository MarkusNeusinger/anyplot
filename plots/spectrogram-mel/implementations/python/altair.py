""" pyplots.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: altair 6.0.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-11
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - synthesize a rich audio signal with melody and harmonics
np.random.seed(42)
sample_rate = 22050
duration = 4.0
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Descending frequency sweep from 1200 Hz to 300 Hz with harmonics
sweep_freq = np.cumsum(1200 * np.exp(-0.35 * t)) / sample_rate
signal = 0.6 * np.sin(2 * np.pi * sweep_freq)
signal += 0.3 * np.sin(2 * np.pi * 2 * sweep_freq)
signal += 0.15 * np.sin(2 * np.pi * 3 * sweep_freq)

# Pulsed tone at 440 Hz (A4) with amplitude modulation
envelope = 0.5 * (1 + np.sin(2 * np.pi * 2.5 * t))
signal += 0.4 * envelope * np.sin(2 * np.pi * 440 * t)

# High-frequency chirp burst in the middle section
chirp_mask = (t > 1.5) & (t < 2.5)
chirp_phase = np.cumsum(chirp_mask * (2000 + 3000 * (t - 1.5))) / sample_rate
signal += 0.35 * chirp_mask * np.sin(2 * np.pi * chirp_phase)

# Subtle noise floor
signal += 0.05 * np.random.randn(n_samples)

# Compute STFT
n_fft = 2048
hop_length = 512
window = np.hanning(n_fft)
n_freq_bins = n_fft // 2 + 1
n_frames = 1 + (n_samples - n_fft) // hop_length

stft_power = np.zeros((n_freq_bins, n_frames))
for i in range(n_frames):
    start = i * hop_length
    frame = signal[start : start + n_fft] * window
    spectrum = np.fft.rfft(frame)
    stft_power[:, i] = np.abs(spectrum) ** 2

# Mel filter bank
n_mels = 128
f_max = sample_rate / 2.0

mel_max = 2595.0 * np.log10(1.0 + f_max / 700.0)
mel_edges = np.linspace(0, mel_max, n_mels + 2)
hz_edges = 700.0 * (10.0 ** (mel_edges / 2595.0) - 1.0)
fft_freqs = np.linspace(0, f_max, n_freq_bins)

filterbank = np.zeros((n_mels, n_freq_bins))
for i in range(n_mels):
    lo, mid, hi = hz_edges[i], hz_edges[i + 1], hz_edges[i + 2]
    up_slope = (fft_freqs >= lo) & (fft_freqs <= mid)
    dn_slope = (fft_freqs > mid) & (fft_freqs <= hi)
    if mid > lo:
        filterbank[i, up_slope] = (fft_freqs[up_slope] - lo) / (mid - lo)
    if hi > mid:
        filterbank[i, dn_slope] = (hi - fft_freqs[dn_slope]) / (hi - mid)

# Apply mel filter and convert to dB
mel_spec = filterbank @ stft_power
mel_spec = np.maximum(mel_spec, 1e-10)
mel_spec_db = 10.0 * np.log10(mel_spec)
mel_spec_db -= mel_spec_db.max()
mel_spec_db = np.maximum(mel_spec_db, -80.0)

# Use ALL mel bins (no subsampling) to fix blockiness at low frequencies
# Only subsample time frames to keep data manageable
frame_step = 2
time_idx = np.arange(0, n_frames, frame_step)
mel_idx = np.arange(0, n_mels)

time_sec = time_idx * hop_length / sample_rate
time_width = frame_step * hop_length / sample_rate

# Build dataframe with explicit rectangle bounds
rows = []
for mi in mel_idx:
    freq_lo = float(hz_edges[mi])
    freq_hi = float(hz_edges[mi + 2])
    for ti_pos, ti in enumerate(time_idx):
        rows.append(
            {
                "t1": round(float(time_sec[ti_pos]), 4),
                "t2": round(float(time_sec[ti_pos]) + time_width, 4),
                "f1": round(max(freq_lo, 20), 1),
                "f2": round(freq_hi, 1),
                "dB": round(float(mel_spec_db[mi, ti]), 1),
            }
        )

df = pd.DataFrame(rows)

# Annotation labels for key audio features (data storytelling)
annotations = pd.DataFrame(
    [
        {"x": 0.6, "y": 1200, "label": "Harmonic Sweep"},
        {"x": 2.2, "y": 6500, "label": "Chirp Burst"},
        {"x": 3.5, "y": 350, "label": "440 Hz Tone"},
    ]
)

# Main spectrogram layer
spectrogram = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X(
            "t1:Q",
            title="Time (s)",
            scale=alt.Scale(domain=[0, duration], nice=False),
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                titlePadding=14,
                values=[0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
                domainColor="#444444",
                tickColor="#444444",
                labelColor="#333333",
                titleColor="#222222",
                tickSize=6,
            ),
        ),
        x2="t2:Q",
        y=alt.Y(
            "f1:Q",
            title="Frequency (Hz)",
            scale=alt.Scale(type="log", domain=[20, 11025], nice=False),
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                titlePadding=14,
                values=[50, 100, 200, 500, 1000, 2000, 5000, 10000],
                domainColor="#444444",
                tickColor="#444444",
                labelColor="#333333",
                titleColor="#222222",
                tickSize=6,
                labelExpr="datum.value >= 1000 ? format(datum.value / 1000, '.0f') + 'k' : format(datum.value, '.0f')",
            ),
        ),
        y2="f2:Q",
        color=alt.Color(
            "dB:Q",
            scale=alt.Scale(scheme="inferno", domain=[-80, 0]),
            legend=alt.Legend(
                title="Power (dB)",
                titleFontSize=18,
                labelFontSize=16,
                gradientLength=480,
                gradientThickness=18,
                titlePadding=10,
                offset=14,
                direction="vertical",
                titleColor="#222222",
                labelColor="#333333",
            ),
        ),
        tooltip=[
            alt.Tooltip("t1:Q", title="Time (s)", format=".2f"),
            alt.Tooltip("f1:Q", title="Freq low (Hz)", format=".0f"),
            alt.Tooltip("f2:Q", title="Freq high (Hz)", format=".0f"),
            alt.Tooltip("dB:Q", title="Power (dB)", format=".1f"),
        ],
    )
)

# Annotation text layer for data storytelling emphasis
annotation_labels = (
    alt.Chart(annotations)
    .mark_text(
        fontSize=16, fontWeight="bold", color="#ffffff", strokeWidth=3, stroke="#1a1a2e", align="left", dx=10, dy=-6
    )
    .encode(x="x:Q", y="y:Q", text="label:N")
)

# Small arrow markers pointing to features
annotation_marks = (
    alt.Chart(annotations)
    .mark_point(shape="triangle-right", size=150, color="#ffffff", strokeWidth=2, stroke="#1a1a2e", filled=True)
    .encode(x="x:Q", y="y:Q")
)

# Layer composition: spectrogram + annotations
chart = (
    alt.layer(spectrogram, annotation_marks, annotation_labels)
    .properties(
        width=1400,
        height=800,
        title=alt.Title(
            "spectrogram-mel · altair · pyplots.ai",
            subtitle="Mel-scaled power spectrogram of a synthesized signal — frequency sweep with harmonics, pulsed 440 Hz tone, and chirp burst",
            fontSize=28,
            subtitleFontSize=17,
            subtitleColor="#555555",
            anchor="start",
            offset=20,
            color="#111111",
        ),
        padding={"left": 24, "right": 24, "top": 24, "bottom": 20},
    )
    .configure_axis(grid=False)
    .configure_view(strokeWidth=0)
    .configure(font="Helvetica Neue, Helvetica, Arial, sans-serif", background="#fafafa")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
