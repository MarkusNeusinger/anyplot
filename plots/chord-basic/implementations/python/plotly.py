"""anyplot.ai
chord-basic: Basic Chord Diagram
Library: plotly | Python 3.14
Quality: pending | Created: 2026-06-17
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme-adaptive chrome (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — continents are abstract categories, so canonical order 1..6
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]
imprint_rgb = [(int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)) for c in IMPRINT]
dim_fill = [f"rgba({r},{g},{b},0.32)" for r, g, b in imprint_rgb]

# Data: bidirectional migration flows between 6 continents (millions of people)
continents = ["Africa", "Asia", "Europe", "N. America", "S. America", "Oceania"]
n = len(continents)

# Flow matrix (row = source, col = target)
flow_matrix = np.array(
    [
        [0, 15, 25, 10, 5, 3],  # Africa to others
        [12, 0, 30, 20, 8, 15],  # Asia to others
        [20, 35, 0, 25, 12, 10],  # Europe to others
        [8, 18, 22, 0, 15, 5],  # N. America to others
        [6, 10, 18, 20, 0, 4],  # S. America to others
        [2, 12, 8, 6, 3, 0],  # Oceania to others
    ]
)

totals = flow_matrix.sum(axis=0) + flow_matrix.sum(axis=1)
total_flow = flow_matrix.sum()

# Arc positions around the circle (gaps separate adjacent continents)
gap = 0.02
arc_starts = []
arc_ends = []
current_pos = 0
for total in totals:
    arc_starts.append(current_pos)
    arc_ends.append(current_pos + (total / total_flow) * (1 - n * gap))
    current_pos = arc_ends[-1] + gap

fig = go.Figure()

# Outer arcs — layered ring (translucent halo + solid band) for depth
for i in range(n):
    angles = np.linspace(2 * np.pi * arc_starts[i] - np.pi / 2, 2 * np.pi * arc_ends[i] - np.pi / 2, 100)
    angles_rev = angles[::-1]

    # Translucent outer halo
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([1.03 * np.cos(angles), 0.99 * np.cos(angles_rev)]),
            y=np.concatenate([1.03 * np.sin(angles), 0.99 * np.sin(angles_rev)]),
            fill="toself",
            fillcolor=dim_fill[i],
            line={"width": 0},
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Solid inner band — the entity arc itself
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([1.0 * np.cos(angles), 0.94 * np.cos(angles_rev)]),
            y=np.concatenate([1.0 * np.sin(angles), 0.94 * np.sin(angles_rev)]),
            fill="toself",
            fillcolor=IMPRINT[i],
            line={"color": PAGE_BG, "width": 1.0},
            hovertemplate=(
                f"<b>{continents[i]}</b><br>"
                f"Outgoing: {int(flow_matrix[i].sum())}M<br>"
                f"Incoming: {int(flow_matrix[:, i].sum())}M<br>"
                f"Total: {int(totals[i])}M people"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )

# Chords — ribbons coloured by source, width proportional to flow magnitude
min_chord_width = 0.01  # floor so the smallest flows stay visible
for i in range(n):
    src_pos = arc_starts[i]
    for j in range(n):
        if i == j or flow_matrix[i, j] == 0:
            continue

        flow = flow_matrix[i, j]
        chord_width = max((flow / total_flow) * (1 - n * gap), min_chord_width)

        # Reserve target-arc space for incoming flows in source order
        tgt_base = arc_starts[j]
        tgt_offset = sum(
            max((flow_matrix[k, j] / total_flow) * (1 - n * gap), min_chord_width)
            for k in range(i)
            if flow_matrix[k, j] > 0
        )

        src_angle1 = 2 * np.pi * src_pos - np.pi / 2
        src_angle2 = 2 * np.pi * (src_pos + chord_width) - np.pi / 2
        sx1, sy1 = 0.94 * np.cos(src_angle1), 0.94 * np.sin(src_angle1)
        sx2, sy2 = 0.94 * np.cos(src_angle2), 0.94 * np.sin(src_angle2)

        tgt_start = tgt_base + tgt_offset
        tgt_end = tgt_start + chord_width
        tgt_angle1 = 2 * np.pi * tgt_start - np.pi / 2
        tgt_angle2 = 2 * np.pi * tgt_end - np.pi / 2
        tx1, ty1 = 0.94 * np.cos(tgt_angle1), 0.94 * np.sin(tgt_angle1)
        tx2, ty2 = 0.94 * np.cos(tgt_angle2), 0.94 * np.sin(tgt_angle2)

        # Quadratic bezier toward circle centre for smooth ribbons
        src_angles = np.linspace(src_angle1, src_angle2, 20)
        src_x = 0.94 * np.cos(src_angles)
        src_y = 0.94 * np.sin(src_angles)

        t = np.linspace(0, 1, 40)
        bez1_x = (1 - t) ** 2 * sx2 + t**2 * tx1
        bez1_y = (1 - t) ** 2 * sy2 + t**2 * ty1

        tgt_angles = np.linspace(tgt_angle1, tgt_angle2, 20)
        tgt_x = 0.94 * np.cos(tgt_angles)
        tgt_y = 0.94 * np.sin(tgt_angles)

        bez2_x = (1 - t) ** 2 * tx2 + t**2 * sx1
        bez2_y = (1 - t) ** 2 * ty2 + t**2 * sy1

        fig.add_trace(
            go.Scatter(
                x=np.concatenate([src_x, bez1_x, tgt_x, bez2_x]),
                y=np.concatenate([src_y, bez1_y, tgt_y, bez2_y]),
                fill="toself",
                fillcolor=IMPRINT[i],
                opacity=0.5,
                line={"color": PAGE_BG, "width": 0.4},
                hovertemplate=(
                    f"<b>{continents[i]} → {continents[j]}</b><br>"
                    f"Flow: {flow}M people<br>"
                    f"Share: {flow / total_flow * 100:.1f}% of total"
                    "<extra></extra>"
                ),
                showlegend=False,
                hoveron="fills",
            )
        )

        src_pos += chord_width

# Perimeter labels — colour-coded to each arc (these replace a redundant legend)
for i in range(n):
    mid_pos = (arc_starts[i] + arc_ends[i]) / 2
    angle = 2 * np.pi * mid_pos - np.pi / 2
    lx, ly = 1.13 * np.cos(angle), 1.13 * np.sin(angle)
    angle_deg = np.degrees(angle) % 360

    if 45 < angle_deg < 135:
        xanchor, yanchor = "center", "bottom"
    elif 135 <= angle_deg < 225:
        xanchor, yanchor = "right", "middle"
    elif 225 <= angle_deg < 315:
        xanchor, yanchor = "center", "top"
    else:
        xanchor, yanchor = "left", "middle"

    fig.add_annotation(
        x=lx,
        y=ly,
        text=(f"<b>{continents[i]}</b> <span style='font-size:13px;color:{INK_MUTED}'>{int(totals[i])}M</span>"),
        font={"size": 17, "color": IMPRINT[i], "family": "Arial, Helvetica, sans-serif"},
        showarrow=False,
        xanchor=xanchor,
        yanchor=yanchor,
    )

# Layout — square canvas (2400 x 2400), theme-adaptive chrome
title = "Continental Migration · chord-basic · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    title={
        "text": title,
        "font": {"size": 15, "color": INK, "family": "Arial, Helvetica, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "showline": False, "range": [-1.7, 1.7]},
    yaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "showline": False,
        "range": [-1.55, 1.55],
        "scaleanchor": "x",
    },
    showlegend=False,
    margin={"l": 30, "r": 30, "t": 70, "b": 30},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    hovermode="closest",
    hoverlabel={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "font": {"size": 14, "family": "Arial, Helvetica, sans-serif", "color": INK},
    },
)

# Save — square 2400 x 2400 (width=600, height=600, scale=4)
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
