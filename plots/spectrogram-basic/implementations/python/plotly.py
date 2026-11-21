""" anyplot.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: plotly 7.1.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import signal


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Continuous colormap: Imprint sequential (brand green to blue)
IMPRINT_SEQ = [[0.0, IMPRINT_PALETTE[0]], [1.0, IMPRINT_PALETTE[2]]]

# Constants
MAX_FREQ_HZ = 60  # upper edge of the EEG band of interest
FLOOR_DB = 40  # dynamic range kept below the strongest component, in dB

# Columns: set these to your table's column names
TIME = "Time (seconds)"  # role: extra
SIGNAL = "EEG amplitude (µV)"  # role: signal
SAMPLE_RATE = "Sample rate (Hz)"  # role: sample_rate

# Data: replace this block with your own table, for example df = pd.read_csv("eeg.csv")
rng = np.random.default_rng(42)
fs = 256  # Hz, standard EEG sampling rate
t = np.arange(0, 4.0, 1 / fs)
alpha = 2.0 * np.sin(2 * np.pi * 10 * t)  # 10 Hz alpha rhythm
beta = 1.5 * np.sin(2 * np.pi * 20 * t + np.pi / 4)  # 20 Hz beta rhythm
muscle = 0.8 * np.sin(2 * np.pi * 50 * t)  # 50 Hz muscle artifact
burst = np.where((t >= 1.5) & (t < 2.2), 3.0 * np.sin(2 * np.pi * 15 * t), 0.0)  # transient burst
noise = rng.normal(0, 0.5, len(t))
df = pd.DataFrame({TIME: t, SIGNAL: alpha + beta + muscle + burst + noise, SAMPLE_RATE: fs})

# Plot: reads only df and the constants above
sample_rate = df[SAMPLE_RATE].iloc[0]
nperseg = min(128, len(df))
samples = df[SIGNAL].interpolate(limit_direction="both").to_numpy()  # a gap is bridged, never zero-filled
frequencies, times, power = signal.spectrogram(samples, fs=sample_rate, nperseg=nperseg, noverlap=nperseg * 15 // 16)
times = times + df[TIME].iloc[0]
keep = frequencies <= MAX_FREQ_HZ
frequencies, power = frequencies[keep], power[keep, :]
power_db = 10 * np.log10(power + 1e-10)
zmax = np.nanmax(power_db)

fig = go.Figure(
    go.Heatmap(
        x=times,
        y=frequencies,
        z=power_db,
        zmin=zmax - FLOOR_DB,
        zmax=zmax,
        colorscale=IMPRINT_SEQ,
        colorbar={
            "title": {"text": "Power (dB)", "font": {"size": 12, "color": INK}},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "len": 0.85,
            "thickness": 16,
            "outlinecolor": INK_SOFT,
            "outlinewidth": 1,
        },
        hovertemplate="Time: %{x:.2f} s<br>Frequency: %{y:.1f} Hz<br>Power: %{z:.1f} dB<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "spectrogram-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": df.columns[0], "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "linecolor": INK_SOFT,
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "Frequency (Hz)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "linecolor": INK_SOFT,
        "showgrid": False,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
