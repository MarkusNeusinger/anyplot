""" anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: plotly 7.1.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-26
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26, 26, 23, 0.10)" if THEME == "light" else "rgba(240, 239, 232, 0.10)"

# Imprint palette: temperature takes position 1, dewpoint position 2
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
C_TEMP = IMPRINT_PALETTE[0]
C_DEWPT = IMPRINT_PALETTE[1]

# Reference line colors: subtle, theme-adaptive (Imprint positions 2, 3 and 1 as translucent rgba)
C_ISO = "rgba(80, 80, 80, 0.22)" if THEME == "light" else "rgba(180, 180, 180, 0.28)"
C_DRY = "rgba(196, 117, 253, 0.22)" if THEME == "light" else "rgba(196, 117, 253, 0.38)"
C_MOIST = "rgba(68, 103, 163, 0.40)" if THEME == "light" else "rgba(68, 103, 163, 0.50)"
C_MIX = "rgba(0, 158, 115, 0.22)" if THEME == "light" else "rgba(0, 158, 115, 0.38)"

# Constants
SKEW = 30.0  # °C shift per log10 decade of pressure from the reference pressure
P_REF_HPA = 1000.0  # pressure where the skew is zero (hPa)
Rd = 287.05  # J/(kg·K)
Cp = 1004.0  # J/(kg·K)
Lv = 2.5e6  # J/kg
Rv = 461.5  # J/(kg·K)
Rd_Cp = Rd / Cp  # ≈ 0.2854
ISOTHERMS_C = range(-70, 55, 10)  # reference isotherms, also the x tick values
THETA_K = range(290, 430, 10)  # dry adiabats by potential temperature (K)
MOIST_START_C = range(-10, 45, 10)  # moist adiabats by temperature at the reference pressure
MIXING_RATIOS_GKG = [1, 2, 4, 8, 16]  # mixing ratio lines (g/kg)
X_MAX = 75.0  # right edge of the skewed temperature axis
STANDARD_LEVELS_HPA = [100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000]  # y tick candidates

# Columns: set these to your table's column names
PRESSURE = "Pressure (hPa)"  # role: pressure
TEMPERATURE = "Temperature (°C)"  # role: temperature
DEWPOINT = "Dewpoint (°C)"  # role: dewpoint

# Data: synthetic warm-moist sounding, US Great Plains summer; replace with df = pd.read_csv("sounding.csv")
df = pd.DataFrame(
    {
        PRESSURE: [1000, 975, 950, 925, 900, 850, 800, 750, 700, 650, 600]
        + [550, 500, 450, 400, 350, 300, 250, 200, 150, 100],
        TEMPERATURE: [32.0, 29.0, 26.0, 23.0, 20.5, 16.0, 11.0, 6.0, 2.0, -3.5, -8.5]
        + [-15.0, -21.5, -29.0, -37.5, -48.0, -56.0, -62.0, -64.5, -68.0, -73.0],
        DEWPOINT: [24.0, 22.0, 20.5, 18.0, 14.5, 9.0, 2.5, -5.0, -13.0, -23.0, -33.0]
        + [-43.0, -53.0, -62.0, -70.0, -76.0, -81.0, -84.0, -86.0, -88.0, -90.0],
    }
)


# Plot: reads only df and the constants above
def skew_x(T, P):
    return T + SKEW * np.log10(P_REF_HPA / P)


def moist_adiabat(T0_C, P_start, P_end, n=150):
    """Integrate a moist adiabat from P_start to P_end starting at T0_C."""
    P = np.linspace(P_start, P_end, n)
    T = np.zeros(n)
    T[0] = T0_C
    for i in range(1, n):
        T_K = T[i - 1] + 273.15
        es = 6.112 * np.exp(17.67 * T[i - 1] / (T[i - 1] + 243.5))
        rs = 0.622 * es / max(P[i - 1] - es, 0.001)
        num = Rd * T_K + Lv * rs
        den = P[i - 1] * (Cp + Lv**2 * rs / (Rv * T_K**2))
        T[i] = T[i - 1] + (num / den) * (P[i] - P[i - 1])
    return P, T


pressure = df[PRESSURE].to_numpy(dtype=float)
temperature = df[TEMPERATURE].to_numpy(dtype=float)
dewpoint = df[DEWPOINT].to_numpy(dtype=float)
p_bottom = float(np.nanmax(pressure))
p_top = float(np.nanmin(pressure))

# Lifting Condensation Level of the surface parcel (Bolton 1980)
i_sfc = int(np.nanargmax(pressure))
T_sfc_K = temperature[i_sfc] + 273.15
Td_sfc_K = dewpoint[i_sfc] + 273.15
T_lcl_K = 1.0 / (1.0 / (Td_sfc_K - 56.0) + np.log(T_sfc_K / Td_sfc_K) / 800.0) + 56.0
lcl_p = pressure[i_sfc] * (T_lcl_K / T_sfc_K) ** (1.0 / Rd_Cp)
lcl_t = T_lcl_K - 273.15

# Pressure array for reference lines
P_ref = np.linspace(p_top, p_bottom, 200)

fig = go.Figure()

# --- Reference lines (background layer) ---

# Isotherms (constant temperature, appear as diagonal lines when skewed)
for idx, T_iso in enumerate(ISOTHERMS_C):
    fig.add_trace(
        go.Scatter(
            x=skew_x(T_iso * np.ones_like(P_ref), P_ref),
            y=P_ref,
            mode="lines",
            line=dict(color=C_ISO, width=0.8),
            legendgroup="iso",
            showlegend=(idx == 0),
            name="Isotherms",
            hoverinfo="skip",
        )
    )

# Dry adiabats (constant potential temperature θ)
for idx, theta in enumerate(THETA_K):
    T_dry = theta * (P_ref / P_REF_HPA) ** Rd_Cp - 273.15
    mask = (T_dry > -55) & (T_dry < 55)
    x_d = np.where(mask, skew_x(T_dry, P_ref), np.nan)
    if not np.all(np.isnan(x_d)):
        fig.add_trace(
            go.Scatter(
                x=x_d,
                y=P_ref,
                mode="lines",
                line=dict(color=C_DRY, width=0.8),
                legendgroup="dry",
                showlegend=(idx == 0),
                name="Dry Adiabats",
                hoverinfo="skip",
            )
        )

# Moist adiabats (saturated adiabatic lapse rate, numerically integrated)
for idx, T0 in enumerate(MOIST_START_C):
    P_m, T_m = moist_adiabat(T0, p_bottom, p_top)
    fig.add_trace(
        go.Scatter(
            x=skew_x(T_m, P_m),
            y=P_m,
            mode="lines",
            line=dict(color=C_MOIST, width=0.8, dash="dot"),
            legendgroup="moist",
            showlegend=(idx == 0),
            name="Moist Adiabats",
            hoverinfo="skip",
        )
    )

# Mixing ratio lines (constant water vapor mixing ratio)
for idx, r_gkg in enumerate(MIXING_RATIOS_GKG):
    r = r_gkg / 1000.0
    es = r * P_ref / (r + 0.622)
    with np.errstate(divide="ignore", invalid="ignore"):
        log_r = np.log(es / 6.112)
        T_mix = 243.5 * log_r / (17.67 - log_r)
    mask = np.isfinite(T_mix) & (T_mix > -50) & (T_mix < 35)
    x_mix = np.where(mask, skew_x(T_mix, P_ref), np.nan)
    fig.add_trace(
        go.Scatter(
            x=x_mix,
            y=P_ref,
            mode="lines",
            line=dict(color=C_MIX, width=0.8, dash="dash"),
            legendgroup="mix",
            showlegend=(idx == 0),
            name="Mixing Ratio",
            hoverinfo="skip",
        )
    )

# --- Atmospheric sounding profiles ---

# Dewpoint (dashed)
fig.add_trace(
    go.Scatter(
        x=skew_x(dewpoint, pressure),
        y=pressure,
        mode="lines+markers",
        name="Dewpoint",
        line=dict(color=C_DEWPT, width=2.5, dash="dash"),
        marker=dict(color=C_DEWPT, size=7),
        customdata=np.column_stack([dewpoint, pressure]),
        hovertemplate="%{customdata[1]:.0f} hPa | Td: %{customdata[0]:.1f}°C<extra></extra>",
    )
)

# Temperature (solid, Imprint position 1)
fig.add_trace(
    go.Scatter(
        x=skew_x(temperature, pressure),
        y=pressure,
        mode="lines+markers",
        name="Temperature",
        line=dict(color=C_TEMP, width=3.0),
        marker=dict(color=C_TEMP, size=7),
        customdata=np.column_stack([temperature, pressure]),
        hovertemplate="%{customdata[1]:.0f} hPa | T: %{customdata[0]:.1f}°C<extra></extra>",
    )
)

# --- Layout ---

# x-axis ticks: at the reference pressure the skew is zero, so tick position = actual temperature
y_ticks = [p for p in STANDARD_LEVELS_HPA if p_top <= p <= p_bottom]

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title=dict(
        text="skewt-logp-atmospheric · python · plotly · anyplot.ai",
        font=dict(size=16, color=INK),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text=TEMPERATURE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        linecolor=INK_SOFT,
        zeroline=False,
        showgrid=False,
        tickmode="array",
        tickvals=[float(t) for t in ISOTHERMS_C],
        ticktext=[f"{t}°" for t in ISOTHERMS_C],
        range=[float(np.nanmin(skew_x(dewpoint, pressure))) - 5.0, X_MAX],
    ),
    yaxis=dict(
        title=dict(text=PRESSURE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zeroline=False,
        type="log",
        range=[np.log10(p_bottom), np.log10(p_top)],  # inverted: surface at the bottom
        tickmode="array",
        tickvals=y_ticks,
        ticktext=[str(p) for p in y_ticks],
        showgrid=True,
    ),
    legend=dict(
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        font=dict(size=10, color=INK_SOFT),
        x=1.01,
        y=1.0,
        xanchor="left",
        yanchor="top",
    ),
    margin=dict(l=80, r=150, t=80, b=60),
    annotations=[
        dict(
            x=skew_x(lcl_t, lcl_p),
            y=np.log10(lcl_p),
            xref="x",
            yref="y",
            text=f"LCL ≈ {lcl_p:.0f} hPa",
            showarrow=True,
            arrowhead=2,
            arrowcolor=INK_SOFT,
            arrowwidth=1.5,
            ax=55,
            ay=-30,
            font=dict(size=10, color=INK),
            bgcolor=ELEVATED_BG,
            bordercolor=INK_SOFT,
            borderwidth=1,
            borderpad=4,
            opacity=0.9,
        )
    ],
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
