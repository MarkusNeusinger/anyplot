""" anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: pygal 3.1.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-21
"""

import os
import sys


# Running as pygal.py: remove script dir from sys.path so 'import pygal' finds the package
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _this_dir]

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
MUTED_LINE = "rgba(107,106,99,0.45)" if THEME == "light" else "rgba(168,167,159,0.40)"

# Meteorological convention: temperature red, dewpoint green (Imprint matte red and brand green);
# the reference families take lighter Imprint tints so both profiles stay on top
TEMP_COLOR = "#AE3030"
DEW_COLOR = "#009E73"
DRY_COLOR = "rgba(189,130,51,0.65)"  # ochre #BD8233
MOIST_COLOR = "rgba(68,103,163,0.60)" if THEME == "light" else "rgba(68,103,163,0.95)"  # blue #4467A3
MIXING_COLOR = "rgba(196,117,253,0.85)"  # lavender #C475FD

# Physical constants
LV = 2.501e6  # Latent heat of vaporization (J/kg)
RD = 287.05  # Gas constant for dry air (J/kg/K)
RV = 461.5  # Gas constant for water vapor (J/kg/K)
CP = 1004.0  # Specific heat of dry air (J/kg/K)
G = 9.81  # Gravity (m/s^2)
KAPPA = RD / CP

# Data — realistic mid-latitude atmospheric sounding
pressure = np.array([1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100])
temperature = np.array([25, 20, 15, 5, -15, -28, -45, -52, -58, -62, -55])
dewpoint = np.array([18, 15, 12, -2, -22, -38, -55, -60, -65, -70, -65])

# Plot: y = log10(1000 / p), so pressure falls upward on a log scale; x = T + SKEW * y skews the
# isotherms to the right. They rise at 45° when one log-p decade spans as many pixels as SKEW °C:
# this canvas's plot box is 2906 x 1360 px for 90 °C by one decade, so SKEW = 90 * 1360 / 2906 ≈ 42
SKEW = 42
X_LO, X_HI = -50, 40
P_BOTTOM, P_TOP = 1000.0, 100.0
lp_top = np.log10(P_BOTTOM / P_TOP)
p_grid = np.geomspace(P_BOTTOM, P_TOP, 181)
lp_grid = np.log10(P_BOTTOM / p_grid)

log_p = np.log10(P_BOTTOM / pressure)
temp_points = list(zip(temperature + SKEW * log_p, log_p, strict=True))
dew_points = list(zip(dewpoint + SKEW * log_p, log_p, strict=True))

# Isotherms every 10 °C: straight lines, clipped to the plot box where they enter and leave it
isotherms = []
for t in np.arange(np.ceil((X_LO - SKEW * lp_top) / 10) * 10, X_HI + 1, 10):
    lp_a, lp_b = max(0.0, (X_LO - t) / SKEW), min(lp_top, (X_HI - t) / SKEW)
    if lp_a < lp_b:
        isotherms += [(t + SKEW * lp_a, lp_a), (t + SKEW * lp_b, lp_b), None]

# Curved families on the pressure grid, one column per line; points outside the box become gaps
dry = (np.arange(250, 481, 10)[None, :] * (p_grid[:, None] / P_BOTTOM) ** KAPPA) - 273.15

# Moist adiabats: integrate the saturated lapse rate dT/dp = Γm·Rd·T / (g·p) upward from 1000 hPa
moist_k = np.arange(0, 37, 6) + 273.15
moist = [moist_k - 273.15]
for p_now, p_next in zip(p_grid[:-1], p_grid[1:], strict=True):
    es = 6.112 * np.exp(17.67 * (moist_k - 273.15) / (moist_k - 273.15 + 243.5))
    ws = 0.622 * es / (p_now - es)
    gamma = G * (1 + LV * ws / (RD * moist_k)) / (CP + LV**2 * ws / (RV * moist_k**2))
    moist_k = moist_k + gamma * RD * moist_k / (G * p_now) * (p_next - p_now)
    moist.append(moist_k - 273.15)
moist = np.array(moist)

# Saturation mixing ratio lines (g/kg), drawn in the lower troposphere where they are conventional
MIXING_RATIOS = (1, 2, 4, 8, 16)
mixing_p = p_grid[p_grid >= 400]
vapour = np.array(MIXING_RATIOS)[None, :] * mixing_p[:, None] / (622 + np.array(MIXING_RATIOS)[None, :])
mixing = 243.5 * np.log(vapour / 6.112) / (17.67 - np.log(vapour / 6.112))

families = {}
for name, temps, lps in (
    ("dry", dry, lp_grid),
    ("moist", moist, lp_grid),
    ("mixing", mixing, lp_grid[: len(mixing_p)]),
):
    points = []
    for column in temps.T:
        x = column + SKEW * lps
        points += [(xi, li) if X_LO <= xi <= X_HI else None for xi, li in zip(x, lps, strict=True)] + [None]
    families[name] = points

# Mixing-ratio values printed at the top end of each line
mixing_labels = [
    {"value": (column[-1] + SKEW * lp_grid[len(mixing_p) - 1], lp_grid[len(mixing_p) - 1] + 0.05), "label": f"{r:g}"}
    for column, r in zip(mixing.T, MIXING_RATIOS, strict=True)
]

LABEL_FS = 34
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(INK, MUTED_LINE, DRY_COLOR, MOIST_COLOR, MIXING_COLOR, TEMP_COLOR, DEW_COLOR),
    value_colors=(INK_SOFT,) * 7,
    opacity=1,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=2.5,  # the reference families; the two profiles are set heavier in the css below
    guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_color=RULE,
    major_guide_stroke_dasharray="none",
    title_font_size=60,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=40,
    # pygal prints a point's label value_font_size px right of it and 4/3 of that below it;
    # at 0.26 x the label size the text sits vertically centred on its point
    value_font_size=round(0.26 * LABEL_FS),
    value_label_font_size=LABEL_FS,
    tooltip_font_size=34,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="skewt-logp-atmospheric · python · pygal · anyplot.ai",
    x_title="Temperature at 1000 hPa (°C) — isotherms run diagonally at 45°",
    y_title="Pressure (hPa)",
    show_x_guides=False,  # the skewed isotherms are the temperature grid
    show_y_guides=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=36,
    truncate_legend=-1,
    range=(0, lp_top),
    xrange=(X_LO, X_HI),
    print_labels=True,
    print_values=False,
    margin=40,
    spacing=24,
    css=(
        "file://style.css",
        "file://graph.css",
        "inline:.text-overlay text.label { text-anchor: start; }",
        "inline:.serie-5 .line, .serie-6 .line { stroke-width: 7px !important; }",
        "inline:.serie-1 .line { stroke-width: 2px !important; }",
        # pygal still draws a solid upright line at the x tick 0 °C; upright lines are no isotherms here
        "inline:.axis.x .guides path { stroke: none !important; }",
        "inline:.plot_title { font-weight: bold; }",
    ),
)
chart.x_labels = list(range(X_LO, X_HI + 1, 10))
chart.y_labels = [{"value": float(np.log10(P_BOTTOM / p)), "label": str(p)} for p in (1000, 850, 700, 500, 400, 300, 200, 150, 100)]

# Labels first and reference families next, so the two profiles are drawn on top of everything
chart.add(None, mixing_labels, stroke=False, dots_size=0)
chart.add("Isotherms (every 10 °C)", isotherms, show_dots=False, allow_interruptions=True)
chart.add("Dry adiabats (θ every 10 K)", families["dry"], show_dots=False, allow_interruptions=True)
chart.add(
    "Moist adiabats",
    families["moist"],
    show_dots=False,
    allow_interruptions=True,
    stroke_style={"dasharray": "16, 10"},
)
chart.add(
    "Mixing ratio (g/kg)",
    families["mixing"],
    show_dots=False,
    allow_interruptions=True,
    stroke_style={"dasharray": "4, 8", "linecap": "round"},
)
chart.add("Temperature", temp_points, dots_size=9, formatter=lambda p: f"{p[0] - SKEW * p[1]:.0f} °C")
chart.add(
    "Dewpoint",
    dew_points,
    dots_size=9,
    stroke_style={"dasharray": "26, 14"},
    formatter=lambda p: f"{p[0] - SKEW * p[1]:.0f} °C",
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
