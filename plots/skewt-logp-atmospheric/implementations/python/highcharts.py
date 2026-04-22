""" pyplots.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-17
"""

import tempfile
import time
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Generate synthetic atmospheric sounding data
np.random.seed(42)

# Standard pressure levels from surface (1000 hPa) to upper troposphere (100 hPa)
pressure = np.array([1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100])

# Typical temperature profile (decreasing with altitude, with tropopause inversion)
temperature = np.array([28, 22, 15, 4, -18, -32, -45, -52, -56, -56, -55])

# Dewpoint profile (typically lower than temperature, showing moisture content)
dewpoint = np.array([20, 16, 10, -2, -25, -42, -55, -62, -70, -75, -80])

# Chart dimensions
WIDTH = 4800
HEIGHT = 2700

# Plot area margins (in pixels)
MARGIN_LEFT = 400
MARGIN_RIGHT = 400
MARGIN_TOP = 200
MARGIN_BOTTOM = 200

# Plot area dimensions
PLOT_WIDTH = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
PLOT_HEIGHT = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

# Temperature range for x-axis (in degrees C)
TEMP_MIN = -80
TEMP_MAX = 50

# Pressure range (logarithmic)
P_MIN = 100
P_MAX = 1000

# Skew angle (45 degrees in radians)
SKEW_ANGLE = 45 * np.pi / 180


def pressure_to_y(p):
    """Convert pressure to y coordinate (logarithmic scale, 1000 hPa at bottom)."""
    log_p = np.log10(p)
    log_min = np.log10(P_MIN)
    log_max = np.log10(P_MAX)
    # Higher pressure (1000 hPa) at bottom (higher y), lower pressure (100 hPa) at top
    frac = (log_p - log_min) / (log_max - log_min)
    return MARGIN_TOP + frac * PLOT_HEIGHT


def temp_to_x_at_pressure(temp, p):
    """Convert temperature to x coordinate with skewing based on pressure."""
    # Base x position (no skew)
    frac = (temp - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)
    base_x = MARGIN_LEFT + frac * PLOT_WIDTH

    # Apply skew based on vertical position (isotherms skew right at lower altitudes/higher pressure)
    y = pressure_to_y(p)
    y_frac = (y - MARGIN_TOP) / PLOT_HEIGHT
    skew_offset = (1 - y_frac) * PLOT_WIDTH * np.tan(SKEW_ANGLE)

    return base_x - skew_offset


# Build SVG elements for the skewed grid and data

svg_elements = []

# Background
svg_elements.append(f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="#f8f9fa"/>')

# Plot area background
svg_elements.append(
    f'<rect x="{MARGIN_LEFT}" y="{MARGIN_TOP}" width="{PLOT_WIDTH}" height="{PLOT_HEIGHT}" fill="white" stroke="#333" stroke-width="3"/>'
)

# Isotherms (skewed temperature lines) - every 10 degrees
isotherm_temps = np.arange(-80, 60, 10)
for temp in isotherm_temps:
    # Draw line from high pressure (bottom) to low pressure (top)
    x1 = temp_to_x_at_pressure(temp, P_MAX)
    y1 = pressure_to_y(P_MAX)  # Bottom (high pressure)
    x2 = temp_to_x_at_pressure(temp, P_MIN)
    y2 = pressure_to_y(P_MIN)  # Top (low pressure)

    # Draw if any part is visible
    svg_elements.append(
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="#aaa" stroke-width="1" stroke-dasharray="5,5" '
        f'clip-path="url(#plotArea)"/>'
    )

    # Label at bottom (high pressure end) if visible
    if MARGIN_LEFT < x1 < MARGIN_LEFT + PLOT_WIDTH:
        svg_elements.append(
            f'<text x="{x1:.1f}" y="{y1 + 50:.1f}" font-size="28" fill="#666" text-anchor="middle">{int(temp)}</text>'
        )

# Isobars (horizontal pressure lines)
isobar_pressures = [1000, 850, 700, 500, 400, 300, 200, 150, 100]
for p in isobar_pressures:
    y = pressure_to_y(p)
    svg_elements.append(
        f'<line x1="{MARGIN_LEFT}" y1="{y:.1f}" x2="{MARGIN_LEFT + PLOT_WIDTH}" y2="{y:.1f}" '
        f'stroke="#aaa" stroke-width="1"/>'
    )
    svg_elements.append(
        f'<text x="{MARGIN_LEFT - 20}" y="{y + 10:.1f}" font-size="28" fill="#333" text-anchor="end">{int(p)}</text>'
    )

# Dry adiabats (lines of constant potential temperature)
# Simplified: using approximate dry adiabatic lapse rate
dry_adiabat_start_temps = np.arange(-40, 60, 10)
for start_temp in dry_adiabat_start_temps:
    points = []
    pressures = np.linspace(P_MAX, P_MIN, 50)
    for p in pressures:
        # Dry adiabatic temperature change: T = T0 * (P/P0)^(R/Cp)
        # Simplified: T decreases ~10C per 100 hPa decrease
        theta = start_temp + 273.15  # Potential temperature at 1000 hPa
        temp = theta * (p / 1000) ** 0.286 - 273.15
        x = temp_to_x_at_pressure(temp, p)
        y = pressure_to_y(p)
        if MARGIN_LEFT <= x <= MARGIN_LEFT + PLOT_WIDTH and MARGIN_TOP <= y <= MARGIN_TOP + PLOT_HEIGHT:
            points.append(f"{x:.1f},{y:.1f}")

    if len(points) >= 2:
        svg_elements.append(
            f'<polyline points="{" ".join(points)}" fill="none" '
            f'stroke="#cc8844" stroke-width="1.5" stroke-opacity="0.5" '
            f'clip-path="url(#plotArea)"/>'
        )

# Moist adiabats (saturated adiabats) - simplified approximation
moist_adiabat_start_temps = np.arange(-20, 40, 10)
for start_temp in moist_adiabat_start_temps:
    points = []
    pressures = np.linspace(P_MAX, P_MIN, 50)
    temp = start_temp
    for i, p in enumerate(pressures):
        if i > 0:
            # Moist adiabatic lapse rate is less steep than dry
            dp = pressures[i - 1] - pressures[i]
            temp -= 0.5 * dp / 50  # Simplified moist adiabatic decrease
        x = temp_to_x_at_pressure(temp, p)
        y = pressure_to_y(p)
        if MARGIN_LEFT <= x <= MARGIN_LEFT + PLOT_WIDTH and MARGIN_TOP <= y <= MARGIN_TOP + PLOT_HEIGHT:
            points.append(f"{x:.1f},{y:.1f}")

    if len(points) >= 2:
        svg_elements.append(
            f'<polyline points="{" ".join(points)}" fill="none" '
            f'stroke="#44aa44" stroke-width="1.5" stroke-opacity="0.4" stroke-dasharray="10,5" '
            f'clip-path="url(#plotArea)"/>'
        )

# Mixing ratio lines (approximately straight on skew-T)
mixing_ratios = [1, 2, 4, 8, 16, 32]  # g/kg
for mr in mixing_ratios:
    points = []
    pressures = np.linspace(P_MAX, 200, 30)
    for p in pressures:
        # Approximate dewpoint from mixing ratio
        # Simplified formula: Td = 243.5 * ln(e/6.112) / (17.67 - ln(e/6.112))
        # where e = mr * p / (622 + mr)
        e = mr * p / (622 + mr)
        if e > 0:
            ln_ratio = np.log(e / 6.112)
            td = 243.5 * ln_ratio / (17.67 - ln_ratio)
            x = temp_to_x_at_pressure(td, p)
            y = pressure_to_y(p)
            if MARGIN_LEFT <= x <= MARGIN_LEFT + PLOT_WIDTH and MARGIN_TOP <= y <= MARGIN_TOP + PLOT_HEIGHT:
                points.append(f"{x:.1f},{y:.1f}")

    if len(points) >= 2:
        svg_elements.append(
            f'<polyline points="{" ".join(points)}" fill="none" '
            f'stroke="#4488cc" stroke-width="1" stroke-opacity="0.4" stroke-dasharray="3,3" '
            f'clip-path="url(#plotArea)"/>'
        )

# Temperature profile (main sounding data)
temp_points = []
for p, t in zip(pressure, temperature, strict=True):
    x = temp_to_x_at_pressure(t, p)
    y = pressure_to_y(p)
    temp_points.append(f"{x:.1f},{y:.1f}")

svg_elements.append(
    f'<polyline points="{" ".join(temp_points)}" fill="none" '
    f'stroke="#c41e3a" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
)

# Data points on temperature profile
for p, t in zip(pressure, temperature, strict=True):
    x = temp_to_x_at_pressure(t, p)
    y = pressure_to_y(p)
    svg_elements.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12" fill="#c41e3a"/>')

# Dewpoint profile
dew_points = []
for p, d in zip(pressure, dewpoint, strict=True):
    x = temp_to_x_at_pressure(d, p)
    y = pressure_to_y(p)
    dew_points.append(f"{x:.1f},{y:.1f}")

svg_elements.append(
    f'<polyline points="{" ".join(dew_points)}" fill="none" '
    f'stroke="#306998" stroke-width="6" stroke-dasharray="20,10" stroke-linecap="round" stroke-linejoin="round"/>'
)

# Data points on dewpoint profile
for p, d in zip(pressure, dewpoint, strict=True):
    x = temp_to_x_at_pressure(d, p)
    y = pressure_to_y(p)
    svg_elements.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12" fill="#306998"/>')

# Title
svg_elements.append(
    f'<text x="{WIDTH // 2}" y="80" font-size="56" font-weight="bold" fill="#333" '
    f'text-anchor="middle" font-family="Arial, sans-serif">'
    f"skewt-logp-atmospheric \u00b7 highcharts \u00b7 pyplots.ai</text>"
)

# Y-axis label (Pressure)
svg_elements.append(
    f'<text x="60" y="{HEIGHT // 2}" font-size="40" fill="#333" '
    f'text-anchor="middle" font-family="Arial, sans-serif" '
    f'transform="rotate(-90, 60, {HEIGHT // 2})">Pressure (hPa)</text>'
)

# X-axis label (Temperature)
svg_elements.append(
    f'<text x="{WIDTH // 2}" y="{HEIGHT - 60}" font-size="40" fill="#333" '
    f'text-anchor="middle" font-family="Arial, sans-serif">Temperature (\u00b0C)</text>'
)

# Legend
legend_x = WIDTH - 350
legend_y = MARGIN_TOP + 50

svg_elements.append(
    f'<rect x="{legend_x - 20}" y="{legend_y - 10}" width="320" height="400" fill="white" stroke="#ccc" stroke-width="2" rx="10"/>'
)

svg_elements.append(
    f'<text x="{legend_x}" y="{legend_y + 30}" font-size="32" font-weight="bold" fill="#333">Legend</text>'
)

# Temperature
svg_elements.append(
    f'<line x1="{legend_x}" y1="{legend_y + 70}" x2="{legend_x + 60}" y2="{legend_y + 70}" stroke="#c41e3a" stroke-width="6"/>'
)
svg_elements.append(f'<text x="{legend_x + 80}" y="{legend_y + 78}" font-size="28" fill="#333">Temperature</text>')

# Dewpoint
svg_elements.append(
    f'<line x1="{legend_x}" y1="{legend_y + 120}" x2="{legend_x + 60}" y2="{legend_y + 120}" stroke="#306998" stroke-width="6" stroke-dasharray="15,8"/>'
)
svg_elements.append(f'<text x="{legend_x + 80}" y="{legend_y + 128}" font-size="28" fill="#333">Dewpoint</text>')

# Dry adiabat
svg_elements.append(
    f'<line x1="{legend_x}" y1="{legend_y + 170}" x2="{legend_x + 60}" y2="{legend_y + 170}" stroke="#cc8844" stroke-width="2" stroke-opacity="0.7"/>'
)
svg_elements.append(f'<text x="{legend_x + 80}" y="{legend_y + 178}" font-size="28" fill="#333">Dry Adiabat</text>')

# Moist adiabat
svg_elements.append(
    f'<line x1="{legend_x}" y1="{legend_y + 220}" x2="{legend_x + 60}" y2="{legend_y + 220}" stroke="#44aa44" stroke-width="2" stroke-opacity="0.7" stroke-dasharray="10,5"/>'
)
svg_elements.append(f'<text x="{legend_x + 80}" y="{legend_y + 228}" font-size="28" fill="#333">Moist Adiabat</text>')

# Mixing ratio
svg_elements.append(
    f'<line x1="{legend_x}" y1="{legend_y + 270}" x2="{legend_x + 60}" y2="{legend_y + 270}" stroke="#4488cc" stroke-width="2" stroke-opacity="0.7" stroke-dasharray="3,3"/>'
)
svg_elements.append(f'<text x="{legend_x + 80}" y="{legend_y + 278}" font-size="28" fill="#333">Mixing Ratio</text>')

# Isotherm
svg_elements.append(
    f'<line x1="{legend_x}" y1="{legend_y + 320}" x2="{legend_x + 60}" y2="{legend_y + 320}" stroke="#aaa" stroke-width="1" stroke-dasharray="5,5"/>'
)
svg_elements.append(f'<text x="{legend_x + 80}" y="{legend_y + 328}" font-size="28" fill="#333">Isotherm</text>')

# Build complete SVG
svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <clipPath id="plotArea">
      <rect x="{MARGIN_LEFT}" y="{MARGIN_TOP}" width="{PLOT_WIDTH}" height="{PLOT_HEIGHT}"/>
    </clipPath>
  </defs>
  {"".join(svg_elements)}
</svg>"""

# Create HTML wrapper for rendering
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Skew-T Log-P Diagram</title>
</head>
<body style="margin:0; padding:0; background:#f8f9fa;">
    {svg_content}
</body>
</html>"""

# Save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Use Selenium to render PNG
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(f"--window-size={WIDTH},{HEIGHT}")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(3)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
