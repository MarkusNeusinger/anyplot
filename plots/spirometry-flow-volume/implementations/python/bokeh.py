""" pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-18
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem
from bokeh.plotting import figure


# Data - Spirometry flow-volume loop (measured vs predicted normal)
np.random.seed(42)
n_points = 150

# Forced Vital Capacity and Peak Expiratory Flow parameters
fvc_measured = 4.2  # liters
pef_measured = 9.5  # L/s
fev1_measured = 3.3  # liters (volume at 1 second)

fvc_predicted = 4.8  # liters
pef_predicted = 10.8  # L/s

# Expiratory limb (measured): sharp rise to PEF then roughly linear decline
volume_exp = np.linspace(0, fvc_measured, n_points)
# Sharp rise phase then linear decline
t_exp = volume_exp / fvc_measured
# PEF occurs early (~10-15% of FVC)
pef_fraction = 0.12
rise = pef_measured * np.sin(np.pi / 2 * t_exp / pef_fraction)
decline = pef_measured * (1 - (t_exp - pef_fraction) / (1 - pef_fraction))
flow_exp = np.where(t_exp <= pef_fraction, rise, decline)
flow_exp = np.maximum(flow_exp, 0.0)
# Add slight concavity to decline for realism
flow_exp[t_exp > pef_fraction] *= 1 - 0.15 * ((t_exp[t_exp > pef_fraction] - pef_fraction) / (1 - pef_fraction)) ** 2

# Inspiratory limb (measured): symmetric U-shape below zero
volume_insp = np.linspace(fvc_measured, 0, n_points)
t_insp = np.linspace(0, 1, n_points)
peak_insp_flow = -6.5  # L/s (negative = inspiratory)
flow_insp = peak_insp_flow * np.sin(np.pi * t_insp)

# Predicted normal - expiratory
volume_pred_exp = np.linspace(0, fvc_predicted, n_points)
t_pred_exp = volume_pred_exp / fvc_predicted
pef_frac_pred = 0.10
rise_pred = pef_predicted * np.sin(np.pi / 2 * t_pred_exp / pef_frac_pred)
decline_pred = pef_predicted * (1 - (t_pred_exp - pef_frac_pred) / (1 - pef_frac_pred))
flow_pred_exp = np.where(t_pred_exp <= pef_frac_pred, rise_pred, decline_pred)
flow_pred_exp = np.maximum(flow_pred_exp, 0.0)
flow_pred_exp[t_pred_exp > pef_frac_pred] *= (
    1 - 0.12 * ((t_pred_exp[t_pred_exp > pef_frac_pred] - pef_frac_pred) / (1 - pef_frac_pred)) ** 2
)

# Predicted normal - inspiratory
volume_pred_insp = np.linspace(fvc_predicted, 0, n_points)
t_pred_insp = np.linspace(0, 1, n_points)
peak_insp_pred = -7.5
flow_pred_insp = peak_insp_pred * np.sin(np.pi * t_pred_insp)

# Combine measured loop into single arrays for closed shape
volume_measured = np.concatenate([volume_exp, volume_insp])
flow_measured = np.concatenate([flow_exp, flow_insp])

volume_predicted = np.concatenate([volume_pred_exp, volume_pred_insp])
flow_predicted = np.concatenate([flow_pred_exp, flow_pred_insp])

# ColumnDataSources
source_measured = ColumnDataSource(data={"volume": volume_measured, "flow": flow_measured})
source_predicted = ColumnDataSource(data={"volume": volume_predicted, "flow": flow_predicted})

# Find PEF point on measured curve
pef_idx = np.argmax(flow_exp)
pef_volume = volume_exp[pef_idx]
pef_flow = flow_exp[pef_idx]

# Find FEV1 point (volume = ~FEV1 on expiratory limb)
fev1_idx = np.argmin(np.abs(volume_exp - fev1_measured))
fev1_flow = flow_exp[fev1_idx]

# Plot
p = figure(
    width=4800,
    height=2700,
    title="spirometry-flow-volume · bokeh · pyplots.ai",
    x_axis_label="Volume (L)",
    y_axis_label="Flow (L/s)",
)

# Filled patch between measured and predicted expiratory limbs to highlight diagnostic gap
# Interpolate predicted flow at measured volume points for consistent comparison
pred_exp_interp = np.interp(volume_exp, volume_pred_exp, flow_pred_exp)
patch_vol = np.concatenate([volume_exp, volume_exp[::-1]])
patch_flow = np.concatenate([flow_exp, pred_exp_interp[::-1]])
p.patch(x=patch_vol, y=patch_flow, fill_color="#306998", fill_alpha=0.08, line_color=None)

# Predicted loop (dashed, background)
r_pred = p.line(
    x="volume",
    y="flow",
    source=source_predicted,
    line_color="#777777",
    line_width=4.5,
    line_dash="dashed",
    line_alpha=0.8,
)

# Measured loop (solid, foreground)
r_meas = p.line(x="volume", y="flow", source=source_measured, line_color="#306998", line_width=5)

# PEF marker
p.scatter(x=[pef_volume], y=[pef_flow], size=22, fill_color="#e63946", line_color="white", line_width=3)

pef_label = Label(
    x=pef_volume,
    y=pef_flow,
    text=f"PEF = {pef_measured:.1f} L/s",
    text_font_size="24pt",
    text_color="#e63946",
    text_font_style="bold",
    x_offset=20,
    y_offset=25,
)
p.add_layout(pef_label)

# FEV1 marker on expiratory limb
p.scatter(x=[fev1_measured], y=[fev1_flow], size=18, fill_color="#457b9d", line_color="white", line_width=3)

fev1_label = Label(
    x=fev1_measured,
    y=fev1_flow,
    text=f"FEV1 = {fev1_measured:.1f} L",
    text_font_size="24pt",
    text_color="#457b9d",
    text_font_style="bold",
    x_offset=20,
    y_offset=-35,
)
p.add_layout(fev1_label)

# Clinical values text box
clinical_text = Label(
    x=fvc_measured * 0.55,
    y=-4.5,
    text=f"FVC = {fvc_measured:.1f} L  |  FEV1 = {fev1_measured:.1f} L  |  FEV1/FVC = {fev1_measured / fvc_measured:.0%}  |  PEF = {pef_measured:.1f} L/s",
    text_font_size="24pt",
    text_color="#2b2d42",
    text_font_style="bold",
)
p.add_layout(clinical_text)

# Zero flow reference line
p.line(
    x=[-0.2, max(fvc_measured, fvc_predicted) + 0.3], y=[0, 0], line_color="#aaaaaa", line_width=2, line_dash="dotted"
)

# Legend
legend = Legend(
    items=[LegendItem(label="Measured", renderers=[r_meas]), LegendItem(label="Predicted Normal", renderers=[r_pred])],
    location="top_right",
    label_text_font_size="24pt",
    glyph_width=60,
    glyph_height=30,
    spacing=15,
    padding=20,
    background_fill_alpha=0.85,
    border_line_alpha=0.3,
)
p.add_layout(legend)

# Hover tool
hover = HoverTool(tooltips=[("Volume", "@volume{0.2f} L"), ("Flow", "@flow{0.2f} L/s")], mode="mouse")
p.add_tools(hover)

# Style
p.title.text_font_size = "42pt"
p.title.text_color = "#1a1a2e"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "26pt"

# Grid - only y-grid for flow reading axis, remove x-grid for cleaner look
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.18
p.ygrid.grid_line_dash = [4, 4]
p.ygrid.grid_line_color = "#888888"

# Clean frame
p.outline_line_color = None
p.toolbar_location = None
p.background_fill_color = "#fafafa"

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2
p.xaxis.axis_line_color = "#444444"
p.yaxis.axis_line_color = "#444444"

# Margins
p.min_border_left = 150
p.min_border_bottom = 120
p.min_border_top = 100
p.min_border_right = 150

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
