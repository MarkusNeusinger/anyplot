"""anyplot.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: plotnine 0.15.9 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    arrow,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_rect,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Semantic spectral mapping (UV=lavender, visible=matte red); brand green marks the ionization limit
LYMAN_COLOR = IMPRINT_PALETTE[1]
BALMER_COLOR = IMPRINT_PALETTE[4]
IONIZATION_COLOR = IMPRINT_PALETTE[0]
# Dark theme: Balmer labels over the dark brownish-red band have ~2.7:1 contrast; use INK_SOFT instead
BALMER_LABEL_COLOR = BALMER_COLOR if THEME == "light" else INK_SOFT
BAND_LYMAN = "#EDE9FE" if THEME == "light" else "#2A1A40"
BAND_BALMER = "#FEE2E2" if THEME == "light" else "#3C1A1A"

# Constants
IONIZATION_ENERGY = 0.0  # a bound level approaches 0 eV, the ionization limit
HC_EV_NM = 1239.84  # h*c in eV·nm, turns an energy gap into a wavelength
X_LEFT, X_RIGHT = 0.15, 0.78  # schematic horizontal extent of every level line
X_LABEL = 0.84  # schematic x of the level labels on the right
X_MAX = 1.08  # right edge of the panel, just past the level labels
LABEL_PT = 8  # point size of every annotation text, the size of the tick labels
X_ARROW_FIRST, X_ARROW_LAST = 0.28, 0.70  # schematic span of the arrow columns
LABEL_MIN_GAP = 0.24  # minimum vertical gap between right-hand level labels (sqrt-eV units)
TICKED_LEVELS = 4  # the lowest levels get an energy tick; the crowded upper ones are labelled at the right
SERIES_STYLE = [
    (LYMAN_COLOR, BAND_LYMAN, LYMAN_COLOR),
    (BALMER_COLOR, BAND_BALMER, BALMER_LABEL_COLOR),
]  # per series, in order of appearance: arrow, band, label

# Columns: set these to your table's column names
LEVEL = "Level n"  # role: level
ENERGY = "Energy (eV)"  # role: energy
TO_LEVEL = "To level"  # role: transitions
SERIES = "Series"  # role: extra
LINE_NAME = "Line"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("levels.csv")
# Hydrogen atom, E_n = -13.6 / n² eV. One row per emission line (from LEVEL down to TO_LEVEL);
# a level with no line (n=1, n=6) has one row with empty transition columns.
rows = [
    (2, 1, "Lyman (UV)", "Ly-α"),
    (3, 1, "Lyman (UV)", "Ly-β"),
    (4, 1, "Lyman (UV)", "Ly-γ"),
    (3, 2, "Balmer (Visible)", "Hα"),
    (4, 2, "Balmer (Visible)", "Hβ"),
    (5, 2, "Balmer (Visible)", "Hγ"),
    (1, np.nan, None, None),
    (6, np.nan, None, None),
]
df = pd.DataFrame(rows, columns=[LEVEL, TO_LEVEL, SERIES, LINE_NAME])
df[ENERGY] = -13.6 / df[LEVEL] ** 2

# Plot: reads only df and the constants above
# Nonlinear visual transform sign(E)*sqrt(|E|) spreads the crowded upper levels
# and compresses the large n=1→n=2 gap (spec: "consider a nonlinear scale")
levels = df.drop_duplicates(LEVEL).sort_values(LEVEL).reset_index(drop=True)
levels["vis"] = np.sign(levels[ENERGY]) * np.sqrt(np.abs(levels[ENERGY]))
vis_of = dict(zip(levels[LEVEL], levels["vis"], strict=True))
energy_of = dict(zip(levels[LEVEL], levels[ENERGY], strict=True))
transitions = df.dropna(subset=[TO_LEVEL]).reset_index(drop=True).rename(columns={LEVEL: "from_level"})
transitions[TO_LEVEL] = transitions[TO_LEVEL].astype(int)

# Level lines, their endpoint dots and the right-hand labels
levels = levels.assign(x_start=X_LEFT, x_end=X_RIGHT, x_c1=X_RIGHT + 0.01, x_c2=X_LABEL - 0.02, x_lab=X_LABEL)
endpoints = pd.concat([levels.assign(x=X_LEFT), levels.assign(x=X_RIGHT)])
ion_vis = IONIZATION_ENERGY

# Right-hand labels keep a minimum gap from the label below them, so crowded upper levels stay legible
label_y = []
for y in levels["vis"]:
    label_y.append(y if not label_y else max(y, label_y[-1] + LABEL_MIN_GAP))
levels["label_y"] = label_y
levels["label"] = [f"n = {n}  ({e:.2f} eV)" for n, e in zip(levels[LEVEL], levels[ENERGY], strict=True)]
ion_label_y = ion_vis + LABEL_MIN_GAP * 0.67

# Transition arrows: columns spread evenly, wavelength from the energy gap
transitions["x_pos"] = np.linspace(X_ARROW_FIRST, X_ARROW_LAST, len(transitions))
transitions["y_start"] = transitions["from_level"].map(vis_of) - 0.04
transitions["y_end"] = transitions[TO_LEVEL].map(vis_of) + 0.08
# Label sits in the lower third of its arrow, where it clears the intermediate level lines
transitions["label_y"] = transitions["y_end"] + 0.3 * (transitions["y_start"] - transitions["y_end"])
gap_ev = transitions["from_level"].map(energy_of) - transitions[TO_LEVEL].map(energy_of)
transitions["label"] = transitions[LINE_NAME] + "\n" + (HC_EV_NM / gap_ev).round().astype("Int64").astype(str) + " nm"

# Shaded band and title per series, from the arrows each series holds
by_series = transitions.groupby(SERIES, sort=False)
series_info = pd.DataFrame(
    {
        "xmin": by_series["x_pos"].min() - 0.05,
        "xmax": by_series["x_pos"].max() + 0.05,
        "ymin": by_series[TO_LEVEL].min().map(vis_of) - 0.12,
        "ymax": by_series["from_level"].max().map(vis_of) + 0.08,
    }
).reset_index()
style_of = [SERIES_STYLE[i % len(SERIES_STYLE)] for i in range(len(series_info))]
SERIES_COLORS = {s: style[0] for s, style in zip(series_info[SERIES], style_of, strict=True)}
series_info["fill"] = [style[1] for style in style_of]
series_info["x"] = (series_info["xmin"] + series_info["xmax"]) / 2
series_info["y"] = ion_vis + 0.30
series_info["label"] = series_info[SERIES].str.replace(" (", " Series (", regex=False)

# Y-axis: real eV values at the transformed tick positions of the lowest levels, plus the limit
y_breaks = [*levels["vis"][:TICKED_LEVELS], ion_vis]
y_labels = [*(f"{e:.3g}" for e in levels[ENERGY][:TICKED_LEVELS]), "0"]

title = "energy-level-atomic · python · plotnine · anyplot.ai"
first_series = series_info[SERIES].iloc[0]
lyman = transitions[transitions[SERIES] == first_series]
balmer = transitions[transitions[SERIES] != first_series]

# Layers: bands → levels → ionization → connectors → labels → arrows
plot = (
    ggplot()
    + geom_rect(
        data=series_info, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"), alpha=0.40
    )
    + scale_fill_identity()
    # Energy level lines (partial width per spec) with endpoint dots
    + geom_segment(data=levels, mapping=aes(x="x_start", xend="x_end", y="vis", yend="vis"), color=INK_SOFT, size=1.8)
    + geom_point(data=endpoints, mapping=aes(x="x", y="vis"), color=INK_SOFT, size=2.5)
    # Ionization limit: dashed reference line, connector and label in brand green
    + annotate(
        "segment", x=X_LEFT, xend=X_RIGHT, y=ion_vis, yend=ion_vis, color=IONIZATION_COLOR, size=1.2, linetype="dashed"
    )
    + annotate(
        "text",
        x=X_LABEL,
        y=ion_label_y,
        label="Ionization\nlimit (0 eV)",
        size=LABEL_PT,
        ha="left",
        color=IONIZATION_COLOR,
    )
    + annotate(
        "segment", x=X_RIGHT + 0.01, xend=X_LABEL - 0.02, y=ion_vis, yend=ion_label_y, color=IONIZATION_COLOR, size=0.4
    )
    # Connector lines from level endpoints to the spread labels, then the labels
    + geom_segment(data=levels, mapping=aes(x="x_c1", xend="x_c2", y="vis", yend="label_y"), color=INK_MUTED, size=0.4)
    + geom_text(data=levels, mapping=aes(x="x_lab", y="label_y", label="label"), size=LABEL_PT, ha="left", color=INK)
    # Transition arrows (emission = downward), colored by series
    + geom_segment(
        data=transitions,
        mapping=aes(x="x_pos", xend="x_pos", y="y_start", yend="y_end", color=SERIES),
        size=1.2,
        arrow=arrow(length=0.08, type="closed"),
    )
    # Wavelength labels, split by series for theme-adaptive Balmer contrast
    + geom_text(
        data=lyman, mapping=aes(x="x_pos", y="label_y", label="label"), size=LABEL_PT, nudge_x=-0.045, color=LYMAN_COLOR
    )
    + geom_text(
        data=balmer,
        mapping=aes(x="x_pos", y="label_y", label="label"),
        size=LABEL_PT,
        nudge_x=-0.045,
        color=BALMER_LABEL_COLOR,
    )
    # Series group labels above the diagram (inline legend, series-matched color)
    + geom_text(data=series_info, mapping=aes(x="x", y="y", label="label", color=SERIES), size=LABEL_PT + 1)
    + scale_color_manual(values=SERIES_COLORS, limits=list(SERIES_COLORS))
    + scale_x_continuous(limits=(0.0, X_MAX), expand=(0, 0))
    + scale_y_continuous(name=ENERGY, breaks=y_breaks, labels=y_labels)
    + coord_cartesian(ylim=(levels["vis"].min() - 0.25, ion_vis + 0.52))
    + labs(title=title, subtitle="Hydrogen Atom Emission Spectrum  —  Lyman (UV) & Balmer (Visible) Series", x="")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, weight="bold", color=INK),
        plot_subtitle=element_text(size=7, color=INK_SOFT),
        axis_title_y=element_text(size=10, color=INK),
        axis_title_x=element_blank(),
        axis_text_y=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_minor_y=element_blank(),
        panel_grid_major_y=element_line(alpha=0.12, color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
