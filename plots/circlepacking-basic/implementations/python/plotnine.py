""" pyplots.ai
circlepacking-basic: Circle Packing Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_fill_manual,
    scale_size_identity,
    theme,
    theme_void,
)


np.random.seed(42)

# Hierarchical data - Company organizational structure
# Format: (id, label, parent_id, value)
nodes = [
    ("root", "Company", None, None),
    ("eng", "Engineering", "root", 50),
    ("ops", "Operations", "root", 35),
    ("prod", "Product", "root", 30),
    ("be", "Backend", "eng", 20),
    ("fe", "Frontend", "eng", 18),
    ("dops", "DevOps", "eng", 12),
    ("fin", "Finance", "ops", 15),
    ("leg", "Legal", "ops", 10),
    ("hr", "HR", "ops", 10),
    ("des", "Design", "prod", 12),
    ("pm", "PM", "prod", 10),
    ("res", "Research", "prod", 8),
]

# Circle positions and radii - manually laid out for proper size differentiation
# Root circle
root_x, root_y, root_r = 0.0, 0.0, 1.0

# Calculate department radii based on their total values (area encoding: r ∝ sqrt(value))
dept_values = {"eng": 50, "ops": 35, "prod": 30}
dept_total = sum(dept_values.values())
dept_scale = 0.48  # Larger scale factor for department circles to fill space better

eng_r = np.sqrt(dept_values["eng"] / dept_total) * dept_scale
ops_r = np.sqrt(dept_values["ops"] / dept_total) * dept_scale
prod_r = np.sqrt(dept_values["prod"] / dept_total) * dept_scale

# Position departments more centrally - place them in a tighter triangular arrangement
eng_x, eng_y = 0.0, 0.30  # Engineering at top center
ops_x, ops_y = -0.28, -0.12  # Operations bottom left, moved up
prod_x, prod_y = 0.28, -0.12  # Product bottom right, moved up

# Calculate team radii with more variation to show size differences clearly
# Teams within Engineering (values: 20, 18, 12) - wider value range
eng_team_values = {"be": 20, "fe": 18, "dops": 12}
eng_team_total = sum(eng_team_values.values())
team_scale_eng = eng_r * 0.75

be_r = np.sqrt(eng_team_values["be"] / eng_team_total) * team_scale_eng
fe_r = np.sqrt(eng_team_values["fe"] / eng_team_total) * team_scale_eng
dops_r = np.sqrt(eng_team_values["dops"] / eng_team_total) * team_scale_eng

# Teams within Operations (values: 15, 10, 10)
ops_team_values = {"fin": 15, "leg": 10, "hr": 10}
ops_team_total = sum(ops_team_values.values())
team_scale_ops = ops_r * 0.75

fin_r = np.sqrt(ops_team_values["fin"] / ops_team_total) * team_scale_ops
leg_r = np.sqrt(ops_team_values["leg"] / ops_team_total) * team_scale_ops
hr_r = np.sqrt(ops_team_values["hr"] / ops_team_total) * team_scale_ops

# Teams within Product (values: 12, 10, 8)
prod_team_values = {"des": 12, "pm": 10, "res": 8}
prod_team_total = sum(prod_team_values.values())
team_scale_prod = prod_r * 0.75

des_r = np.sqrt(prod_team_values["des"] / prod_team_total) * team_scale_prod
pm_r = np.sqrt(prod_team_values["pm"] / prod_team_total) * team_scale_prod
res_r = np.sqrt(prod_team_values["res"] / prod_team_total) * team_scale_prod

# Position teams within their parent departments - tighter arrangement
# Engineering teams - arranged in a triangle
be_x, be_y = eng_x - 0.12, eng_y + 0.0
fe_x, fe_y = eng_x + 0.12, eng_y + 0.0
dops_x, dops_y = eng_x + 0.0, eng_y - 0.14

# Operations teams - arranged in a triangle
fin_x, fin_y = ops_x + 0.0, ops_y + 0.10
leg_x, leg_y = ops_x - 0.10, ops_y - 0.05
hr_x, hr_y = ops_x + 0.10, ops_y - 0.05

# Product teams - arranged in a triangle
des_x, des_y = prod_x + 0.0, prod_y + 0.10
pm_x, pm_y = prod_x - 0.10, prod_y - 0.05
res_x, res_y = prod_x + 0.10, prod_y - 0.05

# All circles data: (id, label, cx, cy, r, depth)
circles_data = [
    ("root", "Company", root_x, root_y, root_r, 0),
    ("eng", "Engineering", eng_x, eng_y, eng_r, 1),
    ("ops", "Operations", ops_x, ops_y, ops_r, 1),
    ("prod", "Product", prod_x, prod_y, prod_r, 1),
    ("be", "Backend", be_x, be_y, be_r, 2),
    ("fe", "Frontend", fe_x, fe_y, fe_r, 2),
    ("dops", "DevOps", dops_x, dops_y, dops_r, 2),
    ("fin", "Finance", fin_x, fin_y, fin_r, 2),
    ("leg", "Legal", leg_x, leg_y, leg_r, 2),
    ("hr", "HR", hr_x, hr_y, hr_r, 2),
    ("des", "Design", des_x, des_y, des_r, 2),
    ("pm", "PM", pm_x, pm_y, pm_r, 2),
    ("res", "Research", res_x, res_y, res_r, 2),
]

# Sort by depth for proper layering (draw root first, teams last/on top)
circles_data = sorted(circles_data, key=lambda c: c[5])

# Build polygon dataframe for drawing circles
polygon_rows = []
n_points = 64

for circle_id, _label, cx, cy, r, depth in circles_data:
    angles = np.linspace(0, 2 * np.pi, n_points)
    xs = cx + r * np.cos(angles)
    ys = cy + r * np.sin(angles)
    for j, (x, y) in enumerate(zip(xs, ys, strict=True)):
        polygon_rows.append({"circle_id": circle_id, "x": x, "y": y, "order": j, "depth": depth})

df_circles = pd.DataFrame(polygon_rows)

# Build labels dataframe - include ALL labels (departments AND teams)
label_rows = []
for _circle_id, label, cx, cy, r, depth in circles_data:
    if depth == 0:
        continue  # Skip root label
    if depth == 1:
        # Department labels: position at top edge of circle
        label_y = cy + r * 0.60
        text_size = 12
    else:
        # Team labels: centered in circle, larger size for visibility
        label_y = cy
        text_size = 10
    label_rows.append({"x": cx, "y": label_y, "label": label, "text_size": text_size, "depth": depth})

df_labels = pd.DataFrame(label_rows)

# Create the plot
plot = (
    ggplot()
    + geom_polygon(
        df_circles, aes(x="x", y="y", group="circle_id", fill="factor(depth)"), color="#333333", size=0.5, alpha=0.92
    )
    + geom_text(
        df_labels,
        aes(x="x", y="y", label="label", size="text_size"),
        color="#222222",
        fontweight="bold",
        show_legend=False,
    )
    + scale_fill_manual(
        values=["#E0E0E0", "#306998", "#FFD43B"], labels=["Root", "Departments", "Teams"], name="Hierarchy Level"
    )
    + scale_size_identity()
    + coord_fixed(ratio=1)
    + labs(title="circlepacking-basic · plotnine · pyplots.ai")
    + theme_void()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=28, ha="center", weight="bold", margin={"b": 20}),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16, weight="bold"),
        legend_position="bottom",
        legend_direction="horizontal",
    )
    + guides(fill=guide_legend(override_aes={"size": 0.5}))
)

plot.save("plot.png", dpi=300, width=12, height=12, verbose=False)
