""" anyplot.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-26
"""
# ruff: noqa: F405

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from scipy import signal


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

COLOR_MAIN = IMPRINT_PALETTE[0]  # brand green: main Nyquist curve
COLOR_MIRROR = IMPRINT_PALETTE[2]  # blue: negative-frequency mirror and phase margin
COLOR_CRITICAL = IMPRINT_PALETTE[4]  # matte red: critical point (semantic: danger)
PM_LABEL_TEXT = COLOR_MIRROR if THEME == "light" else INK_SOFT  # blue on the dark label box is too faint

# Constants
CRITICAL_POINT = (-1.0, 0.0)  # the Nyquist stability criterion looks at (-1, 0)

# Columns: set these to your table's column names
REAL = "Real"  # role: real
IMAGINARY = "Imaginary"  # role: imaginary
FREQUENCY = "Frequency (rad/s)"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("response.csv")
# Third-order system G(s) = 2 / ((s+1)(0.5s+1)(0.2s+1)), 500 log-spaced frequencies
omega = np.logspace(-2, 2, 500)
_, response = signal.freqresp(signal.TransferFunction([2.0], np.polymul(np.polymul([1, 1], [0.5, 1]), [0.2, 1])), omega)
df = pd.DataFrame({REAL: response.real, IMAGINARY: response.imag, FREQUENCY: omega})

# Plot: reads only df and the constants above
df = df.dropna().reset_index(drop=True)
n = len(df)
re = df[REAL].to_numpy()
im = df[IMAGINARY].to_numpy()
freq = df[FREQUENCY].to_numpy()
span = max(np.ptp(re), np.ptp(im))  # label offsets scale with the size of the curve
crit_x, crit_y = CRITICAL_POINT

# Negative-frequency mirror and unit circle
df_mirror = pd.DataFrame({REAL: re, IMAGINARY: -im, FREQUENCY: -freq})
theta = np.linspace(0, 2 * np.pi, 200)
df_circle = pd.DataFrame({REAL: np.cos(theta), IMAGINARY: np.sin(theta)})
df_critical = pd.DataFrame({REAL: [crit_x], IMAGINARY: [crit_y]})
df_origin = pd.DataFrame({REAL: [0.0], IMAGINARY: [0.0]})
df_critical_label = pd.DataFrame({REAL: [crit_x + 0.1 * span], IMAGINARY: [crit_y - 0.12 * span]})

# Gain margin: phase crossover, where the curve crosses the negative real axis
crossings = np.where((im[1:] * im[:-1] < 0) & (re[:-1] < 0))[0]
gm_layers = []
if len(crossings) > 0:
    x_cross = re[crossings[0]]
    gain_margin_db = 20 * np.log10(1.0 / abs(x_cross))
    df_gm = pd.DataFrame({"x": [crit_x], "y": [crit_y], "xend": [x_cross], "yend": [crit_y]})
    df_gm_label = pd.DataFrame(
        {REAL: [(crit_x + x_cross) / 2], IMAGINARY: [crit_y + 0.13 * span], "label": [f"GM = {gain_margin_db:.1f} dB"]}
    )
    gm_layers = [
        geom_segment(
            aes(x="x", y="y", xend="xend", yend="yend"), data=df_gm, color=COLOR_CRITICAL, size=0.7, linetype="dotted"
        ),
        geom_label(
            aes(x=REAL, y=IMAGINARY, label="label"),
            data=df_gm_label,
            size=4,
            color=COLOR_CRITICAL,
            fill=ELEVATED_BG,
            alpha=0.93,
            label_padding=0.3,
            label_r=0.15,
            label_size=0.5,
            fontface="bold",
        ),
    ]

# Phase margin: gain crossover, where |G(jw)| = 1
magnitude = np.hypot(re, im)
gain_crossings = np.where((magnitude[1:] - 1) * (magnitude[:-1] - 1) < 0)[0]
pm_layers = []
if len(gain_crossings) > 0:
    k = gain_crossings[0]
    phase_margin = 180 + np.degrees(np.arctan2(im[k], re[k]))
    df_pm_point = pd.DataFrame({REAL: [re[k]], IMAGINARY: [im[k]]})
    df_pm_label = pd.DataFrame(
        {REAL: [re[k] + 0.09 * span], IMAGINARY: [im[k] - 0.10 * span], "label": [f"PM = {phase_margin:.1f}°"]}
    )
    pm_layers = [
        geom_point(aes(x=REAL, y=IMAGINARY), data=df_pm_point, color=COLOR_MIRROR, size=7, shape=1, stroke=2.0),
        geom_label(
            aes(x=REAL, y=IMAGINARY, label="label"),
            data=df_pm_label,
            size=3.8,
            color=PM_LABEL_TEXT,
            fill=ELEVATED_BG,
            alpha=0.93,
            label_padding=0.3,
            label_r=0.15,
            label_size=0.4,
            fontface="bold",
        ),
    ]

# Direction arrows toward increasing frequency
step = max(n // 100, 1)
arrow_from = (np.array([0.1, 0.3, 0.6]) * (n - 1)).astype(int)
arrow_to = np.minimum(arrow_from + step, n - 1)
df_arrows = pd.DataFrame({"x": re[arrow_from], "y": im[arrow_from], "xend": re[arrow_to], "yend": im[arrow_to]})

# Frequency labels at key points along the curve
label_at = (np.array([0.0, 0.16, 0.4, 0.7]) * (n - 1)).astype(int)
label_text = [f"ω={freq[i]:.2f}" if freq[i] < 10 else f"ω={freq[i]:.0f}" for i in label_at]
label_dx = np.array([0.04, -0.05, -0.05, 0.04]) * span
label_dy = np.array([0.05, -0.04, 0.05, 0.05]) * span
df_freq_labels = pd.DataFrame({REAL: re[label_at] + label_dx, IMAGINARY: im[label_at] + label_dy, "label": label_text})

plot = (
    ggplot()
    # Unit circle reference
    + geom_path(aes(x=REAL, y=IMAGINARY), data=df_circle, color=INK_MUTED, size=0.5, linetype="dashed")
    # Mirror curve (negative frequencies), dashed and fainter
    + geom_path(aes(x=REAL, y=IMAGINARY), data=df_mirror, color=COLOR_MIRROR, size=0.8, alpha=0.38, linetype="dashed")
    # Main Nyquist curve with interactive tooltips
    + geom_path(
        aes(x=REAL, y=IMAGINARY),
        data=df,
        color=COLOR_MAIN,
        size=2.0,
        tooltips=layer_tooltips()
        .line(f"Re: @{{{REAL}}}")
        .line(f"Im: @{{{IMAGINARY}}}")
        .line(f"ω: @{{{FREQUENCY}}} rad/s"),
    )
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=df_arrows,
        color=COLOR_MAIN,
        size=1.4,
        arrow=arrow(length=12, type="closed"),
    )
    + geom_label(
        aes(x=REAL, y=IMAGINARY, label="label"),
        data=df_freq_labels,
        size=3.5,
        color=INK_SOFT,
        fill=ELEVATED_BG,
        alpha=0.9,
        label_padding=0.3,
        label_r=0.2,
        label_size=0.2,
    )
    # Critical point, marked and labelled
    + geom_point(aes(x=REAL, y=IMAGINARY), data=df_critical, color=COLOR_CRITICAL, size=10, shape=4, stroke=3.0)
    + geom_text(
        aes(x=REAL, y=IMAGINARY), data=df_critical_label, label="(−1, 0)", size=4, color=COLOR_CRITICAL, fontface="bold"
    )
    # Origin marker
    + geom_point(aes(x=REAL, y=IMAGINARY), data=df_origin, color=INK_MUTED, size=3, shape=3, stroke=1.5)
    + labs(
        x=REAL,
        y=IMAGINARY,
        title="nyquist-basic · python · letsplot · anyplot.ai",
        subtitle="G(s) = 2 / [(s+1)(0.5s+1)(0.2s+1)]  —  Stable: curve does not encircle (−1, 0)",
    )
    + coord_fixed(ratio=1)  # 1:1 so the unit circle stays circular
    + theme_minimal()
    + theme(
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        plot_title=element_text(size=16, color=INK),
        plot_subtitle=element_text(size=10, color=INK_SOFT),
        panel_grid_major=element_line(color=INK_SOFT, size=0.12),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_blank(),
        axis_line=element_blank(),
        axis_ticks=element_blank(),
        axis_ticks_length=0,
        plot_margin=[10, 20, 15, 15],
    )
)

for layer in gm_layers + pm_layers:
    plot = plot + layer

# The fixed aspect leaves the canvas edges transparent: a one-panel grid paints the page color
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save: theme-suffixed PNG (2400 x 2400 at scale=4) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
