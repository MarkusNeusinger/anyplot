""" pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-21
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave
from scipy import signal


LetsPlot.setup_html()  # noqa: F405

# Data - 3rd-order system: G(s) = 500 / ((s+20)(s^2+2s+25))
# Complex poles (wn=5, zeta=0.2) give a prominent resonance peak ~8 dB
# Real pole at s=-20 preserves resonance shape
# Stable system with GM≈5 dB and PM≈18°
num = [500.0]
den = np.polymul([1, 20], [1, 2.0, 25])
system = signal.TransferFunction(num, den)

omega = np.logspace(-1, 2.5, 500)
_, mag, phase_deg = signal.bode(system, omega)
frequency_hz = omega / (2 * np.pi)

# Build DataFrames
df_mag = pd.DataFrame({"frequency_hz": frequency_hz, "magnitude_db": mag})
df_phase = pd.DataFrame({"frequency_hz": frequency_hz, "phase_deg": phase_deg})

# Gain crossover frequency (where magnitude crosses 0 dB)
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

# Phase crossover frequency (where phase crosses -180 deg)
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

# Colors - colorblind-safe palette (no red-green)
COLOR_MAIN = "#1B4F72"
COLOR_REF = "#AEB6BF"
COLOR_GM = "#D35400"  # Orange for gain margin
COLOR_PM = "#2471A3"  # Blue for phase margin

# Common theme
common_theme = flavor_high_contrast_light() + theme(  # noqa: F405
    axis_text=element_text(size=16),  # noqa: F405
    axis_title=element_text(size=20, face="bold"),  # noqa: F405
    panel_grid_major=element_line(color="#E0E0E0", size=0.3),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
    panel_border=element_blank(),  # noqa: F405
    axis_line=element_line(color="#AAAAAA", size=0.5),  # noqa: F405
    plot_margin=[30, 30, 10, 20],
)

# Magnitude plot
mag_plot = (
    ggplot(df_mag, aes(x="frequency_hz", y="magnitude_db"))  # noqa: F405
    + geom_line(  # noqa: F405
        color=COLOR_MAIN,
        size=2.5,
        tooltips=layer_tooltips()  # noqa: F405
        .format("frequency_hz", ".3f")
        .format("magnitude_db", ".1f")
        .line("Freq: @frequency_hz Hz")
        .line("Mag: @magnitude_db dB"),
    )
    + geom_hline(yintercept=0, color=COLOR_REF, size=0.8, linetype="dashed")  # noqa: F405
    + scale_x_log10()  # noqa: F405
    + scale_y_continuous(limits=[-35, max(mag) + 3])  # noqa: F405
    + labs(  # noqa: F405
        x="", y="Magnitude (dB)", title="bode-basic \u00b7 letsplot \u00b7 pyplots.ai"
    )
    + theme(plot_title=element_text(size=26, hjust=0.5, face="bold"))  # noqa: F405
    + common_theme
    + ggsize(1600, 450)  # noqa: F405
)

# Add gain margin annotation if phase crossover exists
if freq_pc is not None:
    gm_seg = pd.DataFrame({"x": [freq_pc], "y": [mag_at_pc], "xend": [freq_pc], "yend": [0.0]})
    gm_pts = pd.DataFrame({"x": [freq_pc, freq_pc], "y": [0.0, mag_at_pc]})
    gm_label = pd.DataFrame({"x": [freq_pc * 3.0], "y": [mag_at_pc - 5], "label": [f"GM = {gain_margin:.1f} dB"]})
    mag_plot = (
        mag_plot
        + geom_vline(xintercept=freq_pc, color=COLOR_GM, size=0.5, linetype="dotted", alpha=0.5)  # noqa: F405
        + geom_segment(  # noqa: F405
            aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
            data=gm_seg,
            color=COLOR_GM,
            size=3.0,
            arrow=arrow(type="closed", length=8, ends="both"),  # noqa: F405
        )
        + geom_point(  # noqa: F405
            aes(x="x", y="y"),  # noqa: F405
            data=gm_pts,
            color=COLOR_GM,
            size=10,
            shape=18,
        )
        + geom_label(  # noqa: F405
            aes(x="x", y="y", label="label"),  # noqa: F405
            data=gm_label,
            size=18,
            color=COLOR_GM,
            fill="#FDEBD0",
            label_padding=0.3,
            label_r=0.15,
            fontface="bold",
        )
    )

# Add gain crossover point on magnitude plot
if freq_gc is not None:
    gc_mag_pt = pd.DataFrame({"x": [freq_gc], "y": [0.0]})
    mag_plot = mag_plot + geom_point(  # noqa: F405
        aes(x="x", y="y"),  # noqa: F405
        data=gc_mag_pt,
        color=COLOR_PM,
        size=10,
        shape=18,
    )

# Phase plot
phase_plot = (
    ggplot(df_phase, aes(x="frequency_hz", y="phase_deg"))  # noqa: F405
    + geom_line(  # noqa: F405
        color=COLOR_MAIN,
        size=2.5,
        tooltips=layer_tooltips()  # noqa: F405
        .format("frequency_hz", ".3f")
        .format("phase_deg", ".1f")
        .line("Freq: @frequency_hz Hz")
        .line("Phase: @phase_deg\u00b0"),
    )
    + geom_hline(yintercept=-180, color=COLOR_REF, size=0.8, linetype="dashed")  # noqa: F405
    + scale_x_log10()  # noqa: F405
    + labs(x="Frequency (Hz)", y="Phase (\u00b0)")  # noqa: F405
    + common_theme
    + ggsize(1600, 450)  # noqa: F405
)

# Add phase margin annotation if gain crossover exists
if freq_gc is not None:
    pm_seg = pd.DataFrame({"x": [freq_gc], "y": [phase_at_gc], "xend": [freq_gc], "yend": [-180.0]})
    pm_pts = pd.DataFrame({"x": [freq_gc, freq_gc], "y": [-180.0, phase_at_gc]})
    pm_label = pd.DataFrame(
        {"x": [freq_gc * 2.5], "y": [phase_at_gc + 10], "label": [f"PM = {phase_margin:.1f}\u00b0"]}
    )
    phase_plot = (
        phase_plot
        + geom_vline(xintercept=freq_gc, color=COLOR_PM, size=0.5, linetype="dotted", alpha=0.5)  # noqa: F405
        + geom_segment(  # noqa: F405
            aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
            data=pm_seg,
            color=COLOR_PM,
            size=3.0,
            arrow=arrow(type="closed", length=8, ends="both"),  # noqa: F405
        )
        + geom_point(  # noqa: F405
            aes(x="x", y="y"),  # noqa: F405
            data=pm_pts,
            color=COLOR_PM,
            size=10,
            shape=18,
        )
        + geom_label(  # noqa: F405
            aes(x="x", y="y", label="label"),  # noqa: F405
            data=pm_label,
            size=18,
            color=COLOR_PM,
            fill="#D4E6F1",
            label_padding=0.3,
            label_r=0.15,
            fontface="bold",
        )
    )

# Add phase crossover point on phase plot
if freq_pc is not None:
    pc_phase_pt = pd.DataFrame({"x": [freq_pc], "y": [-180.0]})
    phase_plot = phase_plot + geom_point(  # noqa: F405
        aes(x="x", y="y"),  # noqa: F405
        data=pc_phase_pt,
        color=COLOR_GM,
        size=10,
        shape=18,
    )

# Combine vertically
combined = ggbunch(  # noqa: F405
    plots=[mag_plot, phase_plot], regions=[(0, 0, 1, 0.53, 0, 0), (0, 0.47, 1, 0.55, 0, 0)]
)

# Save
export_ggsave(combined, filename="plot.png", path=".", scale=3)
export_ggsave(combined, filename="plot.html", path=".")
