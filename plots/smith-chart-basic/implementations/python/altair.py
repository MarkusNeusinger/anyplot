""" anyplot.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-20
"""

import importlib
import os
import sys


# Drop script directory from sys.path so the `altair` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1 — impedance locus
VSWR_COLOR = "#C475FD"  # Okabe-Ito position 2 — VSWR circles

# Reference impedance
Z0 = 50  # ohms

# Generate Smith chart grid — constant resistance circles
theta = np.linspace(0, 2 * np.pi, 200)
resistance_circles = []
resistance_values = [0, 0.2, 0.5, 1.0, 2.0, 5.0]
for r in resistance_values:
    center_x = r / (r + 1)
    radius = 1 / (r + 1)
    x = center_x + radius * np.cos(theta)
    y = radius * np.sin(theta)
    mask = x**2 + y**2 <= 1.0
    for i in range(len(x)):
        if mask[i]:
            resistance_circles.append({"x": x[i], "y": y[i], "group": f"r_{r}", "idx": i})
resistance_df = pd.DataFrame(resistance_circles)

# Generate constant reactance arcs
reactance_arcs = []
reactance_values = [0.2, 0.5, 1.0, 2.0, 5.0]
arc_theta = np.linspace(-np.pi, np.pi, 200)
for x_val in reactance_values:
    center_y = 1 / x_val
    radius = 1 / x_val
    x = 1 + radius * np.cos(arc_theta)
    y = center_y + radius * np.sin(arc_theta)
    mask = (x**2 + y**2 <= 1.0) & (x >= -0.01)
    y_neg = -center_y - radius * np.sin(arc_theta)
    for i in range(len(x)):
        if mask[i]:
            reactance_arcs.append({"x": x[i], "y": y[i], "group": f"x_pos_{x_val}", "idx": i})
            reactance_arcs.append({"x": x[i], "y": y_neg[i], "group": f"x_neg_{x_val}", "idx": i})

# Zero reactance line (horizontal axis)
x_line = np.linspace(-1, 1, 50)
for i, xi in enumerate(x_line):
    reactance_arcs.append({"x": xi, "y": 0, "group": "x_zero", "idx": i})
reactance_df = pd.DataFrame(reactance_arcs)

# VSWR circles — constant reflection coefficient magnitude
vswr_theta = np.linspace(0, 2 * np.pi, 200)
vswr_circles = []
vswr_entries = [(1.5, (1.5 - 1) / (1.5 + 1)), (2.0, 1 / 3), (3.0, 0.5)]
for vswr_val, gamma_mag in vswr_entries:
    x = gamma_mag * np.cos(vswr_theta)
    y = gamma_mag * np.sin(vswr_theta)
    for i in range(len(x)):
        vswr_circles.append({"x": x[i], "y": y[i], "group": f"vswr_{vswr_val}", "idx": i})
vswr_df = pd.DataFrame(vswr_circles)

# VSWR labels at 45° (upper-right of each circle, away from impedance curve)
vswr_labels_data = [
    {"x": v * np.cos(np.pi / 4), "y": v * np.sin(np.pi / 4), "label": f"VSWR {w}"} for w, v in vswr_entries
]
vswr_labels_df = pd.DataFrame(vswr_labels_data)

# Unit circle boundary
unit_theta = np.linspace(0, 2 * np.pi, 200)
unit_circle_df = pd.DataFrame({"x": np.cos(unit_theta), "y": np.sin(unit_theta), "idx": range(len(unit_theta))})

# Antenna impedance sweep 1–6 GHz
np.random.seed(42)
n_points = 50
frequency = np.linspace(1e9, 6e9, n_points)
t = np.linspace(0, 2.5 * np.pi, n_points)
z_real = 50 * (1 - 0.7 * np.exp(-t / 3))
z_imag = 40 * np.sin(t) * np.exp(-t / 4)
z_norm = (z_real + 1j * z_imag) / Z0
gamma = (z_norm - 1) / (z_norm + 1)

impedance_df = pd.DataFrame(
    {
        "x": gamma.real,
        "y": gamma.imag,
        "frequency_ghz": frequency / 1e9,
        "z_real": z_real,
        "z_imag": z_imag,
        "idx": range(n_points),
    }
)

# Frequency labels — per-label dx/dy offsets; 4.7 GHz skipped (converges with endpoint)
label_configs = [(0, 18, -18), (12, 18, -18), (24, 18, -18), (49, 18, -20)]
label_layers = []
for row_idx, dx, dy in label_configs:
    row = impedance_df.iloc[[row_idx]].copy()
    row["label"] = f"{row['frequency_ghz'].values[0]:.1f} GHz"
    label_layers.append(
        alt.Chart(row)
        .mark_text(fontSize=14, fontWeight="bold", color=INK, dx=dx, dy=dy)
        .encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[-1.2, 1.2])),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[-1.2, 1.2])),
            text="label:N",
        )
    )

scale_x = alt.Scale(domain=[-1.2, 1.2])
scale_y = alt.Scale(domain=[-1.2, 1.2])

# Unit circle boundary
boundary = (
    alt.Chart(unit_circle_df)
    .mark_line(color=INK, strokeWidth=3, opacity=0.8)
    .encode(x=alt.X("x:Q", scale=scale_x), y=alt.Y("y:Q", scale=scale_y), order="idx:O")
)

# Resistance circles
res_circles = (
    alt.Chart(resistance_df)
    .mark_line(strokeWidth=1.0, opacity=0.3)
    .encode(
        x=alt.X("x:Q", scale=scale_x),
        y=alt.Y("y:Q", scale=scale_y),
        detail="group:N",
        order="idx:O",
        color=alt.value(INK_SOFT),
    )
)

# Reactance arcs
react_arcs = (
    alt.Chart(reactance_df)
    .mark_line(strokeWidth=1.0, opacity=0.3)
    .encode(
        x=alt.X("x:Q", scale=scale_x),
        y=alt.Y("y:Q", scale=scale_y),
        detail="group:N",
        order="idx:O",
        color=alt.value(INK_SOFT),
    )
)

# VSWR circles (dashed, subtle)
vswr_layer = (
    alt.Chart(vswr_df)
    .mark_line(strokeWidth=1.2, opacity=0.4, strokeDash=[5, 4])
    .encode(
        x=alt.X("x:Q", scale=scale_x),
        y=alt.Y("y:Q", scale=scale_y),
        detail="group:N",
        order="idx:O",
        color=alt.value(VSWR_COLOR),
    )
)

# VSWR labels
vswr_labels = (
    alt.Chart(vswr_labels_df)
    .mark_text(fontSize=11, color=VSWR_COLOR, fontStyle="italic", dx=6, dy=-8)
    .encode(x=alt.X("x:Q", scale=scale_x), y=alt.Y("y:Q", scale=scale_y), text="label:N")
)

# Impedance locus curve
impedance_line = (
    alt.Chart(impedance_df)
    .mark_line(strokeWidth=4, color=BRAND)
    .encode(x=alt.X("x:Q", scale=scale_x), y=alt.Y("y:Q", scale=scale_y), order="idx:O")
)

# Impedance data points with interactive tooltips
impedance_points = (
    alt.Chart(impedance_df)
    .mark_circle(size=80, color=BRAND, stroke=PAGE_BG, strokeWidth=1)
    .encode(
        x=alt.X("x:Q", scale=scale_x),
        y=alt.Y("y:Q", scale=scale_y),
        tooltip=[
            alt.Tooltip("frequency_ghz:Q", title="Frequency (GHz)", format=".2f"),
            alt.Tooltip("z_real:Q", title="R (Ω)", format=".1f"),
            alt.Tooltip("z_imag:Q", title="X (Ω)", format=".1f"),
        ],
    )
)

# Center point marker (matched condition Z = Z₀)
center_df = pd.DataFrame({"x": [0], "y": [0]})
center_point = (
    alt.Chart(center_df)
    .mark_point(size=200, shape="cross", color=INK, strokeWidth=3)
    .encode(x=alt.X("x:Q", scale=scale_x), y=alt.Y("y:Q", scale=scale_y))
)

# Resistance value labels along real axis
r_labels_data = [
    {"x": 0.0, "y": 0.08, "label": "0"},
    {"x": 0.17, "y": 0.08, "label": "0.2"},
    {"x": 0.33, "y": 0.08, "label": "0.5"},
    {"x": 0.5, "y": 0.08, "label": "1"},
    {"x": 0.67, "y": 0.08, "label": "2"},
    {"x": 0.83, "y": 0.08, "label": "5"},
]
r_labels_df = pd.DataFrame(r_labels_data)
r_labels = (
    alt.Chart(r_labels_df)
    .mark_text(fontSize=12, fontWeight="bold")
    .encode(x=alt.X("x:Q", scale=scale_x), y=alt.Y("y:Q", scale=scale_y), text="label:N", color=alt.value(INK_SOFT))
)

# Compose all layers
chart = (
    alt.layer(
        res_circles,
        react_arcs,
        vswr_layer,
        vswr_labels,
        boundary,
        center_point,
        impedance_line,
        impedance_points,
        *label_layers,
        r_labels,
    )
    .properties(
        width=600,
        height=600,
        background=PAGE_BG,
        title=alt.Title(
            "smith-chart-basic · python · altair · anyplot.ai",
            fontSize=16,
            anchor="middle",
            color=INK,
            subtitle="Antenna Impedance Sweep (1–6 GHz, Z₀ = 50 Ω)",
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(grid=False, domain=False, labels=False, ticks=False, title=None)
    .interactive()
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
