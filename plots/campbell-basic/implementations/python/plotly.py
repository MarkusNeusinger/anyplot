"""anyplot.ai
campbell-basic: Campbell Diagram
Library: plotly | Python 3.13
Quality: pending | Created: 2026-05-28
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
CRITICAL_COLOR = "#AE3030"

# Data
np.random.seed(42)
speed_rpm = np.linspace(0, 6000, 80)
speed_hz = speed_rpm / 60

# Natural frequency modes (Hz) with realistic gyroscopic effects
mode_1_bending = 22 + 0.004 * speed_rpm + np.sin(speed_rpm / 1200) * 1.2
mode_2_bending = 48 - 0.003 * speed_rpm + np.cos(speed_rpm / 1800) * 1.4
mode_1_torsional = 55 + 0.0004 * speed_rpm
mode_axial = 75 - 0.004 * speed_rpm + np.sin(speed_rpm / 1000) * 2.0

orders = [1, 2, 3]
order_freq = {order: order * speed_hz for order in orders}

modes = {
    "1st Bending": mode_1_bending,
    "2nd Bending": mode_2_bending,
    "1st Torsional": mode_1_torsional,
    "Axial": mode_axial,
}

# Find critical speed intersections
critical_speeds = []
critical_freqs = []
critical_labels = []
for order in orders:
    eo_freq = order_freq[order]
    for mode_name, mode_freq in modes.items():
        diff = mode_freq - eo_freq
        sign_changes = np.where(np.diff(np.sign(diff)))[0]
        for idx in sign_changes:
            frac = abs(diff[idx]) / (abs(diff[idx]) + abs(diff[idx + 1]))
            crit_rpm = speed_rpm[idx] + frac * (speed_rpm[idx + 1] - speed_rpm[idx])
            crit_freq = order * (crit_rpm / 60)
            critical_speeds.append(crit_rpm)
            critical_freqs.append(crit_freq)
            critical_labels.append(f"{mode_name} × {order}x")

fig = go.Figure()

# Shade only the 3 most significant critical speed zones (highest frequency) — reduces clutter
y_max = 110
if critical_freqs:
    top_indices = sorted(range(len(critical_freqs)), key=lambda i: critical_freqs[i], reverse=True)[:3]
    for i in top_indices:
        fig.add_vrect(
            x0=critical_speeds[i] - 60,
            x1=critical_speeds[i] + 60,
            fillcolor="rgba(174,48,48,0.08)",
            line_width=0,
            layer="below",
        )

# Natural frequency curves
line_dashes = ["solid", "dash", "dot", "dashdot"]
n_mode_traces = len(modes)
for i, (mode_name, mode_freq) in enumerate(modes.items()):
    fig.add_trace(
        go.Scatter(
            x=speed_rpm,
            y=mode_freq,
            mode="lines",
            name=mode_name,
            line={"color": ANYPLOT_PALETTE[i], "width": 3.5, "dash": line_dashes[i]},
            hovertemplate=f"<b>{mode_name}</b><br>Speed: %{{x:.0f}} RPM<br>Freq: %{{y:.1f}} Hz<extra></extra>",
        )
    )

# Engine order lines
n_eo_traces = len(orders)
for order in orders:
    label = f"{order}x"
    eo_y = order_freq[order]
    mask = eo_y <= y_max
    fig.add_trace(
        go.Scatter(
            x=speed_rpm[mask],
            y=eo_y[mask],
            mode="lines",
            name=f"EO {label}",
            line={"color": INK_SOFT, "width": 2, "dash": "dash"},
            hovertemplate=f"<b>EO {label}</b><br>Speed: %{{x:.0f}} RPM<br>Freq: %{{y:.1f}} Hz<extra></extra>",
        )
    )

# Engine order labels at 75% along visible segment
for order in orders:
    eo_y = order_freq[order]
    visible_indices = np.where(eo_y <= y_max)[0]
    if len(visible_indices) > 0:
        label_idx = visible_indices[int(len(visible_indices) * 0.75)]
        fig.add_annotation(
            x=speed_rpm[label_idx],
            y=eo_y[label_idx],
            text=f"<b>{order}x</b>",
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            xshift=8,
            yshift=4,
            font={"size": 11, "color": INK_SOFT},
            bgcolor=ELEVATED_BG,
            borderpad=2,
        )

# Critical speed markers
fig.add_trace(
    go.Scatter(
        x=critical_speeds,
        y=critical_freqs,
        mode="markers",
        name="Critical Speed",
        marker={"size": 14, "color": CRITICAL_COLOR, "symbol": "diamond", "line": {"width": 2, "color": PAGE_BG}},
        customdata=critical_labels,
        hovertemplate="<b>Critical Speed</b><br>%{customdata}<br>Speed: %{x:.0f} RPM<br>Freq: %{y:.1f} Hz<extra></extra>",
    )
)

# Annotate highest-frequency and first (lowest-RPM) critical intersections
if critical_speeds:
    max_idx = int(np.argmax(critical_freqs))
    fig.add_annotation(
        x=critical_speeds[max_idx],
        y=critical_freqs[max_idx],
        text=f"<b>{critical_freqs[max_idx]:.0f} Hz</b><br>{critical_labels[max_idx]}",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowcolor=CRITICAL_COLOR,
        arrowwidth=2,
        ax=50,
        ay=-45,
        font={"size": 10, "color": CRITICAL_COLOR},
        bgcolor=ELEVATED_BG,
        bordercolor=CRITICAL_COLOR,
        borderwidth=1.5,
        borderpad=4,
    )
    min_rpm_idx = int(np.argmin(critical_speeds))
    if min_rpm_idx != max_idx:
        fig.add_annotation(
            x=critical_speeds[min_rpm_idx],
            y=critical_freqs[min_rpm_idx],
            text=f"<b>1st critical</b><br>{critical_speeds[min_rpm_idx]:.0f} RPM",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
            arrowcolor=CRITICAL_COLOR,
            arrowwidth=2,
            ax=-55,
            ay=40,
            font={"size": 10, "color": CRITICAL_COLOR},
            bgcolor=ELEVATED_BG,
            bordercolor=CRITICAL_COLOR,
            borderwidth=1.5,
            borderpad=4,
        )

# Toggle visibility arrays (simplified: modes + criticals vs all)
total_traces = n_mode_traces + n_eo_traces + 1
all_visible = [True] * total_traces
modes_only = [True] * n_mode_traces + [False] * n_eo_traces + [True]

title = "campbell-basic · python · plotly · anyplot.ai"

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center", "y": 0.97},
    xaxis={
        "title": {"text": "Rotational Speed (RPM)", "font": {"size": 12, "color": INK}, "standoff": 10},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "range": [0, 6100],
        "dtick": 1000,
        "showline": True,
        "linecolor": INK_SOFT,
        "linewidth": 1,
        "mirror": False,
    },
    yaxis={
        "title": {"text": "Frequency (Hz)", "font": {"size": 12, "color": INK}, "standoff": 10},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "range": [0, y_max],
        "dtick": 10,
        "showline": True,
        "linecolor": INK_SOFT,
        "linewidth": 1,
        "mirror": False,
    },
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 0.01,
        "y": 0.99,
        "xanchor": "left",
        "yanchor": "top",
        "tracegroupgap": 0,
        "itemsizing": "constant",
        "orientation": "v",
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    hovermode="closest",
    updatemenus=[
        {
            "type": "buttons",
            "direction": "left",
            "x": 1.0,
            "y": 1.05,
            "xanchor": "right",
            "yanchor": "top",
            "buttons": [
                {"label": "All Modes", "method": "update", "args": [{"visible": all_visible}]},
                {"label": "Modes Only", "method": "update", "args": [{"visible": modes_only}]},
            ],
            "font": {"size": 10, "color": INK},
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
        }
    ],
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
