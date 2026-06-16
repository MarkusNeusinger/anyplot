""" anyplot.ai
network-bipartite: Bipartite Network Graph
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Created: 2026-05-14
"""

import os
from collections import defaultdict

import numpy as np
import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

STUDENT_COLOR = "#009E73"  # Okabe-Ito position 1
COURSE_COLOR = "#C475FD"  # Okabe-Ito position 2
EDGE_COLOR = "rgba(107,106,99,0.30)" if THEME == "light" else "rgba(168,167,159,0.22)"

# Data - student-course enrollment network
np.random.seed(42)

students = ["Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace", "Henry", "Iris", "Jack", "Karen", "Leo"]
courses = [
    "Algorithms",
    "Data Structures",
    "Machine Learning",
    "Statistics",
    "Linear Algebra",
    "Databases",
    "Networks",
    "Computer Vision",
]

# (student_idx, course_idx, weight) — weight encodes credit overlap strength
enrollments = [
    (0, 0, 3),
    (0, 1, 4),
    (0, 2, 4),
    (0, 3, 3),
    (0, 4, 2),  # Alice: 5 courses
    (1, 0, 3),
    (1, 5, 3),
    (1, 7, 2),
    (2, 2, 4),
    (2, 3, 3),
    (2, 6, 2),
    (3, 1, 3),
    (3, 4, 3),
    (3, 6, 2),
    (4, 0, 2),
    (4, 2, 3),
    (4, 7, 3),
    (5, 5, 3),
    (5, 6, 3),
    (5, 7, 4),
    (6, 1, 2),
    (6, 3, 4),
    (6, 4, 2),
    (7, 2, 4),
    (7, 5, 3),
    (7, 6, 2),
    (8, 0, 3),
    (8, 1, 2),
    (8, 3, 3),
    (8, 7, 4),  # Iris: 4 courses
    (9, 4, 3),
    (9, 6, 3),  # Jack: 2 courses
    (10, 5, 2),
    (10, 7, 3),  # Karen: 2 courses
    (11, 3, 3),
    (11, 6, 2),
    (11, 7, 4),
]

# Degree per node
student_degree = [0] * len(students)
course_degree = [0] * len(courses)
for s_i, c_i, _ in enrollments:
    student_degree[s_i] += 1
    course_degree[c_i] += 1

# Node positions: students on left (x=0), courses on right (x=1)
student_y = np.linspace(0.05, 0.95, len(students))
course_y = np.linspace(0.10, 0.90, len(courses))

# Edge traces grouped by weight for variable line width
weight_groups = defaultdict(list)
for s_i, c_i, w in enrollments:
    weight_groups[w].append((s_i, c_i))

traces = []
for w, pairs in sorted(weight_groups.items()):
    xs, ys = [], []
    for s_i, c_i in pairs:
        xs += [0.0, 1.0, None]
        ys += [float(student_y[s_i]), float(course_y[c_i]), None]
    traces.append(
        go.Scatter(
            x=xs, y=ys, mode="lines", line={"width": w * 0.9, "color": EDGE_COLOR}, hoverinfo="none", showlegend=False
        )
    )

# Node size: linear scale on degree
s_min, s_max = min(student_degree), max(student_degree)
student_sizes = [22 + (d - s_min) / (s_max - s_min) * 28 for d in student_degree]

c_min, c_max = min(course_degree), max(course_degree)
course_sizes = [22 + (d - c_min) / (c_max - c_min) * 28 for d in course_degree]

traces.append(
    go.Scatter(
        x=[0.0] * len(students),
        y=list(student_y),
        mode="markers+text",
        marker={"size": student_sizes, "color": STUDENT_COLOR, "line": {"color": PAGE_BG, "width": 2}},
        text=students,
        textposition="middle left",
        textfont={"size": 16, "color": INK},
        name="Students",
        customdata=student_degree,
        hovertemplate="<b>%{text}</b><br>Enrolled in %{customdata} courses<extra></extra>",
    )
)

traces.append(
    go.Scatter(
        x=[1.0] * len(courses),
        y=list(course_y),
        mode="markers+text",
        marker={"size": course_sizes, "color": COURSE_COLOR, "line": {"color": PAGE_BG, "width": 2}},
        text=courses,
        textposition="middle right",
        textfont={"size": 16, "color": INK},
        name="Courses",
        customdata=course_degree,
        hovertemplate="<b>%{text}</b><br>%{customdata} students enrolled<extra></extra>",
    )
)

fig = go.Figure(data=traces)

fig.update_layout(
    title={
        "text": "Student-Course Enrollment · network-bipartite · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 16, "color": INK_SOFT},
        "orientation": "h",
        "x": 0.5,
        "xanchor": "center",
        "y": -0.04,
    },
    xaxis={"range": [-0.55, 1.55], "showgrid": False, "zeroline": False, "showticklabels": False, "showline": False},
    yaxis={"range": [-0.05, 1.12], "showgrid": False, "zeroline": False, "showticklabels": False, "showline": False},
    margin={"l": 20, "r": 20, "t": 80, "b": 60},
)

# Column headers
fig.add_annotation(
    x=0.0, y=1.07, text="<b>Students</b>", font={"size": 22, "color": INK}, showarrow=False, xref="x", yref="y"
)
fig.add_annotation(
    x=1.0, y=1.07, text="<b>Courses</b>", font={"size": 22, "color": INK}, showarrow=False, xref="x", yref="y"
)

# Subtle vertical separator
fig.add_shape(
    type="line",
    x0=0.5,
    x1=0.5,
    y0=0.0,
    y1=1.0,
    xref="x",
    yref="paper",
    line={"color": INK_SOFT, "width": 1, "dash": "dot"},
)

fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
