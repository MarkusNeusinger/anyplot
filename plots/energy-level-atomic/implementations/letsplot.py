""" pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-02-27
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_text,
    geom_band,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Hydrogen atom energy levels (E_n = -13.6/n² eV)
level_names = ["n=1", "n=2", "n=3", "n=4", "n=5", "n=6"]
energies = [-13.6, -3.4, -1.51, -0.85, -0.54, -0.38]

# Visual y-positions: power transform (0.33) to spread converging upper levels more
y_positions = [-(abs(e) ** 0.33) for e in energies]
level_ypos = dict(zip(level_names, y_positions, strict=True))

# Ionization limit
ion_ypos = 0.0

# Energy level lines (x_label_right is offset from x_end to prevent label overlap)
level_df = pd.DataFrame(
    {
        "label": level_names,
        "energy": energies,
        "y": y_positions,
        "x_start": [0.08] * 6,
        "x_end": [0.56] * 6,
        "x_label_right": [0.60] * 6,
        "energy_label": [f"{e:.2f} eV" for e in energies],
    }
)

# Spectral series colors (colorblind-safe: teal, blue, red - all highly distinguishable)
lyman_color = "#009688"
balmer_color = "#1976D2"
paschen_color = "#C0392B"

# Series config: arrow thickness varies to emphasize Balmer (visible spectrum)
series_cfg = {
    "Lyman": {"color": lyman_color, "size": 1.4},
    "Balmer": {"color": balmer_color, "size": 2.2},
    "Paschen": {"color": paschen_color, "size": 1.4},
}

# Transitions with wavelength data (nm)
transitions = [
    ("n=2", "n=1", "Lyman", lyman_color, 121.6),
    ("n=3", "n=1", "Lyman", lyman_color, 102.6),
    ("n=4", "n=1", "Lyman", lyman_color, 97.2),
    ("n=3", "n=2", "Balmer", balmer_color, 656.3),
    ("n=4", "n=2", "Balmer", balmer_color, 486.1),
    ("n=5", "n=2", "Balmer", balmer_color, 434.0),
    ("n=6", "n=2", "Balmer", balmer_color, 410.2),
    ("n=4", "n=3", "Paschen", paschen_color, 1875.1),
    ("n=5", "n=3", "Paschen", paschen_color, 1282.0),
    ("n=6", "n=3", "Paschen", paschen_color, 1093.8),
]

# Stagger arrows horizontally within each series
series_base_x = {"Lyman": 0.14, "Balmer": 0.28, "Paschen": 0.43}
within_series_gap = 0.05

arrow_rows = []
series_counter = {"Lyman": 0, "Balmer": 0, "Paschen": 0}
for from_lvl, to_lvl, series, color, wavelength in transitions:
    idx = series_counter[series]
    x_pos = series_base_x[series] + idx * within_series_gap
    series_counter[series] += 1

    y_top = level_ypos[from_lvl]
    y_bot = level_ypos[to_lvl]
    gap = 0.06
    wl_str = f"{wavelength:.1f} nm"
    arrow_rows.append(
        {
            "x": x_pos,
            "y_from": y_top + gap,
            "y_to": y_bot - gap,
            "series": series,
            "color": color,
            "wavelength": wl_str,
            "transition": f"{from_lvl} → {to_lvl}",
            "is_alpha": idx == 0,
        }
    )

arrow_df = pd.DataFrame(arrow_rows)

# Arrowheads (V-shape at bottom of each arrow)
head_len, head_width = 0.10, 0.014
head_df = pd.DataFrame(
    {
        "x_left": arrow_df["x"] - head_width,
        "x_right": arrow_df["x"] + head_width,
        "x_tip": arrow_df["x"].values,
        "y_base": arrow_df["y_to"] + head_len,
        "y_tip": arrow_df["y_to"].values,
        "color": arrow_df["color"].values,
        "series": arrow_df["series"].values,
    }
)

# Wavelength annotations for α-lines (first transition in each series)
alpha_arrows = arrow_df[arrow_df["is_alpha"]].copy()
alpha_arrows["y_mid"] = (alpha_arrows["y_from"] + alpha_arrows["y_to"]) / 2
alpha_arrows["x_label"] = alpha_arrows["x"] + 0.025

# Legend data (compact construction)
legend_labels = ["Lyman series (UV)", "Balmer series (Visible)", "Paschen series (IR)"]
legend_colors = [lyman_color, balmer_color, paschen_color]
legend_y = [-1.2, -1.7, -2.2]
legend_df = pd.DataFrame(
    {
        "x_seg": [0.68] * 3,
        "xend_seg": [0.74] * 3,
        "x_text": [0.755] * 3,
        "y": legend_y,
        "label": legend_labels,
        "color": legend_colors,
    }
)

# Ionization limit
ion_df = pd.DataFrame({"x": [0.08], "xend": [0.56], "y": [ion_ypos], "yend": [ion_ypos]})
ion_label_df = pd.DataFrame({"x": [0.60], "y": [ion_ypos], "label": ["Ionization (0 eV)"]})

# Y-axis ticks
y_breaks = y_positions + [ion_ypos]
y_labels = [f"{e:.1f}" for e in energies] + ["0.0"]

# Ionization continuum band (shaded region above ionization limit)
ion_band_df = pd.DataFrame({"ymin": [ion_ypos], "ymax": [ion_ypos + 0.3]})

# Build plot
plot = (
    ggplot()
    # Ionization continuum (lets-plot geom_band: subtle shaded region above 0 eV)
    + geom_band(
        data=ion_band_df,
        mapping=aes(ymin="ymin", ymax="ymax"),
        fill="#E8EAF6",
        alpha=0.5,
        color="blank",
        tooltips=layer_tooltips().line("Ionization continuum"),
    )
    # Energy level horizontal lines with interactive tooltips
    + geom_segment(
        data=level_df,
        mapping=aes(x="x_start", xend="x_end", y="y", yend="y"),
        size=2.0,
        color="#2C3E50",
        tooltips=layer_tooltips().line("@label").line("Energy: @energy_label"),
    )
    # Level labels (left side)
    + geom_text(
        data=level_df,
        mapping=aes(x="x_start", y="y", label="label"),
        hjust=1.3,
        size=16,
        color="#2C3E50",
        fontface="bold",
    )
    # Energy values (right side, positioned at x_label_right for clear gap from line)
    + geom_text(
        data=level_df, mapping=aes(x="x_label_right", y="y", label="energy_label"), hjust=0, size=16, color="#555555"
    )
    # Ionization limit (dashed)
    + geom_segment(
        data=ion_df, mapping=aes(x="x", xend="xend", y="y", yend="yend"), size=1.2, color="#AAAAAA", linetype="dashed"
    )
    + geom_text(data=ion_label_df, mapping=aes(x="x", y="y", label="label"), hjust=-0.05, size=16, color="#999999")
)

# Add transition arrows per series (Balmer thicker to emphasize visible spectrum)
for series_name, cfg in series_cfg.items():
    s_arrows = arrow_df[arrow_df["series"] == series_name]
    s_heads = head_df[head_df["series"] == series_name]
    plot = (
        plot
        + geom_segment(
            data=s_arrows,
            mapping=aes(x="x", xend="x", y="y_from", yend="y_to", color="color"),
            size=cfg["size"],
            tooltips=layer_tooltips().line("@series series").line("@transition").line("λ = @wavelength"),
        )
        + geom_segment(
            data=s_heads,
            mapping=aes(x="x_left", xend="x_tip", y="y_base", yend="y_tip", color="color"),
            size=cfg["size"],
        )
        + geom_segment(
            data=s_heads,
            mapping=aes(x="x_right", xend="x_tip", y="y_base", yend="y_tip", color="color"),
            size=cfg["size"],
        )
    )

# Wavelength annotations on α-lines for data storytelling
plot = plot + geom_text(
    data=alpha_arrows,
    mapping=aes(x="x_label", y="y_mid", label="wavelength"),
    hjust=0,
    size=16,
    color="#444444",
    fontface="italic",
)

# Legend, scales, theme
plot = (
    plot
    + scale_color_identity()
    # Legend
    + geom_segment(data=legend_df, mapping=aes(x="x_seg", xend="xend_seg", y="y", yend="y", color="color"), size=2.5)
    + geom_text(data=legend_df, mapping=aes(x="x_text", y="y", label="label", color="color"), hjust=0, size=16)
    + scale_x_continuous(limits=[-0.05, 1.05], expand=[0, 0])
    + scale_y_continuous(breaks=y_breaks, labels=y_labels)
    + labs(
        x="",
        y="Energy (eV)",
        title="energy-level-atomic · letsplot · pyplots.ai",
        subtitle="Hydrogen Atom Energy Levels & Spectral Series",
    )
    + ggsize(1600, 900)
    + theme(
        axis_text_x=element_blank(),
        axis_ticks_x=element_blank(),
        axis_title_x=element_blank(),
        axis_line_x=element_blank(),
        axis_text_y=element_text(size=16, color="#555555"),
        axis_title_y=element_text(size=20, color="#2C3E50"),
        axis_line_y=element_line(color="#CCCCCC", size=0.8),
        axis_ticks_y=element_line(color="#CCCCCC"),
        plot_title=element_text(size=24, hjust=0.5, color="#2C3E50"),
        plot_subtitle=element_text(size=18, hjust=0.5, color="#666666"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color="#EEEEEE", size=0.4),
        panel_grid_minor_y=element_blank(),
        legend_position="none",
        plot_background=element_blank(),
        panel_background=element_blank(),
    )
)

# Save
ggsave(plot, filename="plot.png", path=".", scale=3)
ggsave(plot, filename="plot.html", path=".")
