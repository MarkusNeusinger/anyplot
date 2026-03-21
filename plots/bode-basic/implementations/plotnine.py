""" pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-21
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_hline,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_x_log10,
    theme,
    theme_minimal,
)


# Data - Third-order open-loop transfer function:
# G(s) = 5 / [(s+1)(0.5s+1)(0.2s+1)]
# Poles at s = -1, -2, -5 — stable system with clear gain and phase margins
frequency_hz = np.logspace(-2, 2, 500)
omega = 2 * np.pi * frequency_hz
jw = 1j * omega
K = 5.0
G = K / ((jw + 1) * (0.5 * jw + 1) * (0.2 * jw + 1))

magnitude_db = 20 * np.log10(np.abs(G))
phase_deg = np.degrees(np.angle(G))
phase_deg = np.unwrap(np.radians(phase_deg))
phase_deg = np.degrees(phase_deg)

# Gain crossover: where magnitude crosses 0 dB
gc_idx = np.argmin(np.abs(magnitude_db))
gc_freq = frequency_hz[gc_idx]
phase_at_gc = phase_deg[gc_idx]
phase_margin = 180 + phase_at_gc

# Phase crossover: where phase crosses -180 degrees
pc_idx = np.argmin(np.abs(phase_deg + 180))
pc_freq = frequency_hz[pc_idx]
mag_at_pc = magnitude_db[pc_idx]
gain_margin = -mag_at_pc

# Build long-format DataFrame for faceting
mag_df = pd.DataFrame({"frequency_hz": frequency_hz, "value": magnitude_db, "panel": "Magnitude (dB)"})
phase_df = pd.DataFrame({"frequency_hz": frequency_hz, "value": phase_deg, "panel": "Phase (degrees)"})
df = pd.concat([mag_df, phase_df], ignore_index=True)
df["panel"] = pd.Categorical(df["panel"], categories=["Magnitude (dB)", "Phase (degrees)"], ordered=True)

# Reference lines
ref_lines = pd.DataFrame(
    {
        "panel": pd.Categorical(
            ["Magnitude (dB)", "Phase (degrees)"], categories=["Magnitude (dB)", "Phase (degrees)"], ordered=True
        ),
        "yintercept": [0.0, -180.0],
    }
)

# Gain margin vertical segment at phase crossover on magnitude panel
gm_seg = pd.DataFrame(
    {
        "frequency_hz": [pc_freq, pc_freq],
        "value": [0.0, mag_at_pc],
        "panel": pd.Categorical(
            ["Magnitude (dB)", "Magnitude (dB)"], categories=["Magnitude (dB)", "Phase (degrees)"], ordered=True
        ),
    }
)

# Phase margin vertical segment at gain crossover on phase panel
pm_seg = pd.DataFrame(
    {
        "frequency_hz": [gc_freq, gc_freq],
        "value": [-180.0, phase_at_gc],
        "panel": pd.Categorical(
            ["Phase (degrees)", "Phase (degrees)"], categories=["Magnitude (dB)", "Phase (degrees)"], ordered=True
        ),
    }
)

# Crossover marker points
gc_pt = pd.DataFrame(
    {
        "frequency_hz": [gc_freq],
        "value": [0.0],
        "panel": pd.Categorical(["Magnitude (dB)"], categories=["Magnitude (dB)", "Phase (degrees)"], ordered=True),
    }
)
pm_pt = pd.DataFrame(
    {
        "frequency_hz": [gc_freq],
        "value": [phase_at_gc],
        "panel": pd.Categorical(["Phase (degrees)"], categories=["Magnitude (dB)", "Phase (degrees)"], ordered=True),
    }
)
pc_mag_pt = pd.DataFrame(
    {
        "frequency_hz": [pc_freq],
        "value": [mag_at_pc],
        "panel": pd.Categorical(["Magnitude (dB)"], categories=["Magnitude (dB)", "Phase (degrees)"], ordered=True),
    }
)
pc_phase_pt = pd.DataFrame(
    {
        "frequency_hz": [pc_freq],
        "value": [-180.0],
        "panel": pd.Categorical(["Phase (degrees)"], categories=["Magnitude (dB)", "Phase (degrees)"], ordered=True),
    }
)

# Colors
PYTHON_BLUE = "#306998"
GAIN_MARGIN_COLOR = "#E8833A"
PHASE_MARGIN_COLOR = "#9467BD"

# Annotation labels (panel-specific to avoid appearing in both facets)
gm_label = pd.DataFrame(
    {
        "frequency_hz": [pc_freq * 3],
        "value": [mag_at_pc / 2 - 5],
        "label": [f"GM = {gain_margin:.1f} dB"],
        "panel": pd.Categorical(["Magnitude (dB)"], categories=["Magnitude (dB)", "Phase (degrees)"], ordered=True),
    }
)
pm_label = pd.DataFrame(
    {
        "frequency_hz": [gc_freq * 3],
        "value": [(phase_at_gc + (-180)) / 2],
        "label": [f"PM = {phase_margin:.0f}\u00b0"],
        "panel": pd.Categorical(["Phase (degrees)"], categories=["Magnitude (dB)", "Phase (degrees)"], ordered=True),
    }
)

# Plot
plot = (
    ggplot(df, aes(x="frequency_hz", y="value"))
    + geom_line(size=1.5, color=PYTHON_BLUE)
    # Reference lines (0 dB and -180°)
    + geom_hline(ref_lines, aes(yintercept="yintercept"), linetype="dashed", color="#999999", size=0.7, alpha=0.7)
    # Gain margin segment
    + geom_line(gm_seg, aes(x="frequency_hz", y="value"), color=GAIN_MARGIN_COLOR, size=1.8, linetype="solid")
    # Phase margin segment
    + geom_line(pm_seg, aes(x="frequency_hz", y="value"), color=PHASE_MARGIN_COLOR, size=1.8, linetype="solid")
    # Gain crossover marker on magnitude panel
    + geom_point(gc_pt, aes(x="frequency_hz", y="value"), color=PHASE_MARGIN_COLOR, size=4.5, shape="o", stroke=1.8)
    # Phase at gain crossover marker
    + geom_point(pm_pt, aes(x="frequency_hz", y="value"), color=PHASE_MARGIN_COLOR, size=4.5, shape="o", stroke=1.8)
    # Phase crossover marker on magnitude panel
    + geom_point(
        pc_mag_pt,
        aes(x="frequency_hz", y="value"),
        color=GAIN_MARGIN_COLOR,
        size=4.5,
        shape="s",
        stroke=1.8,
        fill=GAIN_MARGIN_COLOR,
    )
    # Phase crossover marker on phase panel
    + geom_point(
        pc_phase_pt,
        aes(x="frequency_hz", y="value"),
        color=GAIN_MARGIN_COLOR,
        size=4.5,
        shape="s",
        stroke=1.8,
        fill=GAIN_MARGIN_COLOR,
    )
    # Gain margin annotation (magnitude panel only)
    + geom_text(
        gm_label,
        aes(x="frequency_hz", y="value", label="label"),
        color=GAIN_MARGIN_COLOR,
        size=13,
        fontweight="bold",
        ha="left",
    )
    # Phase margin annotation (phase panel only)
    + geom_text(
        pm_label,
        aes(x="frequency_hz", y="value", label="label"),
        color=PHASE_MARGIN_COLOR,
        size=13,
        fontweight="bold",
        ha="left",
    )
    + facet_wrap("~panel", ncol=1, scales="free_y")
    + scale_x_log10()
    + labs(x="Frequency (Hz)", y="", title="bode-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 10),
        text=element_text(size=14, color="#2C3E50"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16, color="#546E7A"),
        plot_title=element_text(size=24, weight="bold", ha="center"),
        strip_text=element_text(size=20, weight="bold", color="#263238"),
        strip_background=element_rect(fill="#F5F5F5", color="none"),
        panel_grid_major=element_line(color="#ECEFF1", size=0.4),
        panel_grid_minor=element_blank(),
        panel_spacing_y=0.15,
        plot_background=element_rect(fill="white", color="white"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
