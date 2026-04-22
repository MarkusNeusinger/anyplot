""" pyplots.ai
campbell-basic: Campbell Diagram
Library: plotly 6.5.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-02-15
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)
speed_rpm = np.linspace(0, 6000, 80)
speed_hz = speed_rpm / 60

# Natural frequency modes (Hz) — enhanced gyroscopic effects for realistic variation
mode_1_bending = 22 + 0.004 * speed_rpm + np.sin(speed_rpm / 1200) * 1.2  # forward whirl stiffening
mode_2_bending = 48 - 0.003 * speed_rpm + np.cos(speed_rpm / 1800) * 1.4  # backward whirl softening
mode_1_torsional = 55 + 0.0004 * speed_rpm  # torsional: nearly speed-independent
mode_axial = 75 - 0.004 * speed_rpm + np.sin(speed_rpm / 1000) * 2.0  # axial with bearing coupling

# Engine order lines: frequency = order * speed_rpm / 60
orders = [1, 2, 3]
order_freq = {order: order * speed_hz for order in orders}

# Find critical speed intersections (engine order line crosses natural frequency curve)
modes = {
    "1st Bending": mode_1_bending,
    "2nd Bending": mode_2_bending,
    "1st Torsional": mode_1_torsional,
    "Axial": mode_axial,
}

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
            crit_hz = crit_rpm / 60
            crit_freq = order * crit_hz
            critical_speeds.append(crit_rpm)
            critical_freqs.append(crit_freq)
            critical_labels.append(f"{mode_name} × {order}x")

# Colorblind-safe palette (avoids red-green confusion)
mode_colors = ["#306998", "#D4A017", "#9467BD", "#E07B39"]
eo_color = "#7F7F7F"
critical_color = "#C44E52"

fig = go.Figure()

# Track trace count for dynamic visibility toggling
trace_count_before_modes = 0

# Shaded bands at critical speed zones
for cs_rpm in critical_speeds:
    fig.add_vrect(x0=cs_rpm - 80, x1=cs_rpm + 80, fillcolor="rgba(196, 78, 82, 0.10)", line_width=0, layer="below")

# Natural frequency curves with distinct dash patterns per mode type
line_dashes = ["solid", "dash", "dot", "dashdot"]
mode_trace_start = len(fig.data)
for i, (mode_name, mode_freq) in enumerate(modes.items()):
    fig.add_trace(
        go.Scatter(
            x=speed_rpm,
            y=mode_freq,
            mode="lines",
            name=mode_name,
            line={"color": mode_colors[i], "width": 3.5, "dash": line_dashes[i]},
            hovertemplate=f"<b>{mode_name}</b><br>Speed: %{{x:.0f}} RPM<br>Freq: %{{y:.1f}} Hz<extra></extra>",
        )
    )
n_mode_traces = len(fig.data) - mode_trace_start

# Engine order lines (clipped to visible y-axis range)
y_max = 110
eo_trace_start = len(fig.data)
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
            line={"color": eo_color, "width": 2.4, "dash": "dash"},
            hovertemplate=f"<b>EO {label}</b><br>Speed: %{{x:.0f}} RPM<br>Freq: %{{y:.1f}} Hz<extra></extra>",
        )
    )
n_eo_traces = len(fig.data) - eo_trace_start

# Engine order labels placed within the visible plot area
for order in orders:
    label = f"{order}x"
    eo_y = order_freq[order]
    visible_mask = eo_y <= y_max
    visible_indices = np.where(visible_mask)[0]
    label_idx = visible_indices[int(len(visible_indices) * 0.75)]
    ann_x = speed_rpm[label_idx]
    ann_y = eo_y[label_idx]
    fig.add_annotation(
        x=ann_x,
        y=ann_y,
        text=f"<b>{label}</b>",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        xshift=8,
        yshift=4,
        font={"size": 16, "color": eo_color, "family": "Arial, sans-serif"},
        bgcolor="rgba(255,255,255,0.85)",
        borderpad=3,
    )

# Critical speed markers with descriptive hover
crit_trace_start = len(fig.data)
fig.add_trace(
    go.Scatter(
        x=critical_speeds,
        y=critical_freqs,
        mode="markers",
        name="Critical Speed",
        marker={"size": 14, "color": critical_color, "symbol": "diamond", "line": {"width": 2, "color": "white"}},
        customdata=critical_labels,
        hovertemplate="<b>Critical Speed</b><br>%{customdata}<br>Speed: %{x:.0f} RPM<br>Freq: %{y:.1f} Hz<extra></extra>",
    )
)
n_crit_traces = len(fig.data) - crit_trace_start

# Annotate the most critical intersection (highest frequency crossing = most dangerous)
if critical_speeds:
    max_idx = int(np.argmax(critical_freqs))
    fig.add_annotation(
        x=critical_speeds[max_idx],
        y=critical_freqs[max_idx],
        text=f"<b>⚠ {critical_freqs[max_idx]:.0f} Hz</b><br>{critical_labels[max_idx]}",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowcolor=critical_color,
        arrowwidth=2,
        ax=50,
        ay=-45,
        font={"size": 13, "color": critical_color, "family": "Arial, sans-serif"},
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor=critical_color,
        borderwidth=1.5,
        borderpad=5,
    )
    # Annotate the lowest-RPM critical speed (first resonance encountered during run-up)
    min_rpm_idx = int(np.argmin(critical_speeds))
    if min_rpm_idx != max_idx:
        fig.add_annotation(
            x=critical_speeds[min_rpm_idx],
            y=critical_freqs[min_rpm_idx],
            text=f"<b>1st critical</b><br>{critical_speeds[min_rpm_idx]:.0f} RPM",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
            arrowcolor=critical_color,
            arrowwidth=2,
            ax=-55,
            ay=40,
            font={"size": 13, "color": critical_color, "family": "Arial, sans-serif"},
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=critical_color,
            borderwidth=1.5,
            borderpad=5,
        )

# Build dynamic visibility arrays for toggle buttons
total_traces = len(fig.data)
all_visible = [True] * total_traces
modes_only = []
for i in range(total_traces):
    if eo_trace_start <= i < eo_trace_start + n_eo_traces:
        modes_only.append(False)
    else:
        modes_only.append(True)

# Layout — compact legend, tight margins
fig.update_layout(
    title={
        "text": "campbell-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#1A2A3A", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={
        "title": {
            "text": "Rotational Speed (RPM)",
            "font": {"size": 22, "color": "#333", "family": "Arial, sans-serif"},
            "standoff": 10,
        },
        "tickfont": {"size": 18, "color": "#444"},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.05)",
        "zeroline": False,
        "range": [0, 6100],
        "dtick": 1000,
        "showline": True,
        "linewidth": 1,
        "linecolor": "rgba(0,0,0,0.12)",
        "mirror": False,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": "rgba(0,0,0,0.3)",
        "spikedash": "dot",
    },
    yaxis={
        "title": {
            "text": "Frequency (Hz)",
            "font": {"size": 22, "color": "#333", "family": "Arial, sans-serif"},
            "standoff": 10,
        },
        "tickfont": {"size": 18, "color": "#444"},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.05)",
        "zeroline": False,
        "range": [0, y_max],
        "dtick": 10,
        "showline": True,
        "linewidth": 1,
        "linecolor": "rgba(0,0,0,0.12)",
        "mirror": False,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": "rgba(0,0,0,0.3)",
        "spikedash": "dot",
    },
    legend={
        "font": {"size": 14, "family": "Arial, sans-serif", "color": "#333"},
        "bgcolor": "rgba(255,255,255,0.92)",
        "bordercolor": "rgba(0,0,0,0.08)",
        "borderwidth": 1,
        "x": 0.01,
        "y": 0.99,
        "xanchor": "left",
        "yanchor": "top",
        "tracegroupgap": 1,
        "itemsizing": "constant",
        "itemwidth": 30,
        "orientation": "h",
    },
    template="plotly_white",
    margin={"l": 75, "r": 30, "t": 70, "b": 65},
    plot_bgcolor="white",
    paper_bgcolor="#F8F9FA",
    hoverlabel={"bgcolor": "white", "font_size": 14, "bordercolor": "#DDD"},
    hovermode="closest",
    dragmode="zoom",
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
            "font": {"size": 12},
            "bgcolor": "rgba(255,255,255,0.9)",
            "bordercolor": "rgba(0,0,0,0.1)",
        }
    ],
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
