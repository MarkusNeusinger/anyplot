""" anyplot.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 89/100 | Updated: 2026-11-08
"""

import os
import sys


# Remove this file's directory from sys.path so `import pygal` resolves to the
# installed package, not this script (which shares the same name).
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _this_dir]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402
from statsmodels.tsa.stattools import acf, pacf  # noqa: E402


# Theme-adaptive tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint categorical palette — canonical order, theme-independent
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")
SIGNIFICANT = IMPRINT_PALETTE[0]  # stems outside the 95% bounds
INSIGNIFICANT = INK_MUTED  # stems inside the bounds (muted anchor)

# Constants
MAX_LAGS = 36  # three seasonal cycles of monthly data
LAG_STEP = 6  # x tick spacing in lags

# Columns: set these to your table's column names
MONTH = "Month"  # role: timestamp
PASSENGERS = "Passengers (thousands)"  # role: value

# Data: synthetic monthly airline-style passenger counts with trend and seasonality;
# replace this block with your own table, for example df = pd.read_csv("passengers.csv")
np.random.seed(42)
n_obs = 200
t = np.arange(n_obs)
df = pd.DataFrame(
    {
        MONTH: pd.date_range("2008-01-01", periods=n_obs, freq="MS"),
        PASSENGERS: 100 + 0.05 * t + 10 * np.sin(2 * np.pi * t / 12) + np.random.normal(0, 2, n_obs),
    }
)

# Plot: one XY chart holds both panels, so they share one lag axis; the ACF panel is the PACF
# panel's coordinates shifted up by its offset, and each panel gets its own tick labels with
# the panel name at its zero line as that panel's y-axis label
series = df.sort_values(MONTH)[PASSENGERS].dropna().to_numpy(dtype=float)
n_lags = min(MAX_LAGS, len(series) // 2 - 1)  # pacf needs fewer lags than half the series
acf_values = acf(series, nlags=n_lags, fft=True)
pacf_values = pacf(series, nlags=n_lags, method="ywm")
conf_bound = 1.96 / np.sqrt(len(series))

TICK = 0.5
PAD = 0.1
GAP = 0.35
lags = np.arange(n_lags + 1)
panels = {
    "PACF": (lags[1:], pacf_values[1:]),  # PACF starts at lag 1
    "ACF": (lags, acf_values),  # ACF includes lag 0 (always 1.0)
}
bounds = {
    name: (min(values.min(), -conf_bound) - PAD, max(values.max(), conf_bound) + PAD)
    for name, (_, values) in panels.items()
}
offsets = {"PACF": 0.0, "ACF": bounds["PACF"][1] - bounds["ACF"][0] + GAP}

stems = {SIGNIFICANT: [], INSIGNIFICANT: []}
heads = {}
ci_lines = []
zero_lines = []
y_labels = []
x_lo, x_hi = -1.0, n_lags + 1.0
for name, (panel_lags, values) in panels.items():
    off = offsets[name]
    heads[name] = []
    for lag, value in zip(panel_lags, values, strict=True):
        color = SIGNIFICANT if abs(value) > conf_bound else INSIGNIFICANT
        stems[color] += [(lag, off), (lag, off + value), None]
        heads[name].append({"value": (lag, off + value), "color": color})
    for level in (conf_bound, -conf_bound):
        ci_lines += [(x_lo, off + level), (x_hi, off + level), None]
    zero_lines += [(x_lo, off), (x_hi, off), None]
    lo, hi = bounds[name]
    ticks = np.arange(np.ceil(lo / TICK), np.floor(hi / TICK) + 1) * TICK
    y_labels += [{"value": off + tick, "label": f"{tick:g}" if tick else name} for tick in ticks]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(INK, SIGNIFICANT, INSIGNIFICANT, SIGNIFICANT, SIGNIFICANT, INK),
    value_colors=(INK,) * 6,
    opacity=1,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=5,  # stems; the CI lines are set thinner in the css below
    guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_color=RULE,
    major_guide_stroke_dasharray="none",
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    value_font_size=44,
    value_label_font_size=52,
    tooltip_font_size=36,
    font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="acf-pacf · python · pygal · anyplot.ai",
    x_title=f"Lag (months)   ·   dashed lines: 95% confidence bounds ±{conf_bound:.3f}",
    show_legend=False,
    show_x_guides=False,
    show_y_guides=True,
    xrange=(x_lo, x_hi),
    range=(bounds["PACF"][0], offsets["ACF"] + bounds["ACF"][1]),
    margin=40,
    spacing=30,
    print_values=False,
    css=(
        "file://style.css",
        "file://graph.css",
        "inline:.serie-0 .line { stroke-width: 2px !important; }",
        "inline:.serie-5 .line { stroke-width: 2.5px !important; }",
        # the lag-0 x label would otherwise draw a vertical axis line through the ACF's lag-0 stem
        "inline:.axis.x .axis.line { stroke: none !important; }",
        "inline:.plot_title { font-weight: bold; }",
    ),
)
chart.x_labels = list(range(0, n_lags + 1, LAG_STEP))
chart.y_labels = y_labels

chart.add("Zero baselines", zero_lines, show_dots=False, allow_interruptions=True)
chart.add("Significant", stems[SIGNIFICANT], show_dots=False, allow_interruptions=True)
chart.add("Inside bounds", stems[INSIGNIFICANT], show_dots=False, allow_interruptions=True)
for name in ("ACF", "PACF"):
    off = offsets[name]
    chart.add(name, heads[name], stroke=False, dots_size=9, formatter=lambda p, off=off: f"{p[1] - off:+.3f}")
chart.add("95% bounds", ci_lines, show_dots=False, allow_interruptions=True, stroke_style={"dasharray": "18, 12"})

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
