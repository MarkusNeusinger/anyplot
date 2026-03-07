""" pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-07
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Arrow, BoxAnnotation, ColumnDataSource, Label, NormalHead, Range1d
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Higgs-strahlung: e- + e+ -> Z* -> Z + H, Z -> mu- mu+, H -> b b-bar + g
# This process showcases all 4 particle types:
#   fermion (solid), photon/Z (wavy), boson/H (dashed), gluon (curly)

# Vertices
v1 = (1.5, 3.0)  # e-e+ annihilation
v2 = (3.2, 3.0)  # Z*/gamma virtual propagator endpoint / ZH splitting
v3 = (5.0, 4.8)  # Z decay vertex
v4 = (5.0, 1.2)  # H decay vertex

# Propagators with all 4 particle types
propagators = [
    # Incoming fermions
    {"start": (0.2, 5.0), "end": v1, "type": "fermion", "label": "e\u207b", "arrow": "forward"},
    {"start": (0.2, 1.0), "end": v1, "type": "fermion", "label": "e\u207a", "arrow": "backward"},
    # Virtual Z/gamma (wavy)
    {"start": v1, "end": v2, "type": "photon", "label": "Z*/\u03b3"},
    # Z boson (wavy)
    {"start": v2, "end": v3, "type": "photon", "label": "Z"},
    # Higgs boson (dashed)
    {"start": v2, "end": v4, "type": "boson", "label": "H"},
    # Z decay products (fermions)
    {"start": v3, "end": (6.4, 5.6), "type": "fermion", "label": "\u03bc\u207b", "arrow": "forward"},
    {"start": v3, "end": (6.4, 4.0), "type": "fermion", "label": "\u03bc\u207a", "arrow": "backward"},
    # H decay products: b quark, b-bar quark, and gluon radiation
    {"start": v4, "end": (6.4, 2.4), "type": "fermion", "label": "b", "arrow": "forward"},
    {"start": v4, "end": (6.4, 1.0), "type": "fermion", "label": "b\u0305", "arrow": "backward"},
    # Gluon radiation - angled downward-right with enough length for clean coils
    {"start": v4, "end": (6.5, -0.2), "type": "gluon", "label": "g"},
]

# Color palette
FERMION_COLOR = "#306998"  # Python blue
PHOTON_COLOR = "#D4A017"  # Gold
GLUON_COLOR = "#2CA02C"  # Green
BOSON_COLOR = "#9467BD"  # Purple
VERTEX_COLOR = "#1a1a1a"  # Near-black

TYPE_COLORS = {"fermion": FERMION_COLOR, "photon": PHOTON_COLOR, "gluon": GLUON_COLOR, "boson": BOSON_COLOR}

# Plot - landscape for horizontal time flow
p = figure(
    width=4800,
    height=2700,
    title="feynman-basic \u00b7 bokeh \u00b7 pyplots.ai",
    x_range=Range1d(-0.3, 7.0),
    y_range=Range1d(-0.6, 6.4),
    toolbar_location=None,
)

p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Style
p.title.text_font_size = "28pt"
p.title.align = "center"
p.background_fill_color = "#f5f5f0"

# Subtle inner border using BoxAnnotation
p.add_layout(
    BoxAnnotation(
        left=0.0, right=6.8, top=6.2, bottom=-0.4, fill_alpha=0, line_color="#cccccc", line_width=2, line_alpha=0.5
    )
)

# Draw all propagators
for prop in propagators:
    x0, y0 = prop["start"]
    x1, y1 = prop["end"]
    dx = x1 - x0
    dy = y1 - y0
    length = np.sqrt(dx**2 + dy**2)
    color = TYPE_COLORS[prop["type"]]
    perp_x, perp_y = -dy / length, dx / length

    if prop["type"] == "fermion":
        # Use ColumnDataSource for fermion lines
        src = ColumnDataSource(data={"x": [x0, x1], "y": [y0, y1]})
        p.line("x", "y", source=src, line_width=4, color=color)

        # Arrow at midpoint showing particle/antiparticle flow
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        offset = 0.15
        if prop.get("arrow") == "backward":
            arrow_sx = mid_x + offset * dx / length
            arrow_sy = mid_y + offset * dy / length
            arrow_ex = mid_x - offset * dx / length
            arrow_ey = mid_y - offset * dy / length
        else:
            arrow_sx = mid_x - offset * dx / length
            arrow_sy = mid_y - offset * dy / length
            arrow_ex = mid_x + offset * dx / length
            arrow_ey = mid_y + offset * dy / length

        p.add_layout(
            Arrow(
                end=NormalHead(size=25, fill_color=color, line_color=color),
                x_start=arrow_sx,
                y_start=arrow_sy,
                x_end=arrow_ex,
                y_end=arrow_ey,
                line_width=0,
                line_alpha=0,
            )
        )

    elif prop["type"] == "photon":
        # Wavy line for photon/Z boson
        n_waves = max(6, int(length * 4.5))
        amplitude = 0.18
        t = np.linspace(0, 1, 500)
        wave = amplitude * np.sin(2 * np.pi * n_waves * t)
        wx = (x0 + t * dx) + wave * perp_x
        wy = (y0 + t * dy) + wave * perp_y
        wavy_src = ColumnDataSource(data={"x": wx.tolist(), "y": wy.tolist()})
        p.line("x", "y", source=wavy_src, line_width=4, color=color)

    elif prop["type"] == "gluon":
        # Curly/coiled line for gluon - tight loops with taper
        n_coils = max(5, int(length * 3))
        amplitude = 0.13
        t = np.linspace(0, 1, 1200)
        angle = 2 * np.pi * n_coils * t
        # Looping coil with controlled radius
        loop_r = amplitude * 1.2
        effective_t = t - (loop_r / length) * np.sin(angle)
        # Taper coils at endpoints for cleaner start/end
        taper = np.minimum(t * 6, 1.0) * np.minimum((1 - t) * 6, 1.0)
        gx = (x0 + effective_t * dx) + amplitude * np.sin(angle) * perp_x * taper
        gy = (y0 + effective_t * dy) + amplitude * np.sin(angle) * perp_y * taper
        gluon_src = ColumnDataSource(data={"x": gx.tolist(), "y": gy.tolist()})
        p.line("x", "y", source=gluon_src, line_width=3.5, color=color)

    elif prop["type"] == "boson":
        # Dashed line for scalar boson (Higgs)
        boson_src = ColumnDataSource(data={"x": [x0, x1], "y": [y0, y1]})
        p.line("x", "y", source=boson_src, line_width=6, color=color, line_dash=[24, 12])

    # Label offset perpendicular to the line
    mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
    label_dist = 0.35
    label_x = mid_x + label_dist * perp_x
    label_y = mid_y + label_dist * perp_y

    p.add_layout(
        Label(
            x=label_x,
            y=label_y,
            text=prop["label"],
            text_font_size="24pt",
            text_font_style="italic",
            text_color="#222222",
            text_align="center",
            text_baseline="middle",
        )
    )

# Draw vertices with distinct styling
vertex_xs = [v1[0], v2[0], v3[0], v4[0]]
vertex_ys = [v1[1], v2[1], v3[1], v4[1]]
vertex_source = ColumnDataSource(data={"x": vertex_xs, "y": vertex_ys})
p.scatter("x", "y", source=vertex_source, size=24, color=VERTEX_COLOR, line_color="white", line_width=3)

# Legend with actual line samples drawn using Bokeh glyphs
legend_x = 0.1
legend_base_y = 6.0
legend_spacing = 0.45
legend_line_len = 0.5

legend_entries = [
    ("fermion", FERMION_COLOR, "solid"),
    ("photon / Z", PHOTON_COLOR, "wavy"),
    ("gluon", GLUON_COLOR, "curly"),
    ("scalar (H)", BOSON_COLOR, "dashed"),
]

for i, (name, color, style) in enumerate(legend_entries):
    y_pos = legend_base_y - i * legend_spacing
    lx0 = legend_x
    lx1 = legend_x + legend_line_len

    if style == "solid":
        leg_src = ColumnDataSource(data={"x": [lx0, lx1], "y": [y_pos, y_pos]})
        p.line("x", "y", source=leg_src, line_width=4, color=color)
        # Small arrow on legend fermion line
        p.add_layout(
            Arrow(
                end=NormalHead(size=18, fill_color=color, line_color=color),
                x_start=lx0 + 0.12,
                y_start=y_pos,
                x_end=lx1 - 0.05,
                y_end=y_pos,
                line_width=0,
                line_alpha=0,
            )
        )
    elif style == "wavy":
        t_leg = np.linspace(0, 1, 200)
        wleg = 0.08 * np.sin(2 * np.pi * 4 * t_leg)
        leg_src = ColumnDataSource(data={"x": (lx0 + t_leg * legend_line_len).tolist(), "y": (y_pos + wleg).tolist()})
        p.line("x", "y", source=leg_src, line_width=4, color=color)
    elif style == "curly":
        t_leg = np.linspace(0, 1, 400)
        angle_leg = 2 * np.pi * 3 * t_leg
        loop_leg = 0.06 * 1.3
        eff_t = t_leg - (loop_leg / legend_line_len) * np.sin(angle_leg)
        taper_leg = np.minimum(t_leg * 6, 1.0) * np.minimum((1 - t_leg) * 6, 1.0)
        leg_src = ColumnDataSource(
            data={
                "x": (lx0 + eff_t * legend_line_len).tolist(),
                "y": (y_pos + 0.06 * np.sin(angle_leg) * taper_leg).tolist(),
            }
        )
        p.line("x", "y", source=leg_src, line_width=3.5, color=color)
    elif style == "dashed":
        leg_src = ColumnDataSource(data={"x": [lx0, lx1], "y": [y_pos, y_pos]})
        p.line("x", "y", source=leg_src, line_width=6, color=color, line_dash=[14, 8])

    # Label text next to line sample
    p.add_layout(
        Label(
            x=lx1 + 0.12,
            y=y_pos,
            text=name,
            text_font_size="20pt",
            text_color=color,
            text_font_style="bold",
            text_align="left",
            text_baseline="middle",
        )
    )

# Time axis arrow
p.add_layout(
    Arrow(
        end=NormalHead(size=20, fill_color="#999999", line_color="#999999"),
        x_start=1.5,
        y_start=-0.35,
        x_end=5.5,
        y_end=-0.35,
        line_width=3,
        line_color="#999999",
    )
)
p.add_layout(
    Label(
        x=3.5,
        y=-0.5,
        text="time",
        text_font_size="22pt",
        text_color="#999999",
        text_align="center",
        text_baseline="top",
    )
)

# Process annotation
p.add_layout(
    Label(
        x=3.5,
        y=6.15,
        text="e\u207be\u207a \u2192 Z* \u2192 ZH \u2192 \u03bc\u207b\u03bc\u207a + bb\u0305 + g",
        text_font_size="24pt",
        text_color="#444444",
        text_align="center",
        text_baseline="middle",
        text_font_style="italic",
    )
)

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Feynman Diagram - Higgs-strahlung")
