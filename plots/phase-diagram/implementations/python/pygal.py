""" anyplot.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order, one per trajectory
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
TRAJECTORY = "Trajectory"  # role: extra
TIME = "Time (s)"  # role: t
POSITION = "Position x (m)"  # role: x
VELOCITY = "Velocity dx/dt (m/s)"  # role: dx_dt

# Data: replace this block with your own table, for example df = pd.read_csv("trajectories.csv")
# Mass-spring oscillator x'' = -omega² x - gamma x', released at rest; closed-form solution
omega = 2.0  # natural angular frequency (rad/s)
t = np.linspace(0, 40, 2000)
frames = []
for name, gamma, x0 in [
    ("Damped (γ = 0.3 s⁻¹)", 0.3, 2.0),
    ("Undamped (center, closed orbit)", 0.0, 1.5),
]:
    omega_d = np.sqrt(omega**2 - (gamma / 2) ** 2)
    decay = np.exp(-gamma * t / 2)
    position = x0 * decay * (np.cos(omega_d * t) + gamma / (2 * omega_d) * np.sin(omega_d * t))
    velocity = -x0 * omega**2 / omega_d * decay * np.sin(omega_d * t)
    frames.append(pd.DataFrame({TRAJECTORY: name, TIME: t, POSITION: position, VELOCITY: velocity}))
# The system's one equilibrium, a single state on the dx/dt = 0 axis
frames.append(pd.DataFrame({TRAJECTORY: ["Equilibrium (fixed point)"], TIME: [np.nan], POSITION: [0.0], VELOCITY: [0.0]}))
df = pd.concat(frames, ignore_index=True)

# Plot: one curve per trajectory in time order; a trajectory of one state is drawn as a fixed-point marker
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=IMPRINT_PALETTE,
    guide_stroke_color=RULE,
    major_guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_dasharray="none",
    title_font_size=66,
    label_font_size=46,
    major_label_font_size=46,
    legend_font_size=46,
    value_font_size=36,
    opacity=1,
    opacity_hover=1,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=5,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="phase-diagram · python · pygal · anyplot.ai",
    x_title=POSITION,
    y_title=VELOCITY,
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=40,
    truncate_legend=-1,
    spacing=24,
    margin=40,
)

for name, states in df.dropna(subset=[POSITION, VELOCITY]).groupby(TRAJECTORY, sort=False):
    states = states.sort_values(TIME)
    points = list(zip(states[POSITION].astype(float), states[VELOCITY].astype(float), strict=True))
    if len(states) == 1:
        chart.add(str(name), points, stroke=False, show_dots=True, dots_size=22)
    else:
        chart.add(str(name), points)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
