""" pyplots.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: pygal 3.1.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-03
"""

import sys
from pathlib import Path


_script_dir = str(Path(__file__).parent)
sys.path = [p for p in sys.path if p != _script_dir]

import base64  # noqa: E402
from io import BytesIO  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


# Data — Mandelbrot set computation
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
max_iter = 200
bailout = 256
grid_w, grid_h = 800, 600

real = np.linspace(x_min, x_max, grid_w)
imag = np.linspace(y_max, y_min, grid_h)
c = real[np.newaxis, :] + 1j * imag[:, np.newaxis]

z = np.zeros_like(c)
escape_iter = np.full(c.shape, max_iter, dtype=np.float64)
mask = np.ones(c.shape, dtype=bool)

for i in range(max_iter):
    z[mask] = z[mask] ** 2 + c[mask]
    escaped = mask & (np.abs(z) > bailout)
    log_zn = np.log(np.abs(z[escaped]))
    nu = np.log(log_zn / np.log(bailout)) / np.log(2)
    escape_iter[escaped] = i + 1 - nu
    mask[escaped] = False

inside = escape_iter >= max_iter
exterior = ~inside

# Viridis-inspired perceptually uniform colormap
viridis_stops = [
    (0.000, (68, 1, 84)),
    (0.125, (72, 36, 117)),
    (0.250, (62, 74, 137)),
    (0.375, (49, 104, 142)),
    (0.500, (38, 130, 142)),
    (0.625, (31, 158, 137)),
    (0.750, (53, 183, 121)),
    (0.875, (110, 206, 88)),
    (1.000, (253, 231, 37)),
]

lut_size = 1024
lut = np.zeros((lut_size, 3), dtype=int)
for idx in range(lut_size):
    t = idx / (lut_size - 1)
    for k in range(len(viridis_stops) - 1):
        t0, c0 = viridis_stops[k]
        t1, c1 = viridis_stops[k + 1]
        if t <= t1 + 1e-10:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0
            lut[idx] = [int(c0[ch] + (c1[ch] - c0[ch]) * f) for ch in range(3)]
            break

# Log-normalized color mapping
cell_colors = np.zeros((*c.shape, 3), dtype=np.uint8)
log_min, log_max = 0.0, 1.0
if np.any(exterior):
    iter_vals = escape_iter[exterior]
    log_vals = np.log(iter_vals + 1)
    log_min, log_max = log_vals.min(), log_vals.max()
    if log_max > log_min:
        normalized = (log_vals - log_min) / (log_max - log_min)
    else:
        normalized = np.zeros_like(log_vals)
    indices = np.clip((normalized * (lut_size - 1)).astype(int), 0, lut_size - 1)
    cell_colors[exterior] = lut[indices]

# Encode heatmap as PNG data URI for SVG embedding
heatmap_img = Image.fromarray(cell_colors)
buf = BytesIO()
heatmap_img.save(buf, format="PNG")
heatmap_data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


class MandelbrotHeatmap(Graph):
    """Custom pygal chart for Mandelbrot set heatmap visualization.

    Subclasses pygal's Graph to render a fractal heatmap using pygal's
    SVG construction, Style system, and rendering pipeline.
    """

    _adapters = []

    def __init__(self, heatmap_uri, x_range, y_range, colorbar_lut, log_range, lut_sz, *args, **kwargs):
        self._heatmap_uri = heatmap_uri
        self._x_range = x_range
        self._y_range = y_range
        self._colorbar_lut = colorbar_lut
        self._log_range = log_range
        self._lut_sz = lut_sz
        super().__init__(*args, **kwargs)

    def _compute(self):
        pass

    def _compute_x_labels(self):
        pass

    def _compute_y_labels(self):
        pass

    def _compute_x_labels_major(self):
        pass

    def _compute_y_labels_major(self):
        pass

    def _plot(self):
        # Available area after pygal's margins (title, etc.)
        gw = self.view.width
        gh = self.view.height

        # Tighter layout for better canvas utilization
        pad_left, pad_top = 250, 50
        pad_right, pad_bottom = 210, 105
        x_span = self._x_range[1] - self._x_range[0]
        y_span = self._y_range[1] - self._y_range[0]

        avail_w = gw - pad_left - pad_right
        avail_h = gh - pad_top - pad_bottom
        if avail_w / avail_h > x_span / y_span:
            plot_h = avail_h
            plot_w = plot_h * x_span / y_span
        else:
            plot_w = avail_w
            plot_h = plot_w * y_span / x_span

        px, py = pad_left, pad_top
        root = self.svg.node(self.nodes["plot"], class_="mandelbrot-heatmap")

        # Subtle shadow behind heatmap for depth
        self.svg.node(
            root, "rect", x=px + 4, y=py + 4, width=plot_w, height=plot_h, style="fill:#d0d0d0;stroke:none;opacity:0.5"
        )

        # Embedded high-resolution heatmap image
        ns = "http://www.w3.org/1999/xlink"
        img = self.svg.node(root, "image", x=px, y=py, width=plot_w, height=plot_h)
        img.attrib["{%s}href" % ns] = self._heatmap_uri
        img.attrib["preserveAspectRatio"] = "none"

        # Refined plot border
        self.svg.node(
            root, "rect", x=px, y=py, width=plot_w, height=plot_h, style="fill:none;stroke:#333;stroke-width:2.5"
        )

        # Subtitle with mathematical formula (italic for elegance)
        sub = self.svg.node(
            root,
            "text",
            x=px + plot_w / 2,
            y=py - 12,
            style="font-size:36px;font-style:italic;font-weight:300;"
            "font-family:'Georgia',serif;fill:#555;letter-spacing:1px",
        )
        sub.text = "z\u2099\u208a\u2081 = z\u2099\u00b2 + c \u00b7 Escape time with smooth iteration count"
        sub.attrib["text-anchor"] = "middle"

        # X-axis ticks and labels
        for val in [-2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0]:
            frac = (val - self._x_range[0]) / x_span
            tx = px + frac * plot_w
            ty = py + plot_h
            self.svg.node(root, "line", x1=tx, y1=ty, x2=tx, y2=ty + 14, style="stroke:#444;stroke-width:2")
            lbl = self.svg.node(root, "text", x=tx, y=ty + 50, style="font-size:34px;font-family:sans-serif;fill:#333")
            lbl.text = f"{val:.1f}"
            lbl.attrib["text-anchor"] = "middle"

        # X-axis title
        xl = self.svg.node(
            root,
            "text",
            x=px + plot_w / 2,
            y=py + plot_h + 95,
            style="font-size:42px;font-weight:600;font-family:sans-serif;fill:#333;letter-spacing:0.5px",
        )
        xl.text = "Real Axis (Re)"
        xl.attrib["text-anchor"] = "middle"

        # Y-axis ticks and labels
        for val in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            frac = (self._y_range[1] - val) / y_span
            ty = py + frac * plot_h
            self.svg.node(root, "line", x1=px - 14, y1=ty, x2=px, y2=ty, style="stroke:#444;stroke-width:2")
            label = f"{val:+.1f}i" if val != 0 else "0.0i"
            lbl = self.svg.node(
                root, "text", x=px - 22, y=ty + 12, style="font-size:34px;font-family:sans-serif;fill:#333"
            )
            lbl.text = label
            lbl.attrib["text-anchor"] = "end"

        # Y-axis title (rotated)
        ylx = px - 200
        yly = py + plot_h / 2
        yl = self.svg.node(
            root,
            "text",
            x=ylx,
            y=yly,
            style="font-size:42px;font-weight:600;font-family:sans-serif;fill:#333;letter-spacing:0.5px",
        )
        yl.text = "Imaginary Axis (Im)"
        yl.attrib["text-anchor"] = "middle"
        yl.attrib["transform"] = f"rotate(-90, {ylx}, {yly})"

        # Feature annotations — guide viewer to key mathematical structures
        annotations = [
            {"label": "Main cardioid", "cx": -0.25, "cy": 0.15, "dx": 60, "dy": -90},
            {"label": "Period-2 bulb", "cx": -1.0, "cy": 0.15, "dx": -40, "dy": -90},
        ]
        for ann in annotations:
            ax = px + (ann["cx"] - self._x_range[0]) / x_span * plot_w
            ay = py + (self._y_range[1] - ann["cy"]) / y_span * plot_h
            tx = ax + ann["dx"]
            ty = ay + ann["dy"]
            # Leader line with subtle white stroke
            self.svg.node(
                root, "line", x1=ax, y1=ay, x2=tx, y2=ty + 5, style="stroke:#ffffff;stroke-width:2.5;opacity:0.9"
            )
            # Small circle at anchor point
            self.svg.node(root, "circle", cx=ax, cy=ay, r=5, style="fill:#ffffff;opacity:0.9;stroke:none")
            # Annotation text with semi-transparent background
            tw = len(ann["label"]) * 14 + 14
            self.svg.node(
                root, "rect", x=tx - 7, y=ty - 24, width=tw, height=32, rx=5, ry=5, style="fill:#000000;opacity:0.65"
            )
            lbl = self.svg.node(
                root, "text", x=tx, y=ty, style="font-size:23px;font-family:sans-serif;fill:#ffffff;font-weight:500"
            )
            lbl.text = ann["label"]

        # Colorbar
        cb_x = px + plot_w + 35
        cb_w = 40
        cb_top = py + 45
        cb_h = plot_h - 90
        n_seg = 100

        for s in range(n_seg):
            t = 1.0 - s / (n_seg - 1)
            ci = min(int(t * (self._lut_sz - 1)), self._lut_sz - 1)
            r, g, b = self._colorbar_lut[ci]
            sy = cb_top + s * cb_h / n_seg
            self.svg.node(
                root,
                "rect",
                x=cb_x,
                y=sy,
                width=cb_w,
                height=cb_h / n_seg + 1,
                style=f"fill:#{r:02x}{g:02x}{b:02x};stroke:none",
            )

        self.svg.node(
            root, "rect", x=cb_x, y=cb_top, width=cb_w, height=cb_h, style="fill:none;stroke:#444;stroke-width:1.5"
        )

        # Colorbar tick labels — round values for readability
        log_span = self._log_range[1] - self._log_range[0]
        for iter_val in [1, 5, 10, 25, 50, 100, 200]:
            log_val = np.log(iter_val + 1)
            if log_val < self._log_range[0] or log_val > self._log_range[1]:
                continue
            t_c = (log_val - self._log_range[0]) / log_span if log_span > 0 else 0
            frac = 1.0 - t_c
            ty = cb_top + frac * cb_h
            self.svg.node(
                root, "line", x1=cb_x + cb_w, y1=ty, x2=cb_x + cb_w + 8, y2=ty, style="stroke:#444;stroke-width:1.5"
            )
            lbl = self.svg.node(
                root, "text", x=cb_x + cb_w + 14, y=ty + 10, style="font-size:28px;font-family:sans-serif;fill:#333"
            )
            lbl.text = str(iter_val)

        # Colorbar title
        cbt = self.svg.node(
            root,
            "text",
            x=cb_x - 5,
            y=cb_top - 22,
            style="font-size:32px;font-weight:600;font-family:sans-serif;fill:#333",
        )
        cbt.text = "Iterations"
        cbt.attrib["text-anchor"] = "start"

        # In-set legend entry
        lg_y = cb_top + cb_h + 40
        self.svg.node(root, "rect", x=cb_x, y=lg_y, width=28, height=28, style="fill:black;stroke:#555;stroke-width:1")
        lg = self.svg.node(
            root, "text", x=cb_x + 40, y=lg_y + 22, style="font-size:26px;font-family:sans-serif;fill:#333"
        )
        lg.text = "In set"


# Chart styling via pygal's Style system
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#000000",),
    title_font_size=56,
    title_font_family="sans-serif",
    label_font_size=34,
    major_label_font_size=34,
    legend_font_size=28,
    value_font_size=28,
)

# Create chart using pygal's rendering pipeline
chart = MandelbrotHeatmap(
    heatmap_uri=heatmap_data_uri,
    x_range=(x_min, x_max),
    y_range=(y_min, y_max),
    colorbar_lut=lut,
    log_range=(log_min, log_max),
    lut_sz=lut_size,
    width=4800,
    height=2700,
    style=custom_style,
    title="heatmap-mandelbrot \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    print_values=False,
    margin=30,
    spacing=10,
)

chart.add("In set", [1])

# Save using pygal's render methods
chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")

# Interactive HTML
svg_content = chart.render().decode("utf-8")
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-mandelbrot - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {svg_content}
    </figure>
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
