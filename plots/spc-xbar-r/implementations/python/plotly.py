""" pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: plotly 6.6.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-19
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data
np.random.seed(42)
n_samples = 30
subgroup_size = 5

# Control chart constants for subgroup size 5
A2 = 0.577
D3 = 0.0
D4 = 2.114

# Generate realistic shaft diameter measurements (mm) from CNC machining
process_mean = 25.0
process_std = 0.05
measurements = np.random.normal(process_mean, process_std, (n_samples, subgroup_size))

# Inject out-of-control points
measurements[7] += 0.15
measurements[18] -= 0.12
measurements[24] += 0.18

# Calculate X-bar and R for each sample
sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

# Control limits for X-bar chart
x_bar_bar = sample_means.mean()
r_bar = sample_ranges.mean()
ucl_xbar = x_bar_bar + A2 * r_bar
lcl_xbar = x_bar_bar - A2 * r_bar
upper_warn_xbar = x_bar_bar + (2 / 3) * A2 * r_bar
lower_warn_xbar = x_bar_bar - (2 / 3) * A2 * r_bar

# Control limits for R chart
ucl_r = D4 * r_bar
lcl_r = D3 * r_bar
upper_warn_r = r_bar + (2 / 3) * (ucl_r - r_bar)
lower_warn_r = max(0, r_bar - (2 / 3) * (r_bar - lcl_r))

sample_ids = np.arange(1, n_samples + 1)

# Identify out-of-control points
ooc_xbar = (sample_means > ucl_xbar) | (sample_means < lcl_xbar)
ooc_r = (sample_ranges > ucl_r) | (sample_ranges < lcl_r)
n_ooc = int(ooc_xbar.sum() + ooc_r.sum())
ooc_samples = ", ".join(f"#{s}" for s in sample_ids[ooc_xbar])

# Colorblind-safe palette
BLUE = "#306998"
LIMIT_COLOR = "#8B0000"
CENTER_COLOR = "#1B5E20"
WARN_COLOR = "#E65100"
OOC_COLOR = "#C62828"
ZONE_A = "rgba(198, 40, 40, 0.06)"
ZONE_B = "rgba(230, 81, 0, 0.05)"

# Plot
fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.10,
    subplot_titles=["<b>X\u0304 Chart</b>  · Sample Means", "<b>R Chart</b>  · Sample Ranges"],
    row_heights=[0.55, 0.45],
)

# Zone shading — X-bar chart
for y0, y1, color in [
    (upper_warn_xbar, ucl_xbar, ZONE_A),
    (lcl_xbar, lower_warn_xbar, ZONE_A),
    (x_bar_bar + (upper_warn_xbar - x_bar_bar) / 2, upper_warn_xbar, ZONE_B),
    (lower_warn_xbar, x_bar_bar - (x_bar_bar - lower_warn_xbar) / 2, ZONE_B),
]:
    fig.add_shape(
        type="rect",
        x0=0.5,
        x1=n_samples + 0.5,
        y0=min(y0, y1),
        y1=max(y0, y1),
        fillcolor=color,
        line={"width": 0},
        layer="below",
        xref="x",
        yref="y",
    )

# Zone shading — R chart
for y0, y1, color in [
    (upper_warn_r, ucl_r, ZONE_A),
    (lcl_r, lower_warn_r, ZONE_A),
    (r_bar + (upper_warn_r - r_bar) / 2, upper_warn_r, ZONE_B),
    (lower_warn_r, r_bar - (r_bar - lower_warn_r) / 2, ZONE_B),
]:
    fig.add_shape(
        type="rect",
        x0=0.5,
        x1=n_samples + 0.5,
        y0=min(y0, y1),
        y1=max(y0, y1),
        fillcolor=color,
        line={"width": 0},
        layer="below",
        xref="x2",
        yref="y2",
    )

# --- X-bar Chart ---
fig.add_trace(
    go.Scatter(
        x=sample_ids,
        y=sample_means,
        mode="lines+markers",
        marker={"size": 10, "color": BLUE},
        line={"width": 2.5, "color": BLUE},
        name="X\u0304",
        hovertemplate="Sample %{x}<br>Mean: %{y:.4f} mm<extra></extra>",
    ),
    row=1,
    col=1,
)

# Out-of-control points (X-bar) with annotations
fig.add_trace(
    go.Scatter(
        x=sample_ids[ooc_xbar],
        y=sample_means[ooc_xbar],
        mode="markers",
        marker={"size": 16, "color": OOC_COLOR, "symbol": "diamond", "line": {"width": 2.5, "color": "white"}},
        name="Out of Control",
        hovertemplate="Sample %{x} (OOC)<br>Mean: %{y:.4f} mm<extra></extra>",
    ),
    row=1,
    col=1,
)

# Annotate OOC points with sample numbers
for idx in np.where(ooc_xbar)[0]:
    above = sample_means[idx] > x_bar_bar
    fig.add_annotation(
        x=sample_ids[idx],
        y=sample_means[idx],
        text=f"<b>#{sample_ids[idx]}</b>",
        font={"size": 13, "color": OOC_COLOR},
        showarrow=True,
        arrowhead=0,
        arrowwidth=1.5,
        arrowcolor=OOC_COLOR,
        ay=-30 if above else 30,
        ax=0,
        xref="x",
        yref="y",
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor=OOC_COLOR,
        borderwidth=1,
        borderpad=3,
    )

# X-bar control limits
fig.add_hline(y=x_bar_bar, line={"color": CENTER_COLOR, "width": 2.5}, row=1, col=1)
fig.add_hline(y=ucl_xbar, line={"color": LIMIT_COLOR, "width": 2, "dash": "dash"}, row=1, col=1)
fig.add_hline(y=lcl_xbar, line={"color": LIMIT_COLOR, "width": 2, "dash": "dash"}, row=1, col=1)
fig.add_hline(y=upper_warn_xbar, line={"color": WARN_COLOR, "width": 1.5, "dash": "dot"}, row=1, col=1)
fig.add_hline(y=lower_warn_xbar, line={"color": WARN_COLOR, "width": 1.5, "dash": "dot"}, row=1, col=1)

# X-bar limit labels (right side)
for y_val, label, color in [
    (ucl_xbar, "UCL", LIMIT_COLOR),
    (lcl_xbar, "LCL", LIMIT_COLOR),
    (x_bar_bar, "CL", CENTER_COLOR),
]:
    fig.add_annotation(
        x=1.0,
        y=y_val,
        text=f"<b>{label}</b>",
        font={"size": 14, "color": color},
        showarrow=False,
        xref="x domain",
        yref="y",
        xanchor="left",
        xshift=8,
    )

# --- R Chart ---
fig.add_trace(
    go.Scatter(
        x=sample_ids,
        y=sample_ranges,
        mode="lines+markers",
        marker={"size": 10, "color": BLUE},
        line={"width": 2.5, "color": BLUE},
        name="Range",
        showlegend=False,
        hovertemplate="Sample %{x}<br>Range: %{y:.4f} mm<extra></extra>",
    ),
    row=2,
    col=1,
)

# Out-of-control points (R)
if ooc_r.any():
    fig.add_trace(
        go.Scatter(
            x=sample_ids[ooc_r],
            y=sample_ranges[ooc_r],
            mode="markers",
            marker={"size": 16, "color": OOC_COLOR, "symbol": "diamond", "line": {"width": 2.5, "color": "white"}},
            name="Out of Control (R)",
            showlegend=False,
        ),
        row=2,
        col=1,
    )
    for idx in np.where(ooc_r)[0]:
        above = sample_ranges[idx] > r_bar
        fig.add_annotation(
            x=sample_ids[idx],
            y=sample_ranges[idx],
            text=f"<b>#{sample_ids[idx]}</b>",
            font={"size": 13, "color": OOC_COLOR},
            showarrow=True,
            arrowhead=0,
            arrowwidth=1.5,
            arrowcolor=OOC_COLOR,
            ay=-30 if above else 30,
            ax=0,
            xref="x2",
            yref="y2",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor=OOC_COLOR,
            borderwidth=1,
            borderpad=3,
        )

# R chart control limits
fig.add_hline(y=r_bar, line={"color": CENTER_COLOR, "width": 2.5}, row=2, col=1)
fig.add_hline(y=ucl_r, line={"color": LIMIT_COLOR, "width": 2, "dash": "dash"}, row=2, col=1)
fig.add_hline(y=lcl_r, line={"color": LIMIT_COLOR, "width": 2, "dash": "dash"}, row=2, col=1)
fig.add_hline(y=upper_warn_r, line={"color": WARN_COLOR, "width": 1.5, "dash": "dot"}, row=2, col=1)
fig.add_hline(y=lower_warn_r, line={"color": WARN_COLOR, "width": 1.5, "dash": "dot"}, row=2, col=1)

# R chart limit labels
for y_val, label, color in [(ucl_r, "UCL", LIMIT_COLOR), (lcl_r, "LCL", LIMIT_COLOR), (r_bar, "CL", CENTER_COLOR)]:
    fig.add_annotation(
        x=1.0,
        y=y_val,
        text=f"<b>{label}</b>",
        font={"size": 14, "color": color},
        showarrow=False,
        xref="x2 domain",
        yref="y2",
        xanchor="left",
        xshift=8,
    )

# Process summary annotation (data storytelling)
fig.add_annotation(
    text=(
        f"<b>⚠ {n_ooc} OOC signal{'s' if n_ooc != 1 else ''} detected</b><br>"
        f"<span style='font-size:12px'>Samples {ooc_samples}<br>"
        f"X\u0304\u0304 = {x_bar_bar:.3f} mm · R\u0304 = {r_bar:.3f} mm</span>"
    ),
    xref="x domain",
    yref="y domain",
    x=0.98,
    y=0.02,
    xanchor="right",
    yanchor="bottom",
    font={"size": 14, "color": "#333"},
    bgcolor="rgba(255, 248, 225, 0.95)",
    bordercolor=WARN_COLOR,
    borderwidth=1.5,
    borderpad=8,
    showarrow=False,
)

# Style
fig.update_layout(
    title={
        "text": (
            "<b>CNC Shaft Diameter Monitoring</b>"
            "<br><span style='font-size:16px;color:#666'>spc-xbar-r · plotly · pyplots.ai"
            "  |  n=5 per subgroup, A₂=0.577, D₃=0, D₄=2.114</span>"
        ),
        "font": {"size": 26},
        "x": 0.02,
        "xanchor": "left",
    },
    template="plotly_white",
    showlegend=True,
    legend={
        "font": {"size": 15},
        "x": 0.01,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "#ccc",
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 80, "t": 90, "b": 60},
    plot_bgcolor="white",
    paper_bgcolor="#FAFAFA",
)

# Subplot title styling
fig.update_annotations(font={"size": 18}, selector={"text": "<b>X\u0304 Chart</b>  · Sample Means"})
fig.update_annotations(font={"size": 18}, selector={"text": "<b>R Chart</b>  · Sample Ranges"})

# Spike lines for cross-chart sample comparison (distinctive Plotly feature)
fig.update_xaxes(
    title={"text": "Sample Number", "font": {"size": 22}},
    tickfont={"size": 18},
    gridcolor="rgba(0,0,0,0.06)",
    spikemode="across",
    spikethickness=1,
    spikecolor="#999",
    spikedash="dot",
    row=2,
    col=1,
)
fig.update_xaxes(
    tickfont={"size": 18},
    gridcolor="rgba(0,0,0,0.06)",
    spikemode="across",
    spikethickness=1,
    spikecolor="#999",
    spikedash="dot",
    row=1,
    col=1,
)
fig.update_yaxes(
    title={"text": "Sample Mean (mm)", "font": {"size": 22}},
    tickfont={"size": 18},
    gridcolor="rgba(0,0,0,0.06)",
    row=1,
    col=1,
)
fig.update_yaxes(
    title={"text": "Sample Range (mm)", "font": {"size": 22}},
    tickfont={"size": 18},
    gridcolor="rgba(0,0,0,0.06)",
    row=2,
    col=1,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", config={"displayModeBar": True, "scrollZoom": True})
