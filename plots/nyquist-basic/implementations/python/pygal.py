"""anyplot.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: pygal 3.1.0 | Python 3.13.14
Quality: 83/100 | Updated: 2026-06-17
"""

import math
import os
import re
import sys
from xml.etree import ElementTree as ET


# Script is named pygal.py — remove its directory from sys.path first so
# 'import pygal' resolves to the installed package, not this file.
sys.path = [p for p in sys.path if p != os.path.dirname(os.path.abspath(__file__))]

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Theme tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data — Transfer function G(s) = 2 / [s(s+1)(s+2)]
omega = np.logspace(-2, 2, 800)
s = 1j * omega
G = 2.0 / (s * (s + 1) * (s + 2))

real_part = G.real
imag_part = G.imag

# Mirror for negative frequencies (Nyquist contour reflection)
real_mirror = real_part[::-1]
imag_mirror = -imag_part[::-1]

# Imprint palette — position 1 (green) for main curve, red (semantic) for critical point
IMPRINT_COLORS = (
    "#009E73",  # brand green — positive frequency curve
    "#C475FD",  # lavender — negative frequency mirror
    "#AE3030",  # matte red — critical point (semantic: stability boundary)
    INK_MUTED,  # muted neutral — unit circle reference
    "#BD8233",  # ochre — frequency markers
)

# Title — 44 chars, use default 66 (no shrink needed)
TITLE = "nyquist-basic · python · pygal · anyplot.ai"
title_size = round(66 * min(1.0, 67 / len(TITLE)))

# Custom style using Imprint palette
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_COLORS,
    title_font_size=title_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

# Chart — square canvas for 1:1 aspect ratio (unit circle must appear circular)
chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title=TITLE,
    x_title="Real",
    y_title="Imaginary",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=36,
    dots_size=3,
    stroke=True,
    show_x_guides=True,
    show_y_guides=True,
    explicit_size=True,
    range=(-2, 2),
    xrange=(-2, 2),
    value_formatter=lambda x: f"{x:.3f}",
)

# Positive frequency curve with tooltips showing frequency values
step = 4
nyquist_positive = [
    {"value": (float(real_part[i]), float(imag_part[i])), "label": f"ω = {omega[i]:.3f} rad/s"}
    for i in range(0, len(omega), step)
]
chart.add("G(jω), ω ≥ 0", nyquist_positive, show_dots=False, stroke_style={"width": 5})

# Negative frequency mirror with tooltips
nyquist_negative = [
    {"value": (float(real_mirror[i]), float(imag_mirror[i])), "label": f"ω = -{omega[len(omega) - 1 - i]:.3f} rad/s"}
    for i in range(0, len(omega), step)
]
chart.add("G(jω), ω < 0", nyquist_negative, show_dots=False, stroke_style={"width": 4, "dasharray": "12,6"})

# Critical point (−1, 0) — red marker (semantic: boundary of stability region)
chart.add(
    "Critical Point (−1, 0)", [{"value": (-1.0, 0.0), "label": "Critical Point: (−1, 0)"}], stroke=False, dots_size=24
)

# Unit circle reference (dashed, muted)
circle_points = [
    {"value": (math.cos(math.radians(a)), math.sin(math.radians(a))), "label": f"{a}°"} for a in range(0, 361, 3)
]
chart.add("Unit Circle", circle_points, stroke=True, show_dots=False, stroke_style={"width": 2, "dasharray": "8,6"})

# Frequency markers at key points along the curve (visible in both PNG and HTML)
freq_targets = [0.5, 1.0, 2.0, 5.0, 10.0]
freq_annotations = []
for ft in freq_targets:
    idx = int(np.argmin(np.abs(omega - ft)))
    freq_annotations.append({"value": (float(real_part[idx]), float(imag_part[idx])), "label": f"ω = {ft} rad/s"})
chart.add("ω markers (rad/s)", freq_annotations, stroke=False, dots_size=16)


# --- SVG post-processing: inject direction arrows and frequency labels ---


def _tf(w):
    """G(jw) = 2 / (jw*(1+jw)*(2+jw))"""
    sv = 1j * w
    return complex(2.0) / (sv * (sv + 1) * (sv + 2))


def _extract_svg_mapping(svg_root, svg_ns):
    """
    Parse guide lines and axis lines to get the data→canvas coordinate mapping.
    Returns (data_to_canvas, canvas_dir) functions.
    """
    tx, ty = 307, 96  # empirical fallback for this chart config

    # Find the dominant translate transform (skip (0,0))
    for el in svg_root.iter():
        if el.tag == f"{{{svg_ns}}}g":
            m = re.match(r"translate\(\s*([\d.]+)\s*[,\s]\s*([\d.]+)\s*\)", el.get("transform", ""))
            if m and float(m.group(1)) > 50:
                tx, ty = float(m.group(1)), float(m.group(2))
                break

    h_ys, v_xs = [], []
    ax_x, ax_y = None, None

    for el in svg_root.iter():
        if el.tag != f"{{{svg_ns}}}path":
            continue
        cls = el.get("class", "")
        d = el.get("d", "")
        if cls == "guide line":
            if " h" in d:
                m = re.search(r"M\s*[\d.]+\s+([\d.]+)\s+h", d)
                if m:
                    h_ys.append(float(m.group(1)))
            if " v" in d:
                m = re.search(r"M\s*([\d.]+)\s+[\d.]+\s+v", d)
                if m:
                    v_xs.append(float(m.group(1)))
        elif cls == "axis major line":
            m = re.search(r"M\s*[\d.]+\s+([\d.]+)\s+h", d)
            if m:
                ax_y = float(m.group(1))
        elif "axis line" in cls and "major" not in cls:
            m = re.search(r"M\s*([\d.]+)\s+[\d.]+\s+v", d)
            if m:
                ax_x = float(m.group(1))

    if h_ys and v_xs and ax_x is not None and ax_y is not None:
        y_inner_bot = max(h_ys)  # y_data = -2
        x_inner_left = min(v_xs)  # x_data = -2
        scale_x = (ax_x - x_inner_left) / 2.0
        scale_y = (y_inner_bot - ax_y) / 2.0
    else:
        # Hardcoded values for 2400×2400, range [-2,2], this style config
        x_inner_left, ax_x = 39.9, 1036.2
        ax_y, y_inner_bot = 978.0, 1918.38
        scale_x, scale_y = 498.15, 470.19

    def data_to_canvas(xd, yd):
        inner_x = x_inner_left + (xd + 2.0) * scale_x
        inner_y = ax_y - yd * scale_y
        return inner_x + tx, inner_y + ty

    def canvas_dir(dx_d, dy_d):
        """Convert a data-space direction vector to SVG canvas direction."""
        return dx_d * scale_x, -dy_d * scale_y

    return data_to_canvas, canvas_dir


def _arrowhead_svg(tx, ty, dx, dy, sz, color):
    """SVG polygon for one filled arrowhead at (tx, ty) pointing along (dx, dy)."""
    ln = math.hypot(dx, dy)
    if ln < 1e-9:
        return ""
    dx, dy = dx / ln, dy / ln
    w = sz * 0.5
    bx, by = tx - dx * sz * 1.1, ty - dy * sz * 1.1
    return (
        f'<polygon points="{tx:.1f},{ty:.1f} {bx - dy * w:.1f},{by + dx * w:.1f} '
        f'{bx + dy * w:.1f},{by - dx * w:.1f}" '
        f'fill="{color}" opacity="0.92" stroke="none"/>'
    )


def _series_dot_canvas_pts(svg_root, svg_ns, series_idx, tx, ty):
    """Return (canvas_x, canvas_y) of dot markers for a pygal series."""
    marker = f"serie-{series_idx}"
    positions = []
    for el in svg_root.iter():
        if marker not in el.get("class", ""):
            continue
        for child in el.iter():
            if child.tag == f"{{{svg_ns}}}circle":
                try:
                    cx = float(child.get("cx", 0)) + tx
                    cy = float(child.get("cy", 0)) + ty
                    positions.append((cx, cy))
                except ValueError:
                    pass
    return positions


# Render to SVG, then inject direction arrows and frequency labels
SVG_NS = "http://www.w3.org/2000/svg"
svg_bytes = chart.render()
svg_str = svg_bytes.decode("utf-8")

try:
    svg_root = ET.fromstring(svg_str)
    d2c, cdir = _extract_svg_mapping(svg_root, SVG_NS)

    # Find translate for dot positions
    tx_val, ty_val = 307, 96
    for el in svg_root.iter():
        if el.tag == f"{{{SVG_NS}}}g":
            m = re.match(r"translate\(\s*([\d.]+)\s*[,\s]\s*([\d.]+)\s*\)", el.get("transform", ""))
            if m and float(m.group(1)) > 50:
                tx_val, ty_val = float(m.group(1)), float(m.group(2))
                break

    inject = []

    # --- Direction arrows on the positive-frequency curve ---
    # Arrow at each ω: tip at G(jω), direction from G(jω) toward G(j*ω_next)
    for w0 in [0.65, 1.1, 2.3]:
        w1 = w0 * 1.08
        g0, g1 = _tf(w0), _tf(w1)
        # Skip if point is outside the data range [-2,2]
        if not (-2 <= g0.real <= 2 and -2 <= g0.imag <= 2):
            continue
        cx, cy = d2c(g0.real, g0.imag)
        dcx, dcy = cdir(g1.real - g0.real, g1.imag - g0.imag)
        inject.append(_arrowhead_svg(cx, cy, dcx, dcy, 68, "#009E73"))

    # --- Direction arrows on the negative-frequency mirror ---
    # Mirror of G(jw): (real=G.real, imag=-G.imag).
    # "Increasing ω_neg" means decreasing |ω|, so direction is toward lower |ω|.
    for w0 in [0.65, 1.1, 2.3]:
        w1 = w0 * 0.92  # decreasing |ω| = increasing ω_neg
        g0, g1 = _tf(w0), _tf(w1)
        x0_neg, y0_neg = g0.real, -g0.imag
        x1_neg, y1_neg = g1.real, -g1.imag
        if not (-2 <= x0_neg <= 2 and -2 <= y0_neg <= 2):
            continue
        cx, cy = d2c(x0_neg, y0_neg)
        dcx, dcy = cdir(x1_neg - x0_neg, y1_neg - y0_neg)
        inject.append(_arrowhead_svg(cx, cy, dcx, dcy, 56, "#C475FD"))

    # --- Frequency labels visible in PNG (text near each ω marker dot) ---
    dot_pts = _series_dot_canvas_pts(svg_root, SVG_NS, 4, tx_val, ty_val)
    # Marker dots are at freq_targets = [0.5, 1.0, 2.0, 5.0, 10.0]
    # Sort by canvas_x ascending: left = low ω (negative real), right = high ω (near origin)
    dot_pts_sorted = sorted(dot_pts, key=lambda p: p[0])
    label_texts = ["0.5", "1.0", "2.0", "5.0", "10.0"]
    for (cx, cy), lab in zip(dot_pts_sorted[: len(label_texts)], label_texts, strict=False):
        inject.append(
            f'<text x="{cx + 20:.1f}" y="{cy - 36:.1f}" fill="#BD8233" '
            f'font-size="38" font-family="sans-serif" font-weight="bold">ω={lab}</text>'
        )

    if inject:
        group = '<g id="nyquist-overlays">' + "".join(inject) + "</g>"
        svg_str = svg_str.replace("</svg>", group + "</svg>", 1)

except Exception:
    pass  # fall through to plain render

cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), write_to=f"plot-{THEME}.png")

# HTML uses the original unmodified SVG (fully interactive with hover labels)
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(svg_bytes)
