"""anyplot.ai
campbell-basic: Campbell Diagram
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-28
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MODE = "Natural frequency"  # kind of a series: a mode curve
EXCITATION = "Engine order"  # kind of a series: an excitation line
OPERATING_RANGE = (2500, 4500)  # RPM band the machine runs in

# Columns: set these to your table's column names
SPEED = "Rotational speed (RPM)"  # role: speed
FREQUENCY = "Frequency (Hz)"  # role: frequency_mode_
SERIES = "Natural frequencies"  # role: extra
KIND = "Kind"  # role: extra
CRITICAL = "Critical speed"  # role: critical_speeds
IN_RANGE = "In operating range"  # role: extra

# Data: replace this block with your own table (one row per speed and series), for example df = pd.read_csv("campbell.csv")
speeds = np.linspace(0, 6000, 80)
mode_shapes = {
    "1st Bending": (45, 0.004, 5e-7),
    "2nd Bending": (95, -0.003, -4e-7),
    "1st Torsional": (130, 0.005, 2e-7),
    "Axial": (175, 0.001, 1e-7),
    "3rd Bending": (220, -0.004, -3e-7),
}
orders = [1, 2, 3]
df = pd.concat(
    [
        pd.DataFrame({SPEED: speeds, FREQUENCY: base + slope * speeds + curve * speeds**2, SERIES: name, KIND: MODE})
        for name, (base, slope, curve) in mode_shapes.items()
    ]
    + [
        pd.DataFrame({SPEED: speeds, FREQUENCY: order * speeds / 60, SERIES: f"{order}x", KIND: EXCITATION})
        for order in orders
    ],
    ignore_index=True,
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
modes = df[df[KIND] == MODE]
lines = df[df[KIND] == EXCITATION]
mode_names = list(modes[SERIES].unique())

# Critical speeds: where an engine order line crosses a mode curve (both are straight between samples)
crossings = []
for name in mode_names:
    curve = modes[modes[SERIES] == name]
    for order_name in lines[SERIES].unique():
        line = lines[lines[SERIES] == order_name]
        gap = curve[FREQUENCY].to_numpy() - line[FREQUENCY].to_numpy()
        x = curve[SPEED].to_numpy()
        for i in np.where(np.diff(np.sign(gap)) != 0)[0]:
            speed = x[i] + gap[i] * (x[i + 1] - x[i]) / (gap[i] - gap[i + 1])
            crossings.append(
                {
                    SPEED: speed,
                    FREQUENCY: np.interp(speed, x, line[FREQUENCY].to_numpy()),
                    CRITICAL: f"{name} / {order_name}",
                    IN_RANGE: OPERATING_RANGE[0] <= speed <= OPERATING_RANGE[1],
                }
            )
crit = pd.DataFrame(crossings, columns=[SPEED, FREQUENCY, CRITICAL, IN_RANGE]).astype({IN_RANGE: bool})
crit_in = crit[crit[IN_RANGE]]
crit_out = crit[~crit[IN_RANGE]]

# Annotate the lowest crossing outside the operating range and the first and third ones inside it
inside = crit_in.sort_values(SPEED)
annot = pd.concat([crit_out.sort_values(FREQUENCY).head(1), inside.iloc[[0, 2]] if len(inside) > 2 else inside.head(1)])

# Scales come from the data
x_max = df[SPEED].max()
x_scale = alt.Scale(domain=[0, x_max * 1.035], nice=False)
y_top = df[FREQUENCY].max() * 1.03
y_scale = alt.Scale(domain=[0, y_top])
x_enc = alt.X(SPEED.translate(ESCAPE), type="quantitative", title=SPEED, scale=x_scale)
y_enc = alt.Y(FREQUENCY.translate(ESCAPE), type="quantitative", title=FREQUENCY, scale=y_scale)

# Operating range band and its label
band = (
    alt.Chart(pd.DataFrame({"start": [OPERATING_RANGE[0]], "end": [OPERATING_RANGE[1]]}))
    .mark_rect(opacity=0.07, color=IMPRINT_PALETTE[2])
    .encode(x=alt.X("start", type="quantitative", scale=x_scale), x2="end")
)
band_label = (
    alt.Chart(pd.DataFrame({SPEED: [sum(OPERATING_RANGE) / 2], FREQUENCY: [y_top * 0.08], "text": ["Operating range"]}))
    .mark_text(fontSize=11, fontStyle="italic", fontWeight="bold", color=IMPRINT_PALETTE[2])
    .encode(x=x_enc, y=y_enc, text=alt.Text("text", type="nominal"))
)

# Engine order lines: dashed, one per order, labeled at their right end
eo_chart = (
    alt.Chart(lines)
    .mark_line(strokeWidth=1.8, strokeDash=[8, 6], opacity=0.68, color=INK_MUTED)
    .encode(x=x_enc, y=y_enc, detail=alt.Detail(SERIES.translate(ESCAPE), type="nominal"))
)
eo_labels = (
    alt.Chart(lines.loc[lines.groupby(SERIES, sort=False)[SPEED].idxmax()])
    .mark_text(fontSize=12, fontWeight="bold", align="left", dx=5, dy=-8, color=INK_SOFT)
    .encode(x=x_enc, y=y_enc, text=alt.Text(SERIES.translate(ESCAPE), type="nominal"))
)

# Natural frequency curves
modes_chart = (
    alt.Chart(modes)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            SERIES.translate(ESCAPE),
            type="nominal",
            title=SERIES,
            sort=None,
            scale=alt.Scale(domain=mode_names, range=IMPRINT_PALETTE),
            legend=alt.Legend(title=SERIES, symbolStrokeWidth=2.5, symbolSize=120),
        ),
    )
)

# Critical speed markers: outlined outside the operating range, larger and filled inside it
tooltip = [
    alt.Tooltip(CRITICAL.translate(ESCAPE), title=CRITICAL),
    alt.Tooltip(SPEED.translate(ESCAPE), title=SPEED, format=".0f"),
    alt.Tooltip(FREQUENCY.translate(ESCAPE), title=FREQUENCY, format=".1f"),
]
crit_out_chart = (
    alt.Chart(crit_out)
    .mark_point(size=150, shape="diamond", filled=False, strokeWidth=1.8, color=IMPRINT_PALETTE[4])
    .encode(x=x_enc, y=y_enc, tooltip=tooltip)
)
crit_in_chart = (
    alt.Chart(crit_in)
    .mark_point(size=340, shape="diamond", filled=True, stroke=PAGE_BG, strokeWidth=2.0, color=IMPRINT_PALETTE[4])
    .encode(x=x_enc, y=y_enc, tooltip=tooltip)
)
annot_chart = (
    alt.Chart(annot)
    .mark_text(fontSize=11, fontWeight="bold", align="left", dx=8, dy=-30, color=IMPRINT_PALETTE[4])
    .encode(x=x_enc, y=y_enc, text=alt.Text(CRITICAL.translate(ESCAPE), type="nominal"))
)

chart = (
    alt.layer(band, eo_chart, modes_chart, crit_out_chart, crit_in_chart, eo_labels, band_label, annot_chart)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(
            "campbell-basic · python · altair · anyplot.ai",
            fontSize=16,
            fontWeight=500,
            anchor="start",
            color=INK,
            subtitle="Natural frequencies vs engine order excitations",
            subtitleFontSize=11,
            subtitleColor=INK_MUTED,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
        gridWidth=0.5,
        labelColor=INK_SOFT,
        labelFontSize=10,
        titleColor=INK,
        titleFontSize=12,
        tickSize=5,
    )
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        labelFontSize=10,
        titleColor=INK,
        titleFontSize=10,
        orient="bottom",
        columns=len(mode_names),
    )
    .configure_title(anchor="start", offset=10, color=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
