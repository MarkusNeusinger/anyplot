"""anyplot.ai
circos-basic: Circos Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    ggsize,
    guide_legend,
    guides,
    labs,
    scale_fill_manual,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per segment in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: layout radii of the circle (unit circle = outer edge of the segment ring)
RING_OUTER, RING_INNER = 1.0, 0.92
TRACK_BANDS = [(0.89, 0.79), (0.75, 0.65), (0.61, 0.51)]  # (outer, inner) per track, up to three
LABEL_RADIUS = 1.10
GAP_SHARE = 0.10  # share of the circle left as gaps between segments
ARC_POINTS = 60

# Columns: set these to your table's column names
CHROMOSOME = "Chromosome"  # role: source
LINKED = "Linked chromosome"  # role: target
LINKS = "Rearrangements"  # role: value
LENGTH = "Length (Mb)"  # role: segment_size
LIVER = "Expression, liver"  # role: track_data
BRAIN = "Expression, brain"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("rearrangements.csv")
# Segment rows carry the length and the track values; link rows carry the linked chromosome and the count.
segments = pd.DataFrame(
    {
        CHROMOSOME: ["Chr1", "Chr2", "Chr3", "Chr4", "Chr5", "Chr6", "Chr7", "Chr8"],
        LENGTH: [120, 95, 85, 75, 70, 65, 55, 50],
        LIVER: [0.85, 0.72, 0.93, 0.68, 0.81, 0.55, 0.78, 0.62],
        BRAIN: [0.45, 0.82, 0.38, 0.91, 0.55, 0.73, 0.42, 0.88],
    }
)
links = pd.DataFrame(
    [
        ("Chr1", "Chr3", 25),
        ("Chr1", "Chr5", 18),
        ("Chr2", "Chr4", 22),
        ("Chr2", "Chr7", 15),
        ("Chr3", "Chr6", 20),
        ("Chr4", "Chr8", 12),
        ("Chr5", "Chr7", 16),
        ("Chr6", "Chr8", 10),
        ("Chr1", "Chr8", 8),
        ("Chr3", "Chr5", 14),
    ],
    columns=[CHROMOSOME, LINKED, LINKS],
)
df = pd.concat([segments, links], ignore_index=True)

# Plot: reads only df and the constants above
tracks = [LIVER, BRAIN]
segments = df[df[LINKED].isna()]
order = list(df[CHROMOSOME].dropna().unique())
# A ribbon is drawn only when both of its ends are segments on the ring
links = df.dropna(subset=[CHROMOSOME, LINKED, LINKS])
links = links[(links[LINKS] > 0) & links[LINKED].isin(order)]
colors = [IMPRINT_PALETTE[i] for i in range(len(order))]

# Arc lengths follow the segment lengths; segments without a length get the mean one
sizes = segments.groupby(CHROMOSOME, sort=False)[LENGTH].sum(min_count=1).reindex(order)
sizes = sizes.fillna(sizes.mean()).fillna(1.0)
gap = 2 * np.pi * GAP_SHARE / len(order)
arcs = sizes / sizes.sum() * (2 * np.pi - gap * len(order))
starts = pd.Series(np.concatenate([[0.0], np.cumsum(arcs.to_numpy() + gap)[:-1]]), index=order)

# Outer segment ring
ring_frames = []
for name in order:
    a = np.linspace(starts[name], starts[name] + arcs[name], ARC_POINTS)
    radius = np.concatenate([np.full(ARC_POINTS, RING_OUTER), np.full(ARC_POINTS, RING_INNER)])
    angle = np.concatenate([a, a[::-1]])
    ring_frames.append(
        pd.DataFrame({"x": radius * np.cos(angle), "y": radius * np.sin(angle), "poly": name, CHROMOSOME: name})
    )
ring_df = pd.concat(ring_frames, ignore_index=True)

# Concentric data tracks: a faint band per segment, and a bar whose height follows the value
track_values = segments.groupby(CHROMOSOME, sort=False)[tracks].mean().reindex(order)
band_frames, bar_frames = [], []
for track, (outer, inner) in zip(tracks, TRACK_BANDS, strict=False):
    peak = track_values[track].max()
    for name in order:
        a = np.linspace(starts[name], starts[name] + arcs[name], ARC_POINTS)
        angle = np.concatenate([a, a[::-1]])
        band_r = np.concatenate([np.full(ARC_POINTS, outer), np.full(ARC_POINTS, inner)])
        band_frames.append(
            pd.DataFrame({"x": band_r * np.cos(angle), "y": band_r * np.sin(angle), "poly": f"{track}|{name}"})
        )
        value = track_values.at[name, track]
        if pd.notna(value) and peak > 0:
            top = inner + (outer - inner) * max(value, 0) / peak
            bar_r = np.concatenate([np.full(ARC_POINTS, top), np.full(ARC_POINTS, inner)])
            bar_frames.append(
                pd.DataFrame(
                    {
                        "x": bar_r * np.cos(angle),
                        "y": bar_r * np.sin(angle),
                        "poly": f"{track}|{name}",
                        CHROMOSOME: name,
                    }
                )
            )
band_df = pd.concat(band_frames, ignore_index=True)
bar_df = (
    pd.concat(bar_frames, ignore_index=True) if bar_frames else pd.DataFrame(columns=["x", "y", "poly", CHROMOSOME])
)

# Ribbons: one angle per link unit everywhere, so a ribbon is equally wide at both ends
chord_radius = TRACK_BANDS[len(tracks) - 1][1] - 0.03
totals = pd.concat([links.groupby(CHROMOSOME)[LINKS].sum(), links.groupby(LINKED)[LINKS].sum()])
totals = totals.groupby(level=0).sum().reindex(order).fillna(0)
unit = np.nanmin(np.where(totals > 0, 0.9 * arcs / totals.where(totals > 0), np.inf))
cursor = starts + (arcs - totals * unit) / 2
t = np.linspace(0, 1, 50)[1:-1]
ribbon_frames = []
for k, (src, tgt, value) in enumerate(zip(links[CHROMOSOME], links[LINKED], links[LINKS], strict=True)):
    width = value * unit
    s0, s1 = cursor[src], cursor[src] + width
    cursor[src] = s1
    e0, e1 = cursor[tgt], cursor[tgt] + width
    cursor[tgt] = e1
    src_arc = np.linspace(s0, s1, 12)
    tgt_arc = np.linspace(e0, e1, 12)
    # Quadratic Bezier curves through the centre join the two anchor arcs
    xs = np.concatenate(
        [
            chord_radius * np.cos(src_arc),
            ((1 - t) ** 2 * np.cos(s1) + t**2 * np.cos(e0)) * chord_radius,
            chord_radius * np.cos(tgt_arc),
            ((1 - t) ** 2 * np.cos(e1) + t**2 * np.cos(s0)) * chord_radius,
        ]
    )
    ys = np.concatenate(
        [
            chord_radius * np.sin(src_arc),
            ((1 - t) ** 2 * np.sin(s1) + t**2 * np.sin(e0)) * chord_radius,
            chord_radius * np.sin(tgt_arc),
            ((1 - t) ** 2 * np.sin(e1) + t**2 * np.sin(s0)) * chord_radius,
        ]
    )
    ribbon_frames.append(pd.DataFrame({"x": xs, "y": ys, "poly": f"link{k}", CHROMOSOME: src}))
ribbon_df = (
    pd.concat(ribbon_frames, ignore_index=True)
    if ribbon_frames
    else pd.DataFrame(columns=["x", "y", "poly", CHROMOSOME])
)

# Segment labels outside the ring
mids = starts + arcs / 2
label_df = pd.DataFrame(
    {"x": LABEL_RADIUS * np.cos(mids.to_numpy()), "y": LABEL_RADIUS * np.sin(mids.to_numpy()), "label": order}
)

limit = LABEL_RADIUS + 0.06
caption = f"Inner tracks, outer to inner: {' · '.join(tracks)}\nRibbon width: {LINKS}"
title = "circos-basic · python · letsplot · anyplot.ai"

plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", group="poly"), data=band_df, fill=INK, alpha=0.06, color=PAGE_BG, size=0.3)
    + geom_polygon(aes(x="x", y="y", group="poly", fill=CHROMOSOME), data=ribbon_df, alpha=0.5, color=PAGE_BG, size=0.2)
    + geom_polygon(aes(x="x", y="y", group="poly", fill=CHROMOSOME), data=bar_df, alpha=0.85, color=PAGE_BG, size=0.3)
    + geom_polygon(aes(x="x", y="y", group="poly", fill=CHROMOSOME), data=ring_df, color=PAGE_BG, size=0.6)
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=6, color=INK, fontface="bold")
    + scale_fill_manual(values=colors, limits=order, name=CHROMOSOME)
    + coord_fixed(ratio=1, xlim=(-limit, limit), ylim=(-limit, limit))
    + guides(fill=guide_legend(ncol=1))
    + labs(title=title, caption=caption)
    + ggsize(600, 600)
    + theme(
        plot_title=element_text(size=16, face="bold", color=INK),
        plot_caption=element_text(size=11, color=INK_SOFT),
        plot_margin=[33, 28, 33, 16],  # pads the fixed-ratio layout out to the square canvas
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_blank(),
        legend_position="right",
        legend_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

# Save: 600 × 600 at scale 4 = 2400 × 2400 px
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
