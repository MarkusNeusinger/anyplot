"""anyplot.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: altair 6.3.0 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os

import altair as alt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette, canonical order, theme-independent
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
HC_EV_NM = 1239.84  # h*c in eV·nm: wavelength of a transition = HC_EV_NM / energy gap

SERIES_NAMES = ["Lyman (UV)", "Balmer (Visible)", "Paschen (IR)"]  # series ending on level 1, 2, 3
SERIES_SPAN = 3  # upper levels drawn per series

# Columns: set these to your table's column names
LEVEL = "Level"  # role: level
ENERGY = "Energy (eV)"  # role: energy

# Data: replace this block with your own table, for example df = pd.read_csv("levels.csv")
# Hydrogen atom: E_n = -13.6 / n² eV, plus the ionization limit n = ∞ at 0 eV.
df = pd.DataFrame(
    {LEVEL: [f"n = {n}" for n in range(1, 7)] + ["n = ∞"], ENERGY: [-13.6 / n**2 for n in range(1, 7)] + [0.0]}
)

# Plot: reads only df and the constants above
energy_of = dict(zip(df[LEVEL], df[ENERGY], strict=True))
# Spectral series end on one lower level; each is drawn from the next SERIES_SPAN levels above it.
# The ionization limit (highest energy) is not a transition level.
bound = df[df[ENERGY] < df[ENERGY].max()].sort_values(ENERGY, ignore_index=True)
transitions = pd.DataFrame(
    [
        (bound[LEVEL][up], bound[LEVEL][k], name)
        for k, name in enumerate(SERIES_NAMES)
        for up in range(k + 1, min(k + 1 + SERIES_SPAN, len(bound)))
    ],
    columns=["upper", "lower", "series"],
)
series_order = list(transitions["series"].unique())
series_scale = alt.Scale(domain=series_order, range=IMPRINT_PALETTE)
ionization = df[ENERGY].idxmax()

# Schematic layout: horizontal position carries no data
X_START, X_END = 1.5, 9.0
line_df = pd.DataFrame(
    {
        "label": df[LEVEL],
        "energy": df[ENERGY],
        "x_start": X_START,
        # Alternate the line ends of the converging upper levels so their labels stay apart
        "x_end": [X_END - 1.0 if (i >= 3 and i % 2 == 1) else X_END for i in range(len(df))],
        "is_limit": df.index == ionization,
    }
)

# One arrow per transition, spread left to right in series order with a gap between series
series_index = transitions["series"].map({s: k for k, s in enumerate(series_order)})
arrow_df = pd.DataFrame(
    {
        "x": 2.5 + 0.55 * pd.RangeIndex(len(transitions)) + 0.4 * series_index,
        "y_upper": transitions["upper"].map(energy_of),
        "y_lower": transitions["lower"].map(energy_of),
        "series": transitions["series"],
        "transition": transitions["upper"] + " → " + transitions["lower"],
    }
)
arrow_df["y_mid"] = (arrow_df["y_upper"] + arrow_df["y_lower"]) / 2
arrow_df["wavelength"] = HC_EV_NM / (arrow_df["y_upper"] - arrow_df["y_lower"])
arrow_df["wl_label"] = arrow_df["wavelength"].round().astype(int).astype(str) + " nm"
# Wavelength labels sit just right of their arrow
arrow_df["x_label"] = arrow_df["x"] + 0.22
arrow_df["is_short"] = (arrow_df["y_upper"] - arrow_df["y_lower"]) < 0.5 * df[ENERGY].abs().max() / 4

# Symlog scale spreads the converging upper levels and compresses the n=1 to n=2 gap
y_scale = alt.Scale(type="symlog", constant=1, domain=[df[ENERGY].min() * 1.1, df[ENERGY].max() + 0.3], nice=False)
y_axis = alt.Axis(
    titleFontSize=14, labelFontSize=11, titlePadding=10, values=df[ENERGY].tolist(), format=".2f", gridOpacity=0.12
)
x_scale = alt.Scale(domain=[0, X_END + 2.5])

# Layer 1: energy levels, thin so the colored arrows read as the primary story
energy_lines = (
    alt.Chart(line_df[~line_df["is_limit"]])
    .mark_rule(strokeWidth=1.5, color=INK_SOFT)
    .encode(
        x=alt.X("x_start:Q", scale=x_scale, axis=None),
        x2="x_end:Q",
        y=alt.Y("energy:Q", title=ENERGY, scale=y_scale, axis=y_axis),
        tooltip=[alt.Tooltip("label:N", title=LEVEL), alt.Tooltip("energy:Q", title=ENERGY, format=".2f")],
    )
)

# Layer 2: ionization limit, dashed
ion_line = (
    alt.Chart(line_df[line_df["is_limit"]])
    .mark_rule(strokeWidth=1.5, strokeDash=[8, 5], color=INK_SOFT)
    .encode(x="x_start:Q", x2="x_end:Q", y="energy:Q")
)

# Layer 3: level labels at the line ends
level_labels = (
    alt.Chart(line_df)
    .mark_text(align="left", baseline="middle", fontSize=12, dx=8, fontWeight="bold", color=INK)
    .encode(x="x_end:Q", y="energy:Q", text="label:N")
)

# Layer 4: arrow shafts
arrow_shafts = (
    alt.Chart(arrow_df)
    .mark_rule(strokeWidth=3.0, opacity=0.9)
    .encode(
        x="x:Q",
        y="y_upper:Q",
        y2="y_lower:Q",
        color=alt.Color(
            "series:N",
            scale=series_scale,
            legend=alt.Legend(
                title="Spectral series",
                orient="bottom-right",
                offset=5,
                padding=8,
                titleFontSize=11,
                labelFontSize=11,
                symbolSize=150,
            ),
        ),
        tooltip=["transition:N", "series:N", alt.Tooltip("wl_label:N", title="Wavelength")],
    )
)

# Layer 5: arrowheads pointing down (emission)
arrowheads = (
    alt.Chart(arrow_df)
    .mark_point(shape="triangle-down", filled=True, size=200, opacity=0.9)
    .encode(x="x:Q", y="y_lower:Q", color=alt.Color("series:N", scale=series_scale, legend=None))
)

# Layer 6: wavelength labels; long arrows carry theirs just above the head, short ones (on the symlog axis) hang below it
wl_style = {"fontSize": 10, "angle": 90, "color": INK_MUTED, "fontStyle": "italic"}
wl_above = (
    alt.Chart(arrow_df[~arrow_df["is_short"]])
    .mark_text(align="right", dx=-12, dy=-1, **wl_style)
    .encode(x="x_label:Q", y="y_lower:Q", text="wl_label:N")
)
wl_below = (
    alt.Chart(arrow_df[arrow_df["is_short"]])
    .mark_text(align="left", dx=12, dy=-1, **wl_style)
    .encode(x="x_label:Q", y="y_lower:Q", text="wl_label:N")
)

chart = (
    alt.layer(energy_lines, ion_line, level_labels, arrow_shafts, arrowheads, wl_above, wl_below)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(
            "energy-level-atomic · python · altair · anyplot.ai",
            fontSize=16,
            anchor="middle",
            color=INK,
            subtitle="Hydrogen atom emission lines · energy levels: −13.6/n² eV",
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.12, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
