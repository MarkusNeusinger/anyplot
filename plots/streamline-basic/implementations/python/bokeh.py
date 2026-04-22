""" pyplots.ai
streamline-basic: Basic Streamline Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.plotting import figure
from bokeh.resources import CDN
from scipy.interpolate import RegularGridInterpolator


# Seed for reproducibility
np.random.seed(42)

# Grid setup
x = np.linspace(-3, 3, 40)
y = np.linspace(-3, 3, 40)
X, Y = np.meshgrid(x, y)

# Vortex flow field: u = -y, v = x (creates circular streamlines)
U = -Y
V = X

# Compute velocity magnitude for coloring
magnitude = np.sqrt(U**2 + V**2)

# Create interpolators for the vector field
u_interp = RegularGridInterpolator((y, x), U, bounds_error=False, fill_value=None)
v_interp = RegularGridInterpolator((y, x), V, bounds_error=False, fill_value=None)
mag_interp = RegularGridInterpolator((y, x), magnitude, bounds_error=False, fill_value=None)

# Seed points for streamlines in a grid pattern
seed_x = np.linspace(-2.5, 2.5, 8)
seed_y = np.linspace(-2.5, 2.5, 8)

# Storage for streamline data
all_xs = []
all_ys = []
all_colors = []

# Compute streamlines from seed points
for sx in seed_x:
    for sy in seed_y:
        # Trace streamline using Euler integration
        xs, ys, mags = [sx], [sy], []
        px, py = sx, sy
        dt, max_steps = 0.05, 300

        # Get initial magnitude
        m = mag_interp([[py, px]])[0]
        if m is None or np.isnan(m):
            continue
        mags.append(m)

        for _ in range(max_steps):
            u_val = u_interp([[py, px]])[0]
            v_val = v_interp([[py, px]])[0]

            if u_val is None or v_val is None or np.isnan(u_val) or np.isnan(v_val):
                break

            speed = np.sqrt(u_val**2 + v_val**2)
            if speed < 1e-6:
                break

            # Normalize and step
            px += u_val / speed * dt
            py += v_val / speed * dt

            # Check bounds
            if px < x.min() or px > x.max() or py < y.min() or py > y.max():
                break

            xs.append(px)
            ys.append(py)
            m = mag_interp([[py, px]])[0]
            if m is None or np.isnan(m):
                break
            mags.append(m)

        # Store if streamline is long enough
        if len(xs) >= 5:
            all_xs.append(np.array(xs))
            all_ys.append(np.array(ys))
            # Color based on average magnitude (blue to yellow gradient)
            avg_mag = np.mean(mags)
            t = np.clip(avg_mag / 3.0, 0, 1)
            r = int(48 + t * (255 - 48))
            g = int(105 + t * (212 - 105))
            b = int(152 + t * (59 - 152))
            all_colors.append(f"#{r:02x}{g:02x}{b:02x}")

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="streamline-basic · bokeh · pyplots.ai",
    x_axis_label="X Position",
    y_axis_label="Y Position",
    x_range=(-3.5, 3.5),
    y_range=(-3.5, 3.5),
)

# Style title and axes for large canvas
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "26pt"
p.yaxis.axis_label_text_font_size = "26pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Draw streamlines with direction arrows
for xs, ys, color in zip(all_xs, all_ys, all_colors, strict=True):
    p.line(xs, ys, line_width=4, line_color=color, line_alpha=0.85)

    # Add arrowhead at the end to show flow direction
    if len(xs) >= 2:
        dx = xs[-1] - xs[-2]
        dy = ys[-1] - ys[-2]
        length = np.sqrt(dx**2 + dy**2)
        if length > 0:
            dx /= length
            dy /= length
            arrow_size = 0.18
            tip_x, tip_y = xs[-1], ys[-1]
            wing1_x = tip_x - arrow_size * (dx + 0.5 * dy)
            wing1_y = tip_y - arrow_size * (dy - 0.5 * dx)
            wing2_x = tip_x - arrow_size * (dx - 0.5 * dy)
            wing2_y = tip_y - arrow_size * (dy + 0.5 * dx)
            p.patch(
                [tip_x, wing1_x, wing2_x], [tip_y, wing1_y, wing2_y], fill_color=color, line_color=color, fill_alpha=0.9
            )

# Background
p.background_fill_color = "#fafafa"

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Streamline Plot")
