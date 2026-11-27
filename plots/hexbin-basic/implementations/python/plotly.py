"""anyplot.ai
hexbin-basic: Basic Hexbin Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 83/100 | Created: 2026-11-27
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

# Imprint palette (full list, canonical order) and the sequential field ramp for hexbin cells
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEQ_FIELDS = (
    [[0.0, "#66E2B2"], [0.369, "#009E73"], [0.803, "#024582"], [1.0, "#351E45"]]
    if THEME == "light"
    else [[0.0, "#404C02"], [0.487, "#009E73"], [1.0, "#CDD9FF"]]
)

# Constants
GRIDSIZE = 28  # hexagons across the plot width, as in matplotlib's hexbin
CANVAS_W, CANVAS_H = 800, 450  # logical canvas; write_image scales it x4 to 3200 x 1800
MARGINS = {"l": 80, "r": 130, "t": 60, "b": 60}

# Columns: set these to your table's column names
TEMPERATURE = "Bearing temperature (°C)"  # role: x
VIBRATION = "Vibration (mm/s)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("sensors.csv")
# Factory sensor readings from a milling spindle: idle, normal load and overload operating modes
rng = np.random.default_rng(42)
modes = [
    # temperature mean, vibration mean, temperature sd, vibration sd, correlation, readings
    (42.0, 1.2, 3.0, 0.35, 0.3, 4500),
    (68.0, 3.4, 4.5, 0.80, 0.6, 5500),
    (86.0, 6.8, 3.5, 1.30, 0.5, 2000),
]
frames = []
for t_mean, v_mean, t_sd, v_sd, rho, n in modes:
    cov = [[t_sd**2, rho * t_sd * v_sd], [rho * t_sd * v_sd, v_sd**2]]
    t_v = rng.multivariate_normal([t_mean, v_mean], cov, size=n)
    frames.append(pd.DataFrame({TEMPERATURE: t_v[:, 0], VIBRATION: t_v[:, 1]}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
x_lo, x_hi = df[TEMPERATURE].min(), df[TEMPERATURE].max()
y_lo, y_hi = df[VIBRATION].min(), df[VIBRATION].max()
x_pad, y_pad = (x_hi - x_lo) * 0.04, (y_hi - y_lo) * 0.04
x_range = [x_lo - x_pad, x_hi + x_pad]
y_range = [y_lo - y_pad, y_hi + y_pad]

# Hexagons are binned in pixel space of the plot area so they stay regular on screen
plot_w = CANVAS_W - MARGINS["l"] - MARGINS["r"]
plot_h = CANVAS_H - MARGINS["t"] - MARGINS["b"]
sx = plot_w / (x_range[1] - x_range[0])
sy = plot_h / (y_range[1] - y_range[0])
radius = plot_w / (GRIDSIZE * np.sqrt(3))  # circumradius of a pointy-top hexagon, in px

u = (df[TEMPERATURE].to_numpy() - x_range[0]) * sx
v = (df[VIBRATION].to_numpy() - y_range[0]) * sy
q_frac = (np.sqrt(3) / 3 * u - v / 3) / radius
r_frac = (2 / 3 * v) / radius
s_frac = -q_frac - r_frac
q, r, s = np.round(q_frac), np.round(r_frac), np.round(s_frac)
dq, dr, ds = np.abs(q - q_frac), np.abs(r - r_frac), np.abs(s - s_frac)
fix_q = (dq > dr) & (dq > ds)
fix_r = ~fix_q & (dr > ds)
q = np.where(fix_q, -r - s, q)
r = np.where(fix_r, -q - s, r)

cells, counts = np.unique(np.column_stack([q, r]), axis=0, return_counts=True)
hex_x = (radius * np.sqrt(3) * (cells[:, 0] + cells[:, 1] / 2)) / sx + x_range[0]
hex_y = (radius * 1.5 * cells[:, 1]) / sy + y_range[0]

# Log color mapping: the densest hexagons hold far more readings than the fringe
log_counts = np.log10(counts)
tick_counts = [c for c in (1, 3, 10, 30, 100, 300, 1000) if c <= counts.max()]
if counts.max() > 1.3 * tick_counts[-1]:
    tick_counts.append(int(counts.max()))

# Pointy-top 'hexagon' symbol matches the lattice, so cells meet edge to edge
order = np.argsort(counts)
marker_size = 2 * radius

fig = go.Figure(
    go.Scatter(
        x=hex_x[order],
        y=hex_y[order],
        mode="markers",
        marker={
            "symbol": "hexagon",
            "size": marker_size,
            "color": log_counts[order],
            "colorscale": SEQ_FIELDS,
            "cmin": 0,
            "cmax": log_counts.max(),
            "line": {"width": 0},
            "colorbar": {
                "title": {
                    "text": "Readings per hexagon (log scale)",
                    "font": {"size": 12, "color": INK},
                    "side": "right",
                },
                "tickfont": {"size": 10, "color": INK_SOFT},
                "tickvals": [float(np.log10(c)) for c in tick_counts],
                "ticktext": [str(c) for c in tick_counts],
                "outlinewidth": 0,
                "thickness": 16,
                "len": 0.9,
            },
        },
        customdata=counts[order],
        hovertemplate=(
            f"{TEMPERATURE}: %{{x:.1f}}<br>{VIBRATION}: %{{y:.2f}}<br>Readings: %{{customdata}}<extra></extra>"
        ),
        showlegend=False,
    )
)

fig.update_layout(
    autosize=False,
    width=CANVAS_W,
    height=CANVAS_H,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=MARGINS,
    font={"color": INK},
    title={
        "text": "hexbin-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": TEMPERATURE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "zeroline": False,
        "linecolor": INK_SOFT,
        "range": x_range,
    },
    yaxis={
        "title": {"text": VIBRATION, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "zeroline": False,
        "linecolor": INK_SOFT,
        "range": y_range,
    },
)

fig.write_image(f"plot-{THEME}.png", width=CANVAS_W, height=CANVAS_H, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
