"""pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-07
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Arrow, ColumnDataSource, Label, NormalHead, Range1d
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Higgs-strahlung: e- + e+ -> Z* -> Z + H, Z -> mu- mu+, H -> b b-bar + g
# This process showcases all 4 particle types:
#   fermion (solid), photon/Z (wavy), boson/H (dashed), gluon (curly)

# Vertices
v1 = (1.2, 3.0)  # e-e+ annihilation
v2 = (3.0, 3.0)  # Z*/gamma virtual propagator endpoint / ZH splitting
v3 = (4.8, 5.0)  # Z decay vertex
v4 = (4.8, 1.0)  # H decay vertex

# Propagators with all 4 particle types
propagators = [
    # Incoming fermions
    {"start": (0.0, 5.4), "end": v1, "type": "fermion", "label": "e\u207b", "arrow": "forward"},
    {"start": (0.0, 0.6), "end": v1, "type": "fermion", "label": "e\u207a", "arrow": "backward"},
    # Virtual Z/gamma (wavy)
    {"start": v1, "end": v2, "type": "photon", "label": "Z*/\u03b3"},
    # Z boson (wavy)
    {"start": v2, "end": v3, "type": "photon", "label": "Z"},
    # Higgs boson (dashed)
    {"start": v2, "end": v4, "type": "boson", "label": "H"},
    # Z decay products (fermions)
    {"start": v3, "end": (6.2, 5.8), "type": "fermion", "label": "\u03bc\u207b", "arrow": "forward"},
    {"start": v3, "end": (6.2, 4.2), "type": "fermion", "label": "\u03bc\u207a", "arrow": "backward"},
    # H decay products: b quark, b-bar quark, and gluon radiation
    {"start": v4, "end": (6.2, 2.0), "type": "fermion", "label": "b", "arrow": "forward"},
    {"start": v4, "end": (6.2, 0.4), "type": "fermion", "label": "b\u0305", "arrow": "backward"},
    {"start": v4, "end": (6.0, -0.3), "type": "gluon", "label": "g"},
]

# Color palette
FERMION_COLOR = "#306998"  # Python blue
PHOTON_COLOR = "#D4A017"  # Gold
GLUON_COLOR = "#2CA02C"  # Green
BOSON_COLOR = "#9467BD"  # Purple
VERTEX_COLOR = "#1a1a1a"  # Near-black

TYPE_COLORS = {"fermion": FERMION_COLOR, "photon": PHOTON_COLOR, "gluon": GLUON_COLOR, "boson": BOSON_COLOR}

# Plot - use landscape for horizontal time flow
p = figure(
    width=4800,
    height=2700,
    title="feynman-basic \u00b7 bokeh \u00b7 pyplots.ai",
    x_range=Range1d(-0.6, 7.2),
    y_range=Range1d(-0.8, 6.8),
    toolbar_location=None,
)

p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Style
p.title.text_font_size = "28pt"
p.title.align = "center"
p.background_fill_color = "#f8f8f8"

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
        p.line([x0, x1], [y0, y1], line_width=4, color=color)

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
        n_waves = 8
        amplitude = 0.2
        t = np.linspace(0, 1, 400)
        wave = amplitude * np.sin(2 * np.pi * n_waves * t)
        wx = (x0 + t * dx) + wave * perp_x
        wy = (y0 + t * dy) + wave * perp_y
        p.line(wx.tolist(), wy.tolist(), line_width=4, color=color)

    elif prop["type"] == "gluon":
        # Curly/coiled line for gluon using looping parametric curve
        n_coils = 5
        amplitude = 0.15
        t = np.linspace(0, 1, 800)
        angle = 2 * np.pi * n_coils * t
        # Looping coil: radius creates visible loops crossing the centerline
        loop_r = amplitude * 1.4
        effective_t = t - (loop_r / length) * np.sin(angle)
        gx = (x0 + effective_t * dx) + amplitude * np.sin(angle) * perp_x
        gy = (y0 + effective_t * dy) + amplitude * np.sin(angle) * perp_y
        p.line(gx.tolist(), gy.tolist(), line_width=3.5, color=color)

    elif prop["type"] == "boson":
        # Dashed line for scalar boson (Higgs)
        p.line([x0, x1], [y0, y1], line_width=6, color=color, line_dash=[24, 12])

    # Label offset perpendicular to the line
    mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
    label_dist = 0.38
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
p.scatter("x", "y", source=vertex_source, size=22, color=VERTEX_COLOR, line_color="white", line_width=3)

# Legend: particle type key using colored labels
legend_items = [
    ("\u2500\u2500  fermion", FERMION_COLOR, 6.4),
    ("\u223c\u223c  photon / Z", PHOTON_COLOR, 6.0),
    ("\u2609\u2609  gluon", GLUON_COLOR, 5.6),
    ("- -  scalar boson (H)", BOSON_COLOR, 5.2),
]
for text, color, y_pos in legend_items:
    p.add_layout(
        Label(
            x=-0.3,
            y=y_pos,
            text=text,
            text_font_size="22pt",
            text_color=color,
            text_font_style="bold",
            text_align="left",
            text_baseline="middle",
        )
    )

# Time axis arrow
p.add_layout(
    Arrow(
        end=NormalHead(size=20, fill_color="#aaaaaa", line_color="#aaaaaa"),
        x_start=1.5,
        y_start=-0.5,
        x_end=5.5,
        y_end=-0.5,
        line_width=3,
        line_color="#aaaaaa",
    )
)
p.add_layout(
    Label(
        x=3.5,
        y=-0.65,
        text="time",
        text_font_size="22pt",
        text_color="#aaaaaa",
        text_align="center",
        text_baseline="top",
    )
)

# Process annotation
p.add_layout(
    Label(
        x=3.5,
        y=6.5,
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
