"""anyplot.ai
network-bipartite: Bipartite Network Graph
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Created: 2026-05-14
"""

import sys


sys.path.pop(0)  # prevent bokeh.py from shadowing the bokeh package

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_A, COLOR_B = IMPRINT_PALETTE[0], IMPRINT_PALETTE[1]

# Canvas
W, H = 3200, 1800

# Columns
SOURCE = "Student"  # role: source
TARGET = "Course"  # role: target

# Data: student-course enrollment, one row per edge; replace with your own table,
# for example df = pd.read_csv("enrollments.csv")
rng = np.random.default_rng(42)
student_names = ["Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace", "Henry"]
student_names += ["Iris", "James", "Kate", "Liam", "Maya", "Noah", "Olivia"]
course_names = ["CS101", "MATH201", "PHYS101", "BIO201", "CHEM101", "ENG101"]
course_names += ["HIST201", "ART101", "CS201", "STAT101", "ECON201", "MUSIC101"]
popularity = np.array([3, 3, 2, 2, 2, 2, 1, 1, 2, 2, 1, 1], dtype=float)
popularity /= popularity.sum()
rows = []
for student in student_names:
    n_enroll = rng.integers(2, 6)
    for c in rng.choice(len(course_names), size=n_enroll, replace=False, p=popularity):
        rows.append((student, course_names[c]))
df = pd.DataFrame(rows, columns=[SOURCE, TARGET])

# Plot
students = list(df[SOURCE].unique())
courses = list(df[TARGET].unique())
n_s, n_c = len(students), len(courses)
s_degree = df[SOURCE].value_counts().reindex(students).to_numpy(dtype=float)
c_degree = df[TARGET].value_counts().reindex(courses).to_numpy(dtype=float)

# Layout: set A left, set B right
X_LEFT, X_RIGHT = 0.22, 0.78
s_y = np.linspace(0.92, 0.05, n_s)
c_y = np.linspace(0.92, 0.05, n_c)
s_pos = dict(zip(students, s_y, strict=True))
c_pos = dict(zip(courses, c_y, strict=True))

# Node sizes proportional to degree
s_sizes = 20 + 46 * s_degree / s_degree.max()
c_sizes = 20 + 46 * c_degree / c_degree.max()

p = figure(
    width=W,
    height=H,
    x_range=(-0.05, 1.05),
    y_range=(-0.02, 1.08),
    toolbar_location=None,
    tools="",
    title="Student-Course Enrollment \u00b7 network-bipartite \u00b7 python \u00b7 bokeh \u00b7 anyplot.ai",
    min_border_top=40,
    min_border_bottom=20,
    min_border_left=20,
    min_border_right=20,
)

# Edges
p.segment(
    x0=[X_LEFT] * len(df),
    y0=df[SOURCE].map(s_pos).tolist(),
    x1=[X_RIGHT] * len(df),
    y1=df[TARGET].map(c_pos).tolist(),
    line_color=INK_MUTED,
    line_alpha=0.35,
    line_width=2,
)

# Nodes
p.scatter(
    x=[X_LEFT] * n_s, y=s_y.tolist(), size=s_sizes.tolist(), color=COLOR_A, line_color=PAGE_BG, line_width=3, alpha=0.92
)
p.scatter(
    x=[X_RIGHT] * n_c,
    y=c_y.tolist(),
    size=c_sizes.tolist(),
    color=COLOR_B,
    line_color=PAGE_BG,
    line_width=3,
    alpha=0.92,
)

# Labels on the outer side of each column
p.text(
    x=[X_LEFT - 0.03] * n_s,
    y=s_y.tolist(),
    text=students,
    text_align="right",
    text_baseline="middle",
    text_font_size="24pt",
    text_color=INK_SOFT,
)
p.text(
    x=[X_RIGHT + 0.03] * n_c,
    y=c_y.tolist(),
    text=courses,
    text_align="left",
    text_baseline="middle",
    text_font_size="24pt",
    text_color=INK_SOFT,
)

# Column headers naming each set
p.text(
    x=[X_LEFT, X_RIGHT],
    y=[1.03, 1.03],
    text=[SOURCE + "s", TARGET + "s"],
    text_align="center",
    text_baseline="middle",
    text_font_size="32pt",
    text_font_style="bold",
    text_color=[COLOR_A, COLOR_B],
)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.title.text_font_size = "40pt"
p.title.text_color = INK
p.title.text_font_style = "normal"

# Save HTML + PNG
output_file(f"plot-{THEME}.html")
save(p)

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
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
