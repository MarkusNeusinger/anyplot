"""anyplot.ai
spectrum-basic: Frequency Spectrum Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — a single spectrum uses it alone

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
AMPLITUDE = "Amplitude (dB)"  # role: amplitude

# Data: replace this block with your own table, for example df = pd.read_csv("spectrum.csv")
np.random.seed(42)
sample_rate = 1000  # Hz
duration = 1.0  # seconds
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)
signal = (
    1.0 * np.sin(2 * np.pi * 50 * t)  # 50 Hz - dominant component
    + 0.5 * np.sin(2 * np.pi * 120 * t)  # 120 Hz - secondary component
    + 0.25 * np.sin(2 * np.pi * 200 * t)  # 200 Hz - weak component
    + 0.1 * np.random.randn(n_samples)  # broadband noise
)
spectrum = np.fft.rfft(signal)
frequencies = np.fft.rfftfreq(n_samples, 1 / sample_rate)
amplitude_db = 20 * np.log10(np.abs(spectrum) * 2 / n_samples + 1e-10)
df = pd.DataFrame({FREQUENCY: frequencies, AMPLITUDE: amplitude_db})
df = df[df[FREQUENCY] <= 300]

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
title = "spectrum-basic · python · altair · anyplot.ai"
title_fontsize = round(16 * (67 / len(title) if len(title) > 67 else 1.0))

chart = (
    alt.Chart(df)
    .mark_line(color=BRAND, strokeWidth=1.5)
    .encode(
        x=alt.X(
            FREQUENCY.translate(ESCAPE),
            type="quantitative",
            title=FREQUENCY,
            scale=alt.Scale(domain=[df[FREQUENCY].min(), df[FREQUENCY].max()], nice=False),
        ),
        y=alt.Y(
            AMPLITUDE.translate(ESCAPE),
            type="quantitative",
            title=AMPLITUDE,
            scale=alt.Scale(domain=[df[AMPLITUDE].min() - 5, df[AMPLITUDE].max() + 5]),
        ),
        tooltip=[
            alt.Tooltip(FREQUENCY.translate(ESCAPE), type="quantitative", title=FREQUENCY, format=".1f"),
            alt.Tooltip(AMPLITUDE.translate(ESCAPE), type="quantitative", title=AMPLITUDE, format=".1f"),
        ],
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        padding={"left": 10, "right": 20, "top": 10, "bottom": 10},
        title=alt.Title(title, fontSize=title_fontsize, anchor="middle", fontWeight="normal"),
    )
    .configure_view(fill=PAGE_BG, stroke=None, continuousWidth=620, continuousHeight=320)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        titleFontWeight="normal",
        domainColor=INK_SOFT,
        ticks=False,
        labelPadding=6,
        titlePadding=10,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_axisX(grid=False)
    .configure_axisY(grid=True, gridColor=INK, gridOpacity=0.12)
    .configure_title(color=INK)
)

# Save: PNG padded to exactly 3200 x 1800, plus the interactive HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
