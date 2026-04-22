""" pyplots.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import BasicTicker, ColorBar, LinearColorMapper
from bokeh.plotting import figure
from scipy import signal


# Data - Generate chirp signal with increasing frequency
np.random.seed(42)
sample_rate = 8000  # 8 kHz sampling rate
duration = 2.0  # 2 seconds
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Create a chirp signal: frequency increases from 200 Hz to 2000 Hz
f0 = 200  # Start frequency
f1 = 2000  # End frequency
chirp_signal = signal.chirp(t, f0, duration, f1, method="linear")

# Add some noise for realism
chirp_signal += 0.1 * np.random.randn(len(chirp_signal))

# Compute spectrogram using scipy.signal
nperseg = 256  # Window size
noverlap = 192  # Overlap (75%)
frequencies, times, Sxx = signal.spectrogram(
    chirp_signal, fs=sample_rate, nperseg=nperseg, noverlap=noverlap, scaling="density"
)

# Convert to dB scale for better visualization
Sxx_db = 10 * np.log10(Sxx + 1e-10)  # Add small value to avoid log(0)

# Viridis palette (256 colors) - perceptually uniform
viridis = [
    "#440154",
    "#440256",
    "#450457",
    "#450559",
    "#46075a",
    "#46085c",
    "#460a5d",
    "#460b5e",
    "#470d60",
    "#470e61",
    "#471063",
    "#471164",
    "#471365",
    "#481467",
    "#481668",
    "#481769",
    "#48186a",
    "#481a6c",
    "#481b6d",
    "#481c6e",
    "#481d6f",
    "#481f70",
    "#482071",
    "#482173",
    "#482374",
    "#482475",
    "#482576",
    "#482677",
    "#482878",
    "#482979",
    "#472a79",
    "#472c7a",
    "#472d7b",
    "#472e7c",
    "#472f7d",
    "#46307e",
    "#46327e",
    "#46337f",
    "#463480",
    "#453581",
    "#453681",
    "#453882",
    "#443983",
    "#443a83",
    "#443b84",
    "#433d84",
    "#433e85",
    "#423f85",
    "#424086",
    "#424186",
    "#414287",
    "#414487",
    "#404588",
    "#404688",
    "#3f4788",
    "#3f4889",
    "#3e4989",
    "#3e4a89",
    "#3d4b89",
    "#3d4c89",
    "#3c4d8a",
    "#3c4e8a",
    "#3b508a",
    "#3b518a",
    "#3a528b",
    "#3a538b",
    "#39548b",
    "#39558b",
    "#38568b",
    "#38578c",
    "#37588c",
    "#37598c",
    "#365a8c",
    "#365b8c",
    "#355c8c",
    "#355d8c",
    "#345e8d",
    "#345f8d",
    "#33608d",
    "#33618d",
    "#32628d",
    "#32638d",
    "#31648d",
    "#31658d",
    "#31668d",
    "#30678d",
    "#30688d",
    "#2f698d",
    "#2f6a8d",
    "#2e6b8e",
    "#2e6c8e",
    "#2e6d8e",
    "#2d6e8e",
    "#2d6f8e",
    "#2c708e",
    "#2c718e",
    "#2c728e",
    "#2b738e",
    "#2b748e",
    "#2a758e",
    "#2a768e",
    "#2a778e",
    "#29788e",
    "#29798e",
    "#297a8e",
    "#287b8e",
    "#287c8e",
    "#277d8e",
    "#277e8e",
    "#277f8e",
    "#26808e",
    "#26818e",
    "#26828e",
    "#25838e",
    "#25848e",
    "#25858e",
    "#24868e",
    "#24878e",
    "#23888e",
    "#23898e",
    "#238a8d",
    "#228b8d",
    "#228c8d",
    "#228d8d",
    "#218e8d",
    "#218f8d",
    "#21908d",
    "#21918c",
    "#20928c",
    "#20938c",
    "#20948c",
    "#1f958b",
    "#1f968b",
    "#1f978b",
    "#1f988a",
    "#1f998a",
    "#1f9a8a",
    "#1e9b89",
    "#1e9c89",
    "#1e9d88",
    "#1f9e88",
    "#1f9f88",
    "#1fa087",
    "#1fa187",
    "#1fa286",
    "#20a386",
    "#20a485",
    "#21a585",
    "#21a684",
    "#22a784",
    "#22a883",
    "#23a982",
    "#24aa82",
    "#24ab81",
    "#25ac81",
    "#26ad80",
    "#27ae80",
    "#27af7f",
    "#28b07e",
    "#29b17e",
    "#2ab27d",
    "#2cb37c",
    "#2db47c",
    "#2eb57b",
    "#2fb67a",
    "#30b77a",
    "#32b879",
    "#33b978",
    "#35ba78",
    "#36bb77",
    "#37bc76",
    "#39bd75",
    "#3abe75",
    "#3cbf74",
    "#3ec073",
    "#3fc172",
    "#41c272",
    "#43c371",
    "#44c470",
    "#46c56f",
    "#48c66e",
    "#4ac76d",
    "#4cc86d",
    "#4ec96c",
    "#50ca6b",
    "#51cb6a",
    "#53cc69",
    "#55cd68",
    "#57ce67",
    "#59cf66",
    "#5bd066",
    "#5dd165",
    "#5fd264",
    "#61d363",
    "#63d462",
    "#65d561",
    "#67d660",
    "#69d75f",
    "#6cd85e",
    "#6ed95d",
    "#70da5c",
    "#72db5b",
    "#74dc5a",
    "#76dd59",
    "#78de58",
    "#7bdf57",
    "#7de056",
    "#7fe155",
    "#81e254",
    "#83e353",
    "#86e452",
    "#88e551",
    "#8ae64f",
    "#8ce74e",
    "#8fe84d",
    "#91e94c",
    "#93ea4b",
    "#96eb4a",
    "#98ec49",
    "#9aed48",
    "#9dee47",
    "#9fef46",
    "#a1f045",
    "#a4f144",
    "#a6f243",
    "#a8f342",
    "#abf341",
    "#adf440",
    "#b0f540",
    "#b2f63f",
    "#b5f73e",
    "#b7f83d",
    "#baf93c",
    "#bcfa3c",
    "#bffb3b",
    "#c1fc3b",
    "#c4fd3a",
    "#c7fd3a",
    "#c9fe39",
    "#ccfe39",
    "#cfff38",
    "#d1ff38",
    "#d4ff38",
    "#d7ff37",
    "#d9ff37",
    "#dcff37",
    "#dfff36",
    "#e1ff36",
    "#e4ff36",
    "#e7ff36",
    "#e9ff36",
    "#ecff36",
    "#efff36",
    "#f1ff36",
    "#f4ff36",
    "#f6ff36",
]

# Create figure with appropriate size
p = figure(
    width=4800,
    height=2700,
    title="spectrogram-basic · bokeh · pyplots.ai",
    x_axis_label="Time (seconds)",
    y_axis_label="Frequency (Hz)",
    x_range=(times.min(), times.max()),
    y_range=(frequencies.min(), frequencies.max()),
    tools="",
    toolbar_location=None,
)

# Create color mapper
color_mapper = LinearColorMapper(palette=viridis, low=Sxx_db.min(), high=Sxx_db.max())

# Render spectrogram as image
p.image(
    image=[Sxx_db],
    x=times.min(),
    y=frequencies.min(),
    dw=times.max() - times.min(),
    dh=frequencies.max() - frequencies.min(),
    color_mapper=color_mapper,
    level="image",
)

# Add colorbar with larger text
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(),
    label_standoff=20,
    border_line_color=None,
    location=(0, 0),
    title="Power (dB)",
    title_text_font_size="36pt",
    major_label_text_font_size="28pt",
    width=80,
    padding=40,
)
p.add_layout(color_bar, "right")

# Style text sizes for 4800x2700 canvas - enlarged for visibility
p.title.text_font_size = "48pt"
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.major_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "28pt"

# Axis styling
p.xaxis.axis_line_width = 3
p.yaxis.axis_line_width = 3
p.xaxis.major_tick_line_width = 3
p.yaxis.major_tick_line_width = 3

# Grid styling - subtle
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = None
p.border_fill_color = None

# Outline
p.outline_line_color = "#333333"
p.outline_line_width = 2

# Save PNG
export_png(p, filename="plot.png")

# Save HTML for interactive viewing
output_file("plot.html", title="spectrogram-basic · bokeh · pyplots.ai")
save(p)
