"""anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (position 1 is the brand green)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Column constants
X_DIM = "Embedding Dimension 1"  # role: x
Y_DIM = "Embedding Dimension 2"  # role: y
LANGUAGE = "Language"  # role: label
GROUP = "Group"  # role: extra
TEXT_SIZE = "Text size (pt)"  # role: extra
TEXT_ALPHA = "Text opacity"  # role: extra

# Data: simulated word embeddings for programming languages.
# Replace this block with your own table, for example df = pd.read_csv("embeddings.csv")
np.random.seed(42)

labels = [
    "Python", "JavaScript", "Java", "C++", "Ruby", "Go", "Rust", "Swift", "Kotlin", "TypeScript",
    "PHP", "Scala", "R", "Julia", "Perl", "Lua", "Haskell", "Clojure", "Erlang", "Elixir",
    "Dart", "MATLAB", "Fortran", "COBOL", "Assembly", "SQL", "Bash", "PowerShell", "Groovy", "F#",
]  # fmt: skip

n = len(labels)
x = np.zeros(n)
y = np.zeros(n)

# Modern general-purpose languages
modern = [0, 1, 2, 8, 9, 10, 18, 20]
for i in modern:
    x[i] = np.random.normal(4, 1.2)
    y[i] = np.random.normal(3, 1.2)

# Systems languages
systems = [3, 5, 6, 7, 24]
for i in systems:
    x[i] = np.random.normal(-3, 1.0)
    y[i] = np.random.normal(4, 1.0)

# Functional languages
functional = [11, 16, 17, 19, 29]
for i, idx in enumerate(functional):
    x[idx] = np.random.normal(-3.5 + i * 0.8, 0.5)
    y[idx] = np.random.normal(-2.5 + i * 0.5, 0.5)

# Data science / scientific
scientific = [4, 12, 13, 21]
for i in scientific:
    x[i] = np.random.normal(1, 1.2)
    y[i] = np.random.normal(-3.5, 1.0)

# Scripting languages
scripting = [14, 15, 26, 27]
for i in scripting:
    x[i] = np.random.normal(-1, 1.5)
    y[i] = np.random.normal(0.5, 1.5)

# Legacy languages
legacy = [22, 23, 25, 28]
legacy_x_offsets = [0, 0.8, -0.8, 0.4]
for idx, x_off in zip(legacy, legacy_x_offsets, strict=True):
    x[idx] = np.random.normal(3 + x_off, 0.8)
    y[idx] = np.random.normal(-1, 0.8)

# Small jitter on the simulated embedding itself
jitter_x = np.random.normal(0, 0.15, n)
jitter_y = np.random.normal(0, 0.15, n)
jitter_x[[18, 23]] *= 0.5
jitter_y[[18, 23]] *= 0.5
x += jitter_x
y += jitter_y

# Per-group text size and opacity: modern prominent, the others subtler
styles = {
    "modern": (modern, 31, 0.95),
    "systems": (systems, 29, 0.80),
    "functional": (functional, 27, 0.75),
    "scientific": (scientific, 30, 0.85),
    "scripting": (scripting, 27, 0.78),
    "legacy": (legacy, 27, 0.73),
}
group = [""] * n
size = [0] * n
alpha = [0.0] * n
for name, (members, pt, opacity) in styles.items():
    for idx in members:
        group[idx], size[idx], alpha[idx] = name, pt, opacity

df = pd.DataFrame({X_DIM: x, Y_DIM: y, LANGUAGE: labels, GROUP: group, TEXT_SIZE: size, TEXT_ALPHA: alpha})

# Plot
p = figure(
    width=3200,
    height=1800,
    title="scatter-text · python · bokeh · anyplot.ai",
    x_axis_label=X_DIM,
    y_axis_label=Y_DIM,
    tools="pan,wheel_zoom,box_zoom,reset,save",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "50pt"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Invisible scatter layer so the hover tooltip works on every label position
source = ColumnDataSource(df)
p.scatter(X_DIM, Y_DIM, source=source, size=1, alpha=0)
p.add_tools(HoverTool(tooltips=[(LANGUAGE, f"@{{{LANGUAGE}}}"), (GROUP, f"@{{{GROUP}}}")]))

# Text labels as the marks, one LabelSet per text style, centered on the exact coordinates
for (pt, opacity), rows in df.groupby([TEXT_SIZE, TEXT_ALPHA], sort=False):
    p.add_layout(
        LabelSet(
            x=X_DIM,
            y=Y_DIM,
            text=LANGUAGE,
            source=ColumnDataSource(rows),
            text_font_size=f"{pt}pt",
            text_color=BRAND,
            text_alpha=opacity,
            text_align="center",
            text_baseline="middle",
        )
    )

# Save HTML + PNG
output_file(f"plot-{THEME}.html")
save(p)

W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
