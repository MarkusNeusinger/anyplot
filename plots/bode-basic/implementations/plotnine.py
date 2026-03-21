""" pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-21
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_hline,
    geom_line,
    geom_point,
    geom_segment,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_x_log10,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Third-order open-loop transfer function:
# G(s) = 5 / [(s+1)(0.5s+1)(0.2s+1)]
# Poles at s = -1, -2, -5 — stable system with clear gain and phase margins
frequency_hz = np.logspace(-1.5, 1.5, 600)
omega = 2 * np.pi * frequency_hz
jw = 1j * omega
G = 5.0 / ((jw + 1) * (0.5 * jw + 1) * (0.2 * jw + 1))

magnitude_db = 20 * np.log10(np.abs(G))
phase_deg = np.degrees(np.unwrap(np.angle(G)))

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

# Clip magnitude for display: show passband and rolloff without excessive range
mag_display = np.clip(magnitude_db, -30, None)

# Panel categories
panels = ["Magnitude (dB)", "Phase (degrees)"]
panel_cat = pd.CategoricalDtype(categories=panels, ordered=True)

# Long-format data for faceted plot
df = pd.concat(
    [
        pd.DataFrame({"freq": frequency_hz, "value": mag_display, "panel": "Magnitude (dB)"}),
        pd.DataFrame({"freq": frequency_hz, "value": phase_deg, "panel": "Phase (degrees)"}),
    ],
    ignore_index=True,
)
df["panel"] = df["panel"].astype(panel_cat)

# Reference lines: 0 dB and -180°
ref_lines = pd.DataFrame({"panel": pd.Categorical(panels, dtype=panel_cat), "yintercept": [0.0, -180.0]})

# Margin segments and crossover markers
gm_seg = pd.DataFrame(
    {"x": [pc_freq], "ymin": [mag_at_pc], "ymax": [0.0], "panel": pd.Categorical(["Magnitude (dB)"], dtype=panel_cat)}
)
pm_seg = pd.DataFrame(
    {
        "x": [gc_freq],
        "ymin": [-180.0],
        "ymax": [phase_at_gc],
        "panel": pd.Categorical(["Phase (degrees)"], dtype=panel_cat),
    }
)

markers = pd.DataFrame(
    {
        "freq": [gc_freq, gc_freq, pc_freq, pc_freq],
        "value": [0.0, phase_at_gc, mag_at_pc, -180.0],
        "panel": pd.Categorical(
            ["Magnitude (dB)", "Phase (degrees)", "Magnitude (dB)", "Phase (degrees)"], dtype=panel_cat
        ),
        "mtype": ["gc", "gc", "pc", "pc"],
    }
)

# Annotation labels positioned to the right of margin segments
gm_label = pd.DataFrame(
    {
        "freq": [pc_freq * 2.0],
        "value": [mag_at_pc / 2],
        "label": [f"GM = {gain_margin:.1f} dB"],
        "panel": pd.Categorical(["Magnitude (dB)"], dtype=panel_cat),
    }
)
pm_label = pd.DataFrame(
    {
        "freq": [gc_freq * 2.0],
        "value": [(phase_at_gc - 180) / 2],
        "label": [f"PM = {phase_margin:.0f}°"],
        "panel": pd.Categorical(["Phase (degrees)"], dtype=panel_cat),
    }
)

# Colors
PYTHON_BLUE = "#306998"
GM_COLOR = "#D35400"
PM_COLOR = "#7D3C98"
DARK_TEXT = "#1A237E"
MID_TEXT = "#37474F"
LIGHT_TEXT = "#546E7A"

# Subtle vertical guides at crossover frequencies
guides = pd.DataFrame(
    {
        "xintercept": [gc_freq, gc_freq, pc_freq, pc_freq],
        "panel": pd.Categorical(
            ["Magnitude (dB)", "Phase (degrees)", "Magnitude (dB)", "Phase (degrees)"], dtype=panel_cat
        ),
    }
)

# Plot
plot = (
    ggplot(df, aes(x="freq", y="value"))
    + geom_line(size=2.5, color=PYTHON_BLUE, alpha=0.92)
    # Reference lines
    + geom_hline(ref_lines, aes(yintercept="yintercept"), linetype="dashed", color="#78909C", size=1.0)
    # Crossover guide lines
    + geom_vline(guides, aes(xintercept="xintercept"), linetype="dotted", color="#B0BEC5", size=0.6)
    # Gain margin segment
    + geom_segment(gm_seg, aes(x="x", xend="x", y="ymin", yend="ymax"), color=GM_COLOR, size=5.0, alpha=0.9)
    # Phase margin segment
    + geom_segment(pm_seg, aes(x="x", xend="x", y="ymin", yend="ymax"), color=PM_COLOR, size=5.0, alpha=0.9)
    # Gain crossover markers (purple circles)
    + geom_point(
        markers[markers["mtype"] == "gc"],
        aes(x="freq", y="value"),
        color=PM_COLOR,
        fill=PM_COLOR,
        size=7,
        shape="o",
        stroke=2.5,
    )
    # Phase crossover markers (orange squares)
    + geom_point(
        markers[markers["mtype"] == "pc"],
        aes(x="freq", y="value"),
        color=GM_COLOR,
        fill=GM_COLOR,
        size=7,
        shape="s",
        stroke=2.5,
    )
    # Annotations
    + geom_text(
        gm_label, aes(x="freq", y="value", label="label"), color=GM_COLOR, size=18, fontweight="bold", ha="left"
    )
    + geom_text(
        pm_label, aes(x="freq", y="value", label="label"), color=PM_COLOR, size=18, fontweight="bold", ha="left"
    )
    + facet_wrap("~panel", ncol=1, scales="free_y")
    + scale_x_log10(
        breaks=[0.1, 1, 10], labels=["0.1", "1", "10"], minor_breaks=[0.03, 0.05, 0.2, 0.3, 0.5, 2, 3, 5, 20, 30]
    )
    + scale_y_continuous(labels=lambda lst: [f"{v:.0f}" for v in lst])
    + labs(x="Frequency (Hz)", y="", title="bode-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(12, 12),
        text=element_text(size=14, color=MID_TEXT),
        axis_title=element_text(size=20, color=MID_TEXT),
        axis_text=element_text(size=16, color=LIGHT_TEXT),
        plot_title=element_text(size=24, weight="bold", ha="center", color=DARK_TEXT),
        strip_text=element_text(size=20, weight="bold", color=DARK_TEXT),
        strip_background=element_rect(fill="#E8EAF6", color="none"),
        panel_grid_major=element_line(color="#E0E0E0", size=0.3),
        panel_grid_minor=element_line(color="#F0F0F0", size=0.15),
        panel_spacing_y=0.3,
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),
        panel_background=element_rect(fill="white", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
