"""anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
"""

import os
import sys
import time
from pathlib import Path


# Remove the current directory from sys.path to avoid circular imports with bokeh.py
sys.path = [p for p in sys.path if p not in ("", ".", os.getcwd(), os.path.dirname(__file__))]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, Label, Span  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # data series and fit
ULT_COLOR = IMPRINT_PALETTE[1]  # Ultimate Strength line
ENDU_COLOR = IMPRINT_PALETTE[2]  # Endurance Limit line
YIELD_COLOR = IMPRINT_PALETTE[3]  # Yield Strength line

# Constants: steel properties that stay true for any test series
ULTIMATE_STRENGTH = 500  # MPa
YIELD_STRENGTH = 350  # MPa
ENDURANCE_LIMIT = 200  # MPa

# Columns: set these to your table's column names
CYCLES = "Number of Cycles to Failure (N)"  # role: cycles
STRESS = "Stress Amplitude (MPa)"  # role: stress

# Data: replace this block with your own table, for example df = pd.read_csv("fatigue_tests.csv")
np.random.seed(42)
basquin_a = 1200  # MPa coefficient
basquin_b = -0.12  # Basquin exponent
stress_levels = np.array([450, 400, 350, 320, 300, 280, 260, 250, 240, 230, 220, 210])
specimens = np.random.randint(2, 5, size=len(stress_levels))
stress_values = np.repeat(stress_levels, specimens)
cycles_values = (stress_values / basquin_a) ** (1 / basquin_b) * np.random.lognormal(0, 0.3, len(stress_values))
df = pd.DataFrame({CYCLES: cycles_values, STRESS: stress_values})

# Plot: reads only df and the constants above
# Basquin fit S = A * N^b, a straight line in log-log space
valid = df[[CYCLES, STRESS]].dropna()
slope, intercept = np.polyfit(np.log10(valid[CYCLES]), np.log10(valid[STRESS]), 1)
x_low = 10 ** (np.floor(np.log10(df[CYCLES].min())) - 1)
x_high = 10 ** (np.ceil(np.log10(df[CYCLES].max())) + 0.3)
y_low = ENDURANCE_LIMIT * 0.75
y_high = ULTIMATE_STRENGTH * 1.3
cycles_fit = np.logspace(np.log10(x_low), np.log10(x_high), 100)
fit_a = 10**intercept

source = ColumnDataSource(df)
source_fit = ColumnDataSource(data={"cycles_fit": cycles_fit, "stress_fit": fit_a * cycles_fit**slope})

p = figure(
    width=3200,
    height=1800,
    title="sn-curve-basic · python · bokeh · anyplot.ai",
    x_axis_label=CYCLES,
    y_axis_label=STRESS,
    x_axis_type="log",
    y_axis_type="log",
    y_range=(y_low, y_high),
    x_range=(x_low, x_high),
    toolbar_location=None,
    min_border_bottom=220,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Infinite-life zone shaded below the endurance limit
p.add_layout(BoxAnnotation(top=ENDURANCE_LIMIT, bottom=y_low, fill_color=ENDU_COLOR, fill_alpha=0.12, line_color=None))

p.line(
    x="cycles_fit",
    y="stress_fit",
    source=source_fit,
    line_width=7,
    line_color=BRAND,
    line_alpha=0.9,
    legend_label=f"Basquin Fit (S = {fit_a:.0f}·N^{slope:.3f})",
)

p.scatter(
    x=CYCLES,
    y=STRESS,
    source=source,
    size=18,
    fill_color=BRAND,
    fill_alpha=0.65,
    line_color=PAGE_BG,
    line_width=1.5,
    legend_label="Fatigue Test Data",
)

hover = HoverTool(
    tooltips=[("Cycles to Failure", f"@{{{CYCLES}}}{{0.00e+0}}"), ("Stress Amplitude", f"@{{{STRESS}}}{{0}} MPa")]
)
p.add_tools(hover)

# Reference lines for material properties, labeled in the sparse left area
for name, level, color, lift in (
    ("Ultimate Strength", ULTIMATE_STRENGTH, ULT_COLOR, 1.07),
    ("Yield Strength", YIELD_STRENGTH, YIELD_COLOR, 1.05),
    ("Endurance Limit", ENDURANCE_LIMIT, ENDU_COLOR, 1.05),
):
    p.add_layout(Span(location=level, dimension="width", line_color=color, line_width=3, line_dash="dashed"))
    below = level == ENDURANCE_LIMIT  # infinite-life label stays left; the fit line passes the left side of the others
    suffix = "  ← infinite life" if below else ""
    p.add_layout(
        Label(
            x=x_low * 1.5 if below else x_high / 1.5,
            y=level * lift,
            text_align="left" if below else "right",
            text=f"{name} ({level} MPa){suffix}",
            text_font_size="28pt",
            text_color=color,
            text_font_style="bold",
        )
    )

# Style — font sizes per default-style-guide.md "Visual Sizing Defaults" for bokeh
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Y-only grid for cleaner line+scatter chart
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.legend.location = "bottom_left"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.glyph_width = 55
p.legend.glyph_height = 40
p.legend.spacing = 18
p.legend.padding = 24

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Save PNG via headless Chrome (Selenium)
W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)

driver = webdriver.Chrome(options=opts)
# Override emulated viewport to exactly W×H regardless of browser chrome overhead
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
