"""pyplots.ai
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
    geom_segment,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_x_log10,
    theme,
    theme_minimal,
)


# Data - Third-order open-loop transfer function:
# G(s) = 5 / [(s+1)(0.5s+1)(0.2s+1)]
# Poles at s = -1, -2, -5 — stable system with clear gain and phase margins
frequency_hz = np.logspace(-1, 1, 500)
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

# Panel categories
panels = ["Magnitude (dB)", "Phase (degrees)"]
panel_cat = pd.CategoricalDtype(categories=panels, ordered=True)

# Long-format data for faceted plot
df = pd.concat(
    [
        pd.DataFrame({"freq": frequency_hz, "value": magnitude_db, "panel": "Magnitude (dB)"}),
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
        "freq": [pc_freq * 2.2],
        "value": [mag_at_pc / 2],
        "label": [f"GM = {gain_margin:.1f} dB"],
        "panel": pd.Categorical(["Magnitude (dB)"], dtype=panel_cat),
    }
)
pm_label = pd.DataFrame(
    {
        "freq": [gc_freq * 2.2],
        "value": [(phase_at_gc - 180) / 2],
        "label": [f"PM = {phase_margin:.0f}°"],
        "panel": pd.Categorical(["Phase (degrees)"], dtype=panel_cat),
    }
)

# Colors
PYTHON_BLUE = "#306998"
GM_COLOR = "#D35400"
PM_COLOR = "#7D3C98"

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
    + geom_line(size=2.2, color=PYTHON_BLUE, alpha=0.9)
    # Reference lines
    + geom_hline(ref_lines, aes(yintercept="yintercept"), linetype="dashed", color="#90A4AE", size=0.8)
    # Crossover guide lines
    + geom_vline(guides, aes(xintercept="xintercept"), linetype="dotted", color="#B0BEC5", size=0.5)
    # Gain margin segment
    + geom_segment(gm_seg, aes(x="x", xend="x", y="ymin", yend="ymax"), color=GM_COLOR, size=4.0, alpha=0.85)
    # Phase margin segment
    + geom_segment(pm_seg, aes(x="x", xend="x", y="ymin", yend="ymax"), color=PM_COLOR, size=4.0, alpha=0.85)
    # Gain crossover markers (purple circles)
    + geom_point(
        markers[markers["mtype"] == "gc"],
        aes(x="freq", y="value"),
        color=PM_COLOR,
        fill=PM_COLOR,
        size=6,
        shape="o",
        stroke=2,
    )
    # Phase crossover markers (orange squares)
    + geom_point(
        markers[markers["mtype"] == "pc"],
        aes(x="freq", y="value"),
        color=GM_COLOR,
        fill=GM_COLOR,
        size=6,
        shape="s",
        stroke=2,
    )
    # Annotations
    + geom_text(
        gm_label, aes(x="freq", y="value", label="label"), color=GM_COLOR, size=14, fontweight="bold", ha="left"
    )
    + geom_text(
        pm_label, aes(x="freq", y="value", label="label"), color=PM_COLOR, size=14, fontweight="bold", ha="left"
    )
    + facet_wrap("~panel", ncol=1, scales="free_y")
    + scale_x_log10(breaks=[0.1, 1, 10], labels=["0.1", "1", "10"])
    + labs(x="Frequency (Hz)", y="", title="bode-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(12, 12),
        text=element_text(size=14, color="#263238"),
        axis_title=element_text(size=20, color="#37474F"),
        axis_text=element_text(size=16, color="#546E7A"),
        plot_title=element_text(size=24, weight="bold", ha="center", color="#1A237E"),
        strip_text=element_text(size=20, weight="bold", color="#1A237E"),
        strip_background=element_rect(fill="#E8EAF6", color="none"),
        panel_grid_major=element_line(color="#E0E0E0", size=0.3),
        panel_grid_minor=element_blank(),
        panel_spacing_y=0.3,
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),
        panel_background=element_rect(fill="white", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
