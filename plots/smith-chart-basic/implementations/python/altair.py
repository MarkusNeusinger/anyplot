"""anyplot.ai
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
Image = importlib.import_module("PIL.Image")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 for the impedance locus, position 2 for the VSWR circles
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
Z0 = 50  # reference impedance in ohms, used to normalize Z
GRID_RESISTANCE = [0.2, 0.5, 1.0, 2.0, 5.0]  # normalized resistance circles drawn on the chart
GRID_REACTANCE = [0.2, 0.5, 1.0, 2.0, 5.0]  # normalized reactance arcs, drawn for both signs
VSWR_LEVELS = [1.5, 2.0, 3.0]  # constant |gamma| circles
N_FREQUENCY_LABELS = 4  # labelled points along the locus, spread evenly in sweep order

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
Z_REAL = "Resistance (Ω)"  # role: z_real
Z_IMAG = "Reactance (Ω)"  # role: z_imag

# Data: replace this block with your own table, for example df = pd.read_csv("s11_sweep.csv")
n_points = 50
sweep = np.linspace(0, 2.5 * np.pi, n_points)
df = pd.DataFrame(
    {
        FREQUENCY: np.linspace(1e9, 6e9, n_points),
        Z_REAL: 50 * (1 - 0.7 * np.exp(-sweep / 3)),
        Z_IMAG: 40 * np.sin(sweep) * np.exp(-sweep / 4),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
LIMIT = 1.08  # half-width of the square view in gamma units; the boundary circle has radius 1
scale_x = alt.Scale(domain=[-LIMIT, LIMIT], nice=False)
scale_y = alt.Scale(domain=[-LIMIT, LIMIT], nice=False)
encode_xy = {"x": alt.X("x:Q", scale=scale_x), "y": alt.Y("y:Q", scale=scale_y)}


def gamma_of(z):
    """Reflection coefficient of a normalized impedance."""
    return (z - 1) / (z + 1)


# Impedance locus: normalized Z/Z0 mapped to the gamma plane
gamma = gamma_of((df[Z_REAL].to_numpy() + 1j * df[Z_IMAG].to_numpy()) / Z0)
locus = df.assign(x=gamma.real, y=gamma.imag, idx=np.arange(len(df)), ghz=df[FREQUENCY] / 1e9)

# Grid: constant-resistance circles
theta = np.linspace(0, 2 * np.pi, 240)  # 240 points per drawn circle
grid_frames = []
for r in GRID_RESISTANCE:
    circle = (r + np.exp(1j * theta)) / (r + 1)
    grid_frames.append(
        pd.DataFrame({"x": circle.real, "y": circle.imag, "group": f"r_{r}", "idx": np.arange(len(theta))})
    )

# Grid: constant-reactance arcs, swept from r = 0 to a very large r (gamma -> 1)
sweep_r = np.concatenate([[0.0], np.geomspace(1e-3, 1e5, 400)])
for x_val in GRID_REACTANCE:
    for sign in (1, -1):
        arc = gamma_of(sweep_r + 1j * sign * x_val)
        grid_frames.append(
            pd.DataFrame({"x": arc.real, "y": arc.imag, "group": f"x_{sign * x_val}", "idx": np.arange(len(arc))})
        )

# Grid: zero-reactance axis
grid_frames.append(pd.DataFrame({"x": [-1.0, 1.0], "y": [0.0, 0.0], "group": "x_0", "idx": [0, 1]}))
grid = pd.concat(grid_frames, ignore_index=True)

# VSWR circles: |gamma| = (VSWR - 1) / (VSWR + 1)
vswr_frames = []
vswr_labels = []
for vswr in VSWR_LEVELS:
    mag = (vswr - 1) / (vswr + 1)
    vswr_frames.append(
        pd.DataFrame(
            {"x": mag * np.cos(theta), "y": mag * np.sin(theta), "group": f"vswr_{vswr}", "idx": np.arange(len(theta))}
        )
    )
    vswr_labels.append({"x": mag * np.cos(np.pi / 4), "y": mag * np.sin(np.pi / 4), "label": f"VSWR {vswr}"})
vswr_circles = pd.concat(vswr_frames, ignore_index=True)
vswr_labels = pd.DataFrame(vswr_labels)

# Boundary: |gamma| = 1
boundary_df = pd.DataFrame({"x": np.cos(theta), "y": np.sin(theta), "idx": np.arange(len(theta))})

# Resistance labels: each sits where its circle crosses the real axis on the left
r_values = [0.0, *GRID_RESISTANCE]
r_labels = pd.DataFrame({"x": [(r - 1) / (r + 1) for r in r_values], "y": 0.0, "label": [f"{r:g}" for r in r_values]})

# Frequency labels at evenly spread points along the sweep
label_rows = np.linspace(0, len(locus) - 1, N_FREQUENCY_LABELS).round().astype(int)
freq_labels = locus.iloc[label_rows].assign(label=[f"{g:.1f} GHz" for g in locus["ghz"].iloc[label_rows]])

boundary = (
    alt.Chart(boundary_df)
    .mark_line(color=INK, strokeWidth=3, opacity=0.8)
    .encode(**encode_xy, order=alt.Order("idx:O"))
)

grid_layer = (
    alt.Chart(grid)
    .mark_line(strokeWidth=1.0, opacity=0.3, color=INK_SOFT)
    .encode(**encode_xy, detail="group:N", order=alt.Order("idx:O"))
)

vswr_layer = (
    alt.Chart(vswr_circles)
    .mark_line(strokeWidth=1.2, opacity=0.5, strokeDash=[5, 4], color=IMPRINT_PALETTE[1])
    .encode(**encode_xy, detail="group:N", order=alt.Order("idx:O"))
)

vswr_text = (
    alt.Chart(vswr_labels)
    .mark_text(fontSize=11, color=IMPRINT_PALETTE[1], fontStyle="italic", dx=6, dy=-8)
    .encode(**encode_xy, text="label:N")
)

r_text = (
    alt.Chart(r_labels)
    .mark_text(fontSize=12, fontWeight="bold", color=INK_SOFT, dx=6, dy=20)
    .encode(**encode_xy, text="label:N")
)

center_df = pd.DataFrame({"x": [0.0], "y": [0.0]})
center_point = alt.Chart(center_df).mark_point(size=200, shape="cross", color=INK, strokeWidth=3).encode(**encode_xy)

locus_line = (
    alt.Chart(locus).mark_line(strokeWidth=4, color=IMPRINT_PALETTE[0]).encode(**encode_xy, order=alt.Order("idx:O"))
)

locus_points = (
    alt.Chart(locus)
    .mark_circle(size=80, color=IMPRINT_PALETTE[0], stroke=PAGE_BG, strokeWidth=1)
    .encode(
        **encode_xy,
        tooltip=[
            alt.Tooltip("ghz:Q", title="Frequency (GHz)", format=".2f"),
            alt.Tooltip(Z_REAL.translate(ESCAPE), type="quantitative", title=Z_REAL, format=".1f"),
            alt.Tooltip(Z_IMAG.translate(ESCAPE), type="quantitative", title=Z_IMAG, format=".1f"),
        ],
    )
)

# Frequency labels: pushed outward from the chart center, away from the curve and the matched mark
freq_layers = []
for _, row in freq_labels.iterrows():
    norm = max(np.hypot(row["x"], row["y"]), 1e-9)
    dx = 26 * row["x"] / norm
    dy = -26 * row["y"] / norm - 16 * (row["idx"] == 0)
    if row["idx"] == locus["idx"].max():  # the sweep ends near the center: label it in the empty lower right
        dx, dy = 52, 26
    freq_layers.append(
        alt.Chart(pd.DataFrame([row]))
        .mark_text(fontSize=14, fontWeight="bold", color=INK, dx=dx, dy=dy)
        .encode(**encode_xy, text="label:N")
    )

chart = (
    alt.layer(grid_layer, vswr_layer, vswr_text, boundary, center_point, locus_line, locus_points, r_text, *freq_layers)
    .properties(
        width=540,
        height=540,
        background=PAGE_BG,
        title=alt.Title(
            "smith-chart-basic · python · altair · anyplot.ai",
            fontSize=16,
            anchor="middle",
            color=INK,
            subtitle=f"Antenna impedance sweep, {df[FREQUENCY].min() / 1e9:g}–{df[FREQUENCY].max() / 1e9:g} GHz, Z₀ = {Z0} Ω",
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(grid=False, domain=False, labels=False, ticks=False, title=None)
    .interactive()
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the 2400 x 2400 square canvas
target = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > target or img.height > target:
    raise SystemExit(f"altair vl-convert produced {img.width}x{img.height}, exceeds {target}x{target}")
canvas = Image.new("RGB", (target, target), PAGE_BG)
canvas.paste(img, ((target - img.width) // 2, (target - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
