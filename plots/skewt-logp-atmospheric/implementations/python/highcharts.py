"""anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: highcharts | Python 3.13
Quality: pending | Updated: 2026-05-20
"""

import os
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
PAGE_BG_RGB = (250, 248, 241) if THEME == "light" else (26, 26, 23)
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data series colors (Okabe-Ito) — warm/cool meteorological convention
TEMP_COLOR = "#D55E00"  # vermillion — temperature profile (warm)
DEW_COLOR = "#0072B2"  # blue — dewpoint profile (cool)
DRY_AD_COLOR = "#E69F00"  # orange — dry adiabats
MOIST_AD_COLOR = "#009E73"  # green — moist adiabats
MIX_COLOR = "#56B4E9"  # sky blue — mixing ratio lines

# Canvas: 3200×1800 landscape (hard rule)
WIDTH = 3200
HEIGHT = 1800
MARGIN_L = 290
MARGIN_R = 100
MARGIN_T = 120
MARGIN_B = 150
PLOT_W = WIDTH - MARGIN_L - MARGIN_R  # 2810
PLOT_H = HEIGHT - MARGIN_T - MARGIN_B  # 1530

# Temperature and pressure extents
TEMP_MIN, TEMP_MAX = -80, 50
P_MIN, P_MAX = 100, 1000
LOG_PMIN = np.log10(P_MIN)  # 2.0
LOG_PMAX = np.log10(P_MAX)  # 3.0
LOG_PRANGE = LOG_PMAX - LOG_PMIN  # 1.0

# Sounding data — standard atmospheric profile
np.random.seed(42)
pressure = np.array([1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100])
temperature = np.array([28, 22, 15, 4, -18, -32, -45, -52, -56, -56, -55])
dewpoint = np.array([20, 16, 10, -2, -25, -42, -55, -62, -70, -75, -80])

# Coordinate transforms (inline numpy, no functions)
# y = MARGIN_T + (log10(p) - LOG_PMIN) / LOG_PRANGE * PLOT_H
# x = MARGIN_L + (T - TEMP_MIN) / (TEMP_MAX - TEMP_MIN) * PLOT_W - (1 - yfrac) * PLOT_W
#   where yfrac = (log10(p) - LOG_PMIN) / LOG_PRANGE  [0=top, 1=bottom]
LOG_P_S = np.log10(pressure)
YFRAC_S = (LOG_P_S - LOG_PMIN) / LOG_PRANGE
Y_S = MARGIN_T + YFRAC_S * PLOT_H
X_TEMP = MARGIN_L + (temperature - TEMP_MIN) / (TEMP_MAX - TEMP_MIN) * PLOT_W - (1 - YFRAC_S) * PLOT_W
X_DEW = MARGIN_L + (dewpoint - TEMP_MIN) / (TEMP_MAX - TEMP_MIN) * PLOT_W - (1 - YFRAC_S) * PLOT_W

# Build SVG elements
svg_elems = []

# Background
svg_elems.append(f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="{PAGE_BG}"/>')

# Plot area
svg_elems.append(
    f'<rect x="{MARGIN_L}" y="{MARGIN_T}" width="{PLOT_W}" height="{PLOT_H}" '
    f'fill="{ELEVATED_BG}" stroke="{INK_SOFT}" stroke-width="2"/>'
)

# Isotherms (skewed temperature lines, every 10°C)
# At P_MAX (yfrac=1): skew_offset=0, x=base_x (bottom of chart)
# At P_MIN (yfrac=0): skew_offset=PLOT_W (top of chart)
isotherm_temps = np.arange(-80, 60, 10)
for t_val in isotherm_temps:
    base_x = MARGIN_L + (t_val - TEMP_MIN) / (TEMP_MAX - TEMP_MIN) * PLOT_W
    x_bot = base_x  # yfrac=1 → offset=0
    y_bot = MARGIN_T + PLOT_H
    x_top = base_x - PLOT_W  # yfrac=0 → offset=PLOT_W
    y_top = MARGIN_T
    svg_elems.append(
        f'<line x1="{x_bot:.1f}" y1="{y_bot:.1f}" x2="{x_top:.1f}" y2="{y_top:.1f}" '
        f'stroke="{INK_SOFT}" stroke-width="1.5" stroke-opacity="0.35" stroke-dasharray="8,6" '
        f'clip-path="url(#plotArea)"/>'
    )
    if MARGIN_L - 5 < x_bot < MARGIN_L + PLOT_W + 5:
        svg_elems.append(
            f'<text x="{x_bot:.1f}" y="{y_bot + 46:.1f}" font-size="32" fill="{INK_SOFT}" '
            f'text-anchor="middle" font-family="Arial, sans-serif">{int(t_val)}</text>'
        )

# Isobars (horizontal lines at standard pressure levels)
isobar_p = np.array([1000, 850, 700, 500, 400, 300, 200, 150, 100])
for p_val in isobar_p:
    y_val = MARGIN_T + (np.log10(p_val) - LOG_PMIN) / LOG_PRANGE * PLOT_H
    svg_elems.append(
        f'<line x1="{MARGIN_L}" y1="{y_val:.1f}" x2="{MARGIN_L + PLOT_W}" y2="{y_val:.1f}" '
        f'stroke="{INK_SOFT}" stroke-width="1.5" stroke-opacity="0.45"/>'
    )
    svg_elems.append(
        f'<text x="{MARGIN_L - 14}" y="{y_val + 11:.1f}" font-size="32" fill="{INK_SOFT}" '
        f'text-anchor="end" font-family="Arial, sans-serif">{int(p_val)}</text>'
    )

# Dry adiabats — orange, solid thin lines
# Formula: T = theta * (p/1000)^0.286 - 273.15  (Poisson's equation)
dry_start_temps = np.arange(-40, 60, 10)
for st in dry_start_temps:
    p_arr = np.linspace(P_MAX, P_MIN, 60)
    theta = st + 273.15
    t_arr = theta * (p_arr / 1000) ** 0.286 - 273.15
    log_p_arr = np.log10(p_arr)
    yfrac_arr = (log_p_arr - LOG_PMIN) / LOG_PRANGE
    y_arr = MARGIN_T + yfrac_arr * PLOT_H
    x_arr = MARGIN_L + (t_arr - TEMP_MIN) / (TEMP_MAX - TEMP_MIN) * PLOT_W - (1 - yfrac_arr) * PLOT_W
    mask = (
        (x_arr >= MARGIN_L - 1)
        & (x_arr <= MARGIN_L + PLOT_W + 1)
        & (y_arr >= MARGIN_T - 1)
        & (y_arr <= MARGIN_T + PLOT_H + 1)
    )
    pts = [f"{x:.1f},{y:.1f}" for x, y, m in zip(x_arr, y_arr, mask, strict=False) if m]
    if len(pts) >= 2:
        svg_elems.append(
            f'<polyline points="{" ".join(pts)}" fill="none" '
            f'stroke="{DRY_AD_COLOR}" stroke-width="2.5" stroke-opacity="0.60" '
            f'clip-path="url(#plotArea)"/>'
        )

# Moist adiabats — green, dashed thin lines
# Approximate saturated adiabatic lapse rate: ~6 K per 100 hPa
moist_start_temps = np.arange(-20, 40, 10)
for st in moist_start_temps:
    p_arr = np.linspace(P_MAX, P_MIN, 60)
    t_arr = np.zeros(len(p_arr))
    t_arr[0] = st
    for i in range(1, len(p_arr)):
        dp = p_arr[i - 1] - p_arr[i]  # positive going up
        t_arr[i] = t_arr[i - 1] - 0.6 * dp / 10
    log_p_arr = np.log10(p_arr)
    yfrac_arr = (log_p_arr - LOG_PMIN) / LOG_PRANGE
    y_arr = MARGIN_T + yfrac_arr * PLOT_H
    x_arr = MARGIN_L + (t_arr - TEMP_MIN) / (TEMP_MAX - TEMP_MIN) * PLOT_W - (1 - yfrac_arr) * PLOT_W
    mask = (
        (x_arr >= MARGIN_L - 1)
        & (x_arr <= MARGIN_L + PLOT_W + 1)
        & (y_arr >= MARGIN_T - 1)
        & (y_arr <= MARGIN_T + PLOT_H + 1)
    )
    pts = [f"{x:.1f},{y:.1f}" for x, y, m in zip(x_arr, y_arr, mask, strict=False) if m]
    if len(pts) >= 2:
        svg_elems.append(
            f'<polyline points="{" ".join(pts)}" fill="none" '
            f'stroke="{MOIST_AD_COLOR}" stroke-width="2.5" stroke-opacity="0.55" stroke-dasharray="12,6" '
            f'clip-path="url(#plotArea)"/>'
        )

# Mixing ratio lines — sky blue, dotted
# Formula: e = mr * p / (622 + mr); Td = 243.5 * ln(e/6.112) / (17.67 - ln(e/6.112))
mixing_ratios = [1, 2, 4, 8, 16, 32]
for mr in mixing_ratios:
    p_arr = np.linspace(P_MAX, 200, 40)
    e_arr = mr * p_arr / (622 + mr)
    ln_ratio = np.log(e_arr / 6.112)
    td_arr = 243.5 * ln_ratio / (17.67 - ln_ratio)
    log_p_arr = np.log10(p_arr)
    yfrac_arr = (log_p_arr - LOG_PMIN) / LOG_PRANGE
    y_arr = MARGIN_T + yfrac_arr * PLOT_H
    x_arr = MARGIN_L + (td_arr - TEMP_MIN) / (TEMP_MAX - TEMP_MIN) * PLOT_W - (1 - yfrac_arr) * PLOT_W
    mask = (
        np.isfinite(x_arr)
        & (x_arr >= MARGIN_L - 1)
        & (x_arr <= MARGIN_L + PLOT_W + 1)
        & (y_arr >= MARGIN_T - 1)
        & (y_arr <= MARGIN_T + PLOT_H + 1)
    )
    pts = [f"{x:.1f},{y:.1f}" for x, y, m in zip(x_arr, y_arr, mask, strict=False) if m]
    if len(pts) >= 2:
        svg_elems.append(
            f'<polyline points="{" ".join(pts)}" fill="none" '
            f'stroke="{MIX_COLOR}" stroke-width="2" stroke-opacity="0.60" stroke-dasharray="4,4" '
            f'clip-path="url(#plotArea)"/>'
        )

# Temperature profile (solid, thick)
temp_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(X_TEMP, Y_S, strict=True))
svg_elems.append(
    f'<polyline points="{temp_pts}" fill="none" stroke="{TEMP_COLOR}" stroke-width="8" '
    f'stroke-linecap="round" stroke-linejoin="round" clip-path="url(#plotArea)"/>'
)
for x_val, y_val in zip(X_TEMP, Y_S, strict=True):
    svg_elems.append(
        f'<circle cx="{x_val:.1f}" cy="{y_val:.1f}" r="14" fill="{TEMP_COLOR}" stroke="{PAGE_BG}" stroke-width="3"/>'
    )

# Dewpoint profile (dashed, thick)
dew_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(X_DEW, Y_S, strict=True))
svg_elems.append(
    f'<polyline points="{dew_pts}" fill="none" stroke="{DEW_COLOR}" stroke-width="8" '
    f'stroke-dasharray="24,12" stroke-linecap="round" stroke-linejoin="round" clip-path="url(#plotArea)"/>'
)
for x_val, y_val in zip(X_DEW, Y_S, strict=True):
    svg_elems.append(
        f'<circle cx="{x_val:.1f}" cy="{y_val:.1f}" r="14" fill="{DEW_COLOR}" stroke="{PAGE_BG}" stroke-width="3"/>'
    )

# Title
svg_elems.append(
    f'<text x="{WIDTH // 2}" y="{MARGIN_T - 24}" font-size="56" font-weight="bold" fill="{INK}" '
    f'text-anchor="middle" font-family="Arial, sans-serif">'
    f"skewt-logp-atmospheric · python · highcharts · anyplot.ai</text>"
)

# Y-axis label (Pressure)
cy_label = MARGIN_T + PLOT_H // 2
svg_elems.append(
    f'<text x="52" y="{cy_label}" font-size="42" fill="{INK_SOFT}" '
    f'text-anchor="middle" font-family="Arial, sans-serif" '
    f'transform="rotate(-90, 52, {cy_label})">Pressure (hPa)</text>'
)

# X-axis label (Temperature)
svg_elems.append(
    f'<text x="{MARGIN_L + PLOT_W // 2}" y="{HEIGHT - 16}" font-size="42" fill="{INK_SOFT}" '
    f'text-anchor="middle" font-family="Arial, sans-serif">Temperature (°C)</text>'
)

# Legend (inside plot area, upper-right corner)
leg_x = MARGIN_L + PLOT_W - 480
leg_y = MARGIN_T + 28
leg_w = 455
svg_elems.append(
    f'<rect x="{leg_x - 12}" y="{leg_y - 12}" width="{leg_w}" height="430" '
    f'fill="{ELEVATED_BG}" stroke="{INK_SOFT}" stroke-width="1.5" rx="8" opacity="0.93"/>'
)
svg_elems.append(
    f'<text x="{leg_x + 6}" y="{leg_y + 32}" font-size="38" font-weight="bold" fill="{INK}" '
    f'font-family="Arial, sans-serif">Legend</text>'
)

legend_entries = [
    (TEMP_COLOR, "solid", "Temperature"),
    (DEW_COLOR, "dashed", "Dewpoint"),
    (DRY_AD_COLOR, "solid_thin", "Dry Adiabat"),
    (MOIST_AD_COLOR, "dashed_thin", "Moist Adiabat"),
    (MIX_COLOR, "dotted_thin", "Mixing Ratio"),
    (INK_SOFT, "isotherm", "Isotherm"),
]
for i, (color, style, label) in enumerate(legend_entries):
    ley = leg_y + 74 + i * 58
    lx1, lx2 = leg_x + 6, leg_x + 76
    if style == "solid":
        svg_elems.append(
            f'<line x1="{lx1}" y1="{ley}" x2="{lx2}" y2="{ley}" '
            f'stroke="{color}" stroke-width="8" stroke-linecap="round"/>'
        )
    elif style == "dashed":
        svg_elems.append(
            f'<line x1="{lx1}" y1="{ley}" x2="{lx2}" y2="{ley}" '
            f'stroke="{color}" stroke-width="8" stroke-dasharray="20,10" stroke-linecap="round"/>'
        )
    elif style == "solid_thin":
        svg_elems.append(
            f'<line x1="{lx1}" y1="{ley}" x2="{lx2}" y2="{ley}" '
            f'stroke="{color}" stroke-width="3.5" stroke-opacity="0.85"/>'
        )
    elif style == "dashed_thin":
        svg_elems.append(
            f'<line x1="{lx1}" y1="{ley}" x2="{lx2}" y2="{ley}" '
            f'stroke="{color}" stroke-width="3.5" stroke-opacity="0.85" stroke-dasharray="14,7"/>'
        )
    elif style == "dotted_thin":
        svg_elems.append(
            f'<line x1="{lx1}" y1="{ley}" x2="{lx2}" y2="{ley}" '
            f'stroke="{color}" stroke-width="3" stroke-opacity="0.85" stroke-dasharray="5,5"/>'
        )
    else:  # isotherm
        svg_elems.append(
            f'<line x1="{lx1}" y1="{ley}" x2="{lx2}" y2="{ley}" '
            f'stroke="{color}" stroke-width="2" stroke-opacity="0.60" stroke-dasharray="8,6"/>'
        )
    svg_elems.append(
        f'<text x="{lx2 + 14}" y="{ley + 13}" font-size="36" fill="{INK}" '
        f'font-family="Arial, sans-serif">{label}</text>'
    )

# Assemble SVG
svg_content = (
    f'<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
    f'viewBox="0 0 {WIDTH} {HEIGHT}">\n'
    f"  <defs>\n"
    f'    <clipPath id="plotArea">\n'
    f'      <rect x="{MARGIN_L}" y="{MARGIN_T}" width="{PLOT_W}" height="{PLOT_H}"/>\n'
    f"    </clipPath>\n"
    f"  </defs>\n" + "".join(svg_elems) + "\n</svg>"
)

html_content = (
    f"<!DOCTYPE html>\n<html>\n<head>\n"
    f'    <meta charset="utf-8">\n'
    f"    <title>Skew-T Log-P Diagram</title>\n"
    f"</head>\n"
    f'<body style="margin:0; padding:0; overflow:hidden; background:{PAGE_BG};">\n'
    f"    {svg_content}\n"
    f"</body>\n</html>"
)

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Render PNG via Selenium with exact viewport sizing
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 3200×1800 (safety net for ±1-2 px rounding)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG_RGB)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
