"""anyplot.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, FixedTicker, HoverTool, Label, Range1d, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GENOME_WIDE_P = 5e-8  # conventional genome-wide significance threshold
SUGGESTIVE_P = 1e-5  # optional suggestive threshold

# Columns: set these to your table's column names
CHROMOSOME = "Chromosome"  # role: chromosome
POSITION = "Position (bp)"  # role: position
P_VALUE = "p-value"  # role: p_value

# Data: replace this block with your own table, for example df = pd.read_csv("gwas.csv")
np.random.seed(42)
chrom_sizes_mb = {
    "1": 248,
    "2": 242,
    "3": 198,
    "4": 190,
    "5": 181,
    "6": 170,
    "7": 159,
    "8": 145,
    "9": 138,
    "10": 133,
    "11": 135,
    "12": 133,
    "13": 114,
    "14": 107,
    "15": 101,
    "16": 90,
    "17": 83,
    "18": 80,
    "19": 58,
    "20": 64,
    "21": 46,
    "22": 50,
}
n_snps_per_chrom = 2000
peak_chromosomes = ["2", "6", "11", "17"]
chunks = []
for chrom, size in chrom_sizes_mb.items():
    positions = np.sort(np.random.randint(1, size * 1_000_000, n_snps_per_chrom))
    p_values = np.random.uniform(0.001, 1.0, n_snps_per_chrom)
    if chrom in peak_chromosomes:
        n_peak = np.random.randint(5, 15)
        peak_idx = np.random.choice(n_snps_per_chrom, n_peak, replace=False)
        p_values[peak_idx] = 10 ** np.random.uniform(-12, -8, n_peak)
    chunks.append(pd.DataFrame({CHROMOSOME: chrom, POSITION: positions, P_VALUE: p_values}))
df = pd.concat(chunks, ignore_index=True)

# Plot: reads only df and the constants above
NEG_LOG_P = "-log₁₀(p-value)"
CUMULATIVE = "Cumulative position (bp)"
chroms = list(df[CHROMOSOME].unique())
extent = df.groupby(CHROMOSOME, sort=False)[POSITION].max()
offsets = extent.cumsum().shift(fill_value=0)
df[CUMULATIVE] = df[POSITION] + df[CHROMOSOME].map(offsets)
df[NEG_LOG_P] = -np.log10(df[P_VALUE])
centers = offsets + extent / 2

sig_line = -np.log10(GENOME_WIDE_P)
sug_line = -np.log10(SUGGESTIVE_P)
is_sig = df[NEG_LOG_P] >= sig_line
is_odd = df[CHROMOSOME].map({c: i % 2 == 0 for i, c in enumerate(chroms)})
groups = [
    ("Odd chromosomes", ~is_sig & is_odd, IMPRINT_PALETTE[0], 4),
    ("Even chromosomes", ~is_sig & ~is_odd, IMPRINT_PALETTE[1], 4),
    ("Genome-wide significant", is_sig, IMPRINT_PALETTE[6], 11),
]

title = "manhattan-gwas · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=CHROMOSOME,
    y_axis_label=NEG_LOG_P,
    tools="pan,wheel_zoom,box_zoom,reset,save",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)
p.y_range = Range1d(0, df[NEG_LOG_P].max() * 1.08)
p.x_range = Range1d(0, extent.sum())

for label, mask, color, size in groups:
    p.scatter(
        x=CUMULATIVE,
        y=NEG_LOG_P,
        source=ColumnDataSource(df[mask]),
        size=size,
        color=color,
        alpha=1.0 if size > 4 else 0.7,
        line_color=None,
        legend_label=label,
    )

# Threshold lines: dashed genome-wide, dotted suggestive
p.add_layout(Span(location=sig_line, dimension="width", line_color=INK_SOFT, line_dash="dashed", line_width=3))
p.add_layout(Span(location=sug_line, dimension="width", line_color=INK_SOFT, line_dash="dotted", line_width=2))
for loc, text in (
    (sig_line, f"p = {GENOME_WIDE_P / 1e-8:.0f}×10⁻⁸"),
    (sug_line, f"p = {SUGGESTIVE_P / 1e-5:.0f}×10⁻⁵"),
):
    p.add_layout(
        Label(
            x=extent.sum(),
            y=loc,
            y_offset=8,
            x_offset=-10,
            text=text,
            text_font_size="24pt",
            text_align="right",
            text_color=INK_SOFT,
            background_fill_color=PAGE_BG,
            background_fill_alpha=0.8,
        )
    )

p.add_tools(
    HoverTool(
        tooltips=[
            (CHROMOSOME, f"@{{{CHROMOSOME}}}"),
            (POSITION, f"@{{{POSITION}}}{{0,0}}"),
            (NEG_LOG_P, f"@{{{NEG_LOG_P}}}{{0.00}}"),
        ]
    )
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.ticker = FixedTicker(ticks=[float(c) for c in centers])
p.xaxis.major_label_overrides = {float(c): str(name) for name, c in centers.items()}
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "30pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.legend.location = "top_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK
p.legend.label_text_font_size = "26pt"
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.padding = 20

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
