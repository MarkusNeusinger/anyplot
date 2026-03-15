""" pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: plotly 6.6.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-15
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


def enthalpy_from_tw(t, w_kg):
    return 1.006 * t + w_kg * (2501 + 1.86 * t)


def wet_bulb_from_tw(t, w_kg, t_wb):
    return t_wb


# Plot
fig = go.Figure()

# Saturation curve (100% RH) - prominent, with hover data
w_sat = w_from_rh(t_db_range, 1.0) * 1000
mask_sat = (w_sat >= 0) & (w_sat <= 30)
h_sat = enthalpy_from_tw(t_db_range[mask_sat], w_sat[mask_sat] / 1000)
fig.add_trace(
    go.Scatter(
        x=t_db_range[mask_sat],
        y=w_sat[mask_sat],
        mode="lines",
        line={"color": "#1a4971", "width": 4},
        name="Saturation (100% RH)",
        showlegend=True,
        customdata=np.column_stack([h_sat, t_db_range[mask_sat], w_sat[mask_sat]]),
        hovertemplate=(
            "<b>Saturation Curve</b><br>"
            "Dry-Bulb: %{customdata[1]:.1f} °C<br>"
            "Humidity Ratio: %{customdata[2]:.2f} g/kg<br>"
            "Enthalpy: %{customdata[0]:.1f} kJ/kg"
            "<extra></extra>"
        ),
    )
)

# Relative humidity curves (10% to 90%)
rh_colors = {
    10: "rgba(48, 105, 152, 0.25)",
    20: "rgba(48, 105, 152, 0.30)",
    30: "rgba(48, 105, 152, 0.35)",
    40: "rgba(48, 105, 152, 0.40)",
    50: "rgba(48, 105, 152, 0.45)",
    60: "rgba(48, 105, 152, 0.50)",
    70: "rgba(48, 105, 152, 0.55)",
    80: "rgba(48, 105, 152, 0.55)",
    90: "rgba(48, 105, 152, 0.60)",
}
for rh_pct in range(10, 100, 10):
    rh = rh_pct / 100.0
    w = w_from_rh(t_db_range, rh) * 1000
    mask = (w >= 0) & (w <= 30)
    t_plot = t_db_range[mask]
    w_plot = w[mask]
    h_vals = enthalpy_from_tw(t_plot, w_plot / 1000)

    fig.add_trace(
        go.Scatter(
            x=t_plot,
            y=w_plot,
            mode="lines",
            line={"color": rh_colors[rh_pct], "width": 1.5},
            showlegend=False,
            customdata=np.column_stack([h_vals, np.full_like(t_plot, rh_pct)]),
            hovertemplate=(
                "<b>%{customdata[1]:.0f}% RH</b><br>"
                "Dry-Bulb: %{x:.1f} °C<br>"
                "Humidity Ratio: %{y:.2f} g/kg<br>"
                "Enthalpy: %{customdata[0]:.1f} kJ/kg"
                "<extra></extra>"
            ),
        )
    )

    # Label each RH curve - position labels in less crowded lower portion
    if len(t_plot) > 20:
        label_frac = 0.55 if rh_pct <= 30 else 0.45 if rh_pct <= 60 else 0.35
        idx = int(len(t_plot) * label_frac)
        fig.add_annotation(
            x=float(t_plot[idx]),
            y=float(w_plot[idx]),
            text=f"<b>{rh_pct}%</b>",
            showarrow=False,
            font={"size": 12, "color": "rgba(48, 105, 152, 0.8)"},
            xshift=10,
            yshift=8,
        )

# Wet-bulb temperature lines
for t_wb in range(0, 35, 5):
    t_arr = np.linspace(t_wb, min(t_wb + 35, 50), 200)
    p_ws_wb = sat_pressure(np.array([t_wb]))[0]
    w_s_wb = 0.621945 * p_ws_wb / (P_ATM - p_ws_wb)
    w = (w_s_wb - 1.006 * (t_arr - t_wb) / (2501 + 1.86 * t_wb)) * 1000
    w_sat_line = w_from_rh(t_arr, 1.0) * 1000

    mask = (w >= 0) & (w <= 30) & (w <= w_sat_line + 0.3) & (t_arr >= -10)
    t_plot = t_arr[mask]
    w_plot = w[mask]

    if len(t_plot) > 5:
        fig.add_trace(
            go.Scatter(
                x=t_plot,
                y=w_plot,
                mode="lines",
                line={"color": "rgba(46, 139, 87, 0.45)", "width": 1.3},
                showlegend=False,
                hovertemplate=(
                    f"<b>Wet-Bulb: {t_wb}°C</b><br>"
                    "Dry-Bulb: %{x:.1f} °C<br>"
                    "Humidity Ratio: %{y:.2f} g/kg"
                    "<extra></extra>"
                ),
            )
        )
        # Label at the saturation boundary (upper-left end)
        fig.add_annotation(
            x=float(t_plot[0]),
            y=float(w_plot[0]),
            text=f"{t_wb}°C",
            showarrow=False,
            font={"size": 11, "color": "rgba(46, 139, 87, 0.8)"},
            xshift=-22,
            yshift=5,
        )

# Enthalpy lines (kJ/kg) - increased visibility
for h in range(10, 120, 10):
    t_arr = np.linspace(-10, 50, 300)
    w = (h - 1.006 * t_arr) / (2501 + 1.86 * t_arr) * 1000
    w_sat_line = w_from_rh(t_arr, 1.0) * 1000

    mask = (w >= 0) & (w <= 30) & (w <= w_sat_line + 0.3) & (t_arr >= -10)
    t_plot = t_arr[mask]
    w_plot = w[mask]

    if len(t_plot) > 5:
        fig.add_trace(
            go.Scatter(
                x=t_plot,
                y=w_plot,
                mode="lines",
                line={"color": "rgba(200, 80, 50, 0.4)", "width": 1.2, "dash": "dot"},
                showlegend=False,
                hovertemplate=(
                    f"<b>Enthalpy: {h} kJ/kg</b><br>"
                    "Dry-Bulb: %{x:.1f} °C<br>"
                    "Humidity Ratio: %{y:.2f} g/kg"
                    "<extra></extra>"
                ),
            )
        )
        # Label at the top (saturation boundary) end
        fig.add_annotation(
            x=float(t_plot[0]),
            y=float(w_plot[0]),
            text=f"<i>{h}</i>",
            showarrow=False,
            font={"size": 10, "color": "rgba(200, 80, 50, 0.7)"},
            xshift=-8,
            yshift=10,
        )

# Specific volume lines (m³/kg) - increased visibility
for v_100 in range(78, 98, 2):
    v = v_100 / 100.0
    t_arr = np.linspace(-10, 50, 300)
    w = (P_ATM * v / (287.042 * (t_arr + 273.15)) - 1) / (1 + 287.042 / 461.524) * 1000
    w_sat_line = w_from_rh(t_arr, 1.0) * 1000

    mask = (w >= 0) & (w <= 30) & (w <= w_sat_line + 0.3) & (t_arr >= -10)
    t_plot = t_arr[mask]
    w_plot = w[mask]

    if len(t_plot) > 5:
        fig.add_trace(
            go.Scatter(
                x=t_plot,
                y=w_plot,
                mode="lines",
                line={"color": "rgba(128, 0, 128, 0.35)", "width": 1.2, "dash": "dashdot"},
                showlegend=False,
                hovertemplate=(
                    f"<b>Specific Volume: {v:.2f} m³/kg</b><br>"
                    "Dry-Bulb: %{x:.1f} °C<br>"
                    "Humidity Ratio: %{y:.2f} g/kg"
                    "<extra></extra>"
                ),
            )
        )
        # Label at the saturation boundary (top end) instead of bottom to avoid x-axis overlap
        fig.add_annotation(
            x=float(t_plot[0]),
            y=float(w_plot[0]),
            text=f"{v:.2f}",
            showarrow=False,
            font={"size": 10, "color": "rgba(128, 0, 128, 0.7)"},
            xshift=5,
            yshift=10,
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
        fillcolor="rgba(48, 105, 152, 0.12)",
        line={"color": "rgba(48, 105, 152, 0.6)", "width": 2.5, "dash": "dash"},
        name="Comfort Zone",
        showlegend=True,
        hovertemplate=("<b>ASHRAE Comfort Zone</b><br>20–26 °C, 30–60% RH<extra></extra>"),
    )
)

fig.add_annotation(
    x=23,
    y=(comfort_w[2] + comfort_w[1]) / 2,
    text="<b>Comfort<br>Zone</b>",
    showarrow=False,
    font={"size": 14, "color": "#306998"},
)

# HVAC process path: cooling and dehumidification (32°C, 60% RH → 24°C, 50% RH)
state_1_t, state_1_rh = 32, 0.60
state_2_t, state_2_rh = 24, 0.50
state_1_w = float(w_from_rh(np.array([state_1_t]), state_1_rh)[0] * 1000)
state_2_w = float(w_from_rh(np.array([state_2_t]), state_2_rh)[0] * 1000)
state_1_h = enthalpy_from_tw(state_1_t, state_1_w / 1000)
state_2_h = enthalpy_from_tw(state_2_t, state_2_w / 1000)

fig.add_trace(
    go.Scatter(
        x=[state_1_t, state_2_t],
        y=[state_1_w, state_2_w],
        mode="lines+markers",
        line={"color": "#C0392B", "width": 4},
        marker={"size": 16, "color": "#C0392B", "symbol": "circle", "line": {"color": "white", "width": 2.5}},
        name="Cooling & Dehumidification",
        showlegend=True,
        customdata=[
            [state_1_t, state_1_rh * 100, state_1_w, state_1_h],
            [state_2_t, state_2_rh * 100, state_2_w, state_2_h],
        ],
        hovertemplate=(
            "<b>State Point</b><br>"
            "Dry-Bulb: %{customdata[0]:.0f} °C<br>"
            "RH: %{customdata[1]:.0f}%<br>"
            "Humidity Ratio: %{customdata[2]:.1f} g/kg<br>"
            "Enthalpy: %{customdata[3]:.1f} kJ/kg"
            "<extra></extra>"
        ),
    )
)

# Add arrow annotation on the process path
fig.add_annotation(
    x=state_2_t + 1.5,
    y=(state_1_w + state_2_w) / 2,
    ax=state_1_t - 1.5,
    ay=(state_1_w + state_2_w) / 2,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=1.5,
    arrowwidth=2.5,
    arrowcolor="#C0392B",
)

fig.add_annotation(
    x=state_1_t,
    y=state_1_w,
    text="<b>32°C, 60% RH</b>",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1.5,
    arrowcolor="#C0392B",
    ax=45,
    ay=-30,
    font={"size": 14, "color": "#C0392B"},
    bgcolor="rgba(255,255,255,0.85)",
    borderpad=3,
)
fig.add_annotation(
    x=state_2_t,
    y=state_2_w,
    text="<b>24°C, 50% RH</b>",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1.5,
    arrowcolor="#C0392B",
    ax=-45,
    ay=30,
    font={"size": 14, "color": "#C0392B"},
    bgcolor="rgba(255,255,255,0.85)",
    borderpad=3,
)

# Legend entries for property line types
fig.add_trace(
    go.Scatter(
        x=[float("nan")],
        y=[float("nan")],
        mode="lines",
        line={"color": "rgba(46, 139, 87, 0.7)", "width": 2},
        name="Wet-Bulb Temp (°C)",
        showlegend=True,
    )
)
fig.add_trace(
    go.Scatter(
        x=[float("nan")],
        y=[float("nan")],
        mode="lines",
        line={"color": "rgba(200, 80, 50, 0.7)", "width": 2, "dash": "dot"},
        name="Enthalpy (kJ/kg)",
        showlegend=True,
    )
)
fig.add_trace(
    go.Scatter(
        x=[float("nan")],
        y=[float("nan")],
        mode="lines",
        line={"color": "rgba(128, 0, 128, 0.6)", "width": 2, "dash": "dashdot"},
        name="Specific Volume (m³/kg)",
        showlegend=True,
    )
)

# Layout with refined styling
fig.update_layout(
    title={
        "text": "psychrometric-basic · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#2c3e50", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    template="plotly_white",
    xaxis={
        "title": {"text": "Dry-Bulb Temperature (°C)", "font": {"size": 22, "color": "#2c3e50"}},
        "tickfont": {"size": 18, "color": "#555"},
        "range": [-10, 50],
        "dtick": 5,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": "#999",
        "mirror": False,
    },
    yaxis={
        "title": {"text": "Humidity Ratio (g/kg dry air)", "font": {"size": 22, "color": "#2c3e50"}},
        "tickfont": {"size": 18, "color": "#555"},
        "range": [0, 30],
        "dtick": 5,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": "#999",
        "mirror": False,
    },
    legend={
        "font": {"size": 15, "color": "#2c3e50"},
        "x": 0.01,
        "y": 0.99,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": "rgba(255,255,255,0.92)",
        "bordercolor": "#bbb",
        "borderwidth": 1,
        "itemsizing": "constant",
    },
    margin={"l": 100, "r": 60, "t": 100, "b": 80},
    plot_bgcolor="rgba(250,252,255,1)",
    hoverlabel={"bgcolor": "white", "font_size": 14, "font_family": "Arial, sans-serif", "bordercolor": "#306998"},
    hovermode="closest",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
