""" pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-21
"""

import numpy as np
import plotly.graph_objects as go


# Data - first-order decomposition reaction rate constants at various temperatures
temperature_K = np.array([300, 330, 360, 400, 440, 480, 520, 560, 600])
activation_energy = 75000  # J/mol (75 kJ/mol)
R = 8.314  # J/(mol·K)
pre_exponential = 1.2e10  # s⁻¹

np.random.seed(42)
rate_constant_k = pre_exponential * np.exp(-activation_energy / (R * temperature_K))
rate_constant_k *= np.exp(np.random.normal(0, 0.08, len(temperature_K)))

# Arrhenius transform
inv_T = 1000 / temperature_K  # 1000/T for cleaner axis values
ln_k = np.log(rate_constant_k)

# Linear regression using numpy
coeffs = np.polyfit(inv_T, ln_k, 1)
slope, intercept = coeffs[0], coeffs[1]
ln_k_pred = slope * inv_T + intercept
ss_res = np.sum((ln_k - ln_k_pred) ** 2)
ss_tot = np.sum((ln_k - np.mean(ln_k)) ** 2)
r_squared = 1 - ss_res / ss_tot
Ea_extracted = -slope * R * 1000  # Convert back (factor of 1000 from 1000/T)

# Fit line
inv_T_fit = np.linspace(inv_T.min() - 0.05, inv_T.max() + 0.05, 200)
ln_k_fit = slope * inv_T_fit + intercept

# Plot
fig = go.Figure()

# Regression line
fig.add_trace(
    go.Scatter(
        x=inv_T_fit,
        y=ln_k_fit,
        mode="lines",
        name=f"Linear Fit (R² = {r_squared:.4f})",
        line={"color": "#1a3a5c", "width": 3},
        hovertemplate="1000/T: %{x:.3f} K⁻¹<br>ln(k): %{y:.2f}<extra></extra>",
    )
)

# Data points
fig.add_trace(
    go.Scatter(
        x=inv_T,
        y=ln_k,
        mode="markers",
        name="Experimental Data",
        marker={"size": 14, "color": "#306998", "line": {"color": "white", "width": 2}, "symbol": "circle"},
        hovertemplate=(
            "<b>T = %{customdata[0]:.0f} K</b><br>"
            "1000/T: %{x:.3f} K⁻¹<br>"
            "ln(k): %{y:.2f}<br>"
            "k: %{customdata[1]:.2e} s⁻¹<extra></extra>"
        ),
        customdata=np.column_stack([temperature_K, rate_constant_k]),
    )
)

# Annotation for extracted activation energy
fig.add_annotation(
    x=inv_T.mean(),
    y=ln_k.max() - 0.3,
    text=(f"<b>E<sub>a</sub> = {Ea_extracted / 1000:.1f} kJ/mol</b><br>R² = {r_squared:.4f}"),
    showarrow=False,
    font={"size": 20, "color": "#1a3a5c", "family": "Arial, sans-serif"},
    bgcolor="rgba(248, 250, 252, 0.92)",
    bordercolor="rgba(48, 105, 152, 0.5)",
    borderwidth=2,
    borderpad=10,
    align="left",
)

# Secondary x-axis tick values (temperature in K)
temp_ticks = np.array([300, 350, 400, 450, 500, 550, 600])
inv_T_ticks = 1000 / temp_ticks

# Layout
fig.update_layout(
    title={
        "text": "line-arrhenius · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#1a3a5c", "family": "Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "1000 / T (K⁻¹)", "font": {"size": 22, "color": "#2d4a6f"}},
        "tickfont": {"size": 18, "color": "#4a4a4a"},
        "showgrid": False,
        "zeroline": False,
        "linecolor": "#c0c0c0",
        "linewidth": 1,
        "ticks": "outside",
        "tickwidth": 1,
        "tickcolor": "#c0c0c0",
        "autorange": "reversed",
    },
    xaxis2={
        "tickfont": {"size": 16, "color": "#4a4a4a"},
        "tickvals": inv_T_ticks.tolist(),
        "ticktext": [f"{t:.0f} K" for t in temp_ticks],
        "overlaying": "x",
        "side": "top",
        "showgrid": False,
        "zeroline": False,
        "linecolor": "#c0c0c0",
        "linewidth": 1,
        "ticks": "outside",
        "tickwidth": 1,
        "tickcolor": "#c0c0c0",
        "autorange": "reversed",
        "range": [inv_T_fit.min(), inv_T_fit.max()],
    },
    yaxis={
        "title": {"text": "ln(k)", "font": {"size": 22, "color": "#2d4a6f"}},
        "tickfont": {"size": 18, "color": "#4a4a4a"},
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "griddash": "dash",
        "zeroline": False,
        "linecolor": "#c0c0c0",
        "linewidth": 1,
        "ticks": "outside",
        "tickwidth": 1,
        "tickcolor": "#c0c0c0",
    },
    template="plotly_white",
    legend={
        "font": {"size": 16, "color": "#4a4a4a"},
        "x": 0.02,
        "y": 0.02,
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": "rgba(248, 250, 252, 0.92)",
        "bordercolor": "rgba(0,0,0,0.15)",
        "borderwidth": 1,
    },
    margin={"l": 100, "r": 80, "t": 120, "b": 80},
    plot_bgcolor="white",
)

# Add invisible trace on secondary x-axis to make it render
fig.add_trace(
    go.Scatter(
        x=inv_T,
        y=ln_k,
        mode="markers",
        marker={"size": 0.01, "opacity": 0},
        showlegend=False,
        xaxis="x2",
        hoverinfo="skip",
    )
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
