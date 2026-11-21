""" anyplot.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, LinearColorMapper, Span
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


def _lerp_hex(c0, c1, t):
    r0, g0, b0 = (int(c0[i : i + 2], 16) for i in (1, 3, 5))
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(a + (c - a) * t) for a, c in ((r0, r1), (g0, g1), (b0, b1)))
    return f"#{r:02X}{g:02X}{b:02X}"


# Imprint sequential ramp (single polarity) for the continuous time axis
IMPRINT_SEQ256 = [_lerp_hex("#009E73", "#4467A3", i / 255.0) for i in range(256)]

# Constants
EQUILIBRIUM = (0.0, 0.0)  # the damped oscillator rests at zero displacement and zero velocity

# Columns: set these to your table's column names
TRAJECTORY = "Trajectory"  # role: extra
TIME = "Time (s)"  # role: t
POSITION = "Position x (m)"  # role: x
VELOCITY = "Velocity dx/dt (m/s)"  # role: dx_dt

# Data: damped harmonic oscillator, dv/dt = -omega^2 x - gamma v, from four initial conditions.
# Replace this block with your own table, for example df = pd.read_csv("trajectories.csv")
omega, gamma, dt, n_steps = 2.0, 0.3, 0.02, 800
initial_conditions = [(2.0, 0.0), (-1.5, 2.0), (0.5, -2.5), (2.5, 1.5)]
frames = []
for k, (x0, v0) in enumerate(initial_conditions, start=1):
    xs, vs = [x0], [v0]
    for _ in range(n_steps):
        a = -(omega**2) * xs[-1] - gamma * vs[-1]
        xs.append(xs[-1] + vs[-1] * dt)
        vs.append(vs[-1] + a * dt)
    frames.append(pd.DataFrame({TRAJECTORY: k, TIME: np.arange(n_steps + 1) * dt, POSITION: xs, VELOCITY: vs}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
p = figure(
    width=3200,
    height=1800,
    title="phase-diagram · python · bokeh · anyplot.ai",
    x_axis_label=POSITION,
    y_axis_label=VELOCITY,
    toolbar_location=None,
    tools="",
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

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
p.outline_line_color = INK_SOFT

color_mapper = LinearColorMapper(palette=IMPRINT_SEQ256, low=df[TIME].min(), high=df[TIME].max())

# dx/dt = 0 axis: fixed points live here
p.add_layout(Span(location=0, dimension="width", line_color=INK_SOFT, line_dash="dashed", line_width=3, line_alpha=0.6))

# One continuous curve per trajectory, built from short segments colored by time
for i, (traj, rows) in enumerate(df.groupby(TRAJECTORY, sort=False)):
    segments = ColumnDataSource(
        {
            "x0": rows[POSITION].to_numpy()[:-1],
            "y0": rows[VELOCITY].to_numpy()[:-1],
            "x1": rows[POSITION].to_numpy()[1:],
            "y1": rows[VELOCITY].to_numpy()[1:],
            "t": rows[TIME].to_numpy()[:-1],
        }
    )
    line = p.segment(
        x0="x0",
        y0="y0",
        x1="x1",
        y1="y1",
        source=segments,
        line_width=7,
        line_color={"field": "t", "transform": color_mapper},
    )

    first = rows.iloc[0]
    p.scatter(
        x=[first[POSITION]],
        y=[first[VELOCITY]],
        size=34,
        color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        line_color=INK,
        line_width=3,
        legend_label=f"Start {traj}: ({first[POSITION]:g}, {first[VELOCITY]:g})",
    )

# Stable equilibrium at the origin of the state space
p.scatter(
    x=[EQUILIBRIUM[0]],
    y=[EQUILIBRIUM[1]],
    size=44,
    marker="x",
    color=IMPRINT_PALETTE[4],
    line_width=8,
    legend_label="Equilibrium (stable)",
)

p.add_tools(HoverTool(renderers=[line], tooltips=[("x0", "@x0{0.00}"), ("dx/dt", "@y0{0.00}"), ("t (s)", "@t{0.0}")]))

# Color bar explains the time gradient
color_bar = ColorBar(
    color_mapper=color_mapper,
    title=TIME,
    title_text_font_size="34pt",
    title_text_color=INK,
    major_label_text_font_size="30pt",
    major_label_text_color=INK_SOFT,
    major_tick_line_color=INK_SOFT,
    bar_line_color=INK_SOFT,
    background_fill_color=PAGE_BG,
    border_line_color=None,
    width=60,
    padding=20,
    label_standoff=14,
)
p.add_layout(color_bar, "right")

p.legend.location = "top_right"
p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.border_line_color = INK_SOFT
p.legend.border_line_width = 2
p.legend.padding = 20
p.legend.spacing = 12
p.legend.glyph_height = 36
p.legend.glyph_width = 36

# Output
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
