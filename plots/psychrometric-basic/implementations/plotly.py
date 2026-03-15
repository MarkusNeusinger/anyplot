"""pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-15
"""

import numpy as np
import plotly.graph_objects as go


# Constants
P_ATM = 101325  # Standard atmospheric pressure (Pa)

# Psychrometric equations (ASHRAE)
t_db_range = np.linspace(-10, 50, 500)


def sat_pressure(t):
    t_k = np.atleast_1d(t + 273.15).astype(float)
    result = np.where(
        t >= 0,
        np.exp(
            -5800.2206 / t_k
            + 1.3914993
            - 0.048640239 * t_k
            + 0.000041764768 * t_k**2
            - 0.000000014452093 * t_k**3
            + 6.5459673 * np.log(t_k)
        ),
        np.exp(
            -5674.5359 / t_k
            + 6.3925247
            - 0.009677843 * t_k
            + 0.00000062215701 * t_k**2
            + 2.0747825e-09 * t_k**3
            - 9.484024e-13 * t_k**4
            + 4.1635019 * np.log(t_k)
        ),
    )
    return result


def w_from_rh(t, rh):
    p_ws = sat_pressure(t)
    p_w = rh * p_ws
    return 0.621945 * p_w / (P_ATM - p_w)


# Plot
fig = go.Figure()

# Relative humidity curves (10% to 100%)
for rh_pct in range(10, 110, 10):
    rh = rh_pct / 100.0
    w = w_from_rh(t_db_range, rh) * 1000
    mask = (w >= 0) & (w <= 30)
    t_plot = t_db_range[mask]
    w_plot = w[mask]

    is_sat = rh_pct == 100
    fig.add_trace(
        go.Scatter(
            x=t_plot,
            y=w_plot,
            mode="lines",
            line=dict(color="#306998" if is_sat else "rgba(48, 105, 152, 0.4)", width=3.5 if is_sat else 1.5),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Label each curve
    if len(t_plot) > 20:
        idx = int(len(t_plot) * (0.7 if is_sat else 0.85))
        fig.add_annotation(
            x=float(t_plot[idx]),
            y=float(w_plot[idx]),
            text=f"{rh_pct}%",
            showarrow=False,
            font=dict(size=13, color="rgba(48, 105, 152, 0.75)"),
            xshift=8,
            yshift=8,
        )

# Wet-bulb temperature lines
for t_wb in range(0, 35, 5):
    t_arr = np.linspace(t_wb, min(t_wb + 35, 50), 200)
    p_ws_wb = sat_pressure(np.array([t_wb]))[0]
    w_s_wb = 0.621945 * p_ws_wb / (P_ATM - p_ws_wb)
    w = (w_s_wb - 1.006 * (t_arr - t_wb) / (2501 + 1.86 * t_wb)) * 1000
    w_sat = w_from_rh(t_arr, 1.0) * 1000

    mask = (w >= 0) & (w <= 30) & (w <= w_sat + 0.3) & (t_arr >= -10)
    t_plot = t_arr[mask]
    w_plot = w[mask]

    if len(t_plot) > 5:
        fig.add_trace(
            go.Scatter(
                x=t_plot,
                y=w_plot,
                mode="lines",
                line=dict(color="rgba(76, 153, 0, 0.35)", width=1.2),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_annotation(
            x=float(t_plot[0]),
            y=float(w_plot[0]),
            text=f"{t_wb}°C",
            showarrow=False,
            font=dict(size=11, color="rgba(76, 153, 0, 0.7)"),
            xshift=-20,
            yshift=5,
        )

# Enthalpy lines (kJ/kg)
for h in range(10, 120, 10):
    t_arr = np.linspace(-10, 50, 300)
    w = (h - 1.006 * t_arr) / (2501 + 1.86 * t_arr) * 1000
    w_sat = w_from_rh(t_arr, 1.0) * 1000

    mask = (w >= 0) & (w <= 30) & (w <= w_sat + 0.3) & (t_arr >= -10)
    t_plot = t_arr[mask]
    w_plot = w[mask]

    if len(t_plot) > 5:
        fig.add_trace(
            go.Scatter(
                x=t_plot,
                y=w_plot,
                mode="lines",
                line=dict(color="rgba(200, 80, 50, 0.25)", width=1),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_annotation(
            x=float(t_plot[0]),
            y=float(w_plot[0]),
            text=f"{h}",
            showarrow=False,
            font=dict(size=10, color="rgba(200, 80, 50, 0.6)"),
            xshift=-5,
            yshift=8,
        )

# Specific volume lines (m³/kg)
for v_100 in range(78, 98, 2):
    v = v_100 / 100.0
    t_arr = np.linspace(-10, 50, 300)
    w = (P_ATM * v / (287.042 * (t_arr + 273.15)) - 1) / (1 + 287.042 / 461.524) * 1000
    w_sat = w_from_rh(t_arr, 1.0) * 1000

    mask = (w >= 0) & (w <= 30) & (w <= w_sat + 0.3) & (t_arr >= -10)
    t_plot = t_arr[mask]
    w_plot = w[mask]

    if len(t_plot) > 5:
        fig.add_trace(
            go.Scatter(
                x=t_plot,
                y=w_plot,
                mode="lines",
                line=dict(color="rgba(128, 0, 128, 0.2)", width=1),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_annotation(
            x=float(t_plot[-1]),
            y=float(w_plot[-1]),
            text=f"{v:.2f}",
            showarrow=False,
            font=dict(size=10, color="rgba(128, 0, 128, 0.55)"),
            yshift=-12,
        )

# Comfort zone (20-26°C, 30-60% RH)
comfort_t = [20, 26, 26, 20, 20]
comfort_w = [
    float(w_from_rh(np.array([20]), 0.30)[0] * 1000),
    float(w_from_rh(np.array([26]), 0.30)[0] * 1000),
    float(w_from_rh(np.array([26]), 0.60)[0] * 1000),
    float(w_from_rh(np.array([20]), 0.60)[0] * 1000),
    float(w_from_rh(np.array([20]), 0.30)[0] * 1000),
]

fig.add_trace(
    go.Scatter(
        x=comfort_t,
        y=comfort_w,
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.1)",
        line=dict(color="rgba(48, 105, 152, 0.5)", width=2),
        name="Comfort Zone",
        showlegend=True,
        hoverinfo="skip",
    )
)

fig.add_annotation(
    x=23,
    y=(comfort_w[2] + comfort_w[1]) / 2,
    text="Comfort<br>Zone",
    showarrow=False,
    font=dict(size=14, color="#306998"),
)

# HVAC process path: cooling and dehumidification (32°C, 60% RH → 24°C, 50% RH)
state_1_w = float(w_from_rh(np.array([32]), 0.60)[0] * 1000)
state_2_w = float(w_from_rh(np.array([24]), 0.50)[0] * 1000)

fig.add_trace(
    go.Scatter(
        x=[32, 24],
        y=[state_1_w, state_2_w],
        mode="lines+markers",
        line=dict(color="#E74C3C", width=4),
        marker=dict(size=14, color="#E74C3C", symbol="circle", line=dict(color="white", width=2)),
        name="Cooling & Dehumidification",
        showlegend=True,
    )
)

fig.add_annotation(
    x=32,
    y=state_1_w,
    text="32°C, 60% RH",
    showarrow=True,
    arrowhead=0,
    ax=30,
    ay=-25,
    font=dict(size=13, color="#E74C3C"),
)
fig.add_annotation(
    x=24,
    y=state_2_w,
    text="24°C, 50% RH",
    showarrow=True,
    arrowhead=0,
    ax=-30,
    ay=25,
    font=dict(size=13, color="#E74C3C"),
)

# Legend entries for property line types
fig.add_trace(
    go.Scatter(
        x=[float("nan")],
        y=[float("nan")],
        mode="lines",
        line=dict(color="rgba(76, 153, 0, 0.7)", width=2),
        name="Wet-Bulb Temp (°C)",
        showlegend=True,
    )
)
fig.add_trace(
    go.Scatter(
        x=[float("nan")],
        y=[float("nan")],
        mode="lines",
        line=dict(color="rgba(200, 80, 50, 0.6)", width=2),
        name="Enthalpy (kJ/kg)",
        showlegend=True,
    )
)
fig.add_trace(
    go.Scatter(
        x=[float("nan")],
        y=[float("nan")],
        mode="lines",
        line=dict(color="rgba(128, 0, 128, 0.55)", width=2),
        name="Specific Volume (m³/kg)",
        showlegend=True,
    )
)

# Layout
fig.update_layout(
    title=dict(text="psychrometric-basic · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    template="plotly_white",
    xaxis=dict(
        title=dict(text="Dry-Bulb Temperature (°C)", font=dict(size=22)),
        tickfont=dict(size=18),
        range=[-10, 50],
        dtick=5,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Humidity Ratio (g/kg dry air)", font=dict(size=22)),
        tickfont=dict(size=18),
        range=[0, 30],
        dtick=5,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False,
    ),
    legend=dict(
        font=dict(size=16),
        x=0.01,
        y=0.99,
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#cccccc",
        borderwidth=1,
    ),
    margin=dict(l=100, r=80, t=120, b=80),
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
