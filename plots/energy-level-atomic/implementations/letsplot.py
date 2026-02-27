""" pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 80/100 | Created: 2026-02-27
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_text,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_color_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Hydrogen atom energy levels (eV)
level_names = ["n=1", "n=2", "n=3", "n=4", "n=5", "n=6"]
energies = [-13.6, -3.4, -1.51, -0.85, -0.54, -0.38]

# Visual y-positions: power transform (0.4) to spread converging upper levels
y_positions = [-(abs(e) ** 0.4) for e in energies]
level_energy = dict(zip(level_names, energies, strict=True))
level_ypos = dict(zip(level_names, y_positions, strict=True))

# Ionization limit
ion_ypos = 0.0

# Energy level lines
level_df = pd.DataFrame(
    {
        "label": level_names,
        "energy": energies,
        "y": y_positions,
        "x_start": [0.10] * 6,
        "x_end": [0.68] * 6,
        "energy_label": [f"{e:.2f} eV" for e in energies],
    }
)

# Transitions grouped by spectral series
# Emission: arrow points down from higher n to lower n
lyman_color = "#7B2FBE"
balmer_color = "#306998"
paschen_color = "#C0392B"

transitions = [
    ("n=2", "n=1", "Lyman", lyman_color),
    ("n=3", "n=1", "Lyman", lyman_color),
    ("n=4", "n=1", "Lyman", lyman_color),
    ("n=3", "n=2", "Balmer", balmer_color),
    ("n=4", "n=2", "Balmer", balmer_color),
    ("n=5", "n=2", "Balmer", balmer_color),
    ("n=6", "n=2", "Balmer", balmer_color),
    ("n=4", "n=3", "Paschen", paschen_color),
    ("n=5", "n=3", "Paschen", paschen_color),
    ("n=6", "n=3", "Paschen", paschen_color),
]

# Stagger arrows by series with spacing within each series
series_base_x = {"Lyman": 0.18, "Balmer": 0.38, "Paschen": 0.56}
within_series_gap = 0.04

arrow_rows = []
series_counter = {"Lyman": 0, "Balmer": 0, "Paschen": 0}
for from_lvl, to_lvl, series, color in transitions:
    idx = series_counter[series]
    x_pos = series_base_x[series] + idx * within_series_gap
    series_counter[series] += 1

    y_top = level_ypos[from_lvl]
    y_bot = level_ypos[to_lvl]
    # Small gap so arrows don't touch the level lines
    gap = 0.06
    arrow_rows.append({"x": x_pos, "y_from": y_top + gap, "y_to": y_bot - gap, "series": series, "color": color})

arrow_df = pd.DataFrame(arrow_rows)

# Arrowheads - two short diagonal segments forming a V at the bottom
head_len = 0.12
head_width = 0.012
head_rows = []
for _, row in arrow_df.iterrows():
    head_rows.append(
        {
            "x_left": row["x"] - head_width,
            "x_right": row["x"] + head_width,
            "x_tip": row["x"],
            "y_base": row["y_to"] + head_len,
            "y_tip": row["y_to"],
            "color": row["color"],
        }
    )
head_df = pd.DataFrame(head_rows)

# Legend data - positioned in the right portion of the plot
legend_items = [
    ("Lyman series (UV)", lyman_color, -1.2),
    ("Balmer series (Visible)", balmer_color, -1.7),
    ("Paschen series (IR)", paschen_color, -2.2),
]
legend_seg_df = pd.DataFrame(
    {
        "x": [0.78] * 3,
        "xend": [0.84] * 3,
        "y": [item[2] for item in legend_items],
        "yend": [item[2] for item in legend_items],
        "color": [item[1] for item in legend_items],
    }
)
legend_text_df = pd.DataFrame(
    {
        "x": [0.855] * 3,
        "y": [item[2] for item in legend_items],
        "label": [item[0] for item in legend_items],
        "color": [item[1] for item in legend_items],
    }
)

# Ionization limit
ion_df = pd.DataFrame({"x": [0.10], "xend": [0.68], "y": [ion_ypos], "yend": [ion_ypos]})
ion_label_df = pd.DataFrame({"x": [0.70], "y": [ion_ypos], "label": ["Ionization (0 eV)"]})

# Y-axis tick positions and labels (show actual energy values)
y_breaks = y_positions + [ion_ypos]
y_labels = [f"{e:.1f}" for e in energies] + ["0.0"]

# Plot
plot = (
    ggplot()
    # Energy level horizontal lines
    + geom_segment(data=level_df, mapping=aes(x="x_start", xend="x_end", y="y", yend="y"), size=2.5, color="#2C3E50")
    # Level labels (left side)
    + geom_text(
        data=level_df,
        mapping=aes(x="x_start", y="y", label="label"),
        hjust=1.3,
        size=13,
        color="#2C3E50",
        fontface="bold",
    )
    # Energy values (right side of level lines)
    + geom_text(
        data=level_df, mapping=aes(x="x_end", y="y", label="energy_label"), hjust=-0.2, size=11, color="#555555"
    )
    # Ionization limit (dashed)
    + geom_segment(
        data=ion_df, mapping=aes(x="x", xend="xend", y="y", yend="yend"), size=1.2, color="#AAAAAA", linetype="dashed"
    )
    + geom_text(data=ion_label_df, mapping=aes(x="x", y="y", label="label"), hjust=-0.05, size=11, color="#999999")
    # Transition arrows (vertical segments)
    + geom_segment(data=arrow_df, mapping=aes(x="x", xend="x", y="y_from", yend="y_to", color="color"), size=1.6)
    # Arrowheads (left leg)
    + geom_segment(
        data=head_df, mapping=aes(x="x_left", xend="x_tip", y="y_base", yend="y_tip", color="color"), size=1.6
    )
    # Arrowheads (right leg)
    + geom_segment(
        data=head_df, mapping=aes(x="x_right", xend="x_tip", y="y_base", yend="y_tip", color="color"), size=1.6
    )
    + scale_color_identity()
    # Legend
    + geom_segment(data=legend_seg_df, mapping=aes(x="x", xend="xend", y="y", yend="yend", color="color"), size=2.5)
    + geom_text(data=legend_text_df, mapping=aes(x="x", y="y", label="label", color="color"), hjust=0, size=11)
    # Scales
    + scale_x_continuous(limits=[-0.05, 1.18], expand=[0, 0])
    + scale_y_continuous(breaks=y_breaks, labels=y_labels)
    + labs(x="", y="Energy (eV)", title="Hydrogen Atom Energy Levels · energy-level-atomic · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + theme(
        axis_text_x=element_blank(),
        axis_ticks_x=element_blank(),
        axis_title_x=element_blank(),
        axis_line_x=element_blank(),
        axis_text_y=element_text(size=15, color="#555555"),
        axis_title_y=element_text(size=20, color="#2C3E50"),
        axis_line_y=element_line(color="#CCCCCC", size=0.8),
        axis_ticks_y=element_line(color="#CCCCCC"),
        plot_title=element_text(size=22, hjust=0.5, color="#2C3E50"),
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
