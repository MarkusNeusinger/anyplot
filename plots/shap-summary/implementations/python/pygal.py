"""anyplot.ai
shap-summary: SHAP Summary Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 81/100 | Created: 2026-05-14
"""

import os
import sys


sys.path = [p for p in sys.path if not p.endswith("implementations/python")]  # noqa: E402

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LOW_COLOR = "#4467A3"  # Imprint blue: low feature values
MID_COLOR = "#9C9786"  # mid-tone of imprint_div, visible on both page colors
HIGH_COLOR = "#AE3030"  # Imprint red: high feature values
N_BINS = 11  # color steps of the low-to-high scale

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature_names
SHAP = "SHAP value (impact on model output)"  # role: shap_values
FEATURE_VALUE = "Feature value"  # role: feature_values

# Data: replace this block with your own table, for example df = pd.read_csv("shap.csv")
np.random.seed(42)
n_samples = 200
names = [
    "Age",
    "Income",
    "Credit Score",
    "Debt Ratio",
    "Employment Years",
    "Savings",
    "Loan Amount",
    "Interest Rate",
    "Payment History",
    "Inquiries",
]
parts = []
for i, name in enumerate(names):
    shap_i = np.random.normal(0, 0.3 + i * 0.05, n_samples)
    value_i = np.random.uniform(0, 1, n_samples)
    parts.append(pd.DataFrame({FEATURE: name, SHAP: shap_i, FEATURE_VALUE: value_i}))
df = pd.concat(parts, ignore_index=True)

# Plot: reads only df and the constants above


def lerp_hex(c0, c1, t):
    """Linear blend of two hex colors."""
    a = [int(c0[k : k + 2], 16) for k in (1, 3, 5)]
    b = [int(c1[k : k + 2], 16) for k in (1, 3, 5)]
    r, g, bl = (round(x + (y - x) * t) for x, y in zip(a, b, strict=True))
    return f"#{r:02X}{g:02X}{bl:02X}"


def diverging(t):
    """imprint_div: blue (t=0) through the mid-tone to red (t=1)."""
    return lerp_hex(LOW_COLOR, MID_COLOR, 2 * t) if t < 0.5 else lerp_hex(MID_COLOR, HIGH_COLOR, 2 * t - 1)


# Rows sorted by mean |SHAP|, most important at the top (highest y position)
importance = df.groupby(FEATURE, sort=False)[SHAP].apply(lambda s: s.abs().mean()).sort_values()
row_of = {name: pos for pos, name in enumerate(importance.index)}
n_rows = len(row_of)

# Feature value scaled to 0..1 within its own feature, then binned into color steps
scaled = df.groupby(FEATURE, sort=False)[FEATURE_VALUE].transform(lambda s: (s - s.min()) / (s.max() - s.min()))
bin_of = np.clip(np.floor(scaled * N_BINS), 0, N_BINS - 1)

# Vertical jitter inside the row (layout only); the SHAP value stays on the x axis untouched
rng = np.random.default_rng(7)
jitter = np.clip(rng.normal(0, 0.13, len(df)), -0.35, 0.35)
y_pos = df[FEATURE].map(row_of).to_numpy() + jitter

# Zero line first so the dots draw on top of it; one series per color step
series = [("SHAP = 0", [(0, -0.6), (0, n_rows - 0.4)], INK_SOFT)]
for b in range(N_BINS):
    mask = (bin_of == b).to_numpy()
    if mask.any():
        pts = list(zip(df.loc[mask, SHAP].tolist(), y_pos[mask].tolist(), strict=True))
        series.append((f"Feature value bin {b + 1}", pts, diverging((b + 0.5) / N_BINS)))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=tuple(color for _, _, color in series),
    opacity="0.8",
    opacity_hover="1",
    title_font_size=66,
    label_font_size=52,
    major_label_font_size=44,
    legend_font_size=44,
    stroke_width=3,
)

title = "shap-summary · python · pygal · anyplot.ai"
chart = pygal.XY(
    style=custom_style,
    title=title,
    x_title=SHAP,
    y_title=FEATURE,
    width=3200,
    height=1800,
    show_legend=False,
    show_x_guides=True,
    show_y_guides=True,
    dots_size=7,
    stroke=False,
    margin_right=330,
    range=(-0.6, n_rows - 0.4),
    y_labels=[{"label": name, "value": pos} for name, pos in row_of.items()],
    y_labels_major=list(range(n_rows)),
    truncate_label=-1,
)
chart.add(series[0][0], series[0][1], stroke=True, show_dots=False, stroke_style={"width": 4, "dasharray": "18,12"})
for label, pts, _ in series[1:]:
    chart.add(label, pts)

# Color bar: pygal has none, so a gradient is injected into the SVG next to the plot
svg = chart.render(is_unicode=True)
bar_x, bar_y, bar_w, bar_h = 3200 - 250, 640, 46, 520
stops = "".join(
    f'<stop offset="{t:.2f}" stop-color="{diverging(1 - t)}"/>' for t in np.linspace(0, 1, 2 * N_BINS + 1).tolist()
)
colorbar = (
    f'<defs><linearGradient id="fvbar" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient></defs>'
    f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" fill="url(#fvbar)" '
    f'stroke="{INK_MUTED}" stroke-width="2"/>'
    f'<g fill="{INK}" font-family="sans-serif" font-size="44">'
    f'<text x="{bar_x + bar_w + 18}" y="{bar_y + 40}">High</text>'
    f'<text x="{bar_x + bar_w + 18}" y="{bar_y + bar_h}">Low</text>'
    f'<text x="{bar_x + bar_w / 2}" y="{bar_y - 40}" text-anchor="middle" font-size="46">{FEATURE_VALUE}</text></g>'
)
svg = svg.replace("</svg>", colorbar + "</svg>")

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=3200, output_height=1800)
