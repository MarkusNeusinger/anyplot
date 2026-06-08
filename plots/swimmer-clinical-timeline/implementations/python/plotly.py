""" anyplot.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: plotly 6.8.0 | Python 3.13.13
Quality: 86/100 | Created: 2026-06-08
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — first series always #009E73 (brand green)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"  # adverse events / warning

ARM_COLORS = {"Arm A": IMPRINT_PALETTE[0], "Arm B": IMPRINT_PALETTE[1]}

EVENT_CONFIG = {
    "partial_response": {"symbol": "triangle-up", "color": IMPRINT_PALETTE[5], "name": "Partial Response"},
    "complete_response": {"symbol": "star", "color": IMPRINT_PALETTE[2], "name": "Complete Response"},
    "progressive_disease": {"symbol": "diamond", "color": IMPRINT_PALETTE[4], "name": "Progressive Disease"},
    "adverse_event": {"symbol": "circle", "color": ANYPLOT_AMBER, "name": "Adverse Event"},
}

# Data — simulated Phase II oncology trial, 25 patients across two treatment arms
np.random.seed(42)

n_patients = 25
patient_ids = [f"PT-{i:03d}" for i in range(1, n_patients + 1)]
arm_labels = ["Arm A"] * 12 + ["Arm B"] * 13

durations = np.concatenate([np.random.uniform(8, 52, 12), np.random.uniform(4, 48, 13)])
ongoing_flags = np.random.choice([True, False], n_patients, p=[0.3, 0.7])

event_type_keys = list(EVENT_CONFIG.keys())
patient_events = []
for i in range(n_patients):
    dur = durations[i]
    n_ev = np.random.randint(1, 4)
    evs = []
    for _ in range(n_ev):
        et = event_type_keys[np.random.randint(len(event_type_keys))]
        t = np.random.uniform(1.0, max(dur * 0.85, 1.5))
        evs.append((et, t))
    patient_events.append(evs)

# Sort ascending by duration — plotly categorical y-axis places first entry at bottom,
# last at top, so ascending sort puts the longest-duration patient at the top
sort_idx = np.argsort(durations)
sorted_ids = [patient_ids[i] for i in sort_idx]
sorted_arms = [arm_labels[i] for i in sort_idx]
sorted_durs = [float(durations[i]) for i in sort_idx]
sorted_ongoing = [bool(ongoing_flags[i]) for i in sort_idx]
sorted_events = [patient_events[i] for i in sort_idx]

# Plot
fig = go.Figure()

# Patient duration bars — each bar colored by treatment arm
bar_colors = [ARM_COLORS[arm] for arm in sorted_arms]
fig.add_trace(
    go.Bar(
        x=sorted_durs,
        y=sorted_ids,
        orientation="h",
        marker=dict(color=bar_colors, opacity=0.75, line=dict(width=0)),
        width=0.65,
        showlegend=False,
        hovertemplate="%{y}: %{x:.1f} wk<extra></extra>",
    )
)

# Dummy bar traces for treatment arm legend entries
for arm, color in ARM_COLORS.items():
    fig.add_trace(go.Bar(x=[None], y=[None], orientation="h", name=arm, marker=dict(color=color, opacity=0.75)))

# Clinical event markers — one scatter trace per event type
for et_key, config in EVENT_CONFIG.items():
    ex, ey = [], []
    for j, evs in enumerate(sorted_events):
        for et, t in evs:
            if et == et_key:
                ex.append(t)
                ey.append(sorted_ids[j])
    if ex:
        fig.add_trace(
            go.Scatter(
                x=ex,
                y=ey,
                mode="markers",
                name=config["name"],
                marker=dict(symbol=config["symbol"], size=13, color=config["color"], line=dict(color=INK, width=1.0)),
                hovertemplate=f"{config['name']}: %{{x:.1f}} wk<extra></extra>",
            )
        )

# Ongoing patients: right-pointing triangle placed just beyond bar end
ong_x = [sorted_durs[j] + 0.4 for j in range(n_patients) if sorted_ongoing[j]]
ong_y = [sorted_ids[j] for j in range(n_patients) if sorted_ongoing[j]]
if ong_x:
    fig.add_trace(
        go.Scatter(
            x=ong_x,
            y=ong_y,
            mode="markers",
            name="Ongoing",
            marker=dict(symbol="triangle-right", size=14, color=INK, line=dict(color=INK, width=0.5)),
            hovertemplate="Still on study<extra></extra>",
        )
    )

# Style
title = "swimmer-clinical-timeline · python · plotly · anyplot.ai"

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    barmode="overlay",
    title=dict(text=title, font=dict(size=16, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Weeks on Study", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        showgrid=True,
        range=[0, 57],
    ),
    yaxis=dict(
        title=dict(text="Patient ID", font=dict(size=12, color=INK)),
        tickfont=dict(size=8, color=INK_SOFT),
        linecolor=INK_SOFT,
        showgrid=False,
        tickmode="array",
        tickvals=sorted_ids,
        ticktext=sorted_ids,
    ),
    legend=dict(
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        font=dict(size=10, color=INK_SOFT),
        x=1.02,
        xanchor="left",
        y=1.0,
        yanchor="top",
    ),
    margin=dict(l=90, r=170, t=80, b=60),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
