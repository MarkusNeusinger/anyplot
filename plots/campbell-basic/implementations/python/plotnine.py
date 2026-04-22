""" pyplots.ai
campbell-basic: Campbell Diagram
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-02-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_rect,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — Natural frequencies vs rotational speed for rotating machinery
np.random.seed(42)
speed = np.linspace(0, 6000, 80)

# Natural frequency modes with pronounced gyroscopic speed dependence
modes = {
    "1st Bending": 18 + speed * 0.0015 + np.random.normal(0, 0.12, len(speed)),
    "2nd Bending": 45 - speed * 0.002 + np.random.normal(0, 0.12, len(speed)),
    "1st Torsional": 52 + speed * 0.0025 + np.random.normal(0, 0.12, len(speed)),
    "2nd Torsional": 75 + speed * 0.001 + np.random.normal(0, 0.12, len(speed)),
    "Axial": 90 - speed * 0.0004 + np.random.normal(0, 0.12, len(speed)),
}

# Colorblind-safe palette starting with Python Blue
palette = ["#306998", "#E69F00", "#882D9E", "#D55E00", "#009E73"]
mode_names = list(modes.keys())
mode_colors = dict(zip(mode_names, palette, strict=True))
eo_color = "#888888"

# Long-format DataFrame for natural frequency curves
df_modes = pd.DataFrame(
    [
        {"Speed": s, "Frequency": f, "Mode": name}
        for name, freqs in modes.items()
        for s, f in zip(speed, freqs, strict=True)
    ]
)

# Engine order lines: frequency = order × speed / 60
engine_orders = [1, 2, 3]
eo_names = [f"{o}x EO" for o in engine_orders]
df_eo = pd.DataFrame(
    [{"Speed": s, "Frequency": order * s / 60, "Mode": f"{order}x EO"} for order in engine_orders for s in speed]
)

# Critical speed intersections (EO line crosses natural frequency curve)
critical_points = []
for order in engine_orders:
    eo_freq = order * speed / 60
    for _mode_name, freq_values in modes.items():
        diff = eo_freq - freq_values
        sign_changes = np.where(np.diff(np.sign(diff)))[0]
        for idx in sign_changes:
            s0, s1 = speed[idx], speed[idx + 1]
            f0_eo, f1_eo = eo_freq[idx], eo_freq[idx + 1]
            f0_m, f1_m = freq_values[idx], freq_values[idx + 1]
            t = (f0_m - f0_eo) / ((f1_eo - f0_eo) - (f1_m - f0_m))
            cs, cf = s0 + t * (s1 - s0), f0_eo + t * (f1_eo - f0_eo)
            if 0 < cs < 6000 and 0 < cf < 110:
                critical_points.append({"Speed": cs, "Frequency": cf})
df_critical = pd.DataFrame(critical_points)

# Storytelling: 1x / 1st Bending critical speed (most operationally significant)
eo1_freq = speed / 60
diff_1b = eo1_freq - modes["1st Bending"]
sc_idx = np.where(np.diff(np.sign(diff_1b)))[0]
annot_speed = annot_freq = None
if len(sc_idx) > 0:
    idx = sc_idx[0]
    t = (modes["1st Bending"][idx] - eo1_freq[idx]) / (
        (eo1_freq[idx + 1] - eo1_freq[idx]) - (modes["1st Bending"][idx + 1] - modes["1st Bending"][idx])
    )
    annot_speed = speed[idx] + t * (speed[idx + 1] - speed[idx])
    annot_freq = eo1_freq[idx] + t * (eo1_freq[idx + 1] - eo1_freq[idx])

# Combine all line data and add line weight column for size differentiation
df_lines = pd.concat([df_modes, df_eo], ignore_index=True)
df_lines["_lw"] = df_lines["Mode"].apply(lambda m: 2.0 if "EO" not in m else 1.0)

# Legend mappings — consolidated EO into one entry
color_map = {**mode_colors, **dict.fromkeys(eo_names, eo_color)}
ltype_map = {**dict.fromkeys(mode_names, "solid"), **dict.fromkeys(eo_names, "dashed")}
breaks = mode_names + eo_names[:1]
labels = mode_names + ["Engine Order (1×, 2×, 3×)"]

# Operating range band (nominal: 2000–4500 RPM)
df_band = pd.DataFrame([{"xmin": 2000, "xmax": 4500, "ymin": 0, "ymax": 110}])

# EO labels positioned along lines
eo_labels = pd.DataFrame(
    [
        {"Speed": 4500, "Frequency": 4500 / 60 + 3, "label": "1×"},
        {"Speed": 2200, "Frequency": 2 * 2200 / 60 + 3, "label": "2×"},
        {"Speed": 1500, "Frequency": 3 * 1500 / 60 + 3, "label": "3×"},
    ]
)

# Plot — grammar of graphics layer composition
plot = (
    ggplot(df_lines, aes("Speed", "Frequency", color="Mode", linetype="Mode", group="Mode"))
    # Operating range shading
    + geom_rect(
        df_band,
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill="#306998",
        alpha=0.04,
        color="none",
        inherit_aes=False,
    )
    # Natural frequency + EO lines with size-identity for weight differentiation
    + geom_line(aes(size="_lw"))
    + scale_size_identity()
    # Critical speed markers
    + geom_point(
        df_critical,
        aes("Speed", "Frequency"),
        color="#C62828",
        fill="#EF5350",
        size=4.5,
        shape="D",
        stroke=0.7,
        inherit_aes=False,
        show_legend=False,
    )
    # EO line labels
    + geom_text(
        eo_labels,
        aes("Speed", "Frequency", label="label"),
        color="#555555",
        size=11,
        fontstyle="italic",
        fontweight="bold",
        inherit_aes=False,
        show_legend=False,
    )
    # Unified legend via scale_manual with custom breaks/labels
    + scale_color_manual(values=color_map, breaks=breaks, labels=labels)
    + scale_linetype_manual(values=ltype_map, breaks=breaks, labels=labels)
    + guides(color=guide_legend(override_aes={"size": [1.8] * 5 + [1.0]}), linetype=guide_legend())
    # coord_cartesian for zoom without data removal
    + scale_x_continuous(breaks=range(0, 7000, 1000))
    + scale_y_continuous(breaks=range(0, 111, 10))
    + coord_cartesian(xlim=(0, 6200), ylim=(0, 108))
    + labs(x="Rotational Speed (RPM)", y="Natural Frequency (Hz)", title="campbell-basic · plotnine · pyplots.ai")
    # Publication-quality theme
    + theme_minimal(base_size=14)
    + theme(
        figure_size=(16, 9),
        text=element_text(family="sans-serif", color="#333333"),
        plot_title=element_text(size=24, ha="center", face="bold", color="#1a1a1a"),
        axis_title_x=element_text(size=20, face="bold", color="#222222"),
        axis_title_y=element_text(size=20, face="bold", color="#222222"),
        axis_text=element_text(size=16, color="#555555"),
        legend_text=element_text(size=13),
        legend_title=element_blank(),
        legend_position="bottom",
        legend_direction="horizontal",
        legend_background=element_rect(fill="white", alpha=0.9, color="#CCCCCC", size=0.4),
        legend_key_width=35,
        legend_key_height=18,
        panel_grid_major=element_line(color="#E5E5E5", size=0.25),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="#FAFAFA", color="#E0E0E0", size=0.3),
        axis_line=element_line(color="#CCCCCC", size=0.4),
        plot_margin=0.02,
    )
)

# Storytelling: annotate the most significant critical speed
if annot_speed is not None:
    plot = (
        plot
        + annotate(
            "segment",
            x=annot_speed,
            xend=annot_speed,
            y=0,
            yend=annot_freq,
            color="#C62828",
            linetype="dotted",
            size=0.7,
            alpha=0.6,
        )
        + annotate(
            "text",
            x=annot_speed + 180,
            y=annot_freq + 5,
            label=f"Critical: {int(round(annot_speed))} RPM",
            color="#C62828",
            size=9,
            ha="left",
            fontstyle="italic",
            fontweight="bold",
        )
    )

# Operating range label
plot = plot + annotate(
    "text", x=3250, y=104, label="Operating Range", color="#306998", size=8, alpha=0.5, fontweight="bold"
)

plot.save("plot.png", dpi=300, verbose=False)
