"""pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: letsplot | Python
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot import ggsave
from scipy import signal


LetsPlot.setup_html()  # noqa: F405

THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome tokens
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_MAIN = IMPRINT_PALETTE[0]  # brand green — main frequency response line
COLOR_GM = IMPRINT_PALETTE[3]  # ochre — gain margin annotation
COLOR_PM = IMPRINT_PALETTE[2]  # blue — phase margin annotation

# Data: 3rd-order system G(s) = 500 / ((s+20)(s²+2s+25))
# Complex poles (wn=5, ζ=0.2) → resonance peak; stable with GM≈5 dB, PM≈18°
num = [500.0]
den = np.polymul([1, 20], [1, 2.0, 25])
system = signal.TransferFunction(num, den)

omega = np.logspace(-1, 2.5, 500)
_, mag, phase_deg = signal.bode(system, omega)
frequency_hz = omega / (2 * np.pi)

df_mag = pd.DataFrame({"frequency_hz": frequency_hz, "magnitude_db": mag})
df_phase = pd.DataFrame({"frequency_hz": frequency_hz, "phase_deg": phase_deg})

# Gain crossover: where magnitude = 0 dB
zero_crossings = np.where(np.diff(np.sign(mag)))[0]
if len(zero_crossings) > 0:
    idx_gc = zero_crossings[0]
    t = abs(mag[idx_gc]) / (abs(mag[idx_gc]) + abs(mag[idx_gc + 1]))
    freq_gc = frequency_hz[idx_gc] + t * (frequency_hz[idx_gc + 1] - frequency_hz[idx_gc])
    phase_at_gc = phase_deg[idx_gc] + t * (phase_deg[idx_gc + 1] - phase_deg[idx_gc])
    phase_margin = 180 + phase_at_gc
else:
    freq_gc = None
    phase_margin = None

# Phase crossover: where phase = -180°
phase_crossings = np.where(np.diff(np.sign(phase_deg + 180)))[0]
if len(phase_crossings) > 0:
    idx_pc = phase_crossings[0]
    t_pc = abs(phase_deg[idx_pc] + 180) / (abs(phase_deg[idx_pc] + 180) + abs(phase_deg[idx_pc + 1] + 180))
    freq_pc = frequency_hz[idx_pc] + t_pc * (frequency_hz[idx_pc + 1] - frequency_hz[idx_pc])
    mag_at_pc = mag[idx_pc] + t_pc * (mag[idx_pc + 1] - mag[idx_pc])
    gain_margin = -mag_at_pc
else:
    freq_pc = None
    gain_margin = None

# Theme-adaptive chrome
anyplot_theme = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
    panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
    panel_grid_major=element_line(color=INK_SOFT, size=0.2),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
    panel_border=element_blank(),  # noqa: F405
    axis_title=element_text(color=INK, size=12, face="bold"),  # noqa: F405
    axis_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
    axis_line=element_line(color=INK_SOFT, size=0.5),  # noqa: F405
    plot_title=element_text(color=INK, size=16, hjust=0.5, face="bold"),  # noqa: F405
    plot_margin=[20, 20, 5, 15],
)

# --- Magnitude plot ---
mag_plot = (
    ggplot(df_mag, aes(x="frequency_hz", y="magnitude_db"))  # noqa: F405
    + geom_line(  # noqa: F405
        color=COLOR_MAIN,
        size=1.0,
        tooltips=layer_tooltips()  # noqa: F405
        .format("frequency_hz", ".3f")
        .format("magnitude_db", ".1f")
        .line("Freq: @frequency_hz Hz")
        .line("Mag: @magnitude_db dB"),
    )
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.5, linetype="dashed")  # noqa: F405
    + scale_x_log10()  # noqa: F405
    + scale_y_continuous(limits=[-35, max(mag) + 5])  # noqa: F405
    + labs(x="", y="Magnitude (dB)", title="bode-basic · python · letsplot · anyplot.ai")  # noqa: F405
    + anyplot_theme
    + ggsize(800, 216)  # noqa: F405
)

if freq_pc is not None:
    gm_seg = pd.DataFrame({"x": [freq_pc], "y": [mag_at_pc], "xend": [freq_pc], "yend": [0.0]})
    gm_pts = pd.DataFrame({"x": [freq_pc, freq_pc], "y": [0.0, mag_at_pc]})
    gm_label = pd.DataFrame({"x": [freq_pc * 3.5], "y": [mag_at_pc - 4], "label": [f"GM = {gain_margin:.1f} dB"]})
    mag_plot = (
        mag_plot
        + geom_vline(xintercept=freq_pc, color=COLOR_GM, size=0.4, linetype="dotted", alpha=0.6)  # noqa: F405
        + geom_segment(  # noqa: F405
            aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
            data=gm_seg,
            color=COLOR_GM,
            size=2.5,
            arrow=arrow(type="closed", length=7, ends="both"),  # noqa: F405
        )
        + geom_point(aes(x="x", y="y"), data=gm_pts, color=COLOR_GM, size=8, shape=18)  # noqa: F405
        + geom_label(  # noqa: F405
            aes(x="x", y="y", label="label"),  # noqa: F405
            data=gm_label,
            size=18,
            color=COLOR_GM,
            fill=ELEVATED_BG,
            label_padding=0.3,
            label_r=0.15,
            fontface="bold",
        )
    )

if freq_gc is not None:
    gc_mag_pt = pd.DataFrame({"x": [freq_gc], "y": [0.0]})
    mag_plot = mag_plot + geom_point(  # noqa: F405
        aes(x="x", y="y"),  # noqa: F405
        data=gc_mag_pt,
        color=COLOR_PM,
        size=8,
        shape=18,  # noqa: F405
    )

# --- Phase plot ---
phase_plot = (
    ggplot(df_phase, aes(x="frequency_hz", y="phase_deg"))  # noqa: F405
    + geom_line(  # noqa: F405
        color=COLOR_MAIN,
        size=1.0,
        tooltips=layer_tooltips()  # noqa: F405
        .format("frequency_hz", ".3f")
        .format("phase_deg", ".1f")
        .line("Freq: @frequency_hz Hz")
        .line("Phase: @phase_deg°"),
    )
    + geom_hline(yintercept=-180, color=INK_SOFT, size=0.5, linetype="dashed")  # noqa: F405
    + scale_x_log10()  # noqa: F405
    + labs(x="Frequency (Hz)", y="Phase (°)")  # noqa: F405
    + anyplot_theme
    + ggsize(800, 216)  # noqa: F405
)

if freq_gc is not None:
    pm_seg = pd.DataFrame({"x": [freq_gc], "y": [phase_at_gc], "xend": [freq_gc], "yend": [-180.0]})
    pm_pts = pd.DataFrame({"x": [freq_gc, freq_gc], "y": [-180.0, phase_at_gc]})
    pm_label = pd.DataFrame({"x": [freq_gc * 2.5], "y": [phase_at_gc + 12], "label": [f"PM = {phase_margin:.1f}°"]})
    phase_plot = (
        phase_plot
        + geom_vline(xintercept=freq_gc, color=COLOR_PM, size=0.4, linetype="dotted", alpha=0.6)  # noqa: F405
        + geom_segment(  # noqa: F405
            aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
            data=pm_seg,
            color=COLOR_PM,
            size=2.5,
            arrow=arrow(type="closed", length=7, ends="both"),  # noqa: F405
        )
        + geom_point(aes(x="x", y="y"), data=pm_pts, color=COLOR_PM, size=8, shape=18)  # noqa: F405
        + geom_label(  # noqa: F405
            aes(x="x", y="y", label="label"),  # noqa: F405
            data=pm_label,
            size=18,
            color=COLOR_PM,
            fill=ELEVATED_BG,
            label_padding=0.3,
            label_r=0.15,
            fontface="bold",
        )
    )

if freq_pc is not None:
    pc_phase_pt = pd.DataFrame({"x": [freq_pc], "y": [-180.0]})
    phase_plot = phase_plot + geom_point(  # noqa: F405
        aes(x="x", y="y"),  # noqa: F405
        data=pc_phase_pt,
        color=COLOR_GM,
        size=8,
        shape=18,  # noqa: F405
    )

# Combine panels vertically with a 4% gap; use explicit pixel dimensions since
# ggbunch adds internal overhead that breaks the simple scale= formula
combined = ggbunch(  # noqa: F405
    plots=[mag_plot, phase_plot], regions=[(0, 0, 1, 0.48, 0, 0), (0, 0.52, 1, 0.48, 0, 0)]
)

ggsave(combined, f"plot-{THEME}.png", path=".", w=3200, h=1800, unit="px")
ggsave(combined, f"plot-{THEME}.html", path=".")
