"""anyplot.ai
spectrum-basic: Frequency Spectrum Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: first position is the single series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_PEAKS = 3  # the dominant components that get a label

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
AMPLITUDE = "Amplitude (dB)"  # role: amplitude

# Data: replace this block with your own table, for example df = pd.read_csv("spectrum.csv")
np.random.seed(42)
sample_rate = 1000  # Hz
n_samples = 1000  # one second of signal
t = np.arange(n_samples) / sample_rate
signal = (
    1.0 * np.sin(2 * np.pi * 50 * t)
    + 0.5 * np.sin(2 * np.pi * 120 * t)
    + 0.3 * np.sin(2 * np.pi * 300 * t)
    + 0.1 * np.random.randn(n_samples)
)
fft_result = np.fft.rfft(signal)
df = pd.DataFrame(
    {
        FREQUENCY: np.fft.rfftfreq(n_samples, 1 / sample_rate),
        AMPLITUDE: 20 * np.log10(np.abs(fft_result) / n_samples + 1e-10),
    }
)

# Plot: reads only df and the constants above
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[FREQUENCY],
        y=df[AMPLITUDE],
        mode="lines",
        line={"color": IMPRINT_PALETTE[0], "width": 2.5},
        fill="tozeroy",
        fillcolor="rgba(0, 158, 115, 0.15)",
        name="Spectrum",
        hovertemplate="<b>Frequency:</b> %{x:.1f} Hz<br><b>Amplitude:</b> %{y:.1f} dB<extra></extra>",
    )
)

# Label the strongest bins, found by rule
for idx in df[AMPLITUDE].nlargest(N_PEAKS).index:
    fig.add_annotation(
        x=df.loc[idx, FREQUENCY],
        y=df.loc[idx, AMPLITUDE],
        text=f"{df.loc[idx, FREQUENCY]:.0f} Hz",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=1.5,
        arrowcolor=INK_SOFT,
        font={"size": 11, "color": INK},
        ax=0,
        ay=-30,
    )

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    title={
        "text": "spectrum-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": FREQUENCY, "font": {"size": 13, "color": INK}},
        "tickfont": {"size": 11, "color": INK_SOFT},
        "range": [0, df[FREQUENCY].max()],
        "gridcolor": GRID,
        "gridwidth": 0.8,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": AMPLITUDE, "font": {"size": 13, "color": INK}},
        "tickfont": {"size": 11, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 0.8,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    hovermode="x unified",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
