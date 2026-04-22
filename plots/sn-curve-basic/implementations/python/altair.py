""" pyplots.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-15
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Fatigue test results for steel specimens
np.random.seed(42)

# Generate S-N curve data points with realistic scatter
# Using Basquin equation: S = A * N^b (linear in log-log space)
A = 800  # Coefficient (MPa)
b = -0.12  # Basquin exponent

# Stress levels (MPa) from high to low
stress_levels = np.array([450, 400, 350, 300, 275, 250, 225, 200, 180, 160])

# Generate multiple test samples per stress level with scatter
cycles_list = []
stress_list = []

for stress in stress_levels:
    # Calculate theoretical cycles to failure (Basquin equation inverted)
    theoretical_cycles = (stress / A) ** (1 / b)

    # Add 3-5 test samples with log-normal scatter
    n_samples = np.random.randint(3, 6)
    scatter = np.exp(np.random.normal(0, 0.3, n_samples))
    sample_cycles = theoretical_cycles * scatter

    cycles_list.extend(sample_cycles)
    stress_list.extend([stress] * n_samples)

# Create DataFrame
df = pd.DataFrame({"Cycles to Failure (N)": cycles_list, "Stress Amplitude (MPa)": stress_list})

# Material property reference lines
ultimate_strength = 520  # MPa
yield_strength = 380  # MPa
endurance_limit = 150  # MPa

# Create reference lines DataFrame
ref_lines = pd.DataFrame(
    {
        "property": ["Ultimate Strength: 520 MPa", "Yield Strength: 380 MPa", "Endurance Limit: 150 MPa"],
        "stress": [ultimate_strength, yield_strength, endurance_limit],
    }
)

# Fit line data (Basquin equation)
fit_cycles = np.logspace(2, 8, 100)
fit_stress = A * fit_cycles**b

fit_df = pd.DataFrame({"Cycles to Failure (N)": fit_cycles, "Stress Amplitude (MPa)": fit_stress})

# Create scatter plot with data points
points = (
    alt.Chart(df)
    .mark_point(size=200, filled=True, opacity=0.8)
    .encode(
        x=alt.X(
            "Cycles to Failure (N):Q", scale=alt.Scale(type="log", domain=[100, 1e8]), title="Cycles to Failure (N)"
        ),
        y=alt.Y(
            "Stress Amplitude (MPa):Q", scale=alt.Scale(type="log", domain=[100, 600]), title="Stress Amplitude (MPa)"
        ),
        color=alt.value("#306998"),
        tooltip=["Cycles to Failure (N)", "Stress Amplitude (MPa)"],
    )
)

# Fit line (Basquin curve)
fit_line = (
    alt.Chart(fit_df)
    .mark_line(strokeWidth=3, opacity=0.7)
    .encode(x="Cycles to Failure (N):Q", y="Stress Amplitude (MPa):Q", color=alt.value("#306998"))
)

# Reference lines for material properties
ref_rules = (
    alt.Chart(ref_lines)
    .mark_rule(strokeDash=[8, 4], strokeWidth=2.5)
    .encode(
        y="stress:Q",
        color=alt.Color(
            "property:N",
            scale=alt.Scale(
                domain=["Ultimate Strength: 520 MPa", "Yield Strength: 380 MPa", "Endurance Limit: 150 MPa"],
                range=["#c44e52", "#FFD43B", "#55a868"],
            ),
            legend=alt.Legend(title="Material Properties", titleFontSize=18, labelFontSize=16, labelLimit=300),
        ),
    )
)

# Combine all layers
chart = (
    (points + fit_line + ref_rules)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(text="sn-curve-basic · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_legend(titleFontSize=18, labelFontSize=16, orient="right")
    .configure_view(strokeWidth=0)
)

# Save as PNG (4800x2700 with scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.interactive().save("plot.html")
