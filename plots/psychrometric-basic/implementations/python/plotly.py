""" pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: plotly 6.6.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-15
"""

import numpy as np
import plotly.graph_objects as go


# Constants
P_ATM = 101325  # Standard atmospheric pressure (Pa)
t_db_range = np.linspace(-10, 50, 500)

# Saturation pressure (ASHRAE) - vectorized inline
t_k = t_db_range + 273.15
p_sat_pos = np.exp(
    -5800.2206 / t_k
    + 1.3914993
    - 0.048640239 * t_k
    + 0.000041764768 * t_k**2
    - 0.000000014452093 * t_k**3
    + 6.5459673 * np.log(t_k)
)
p_sat_neg = np.exp(
    -5674.5359 / t_k
    + 6.3925247
    - 0.009677843 * t_k
    + 0.00000062215701 * t_k**2
    + 2.0747825e-09 * t_k**3
    - 9.484024e-13 * t_k**4
    + 4.1635019 * np.log(t_k)
)
p_ws = np.where(t_db_range >= 0, p_sat_pos, p_sat_neg)

fig = go.Figure()

# --- Saturation curve (100% RH) ---
w_sat = 0.621945 * p_ws / (P_ATM - p_ws) * 1000
mask_sat = (w_sat >= 0) & (w_sat <= 30)
h_sat = 1.006 * t_db_range[mask_sat] + (w_sat[mask_sat] / 1000) * (2501 + 1.86 * t_db_range[mask_sat])
fig.add_trace(
    go.Scatter(
        x=t_db_range[mask_sat],
        y=w_sat[mask_sat],
        mode="lines",
        line={"color": "#0d3b66", "width": 5},
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

# --- Relative humidity curves (10% to 90%) ---
# Stagger label positions to avoid crowding
rh_label_fracs = {10: 0.78, 20: 0.72, 30: 0.66, 40: 0.60, 50: 0.54, 60: 0.48, 70: 0.42, 80: 0.36, 90: 0.30}
for rh_pct in range(10, 100, 10):
    rh = rh_pct / 100.0
    p_w = rh * p_ws
    w = 0.621945 * p_w / (P_ATM - p_w) * 1000
    mask = (w >= 0) & (w <= 30)
    t_plot = t_db_range[mask]
    w_plot = w[mask]
    h_vals = 1.006 * t_plot + (w_plot / 1000) * (2501 + 1.86 * t_plot)

    alpha = 0.25 + rh_pct * 0.004  # 0.29 to 0.61
    fig.add_trace(
        go.Scatter(
            x=t_plot,
            y=w_plot,
            mode="lines",
            line={"color": f"rgba(13, 59, 102, {alpha:.2f})", "width": 1.8},
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

    # Label RH curves — stagger positions along the curve to prevent clustering
    if len(t_plot) > 20:
        idx = int(len(t_plot) * rh_label_fracs[rh_pct])
        fig.add_annotation(
            x=float(t_plot[idx]),
            y=float(w_plot[idx]),
            text=f"<b>{rh_pct}%</b>",
            showarrow=False,
            font={"size": 13, "color": "rgba(13, 59, 102, 0.85)"},
            xshift=12,
            yshift=6,
            bgcolor="rgba(250,252,255,0.7)",
        )

# --- Wet-bulb temperature lines ---
for t_wb in range(0, 35, 5):
    t_arr = np.linspace(t_wb, min(t_wb + 35, 50), 200)
    t_k_wb = np.array([t_wb + 273.15])
    p_ws_wb = np.where(
        t_wb >= 0,
        np.exp(
            -5800.2206 / t_k_wb
            + 1.3914993
            - 0.048640239 * t_k_wb
            + 0.000041764768 * t_k_wb**2
            - 0.000000014452093 * t_k_wb**3
            + 6.5459673 * np.log(t_k_wb)
        ),
        np.exp(
            -5674.5359 / t_k_wb
            + 6.3925247
            - 0.009677843 * t_k_wb
            + 0.00000062215701 * t_k_wb**2
            + 2.0747825e-09 * t_k_wb**3
            - 9.484024e-13 * t_k_wb**4
            + 4.1635019 * np.log(t_k_wb)
        ),
    )[0]
    w_s_wb = 0.621945 * p_ws_wb / (P_ATM - p_ws_wb)
    w = (w_s_wb - 1.006 * (t_arr - t_wb) / (2501 + 1.86 * t_wb)) * 1000

    # Saturation line for clipping
    t_k_arr = t_arr + 273.15
    p_ws_arr = np.where(
        t_arr >= 0,
        np.exp(
            -5800.2206 / t_k_arr
            + 1.3914993
            - 0.048640239 * t_k_arr
            + 0.000041764768 * t_k_arr**2
            - 0.000000014452093 * t_k_arr**3
            + 6.5459673 * np.log(t_k_arr)
        ),
        np.exp(
            -5674.5359 / t_k_arr
            + 6.3925247
            - 0.009677843 * t_k_arr
            + 0.00000062215701 * t_k_arr**2
            + 2.0747825e-09 * t_k_arr**3
            - 9.484024e-13 * t_k_arr**4
            + 4.1635019 * np.log(t_k_arr)
        ),
    )
    w_sat_line = 0.621945 * p_ws_arr / (P_ATM - p_ws_arr) * 1000

    mask = (w >= 0) & (w <= 30) & (w <= w_sat_line + 0.3) & (t_arr >= -10)
    t_plot = t_arr[mask]
    w_plot = w[mask]

    if len(t_plot) > 5:
        fig.add_trace(
            go.Scatter(
                x=t_plot,
                y=w_plot,
                mode="lines",
                line={"color": "rgba(34, 120, 74, 0.55)", "width": 1.5},
                showlegend=False,
                hovertemplate=(
                    f"<b>Wet-Bulb: {t_wb}°C</b><br>"
                    "Dry-Bulb: %{x:.1f} °C<br>"
                    "Humidity Ratio: %{y:.2f} g/kg"
                    "<extra></extra>"
                ),
            )
        )
        # Label at ~30% along line (away from both saturation boundary and x-axis)
        label_idx = max(1, int(len(t_plot) * 0.25))
        fig.add_annotation(
            x=float(t_plot[label_idx]),
            y=float(w_plot[label_idx]),
            text=f"<b>{t_wb}°C</b>",
            showarrow=False,
            font={"size": 13, "color": "rgba(34, 120, 74, 0.9)"},
            xshift=12,
            yshift=6,
            bgcolor="rgba(250,252,255,0.7)",
            textangle=-45,
        )

# --- Enthalpy lines (kJ/kg) — increased opacity ---
for h in range(10, 120, 10):
    t_arr = np.linspace(-10, 50, 300)
    w = (h - 1.006 * t_arr) / (2501 + 1.86 * t_arr) * 1000

    t_k_arr = t_arr + 273.15
    p_ws_arr = np.where(
        t_arr >= 0,
        np.exp(
            -5800.2206 / t_k_arr
            + 1.3914993
            - 0.048640239 * t_k_arr
            + 0.000041764768 * t_k_arr**2
            - 0.000000014452093 * t_k_arr**3
            + 6.5459673 * np.log(t_k_arr)
        ),
        np.exp(
            -5674.5359 / t_k_arr
            + 6.3925247
            - 0.009677843 * t_k_arr
            + 0.00000062215701 * t_k_arr**2
            + 2.0747825e-09 * t_k_arr**3
            - 9.484024e-13 * t_k_arr**4
            + 4.1635019 * np.log(t_k_arr)
        ),
    )
    w_sat_line = 0.621945 * p_ws_arr / (P_ATM - p_ws_arr) * 1000

    mask = (w >= 0) & (w <= 30) & (w <= w_sat_line + 0.3) & (t_arr >= -10)
    t_plot = t_arr[mask]
    w_plot = w[mask]

    if len(t_plot) > 5:
        fig.add_trace(
            go.Scatter(
                x=t_plot,
                y=w_plot,
                mode="lines",
                line={"color": "rgba(190, 60, 35, 0.55)", "width": 1.4, "dash": "dot"},
                showlegend=False,
                hovertemplate=(
                    f"<b>Enthalpy: {h} kJ/kg</b><br>"
                    "Dry-Bulb: %{x:.1f} °C<br>"
                    "Humidity Ratio: %{y:.2f} g/kg"
                    "<extra></extra>"
                ),
            )
        )
        # Label every 20 kJ/kg at upper-left end near saturation to reduce clutter
        if h % 20 == 0:
            fig.add_annotation(
                x=float(t_plot[0]),
                y=float(w_plot[0]),
                text=f"<i>{h}</i>",
                showarrow=False,
                font={"size": 13, "color": "rgba(190, 60, 35, 0.85)"},
                xshift=-15,
                yshift=10,
                bgcolor="rgba(250,252,255,0.7)",
                textangle=-45,
            )

# --- Specific volume lines (m³/kg) — increased opacity ---
for v_100 in range(78, 98, 2):
    v = v_100 / 100.0
    t_arr = np.linspace(-10, 50, 300)
    w = (P_ATM * v / (287.042 * (t_arr + 273.15)) - 1) / (1 + 287.042 / 461.524) * 1000

    t_k_arr = t_arr + 273.15
    p_ws_arr = np.where(
        t_arr >= 0,
        np.exp(
            -5800.2206 / t_k_arr
            + 1.3914993
            - 0.048640239 * t_k_arr
            + 0.000041764768 * t_k_arr**2
            - 0.000000014452093 * t_k_arr**3
            + 6.5459673 * np.log(t_k_arr)
        ),
        np.exp(
            -5674.5359 / t_k_arr
            + 6.3925247
            - 0.009677843 * t_k_arr
            + 0.00000062215701 * t_k_arr**2
            + 2.0747825e-09 * t_k_arr**3
            - 9.484024e-13 * t_k_arr**4
            + 4.1635019 * np.log(t_k_arr)
        ),
    )
    w_sat_line = 0.621945 * p_ws_arr / (P_ATM - p_ws_arr) * 1000

    mask = (w >= 0) & (w <= 30) & (w <= w_sat_line + 0.3) & (t_arr >= -10)
    t_plot = t_arr[mask]
    w_plot = w[mask]

    if len(t_plot) > 5:
        fig.add_trace(
            go.Scatter(
                x=t_plot,
                y=w_plot,
                mode="lines",
                line={"color": "rgba(110, 20, 140, 0.50)", "width": 1.4, "dash": "dashdot"},
                showlegend=False,
                hovertemplate=(
                    f"<b>Specific Volume: {v:.2f} m³/kg</b><br>"
                    "Dry-Bulb: %{x:.1f} °C<br>"
                    "Humidity Ratio: %{y:.2f} g/kg"
                    "<extra></extra>"
                ),
            )
        )
        # Label every other volume line at ~40% along line to avoid clustering
        if v_100 % 4 == 0:
            label_idx = max(1, int(len(t_plot) * 0.4))
            fig.add_annotation(
                x=float(t_plot[label_idx]),
                y=float(w_plot[label_idx]),
                text=f"{v:.2f}",
                showarrow=False,
                font={"size": 12, "color": "rgba(110, 20, 140, 0.85)"},
                xshift=-12,
                yshift=8,
                bgcolor="rgba(250,252,255,0.65)",
                textangle=-70,
            )

# --- Comfort zone (20-26°C, 30-60% RH) ---
comfort_temps = np.array([20.0, 26.0, 26.0, 20.0])
comfort_rhs = np.array([0.30, 0.30, 0.60, 0.60])
t_k_c = comfort_temps + 273.15
p_ws_c = np.exp(
    -5800.2206 / t_k_c
    + 1.3914993
    - 0.048640239 * t_k_c
    + 0.000041764768 * t_k_c**2
    - 0.000000014452093 * t_k_c**3
    + 6.5459673 * np.log(t_k_c)
)
comfort_w = (0.621945 * (comfort_rhs * p_ws_c) / (P_ATM - comfort_rhs * p_ws_c) * 1000).tolist()
comfort_t = [20, 26, 26, 20, 20]
comfort_w_closed = comfort_w + [comfort_w[0]]

fig.add_trace(
    go.Scatter(
        x=comfort_t,
        y=comfort_w_closed,
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.10)",
        line={"color": "rgba(48, 105, 152, 0.65)", "width": 2.8, "dash": "dash"},
        name="Comfort Zone",
        showlegend=True,
        hovertemplate="<b>ASHRAE Comfort Zone</b><br>20–26 °C, 30–60% RH<extra></extra>",
    )
)

fig.add_annotation(
    x=23,
    y=(comfort_w[2] + comfort_w[1]) / 2,
    text="<b>Comfort<br>Zone</b>",
    showarrow=False,
    font={"size": 16, "color": "#306998"},
    bgcolor="rgba(255,255,255,0.6)",
)

# --- HVAC process path: cooling and dehumidification (32°C, 60% RH → 24°C, 50% RH) ---
state_1_t, state_1_rh = 32.0, 0.60
state_2_t, state_2_rh = 24.0, 0.50
t_k_s = np.array([state_1_t, state_2_t]) + 273.15
p_ws_s = np.exp(
    -5800.2206 / t_k_s
    + 1.3914993
    - 0.048640239 * t_k_s
    + 0.000041764768 * t_k_s**2
    - 0.000000014452093 * t_k_s**3
    + 6.5459673 * np.log(t_k_s)
)
state_rhs = np.array([state_1_rh, state_2_rh])
state_ws = 0.621945 * (state_rhs * p_ws_s) / (P_ATM - state_rhs * p_ws_s) * 1000
state_hs = 1.006 * np.array([state_1_t, state_2_t]) + (state_ws / 1000) * (
    2501 + 1.86 * np.array([state_1_t, state_2_t])
)

fig.add_trace(
    go.Scatter(
        x=[state_1_t, state_2_t],
        y=[float(state_ws[0]), float(state_ws[1])],
        mode="lines+markers",
        line={"color": "#C0392B", "width": 4.5},
        marker={"size": 16, "color": "#C0392B", "symbol": "circle", "line": {"color": "white", "width": 2.5}},
        name="Cooling & Dehumidification",
        showlegend=True,
        customdata=[
            [state_1_t, state_1_rh * 100, float(state_ws[0]), float(state_hs[0])],
            [state_2_t, state_2_rh * 100, float(state_ws[1]), float(state_hs[1])],
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

# Arrow on process path
fig.add_annotation(
    x=state_2_t + 1.5,
    y=(float(state_ws[0]) + float(state_ws[1])) / 2,
    ax=state_1_t - 1.5,
    ay=(float(state_ws[0]) + float(state_ws[1])) / 2,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=1.8,
    arrowwidth=3,
    arrowcolor="#C0392B",
)

fig.add_annotation(
    x=state_1_t,
    y=float(state_ws[0]),
    text="<b>32°C, 60% RH</b>",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1.5,
    arrowcolor="#C0392B",
    ax=50,
    ay=-35,
    font={"size": 15, "color": "#C0392B"},
    bgcolor="rgba(255,255,255,0.9)",
    borderpad=4,
)
fig.add_annotation(
    x=state_2_t,
    y=float(state_ws[1]),
    text="<b>24°C, 50% RH</b>",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1.5,
    arrowcolor="#C0392B",
    ax=-50,
    ay=35,
    font={"size": 15, "color": "#C0392B"},
    bgcolor="rgba(255,255,255,0.9)",
    borderpad=4,
)

# --- Legend entries for property line types ---
for lname, lcolor, ldash in [
    ("Wet-Bulb Temp (°C)", "rgba(34, 120, 74, 0.8)", "solid"),
    ("Enthalpy (kJ/kg)", "rgba(190, 60, 35, 0.8)", "dot"),
    ("Specific Volume (m³/kg)", "rgba(110, 20, 140, 0.7)", "dashdot"),
]:
    fig.add_trace(
        go.Scatter(
            x=[float("nan")],
            y=[float("nan")],
            mode="lines",
            line={"color": lcolor, "width": 2.5, "dash": ldash},
            name=lname,
            showlegend=True,
        )
    )

# --- Layout ---
fig.update_layout(
    title={
        "text": "psychrometric-basic · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#1a2a3a", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    template="plotly_white",
    xaxis={
        "title": {"text": "Dry-Bulb Temperature (°C)", "font": {"size": 24, "color": "#1a2a3a"}},
        "tickfont": {"size": 18, "color": "#444"},
        "range": [-10, 50],
        "dtick": 5,
        "gridcolor": "rgba(0,0,0,0.05)",
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linewidth": 1.8,
        "linecolor": "#888",
        "mirror": False,
    },
    yaxis={
        "title": {"text": "Humidity Ratio (g/kg dry air)", "font": {"size": 24, "color": "#1a2a3a"}},
        "tickfont": {"size": 18, "color": "#444"},
        "range": [0, 30],
        "dtick": 5,
        "gridcolor": "rgba(0,0,0,0.05)",
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linewidth": 1.8,
        "linecolor": "#888",
        "mirror": False,
    },
    legend={
        "font": {"size": 15, "color": "#1a2a3a"},
        "x": 0.01,
        "y": 0.99,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": "rgba(255,255,255,0.94)",
        "bordercolor": "#aaa",
        "borderwidth": 1,
        "itemsizing": "constant",
    },
    margin={"l": 100, "r": 60, "t": 100, "b": 85},
    plot_bgcolor="rgba(248,251,255,1)",
    hoverlabel={"bgcolor": "white", "font_size": 14, "font_family": "Arial, sans-serif", "bordercolor": "#306998"},
    hovermode="closest",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
