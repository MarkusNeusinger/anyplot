""" anyplot.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-27
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
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

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
HC_EV_NM = 1239.84  # photon energy (eV) times wavelength (nm)
VISIBLE_NM = (380, 750)  # visible window; the series that falls in it is drawn thicker
SERIES_NAMES = ["Lyman (UV)", "Balmer (Visible)", "Paschen (IR)"]  # by lower level, ground state first
N_SERIES = 3  # the lowest levels that end a transition series
MAX_JUMP = 3  # how many levels above its end level a series is drawn
POWER = 0.33  # nonlinear energy axis: spreads the levels converging on the ionization limit

# Columns: set these to your table's column names
LEVEL = "Level"  # role: level
ENERGY = "Energy (eV)"  # role: energy

# Data: replace this block with your own table, for example df = pd.read_csv("levels.csv")
# Hydrogen atom: E_n = -13.6 / n² eV for n = 1..6
df = pd.DataFrame({LEVEL: [f"n={n}" for n in range(1, 7)], ENERGY: [-13.6 / n**2 for n in range(1, 7)]})

# Plot: reads only df and the constants above
df = df.sort_values(ENERGY).reset_index(drop=True)
df["y"] = -((-df[ENERGY]) ** POWER)  # level energies are negative below the ionization limit
df["energy_label"] = df[ENERGY].map(lambda e: f"{e:.2f} eV")
n_levels = len(df)
ion_y = 0.0
y_span = ion_y - df["y"].min()

# Schematic horizontal layout (not data)
x_start, x_end = 0.08, 0.56
x_label_right = x_end + 0.04
df["x_start"], df["x_end"], df["x_label_right"], df["x_label_left"] = x_start, x_end, x_label_right, x_start - 0.012

# Emission transitions: each of the lowest levels ends a series fed by the levels just above it
series_gap = (x_end - x_start - 0.06) / N_SERIES
arrow_rows = []
for s in range(min(N_SERIES, n_levels - 1)):
    for k, hi in enumerate(range(s + 1, min(s + 1 + MAX_JUMP, n_levels))):
        delta = df.loc[hi, ENERGY] - df.loc[s, ENERGY]
        arrow_rows.append(
            {
                "series_idx": s,
                "series": SERIES_NAMES[s] if s < len(SERIES_NAMES) else f"to {df.loc[s, LEVEL]}",
                "x": x_start + 0.06 + s * series_gap + k * 0.045,
                "y_from": df.loc[hi, "y"],
                "y_to": df.loc[s, "y"],
                "wavelength_nm": HC_EV_NM / delta,
                "transition": f"{df.loc[hi, LEVEL]} → {df.loc[s, LEVEL]}",
                "is_last": hi == min(s + MAX_JUMP, n_levels - 1),
                "color": IMPRINT_PALETTE[s],
            }
        )
arrow_df = pd.DataFrame(arrow_rows)
arrow_df["wavelength"] = arrow_df["wavelength_nm"].map(lambda w: f"{w:.1f} nm")
in_visible = arrow_df["wavelength_nm"].between(*VISIBLE_NM)
arrow_df["size"] = (
    arrow_df["series_idx"].map(in_visible.groupby(arrow_df["series_idx"]).any()).map({True: 2.2, False: 1.4})
)

# V-shape arrowheads at the lower end of each arrow (emission direction)
head_len, head_width = 0.10, 0.014
head_df = pd.DataFrame(
    {
        "x_left": arrow_df["x"] - head_width,
        "x_right": arrow_df["x"] + head_width,
        "x_tip": arrow_df["x"],
        "y_base": arrow_df["y_to"] + head_len,
        "y_tip": arrow_df["y_to"],
        "color": arrow_df["color"],
        "size": arrow_df["size"],
    }
)

# Wavelength annotation beside the last (rightmost) transition of each series
alpha_arrows = arrow_df[arrow_df["is_last"]].copy()
first_series = alpha_arrows["series_idx"] == alpha_arrows["series_idx"].min()
# The first series (longest arrows) is labelled beside its arrow; the others sit just below their arrow tips
alpha_arrows["y_mid"] = alpha_arrows["y_to"].where(first_series, alpha_arrows["y_to"] - 0.13) + 0.3 * first_series
alpha_arrows["x_label"] = alpha_arrows["x"] + 0.02 - 0.05 * (~first_series)

# Manual legend in the sparse upper right, one row per series
legend_df = arrow_df.drop_duplicates("series_idx")[["series", "color"]].reset_index(drop=True)
legend_df["x_seg"], legend_df["xend_seg"], legend_df["x_text"] = 0.68, 0.74, 0.755
legend_df["y"] = ion_y - y_span * (0.15 + 0.15 * legend_df.index)

# Ionization limit line, label and continuum band above it
ion_df = pd.DataFrame({"x": [x_start], "xend": [x_end], "y": [ion_y], "yend": [ion_y]})
ion_label_df = pd.DataFrame({"x": [x_label_right], "y": [ion_y], "label": ["0 eV (ionization)"]})
ion_band_df = pd.DataFrame({"xmin": [x_start], "xmax": [x_end], "ymin": [ion_y], "ymax": [ion_y + 0.1 * y_span]})

# Y-axis ticks at actual energy values (transformed positions, eV labels)
ticks = pd.DataFrame({"y": [*df["y"], ion_y], "label": [f"{e:.3g}" for e in df[ENERGY]] + ["0"]})
ticks = ticks.dropna().drop_duplicates("y")
y_limits = [ticks["y"].min() - 0.05 * y_span, ion_y + 0.1 * y_span + 0.02 * y_span]

# Theme — fully adaptive chrome
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    axis_text_x=element_blank(),
    axis_ticks_x=element_blank(),
    axis_title_x=element_blank(),
    axis_line_x=element_blank(),
    axis_text_y=element_text(size=10, color=INK_SOFT),
    axis_title_y=element_text(size=12, color=INK),
    axis_line_y=element_line(color=INK_SOFT, size=0.8),
    axis_ticks_y=element_line(color=INK_SOFT),
    plot_title=element_text(size=16, hjust=0.5, color=INK),
    plot_subtitle=element_text(size=12, hjust=0.5, color=INK_SOFT),
    panel_grid_major_x=element_blank(),
    panel_grid_minor_x=element_blank(),
    panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
    panel_grid_minor_y=element_blank(),
    legend_position="none",
)

plot = (
    ggplot()
    # Ionization continuum — subtle band above 0 eV
    + geom_rect(
        data=ion_band_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill=INK_SOFT,
        alpha=0.10,
        color=PAGE_BG,
    )
    # Energy level horizontal lines
    + geom_segment(
        data=df,
        mapping=aes(x="x_start", xend="x_end", y="y", yend="y"),
        size=2.0,
        color=INK,
        tooltips=layer_tooltips().line(f"@{LEVEL}").line("Energy: @energy_label"),
    )
    # Quantum state labels (left of each level line)
    + geom_text(
        data=df, mapping=aes(x="x_label_left", y="y", label=LEVEL), hjust=1, size=4.2, color=INK, fontface="bold"
    )
    # Energy value labels (right of each level line)
    + geom_text(data=df, mapping=aes(x="x_label_right", y="y", label="energy_label"), hjust=0, size=3.6, color=INK_SOFT)
    # Ionization limit dashed line and label
    + geom_segment(
        data=ion_df, mapping=aes(x="x", xend="xend", y="y", yend="yend"), size=1.2, color=INK_SOFT, linetype="dashed"
    )
    + geom_text(data=ion_label_df, mapping=aes(x="x", y="y", label="label"), hjust=0, size=4, color=INK_MUTED)
)

# Transition arrows and arrowheads, one layer set per line width
for width in sorted(arrow_df["size"].unique()):
    s_arrows = arrow_df[arrow_df["size"] == width]
    s_heads = head_df[head_df["size"] == width]
    plot = (
        plot
        + geom_segment(
            data=s_arrows,
            mapping=aes(x="x", xend="x", y="y_from", yend="y_to", color="color"),
            size=width,
            tooltips=layer_tooltips().line("@series series").line("@transition").line("λ = @wavelength"),
        )
        + geom_segment(
            data=s_heads, mapping=aes(x="x_left", xend="x_tip", y="y_base", yend="y_tip", color="color"), size=width
        )
        + geom_segment(
            data=s_heads, mapping=aes(x="x_right", xend="x_tip", y="y_base", yend="y_tip", color="color"), size=width
        )
    )

plot = (
    plot
    # Wavelength labels on the last transition of each series
    + geom_text(
        data=alpha_arrows,
        mapping=aes(x="x_label", y="y_mid", label="wavelength"),
        hjust=0,
        size=3.8,
        color=INK_MUTED,
        fontface="italic",
    )
    + scale_color_identity()
    + geom_segment(data=legend_df, mapping=aes(x="x_seg", xend="xend_seg", y="y", yend="y", color="color"), size=2.5)
    + geom_text(data=legend_df, mapping=aes(x="x_text", y="y", label="series", color="color"), hjust=0, size=4)
    + scale_x_continuous(limits=[-0.05, 1.05], expand=[0, 0])
    + scale_y_continuous(breaks=list(ticks["y"]), labels=list(ticks["label"]), limits=y_limits)
    + labs(
        x="",
        y=ENERGY,
        title="energy-level-atomic · python · letsplot · anyplot.ai",
        subtitle="Hydrogen Atom: Lyman, Balmer & Paschen Series",
    )
    + ggsize(800, 450)
    + anyplot_theme
)

# Save — PNG at 3200×1800 (scale=4 × ggsize 800×450) + HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
