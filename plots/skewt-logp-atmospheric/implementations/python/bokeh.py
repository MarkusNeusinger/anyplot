""" anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 88/100 | Updated: 2026-11-26
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, CrosshairTool, HoverTool, Label, WheelZoomTool
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SKEW_FACTOR = 45  # degrees C of horizontal shift per decade of pressure (45 degree isotherms)
P_REF = 1000.0  # reference pressure (hPa) for skew, adiabats and mixing ratios
KAPPA = 0.286  # R/cp for dry air
R_DRY = 287.0  # gas constant of dry air (J/kg/K)
CP_DRY = 1004.0  # specific heat of dry air (J/kg/K)
L_VAP = 2.5e6  # latent heat of vaporisation (J/kg)
EPS = 0.622  # ratio of gas constants, dry air to water vapour
ISOTHERMS = np.arange(-80, 50, 10)
DRY_THETAS = np.arange(250, 400, 20)  # potential temperatures (K)
MOIST_STARTS = np.arange(-10, 35, 10)  # surface temperatures (C) of the pseudoadiabats
MIXING_RATIOS = [1, 2, 4, 8, 12, 16, 20]
X_RANGE = (-50, 50)

# Column constants
PRESSURE = "Pressure (hPa)"  # role: pressure
TEMPERATURE = "Temperature (°C)"  # role: temperature
DEWPOINT = "Dewpoint (°C)"  # role: dewpoint

# Data: replace this block with your own sounding, for example df = pd.read_csv("sounding.csv")
np.random.seed(42)
levels = [1000, 975, 950, 925, 900, 875, 850, 825, 800, 775, 750, 725, 700]
levels += [650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100]
temp_base = [25, 23, 21, 19, 17, 15, 13, 11, 9, 7, 5, 3, 1, -3, -8, -14, -20, -28, -36, -44, -52, -58, -62, -66, -68]
dew_base = [
    20,
    18,
    16,
    14,
    12,
    10,
    7,
    4,
    1,
    -3,
    -7,
    -12,
    -17,
    -24,
    -32,
    -40,
    -45,
    -50,
    -54,
    -58,
    -62,
    -66,
    -70,
    -74,
    -78,
]
temp_noisy = np.array(temp_base) + np.random.randn(len(levels)) * 0.5
dew_noisy = np.array(dew_base) + np.random.randn(len(levels)) * 0.3
df = pd.DataFrame({PRESSURE: levels, TEMPERATURE: temp_noisy, DEWPOINT: np.minimum(dew_noisy, temp_noisy - 0.5)})

# Plot
pressure = df[PRESSURE].to_numpy()
p_range = np.logspace(np.log10(pressure.max()), np.log10(pressure.min()), 50)
log_p = np.log10(p_range / P_REF)
x_temp = df[TEMPERATURE] - SKEW_FACTOR * np.log10(df[PRESSURE] / P_REF)
x_dewpoint = df[DEWPOINT] - SKEW_FACTOR * np.log10(df[PRESSURE] / P_REF)
sounding = ColumnDataSource(
    {
        "x_temp": x_temp,
        "x_dew": x_dewpoint,
        "y": df[PRESSURE],
        "temp_c": df[TEMPERATURE].round(1),
        "dew_c": df[DEWPOINT].round(1),
    }
)

fig = figure(
    width=3200,
    height=1800,
    title="skewt-logp-atmospheric · python · bokeh · anyplot.ai",
    x_axis_label=f"{TEMPERATURE} — Skewed Coordinates",
    y_axis_label=PRESSURE,
    y_axis_type="log",
    y_range=(pressure.max() * 1.05, pressure.min() * 0.95),
    x_range=X_RANGE,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

# Theme-adaptive chrome
fig.background_fill_color = PAGE_BG
fig.border_fill_color = PAGE_BG
fig.outline_line_color = None

fig.title.text_color = INK
fig.title.text_font_size = "50pt"
fig.xaxis.axis_label_text_color = INK
fig.yaxis.axis_label_text_color = INK
fig.xaxis.axis_label_text_font_size = "42pt"
fig.yaxis.axis_label_text_font_size = "42pt"
fig.xaxis.major_label_text_color = INK_SOFT
fig.yaxis.major_label_text_color = INK_SOFT
fig.xaxis.major_label_text_font_size = "34pt"
fig.yaxis.major_label_text_font_size = "34pt"
fig.xaxis.axis_line_color = INK_SOFT
fig.yaxis.axis_line_color = INK_SOFT
fig.xaxis.major_tick_line_color = INK_SOFT
fig.yaxis.major_tick_line_color = INK_SOFT
fig.xgrid.grid_line_color = INK
fig.ygrid.grid_line_color = INK
fig.xgrid.grid_line_alpha = 0.10
fig.ygrid.grid_line_alpha = 0.10

# Isotherms (45° skewed background reference lines)
for t in ISOTHERMS:
    x_iso = np.full_like(p_range, t) - SKEW_FACTOR * log_p
    src = ColumnDataSource(data={"x": x_iso, "y": p_range})
    fig.line(x="x", y="y", source=src, line_color=INK_MUTED, line_width=1.2, line_alpha=0.20)

# Dry adiabats (lines of constant potential temperature)
for theta in DRY_THETAS:
    t_adiabat = theta * (p_range / P_REF) ** KAPPA - 273.15
    x_adiabat = t_adiabat - SKEW_FACTOR * log_p
    mask = (t_adiabat > -80) & (t_adiabat < 60)
    if np.any(mask):
        src = ColumnDataSource(data={"x": x_adiabat[mask], "y": p_range[mask]})
        fig.line(
            x="x", y="y", source=src, line_color=IMPRINT_PALETTE[4], line_width=1.5, line_alpha=0.50, line_dash="dashed"
        )

# Moist adiabats (pseudoadiabats: integrated saturated lapse rate)
for t_start in MOIST_STARTS:
    t_moist = [t_start]
    t_k = t_start + 273.15
    for p_prev, p_level in zip(p_range[:-1], p_range[1:], strict=True):
        n_sub = 8
        dp = (p_level - p_prev) / n_sub
        p_cur = p_prev
        for _ in range(n_sub):
            e_sat = 6.112 * np.exp(17.67 * (t_k - 273.15) / (t_k - 273.15 + 243.5))
            r_sat = EPS * e_sat / (p_cur - e_sat)
            dt_dp = (R_DRY * t_k + L_VAP * r_sat) / (p_cur * (CP_DRY + L_VAP**2 * r_sat * EPS / (R_DRY * t_k**2)))
            t_k += dt_dp * dp
            p_cur += dp
        t_moist.append(t_k - 273.15)
    t_moist = np.array(t_moist)
    x_moist = t_moist - SKEW_FACTOR * log_p
    mask = (t_moist > -80) & (t_moist < 60)
    if np.any(mask):
        src = ColumnDataSource(data={"x": x_moist[mask], "y": p_range[mask]})
        fig.line(
            x="x",
            y="y",
            source=src,
            line_color=IMPRINT_PALETTE[5],
            line_width=1.5,
            line_alpha=0.50,
            line_dash="dotdash",
        )

# Mixing ratio lines
for mr in MIXING_RATIOS:
    e_mr = mr / 1000 * p_range / (EPS + mr / 1000)  # vapour pressure (hPa) at each level
    ln_e = np.log(e_mr / 6.112)
    td_mr = 243.5 * ln_e / (17.67 - ln_e)  # inverse Magnus formula
    x_mr = td_mr - SKEW_FACTOR * log_p
    src = ColumnDataSource(data={"x": x_mr, "y": p_range})
    fig.line(x="x", y="y", source=src, line_color=IMPRINT_PALETTE[3], line_width=2, line_alpha=0.60, line_dash="dotted")

# Highlighted 0°C isotherm
x_freeze = -SKEW_FACTOR * log_p
src_freeze = ColumnDataSource(data={"x": x_freeze, "y": p_range})
fig.line(
    x="x",
    y="y",
    source=src_freeze,
    line_color=IMPRINT_PALETTE[2],
    line_width=3,
    line_alpha=0.85,
    legend_label="0°C Isotherm",
)

# Temperature profile
fig.line(x="x_temp", y="y", source=sounding, line_color=IMPRINT_PALETTE[0], line_width=5, legend_label="Temperature")
temp_scatter = fig.scatter(x="x_temp", y="y", source=sounding, size=14, color=IMPRINT_PALETTE[0], alpha=0.85)

# Dewpoint profile
fig.line(
    x="x_dew",
    y="y",
    source=sounding,
    line_color=IMPRINT_PALETTE[1],
    line_width=5,
    line_dash="dashed",
    legend_label="Dewpoint",
)
dew_scatter = fig.scatter(
    x="x_dew", y="y", source=sounding, size=14, color=IMPRINT_PALETTE[1], alpha=0.85, marker="diamond"
)

# HoverTools for interactive temperature/pressure display
fig.add_tools(HoverTool(renderers=[temp_scatter], tooltips=[(PRESSURE, "@y{0}"), (TEMPERATURE, "@temp_c")]))
fig.add_tools(HoverTool(renderers=[dew_scatter], tooltips=[(PRESSURE, "@y{0}"), (DEWPOINT, "@dew_c")]))
fig.add_tools(CrosshairTool(), WheelZoomTool())

# Reference line labels
fig.add_layout(
    Label(x=-12, y=270, text="Dry Adiabats", text_font_size="33pt", text_color=IMPRINT_PALETTE[4], text_alpha=0.90)
)
fig.add_layout(
    Label(x=34, y=195, text="Moist Adiabats", text_font_size="33pt", text_color=IMPRINT_PALETTE[5], text_alpha=0.90)
)
fig.add_layout(
    Label(x=-44, y=590, text="Mixing Ratio", text_font_size="33pt", text_color=IMPRINT_PALETTE[3], text_alpha=0.90)
)

# Legend
fig.legend.location = "top_left"
fig.legend.label_text_font_size = "34pt"
fig.legend.label_text_color = INK_SOFT
fig.legend.background_fill_color = ELEVATED_BG
fig.legend.border_line_color = INK_SOFT
fig.legend.glyph_height = 50
fig.legend.glyph_width = 50
fig.legend.spacing = 12
fig.legend.padding = 18

# Save interactive HTML
output_file(f"plot-{THEME}.html")
save(fig)

# Screenshot with headless Chrome (Selenium 4 / Selenium Manager)
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
# Override emulated viewport to exactly W×H regardless of browser chrome overhead
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
