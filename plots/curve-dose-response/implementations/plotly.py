"""pyplots.ai
curve-dose-response: Pharmacological Dose-Response Curve
Library: plotly 6.6.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-18
"""

import numpy as np
import plotly.graph_objects as go
from scipy.optimize import curve_fit


# Data
np.random.seed(42)
concentrations = np.logspace(-9, -4, 8)

compound_names = ["Compound A", "Compound B"]
colors = ["#306998", "#E8793A"]


ec50_true = [1e-7, 5e-7]
hill_true = [1.2, 0.9]
top_true = [100, 95]
bottom_true = [5, 10]

raw_data = {}
for i, name in enumerate(compound_names):
    responses = []
    sems = []
    for conc in concentrations:
        true_resp = bottom_true[i] + (top_true[i] - bottom_true[i]) / (1 + (ec50_true[i] / conc) ** hill_true[i])
        reps = true_resp + np.random.normal(0, 3, 3)
        responses.append(np.mean(reps))
        sems.append(np.std(reps, ddof=1) / np.sqrt(3))
    raw_data[name] = {"concentrations": concentrations, "responses": np.array(responses), "sems": np.array(sems)}


# 4PL model
def logistic_4pl(x, bottom, top, ec50, hill):
    return bottom + (top - bottom) / (1 + (ec50 / x) ** hill)


# Fit curves
fit_results = {}
conc_fine = np.logspace(-9.5, -3.8, 300)

for i, name in enumerate(compound_names):
    popt, pcov = curve_fit(
        logistic_4pl,
        raw_data[name]["concentrations"],
        raw_data[name]["responses"],
        p0=[bottom_true[i], top_true[i], ec50_true[i], hill_true[i]],
        maxfev=10000,
    )
    perr = np.sqrt(np.diag(pcov))
    fit_results[name] = {"popt": popt, "perr": perr}

# Plot
fig = go.Figure()

for i, name in enumerate(compound_names):
    popt = fit_results[name]["popt"]
    bottom, top, ec50, hill = popt

    fitted_curve = logistic_4pl(conc_fine, *popt)

    # 95% CI band for Compound A
    if i == 0:
        perr = fit_results[name]["perr"]
        upper = logistic_4pl(conc_fine, bottom - perr[0], top + perr[1], ec50, hill)
        lower = logistic_4pl(conc_fine, bottom + perr[0], top - perr[1], ec50, hill)

        fig.add_trace(
            go.Scatter(x=conc_fine, y=upper, mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip")
        )
        fig.add_trace(
            go.Scatter(
                x=conc_fine,
                y=lower,
                mode="lines",
                line={"width": 0},
                fill="tonexty",
                fillcolor="rgba(48, 105, 152, 0.15)",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Fitted curve
    fig.add_trace(
        go.Scatter(
            x=conc_fine,
            y=fitted_curve,
            mode="lines",
            name=f"{name} (EC₅₀ = {ec50:.2e} M)",
            line={"color": colors[i], "width": 3.5},
            hovertemplate=f"<b>{name}</b><br>Conc: %{{x:.2e}} M<br>Response: %{{y:.1f}}%<extra></extra>",
        )
    )

    # Data points with error bars
    fig.add_trace(
        go.Scatter(
            x=raw_data[name]["concentrations"],
            y=raw_data[name]["responses"],
            mode="markers",
            name=f"{name} data",
            marker={"size": 14, "color": colors[i], "line": {"color": "white", "width": 2}},
            error_y={
                "type": "data",
                "array": raw_data[name]["sems"],
                "visible": True,
                "color": colors[i],
                "thickness": 2,
            },
            showlegend=False,
            hovertemplate=f"<b>{name}</b><br>Conc: %{{x:.2e}} M<br>Response: %{{y:.1f}} ± %{{error_y.array:.1f}}%<extra></extra>",
        )
    )

    # EC50 reference lines
    half_response = bottom + (top - bottom) / 2
    fig.add_shape(
        type="line", x0=ec50, x1=ec50, y0=-5, y1=half_response, line={"color": colors[i], "width": 1.5, "dash": "dash"}
    )
    fig.add_shape(
        type="line",
        x0=1e-10,
        x1=ec50,
        y0=half_response,
        y1=half_response,
        line={"color": colors[i], "width": 1.5, "dash": "dash"},
    )

    # EC50 annotation on plot
    fig.add_annotation(
        x=np.log10(ec50),
        y=half_response + 5 + i * 8,
        text=f"<b>EC₅₀ = {ec50:.2e} M</b>",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=1.5,
        arrowcolor=colors[i],
        ax=40 + i * 30,
        ay=-30 - i * 10,
        font={"size": 14, "color": colors[i]},
        bordercolor=colors[i],
        borderwidth=1.5,
        borderpad=4,
        bgcolor="rgba(255,255,255,0.85)",
    )

# Top and bottom asymptote lines
fig.add_shape(
    type="line", x0=1e-10, x1=1e-3, y0=top_true[0], y1=top_true[0], line={"color": "#999999", "width": 1, "dash": "dot"}
)
fig.add_shape(
    type="line",
    x0=1e-10,
    x1=1e-3,
    y0=bottom_true[0],
    y1=bottom_true[0],
    line={"color": "#999999", "width": 1, "dash": "dot"},
)

# Asymptote annotations
fig.add_annotation(
    x=np.log10(5e-4),
    y=top_true[0],
    text="Top asymptote",
    showarrow=False,
    font={"size": 12, "color": "#999999"},
    yshift=10,
)
fig.add_annotation(
    x=np.log10(5e-4),
    y=bottom_true[0],
    text="Bottom asymptote",
    showarrow=False,
    font={"size": 12, "color": "#999999"},
    yshift=-12,
)

# Style
fig.update_layout(
    title={
        "text": "curve-dose-response · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2c3e50", "family": "Arial, Helvetica, sans-serif"},
        "x": 0.5,
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Concentration (M)", "font": {"size": 22, "color": "#34495e"}},
        "type": "log",
        "tickfont": {"size": 18, "color": "#555"},
        "showgrid": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": "#ccc",
        "range": [-9.5, -3.8],
    },
    yaxis={
        "title": {"text": "Response (%)", "font": {"size": 22, "color": "#34495e"}},
        "tickfont": {"size": 18, "color": "#555"},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 0.5,
        "range": [-5, 115],
        "zeroline": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": "#ccc",
    },
    template="plotly_white",
    legend={
        "font": {"size": 16, "color": "#34495e"},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "rgba(0,0,0,0.1)",
        "borderwidth": 1,
        "traceorder": "normal",
    },
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 80, "r": 40, "t": 70, "b": 70},
    width=1600,
    height=900,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
