"""anyplot.ai
campbell-basic: Campbell Diagram
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-28
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
CRITICAL_COLOR = "#AE3030"

# Constants
ORDERS = [1, 2, 3]  # engine orders: excitation lines at order x speed / 60 Hz
ZONE_HALF_WIDTH = 60  # RPM half-width of a shaded critical speed zone
TOP_ZONES = 3  # only the highest-frequency critical speeds get a shaded zone

# Columns: set these to your table's column names
SPEED = "Rotational Speed (RPM)"  # role: speed
MODES = ["1st Bending", "2nd Bending", "1st Torsional", "Axial"]  # role: frequency_mode_
ORDER_LABEL = "Engine order"  # role: engine_order
CRITICAL = "Critical Speed"  # role: critical_speeds
FREQ = "Frequency (Hz)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("campbell.csv")
speed_rpm = np.linspace(0, 6000, 80)
df = pd.DataFrame(
    {
        SPEED: speed_rpm,
        MODES[0]: 22 + 0.004 * speed_rpm + np.sin(speed_rpm / 1200) * 1.2,
        MODES[1]: 48 - 0.003 * speed_rpm + np.cos(speed_rpm / 1800) * 1.4,
        MODES[2]: 55 + 0.0004 * speed_rpm,
        MODES[3]: 75 - 0.004 * speed_rpm + np.sin(speed_rpm / 1000) * 2.0,
    }
)

# Plot: reads only df and the constants above
speed_rpm = df[SPEED].to_numpy()
speed_hz = speed_rpm / 60
modes = {name: df[name].to_numpy() for name in MODES}
order_freq = {order: order * speed_hz for order in ORDERS}
y_max = np.ceil(max(m.max() for m in modes.values()) * 1.4 / 10) * 10
x_max = speed_rpm.max() * 6100 / 6000

# Find critical speed intersections
critical_speeds = []
critical_freqs = []
critical_labels = []
for order in ORDERS:
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

# Shade only the most significant critical speed zones (highest frequency) — reduces clutter
if critical_freqs:
    top_indices = sorted(range(len(critical_freqs)), key=lambda i: critical_freqs[i], reverse=True)[:TOP_ZONES]
    for i in top_indices:
        fig.add_vrect(
            x0=critical_speeds[i] - ZONE_HALF_WIDTH,
            x1=critical_speeds[i] + ZONE_HALF_WIDTH,
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
            line={"color": IMPRINT_PALETTE[i], "width": 3.5, "dash": line_dashes[i]},
            hovertemplate=f"<b>{mode_name}</b><br>Speed: %{{x:.0f}} RPM<br>Freq: %{{y:.1f}} Hz<extra></extra>",
        )
    )

# Engine order lines
n_eo_traces = len(ORDERS)
for order in ORDERS:
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
for order in ORDERS:
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
        name=CRITICAL,
        marker={"size": 14, "color": CRITICAL_COLOR, "symbol": "diamond", "line": {"width": 2, "color": PAGE_BG}},
        customdata=critical_labels,
        hovertemplate=f"<b>{CRITICAL}</b><br>%{{customdata}}<br>Speed: %{{x:.0f}} RPM<br>Freq: %{{y:.1f}} Hz<extra></extra>",
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
        "title": {"text": SPEED, "font": {"size": 12, "color": INK}, "standoff": 10},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "range": [0, x_max],
        "dtick": 1000,
        "showline": True,
        "linecolor": INK_SOFT,
        "linewidth": 1,
        "mirror": False,
    },
    yaxis={
        "title": {"text": FREQ, "font": {"size": 12, "color": INK}, "standoff": 10},
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
            "active": -1,
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
