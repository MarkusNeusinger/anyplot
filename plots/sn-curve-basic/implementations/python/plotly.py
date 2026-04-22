""" pyplots.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: plotly 6.5.2 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-15
"""

import numpy as np
import plotly.graph_objects as go


# Data: Simulated fatigue test results for steel
np.random.seed(42)

# Generate realistic S-N curve data with scatter
# Basquin equation: S = A * N^b (where b is negative)
A = 1200  # Material constant (MPa)
b = -0.12  # Fatigue strength exponent

# Generate stress levels and corresponding cycles with scatter
stress_levels = np.array([600, 550, 500, 450, 400, 350, 320, 300, 280, 260, 250, 240])
cycles_base = (stress_levels / A) ** (1 / b)

# Add scatter (multiple specimens at each stress level)
cycles = []
stress = []
for s, n_base in zip(stress_levels, cycles_base, strict=False):
    n_samples = np.random.randint(2, 5)  # 2-4 specimens per stress level
    scatter = 10 ** (np.random.normal(0, 0.15, n_samples))  # Log-normal scatter
    for factor in scatter:
        cycles.append(n_base * factor)
        stress.append(s)

cycles = np.array(cycles)
stress = np.array(stress)

# Material properties for reference lines
ultimate_strength = 650  # MPa
yield_strength = 450  # MPa
endurance_limit = 230  # MPa

# Fit line data (smooth curve)
fit_cycles = np.logspace(2, 8, 100)
fit_stress = A * fit_cycles**b

# Create figure
fig = go.Figure()

# Add S-N curve fit line
fig.add_trace(
    go.Scatter(x=fit_cycles, y=fit_stress, mode="lines", name="Basquin Fit", line={"color": "#306998", "width": 4})
)

# Add fatigue test data points
fig.add_trace(
    go.Scatter(
        x=cycles,
        y=stress,
        mode="markers",
        name="Test Data",
        marker={"color": "#FFD43B", "size": 14, "line": {"color": "#306998", "width": 2}},
    )
)

# Add horizontal reference lines as traces for legend visibility
x_range = [100, 1e8]

fig.add_trace(
    go.Scatter(
        x=x_range,
        y=[ultimate_strength, ultimate_strength],
        mode="lines",
        name=f"Ultimate Strength ({ultimate_strength} MPa)",
        line={"color": "#D62728", "width": 3, "dash": "dash"},
    )
)

fig.add_trace(
    go.Scatter(
        x=x_range,
        y=[yield_strength, yield_strength],
        mode="lines",
        name=f"Yield Strength ({yield_strength} MPa)",
        line={"color": "#2CA02C", "width": 3, "dash": "dash"},
    )
)

fig.add_trace(
    go.Scatter(
        x=x_range,
        y=[endurance_limit, endurance_limit],
        mode="lines",
        name=f"Endurance Limit ({endurance_limit} MPa)",
        line={"color": "#9467BD", "width": 3, "dash": "dash"},
    )
)

# Update layout
fig.update_layout(
    title={"text": "sn-curve-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Cycles to Failure (N)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "type": "log",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
        "showline": True,
        "linewidth": 2,
        "linecolor": "black",
        "range": [2, 8],  # 10^2 to 10^8
    },
    yaxis={
        "title": {"text": "Stress Amplitude (MPa)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "type": "log",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
        "showline": True,
        "linewidth": 2,
        "linecolor": "black",
        "range": [2.3, 2.9],  # ~200 to ~800 MPa
    },
    legend={
        "font": {"size": 18},
        "x": 0.95,
        "y": 0.95,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": "rgba(255,255,255,0.8)",
        "bordercolor": "black",
        "borderwidth": 1,
    },
    template="plotly_white",
    margin={"l": 100, "r": 150, "t": 100, "b": 100},
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactive viewing
fig.write_html("plot.html")
