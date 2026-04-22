""" pyplots.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-20
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — root locus for G(s) = (s+3) / [s(s+1)(s+2)(s+4)]
# Open-loop poles: 0, -1, -2, -4  |  Open-loop zero: -3
num = np.array([1, 3])
den = np.polymul(np.polymul([1, 0], [1, 1]), np.polymul([1, 2], [1, 4]))

ol_poles = np.sort(np.roots(den).real)
ol_zeros = np.sort(np.roots(num).real)
n_branches = len(den) - 1
num_padded = np.zeros(len(den))
num_padded[-len(num) :] = num

# Gain sweep with variable density: finer near breakaway and jω crossing
gains = np.concatenate(
    [np.linspace(0, 2, 200), np.linspace(2, 15, 300), np.linspace(15, 80, 200), np.linspace(80, 500, 150)]
)

# Compute closed-loop poles for each gain: roots of den(s) + K·num(s) = 0
loci = np.zeros((len(gains), n_branches), dtype=complex)
for i, K in enumerate(gains):
    roots = np.roots(den + K * num_padded)
    if i == 0:
        loci[i] = roots[np.argsort(roots.real)]
    else:
        prev = loci[i - 1]
        available = list(range(n_branches))
        for j in range(n_branches):
            dists = [abs(roots[k] - prev[j]) if k in available else np.inf for k in range(n_branches)]
            best = int(np.argmin(dists))
            loci[i, j] = roots[best]
            available.remove(best)

# Find imaginary axis crossings (stability boundary)
jw_crossings = []
for b in range(n_branches):
    reals = loci[:, b].real
    for i in range(len(reals) - 1):
        if reals[i] * reals[i + 1] < 0 and abs(loci[i, b].imag) > 0.1:
            frac = abs(reals[i]) / (abs(reals[i]) + abs(reals[i + 1]))
            im = float(loci[i, b].imag + frac * (loci[i + 1, b].imag - loci[i, b].imag))
            K_cross = float(gains[i] + frac * (gains[i + 1] - gains[i]))
            jw_crossings.append((round(im, 3), round(K_cross, 2)))

# Find breakaway point: on real axis between poles at -1 and -2
# d/ds[1 + K·N(s)/D(s)] = 0 → d/ds[D(s)/N(s)] = 0
# Numerically search between -1 and -2
s_test = np.linspace(-1.01, -1.99, 500)
ratio = np.polyval(den, s_test) / np.polyval(num, s_test)
breakaway_idx = np.argmin(np.abs(np.gradient(ratio, s_test)))
breakaway_s = round(float(s_test[breakaway_idx]), 3)
breakaway_K = round(float(-np.polyval(den, breakaway_s) / np.polyval(num, breakaway_s)), 2)

# Real-axis locus segments (to the left of an odd number of real poles+zeros)
real_segments = [(0, -1), (-2, -3), (-4, -6)]

# Constant damping ratio guide lines (ζ = 0.2, 0.4, 0.6, 0.8)
zeta_values = [0.2, 0.4, 0.6, 0.8]
guide_extent = 5.5

# Constant natural frequency semicircles (ωn = 1, 2, 3, 4, 5)
wn_values = [1, 2, 3, 4, 5]

# Style — refined palette with warm background tint for polish
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background="#fafafa",
    plot_background="#fefefe",
    foreground="#1a1a2e",
    foreground_strong="#1a1a2e",
    foreground_subtle="#d8d8d8",
    guide_stroke_color="#eaeaea",
    guide_stroke_dasharray="2, 4",
    colors=(
        "#c0c0c0",  # 0: ζ guide lines (soft gray, background)
        "#c0c0c0",  # 1: ωn guide semicircles (soft gray, background)
        "#2563EB",  # 2: Root locus branches (vivid blue)
        "#EA580C",  # 3: Real-axis locus (burnt orange)
        "#DC2626",  # 4: Open-loop poles (red)
        "#7C3AED",  # 5: Open-loop zero (violet — colorblind-safe vs red)
        "#16A34A",  # 6: Breakaway point (green — distinct emphasis)
        "#D97706",  # 7: Stability boundary (amber)
        "#1D4ED8",  # 8: Gain direction markers (dark blue)
    ),
    font_family=font,
    title_font_family=font,
    title_font_size=52,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=26,
    legend_font_family=font,
    value_font_size=24,
    tooltip_font_size=26,
    tooltip_font_family=font,
    opacity=0.92,
    opacity_hover=1.0,
    stroke_width=5,
)

chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="root-locus-basic · pygal · pyplots.ai",
    x_title="Real Axis (σ)",
    y_title="Imaginary Axis (jω)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=22,
    stroke=True,
    dots_size=0,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda v: f"{v:.1f}",
    value_formatter=lambda v: f"{v:.1f}",
    margin_bottom=90,
    margin_left=80,
    margin_right=50,
    margin_top=55,
    xrange=(-6, 4),
    range=(-5, 5),
    print_values=False,
    print_zeroes=False,
    js=[],
    truncate_legend=-1,
    include_x_axis=True,
    allow_interruptions=True,
    spacing=18,
)

# Constant damping ratio guide lines (ζ rays from origin) — rendered first as background
zeta_pts = []
for zeta in zeta_values:
    theta = np.arccos(zeta)
    for t in np.linspace(0, guide_extent, 25):
        zeta_pts.append((round(-t * np.cos(theta), 3), round(t * np.sin(theta), 3)))
    zeta_pts.append(None)
    for t in np.linspace(0, guide_extent, 25):
        zeta_pts.append((round(-t * np.cos(theta), 3), round(-t * np.sin(theta), 3)))
    zeta_pts.append(None)
chart.add(
    "ζ guides", zeta_pts, stroke_style={"width": 1.2, "dasharray": "6, 5"}, show_dots=False, allow_interruptions=True
)

# Constant natural frequency semicircles (ωn arcs in left half-plane)
wn_pts = []
for wn in wn_values:
    angles = np.linspace(np.pi / 2, 3 * np.pi / 2, 50)
    for a in angles:
        wn_pts.append((round(wn * np.cos(a), 3), round(wn * np.sin(a), 3)))
    wn_pts.append(None)
chart.add(
    "ωn guides", wn_pts, stroke_style={"width": 1.2, "dasharray": "6, 5"}, show_dots=False, allow_interruptions=True
)

# Root locus branches — skip points near zero at s=-3 to avoid obscuring it
zero_exclusion_radius = 0.35
locus_pts = []
for b in range(n_branches):
    branch_data = []
    for i in range(len(gains)):
        r, im = float(loci[i, b].real), float(loci[i, b].imag)
        if -6 <= r <= 4 and -5 <= im <= 5:
            near_zero = any(
                abs(r - float(z)) < zero_exclusion_radius and abs(im) < zero_exclusion_radius for z in ol_zeros
            )
            if near_zero:
                if branch_data:
                    locus_pts.extend(branch_data)
                    locus_pts.append(None)
                    branch_data = []
            else:
                branch_data.append({"value": (round(r, 4), round(im, 4)), "label": f"K = {gains[i]:.2f}"})
    if branch_data:
        locus_pts.extend(branch_data)
    locus_pts.append(None)

chart.add(
    "Root Locus", locus_pts, stroke_style={"width": 7, "linecap": "round"}, show_dots=False, allow_interruptions=True
)

# Real-axis locus segments — thick orange line
real_pts = []
for seg_start, seg_end in real_segments:
    for x in np.linspace(seg_start, seg_end, 60):
        real_pts.append((round(float(x), 3), 0.0))
    real_pts.append(None)
chart.add(
    "Real-Axis Locus",
    real_pts,
    stroke_style={"width": 12, "linecap": "round"},
    show_dots=False,
    allow_interruptions=True,
)

# Open-loop poles (marked with ×)
pole_pts = [{"value": (round(float(p), 2), 0.0), "label": f"Pole at s = {p:.0f}"} for p in ol_poles]
chart.add("Poles (×)", pole_pts, stroke=False, dots_size=22)

# Open-loop zero (marked with ○) — large dot, rendered after locus to stay on top
zero_pts = [{"value": (round(float(z), 2), 0.0), "label": f"Zero at s = {z:.0f}"} for z in ol_zeros]
chart.add("Zero (○)", zero_pts, stroke=False, dots_size=28)

# Breakaway point — emphasized with distinct green marker
breakaway_pts = [{"value": (breakaway_s, 0.0), "label": f"Breakaway: s = {breakaway_s}, K = {breakaway_K}"}]
chart.add("Breakaway Point", breakaway_pts, stroke=False, dots_size=30)

# Imaginary axis crossings — stability boundary markers
jw_pts = [{"value": (0.0, im), "label": f"jω crossing: s = {im:+.3f}j, K = {K:.2f}"} for im, K in jw_crossings]
chart.add("Stability Boundary", jw_pts, stroke=False, dots_size=24)

# Gain direction markers along locus at selected gains
arrow_pts = []
arrow_gains = [5, 15, 40, 100, 250]
for ag in arrow_gains:
    idx = np.argmin(np.abs(gains - ag))
    for b in range(n_branches):
        r, im = float(loci[idx, b].real), float(loci[idx, b].imag)
        if -6 <= r <= 4 and -5 <= im <= 5:
            arrow_pts.append({"value": (round(r, 3), round(im, 3)), "label": f"K = {ag} →"})
chart.add("Gain K →", arrow_pts, stroke=False, dots_size=20)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
