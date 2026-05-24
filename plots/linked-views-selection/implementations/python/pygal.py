"""anyplot.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: pygal | Python 3.13
Quality: pending | Updated: 2026-05-24
"""

import os
import sys


# Prioritize venv packages over the current directory (script is named pygal.py)
venv_path = [p for p in sys.path if ".venv" in p]
sys.path = venv_path + [p for p in sys.path if ".venv" not in p and p != ""]

import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from PIL import Image  # noqa: E402
from pygal.style import Style  # noqa: E402
from sklearn.datasets import load_iris  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

ANYPLOT_PALETTE = ("#009E73", "#9418DB", "#B71D27", "#16B8F3", "#99B314", "#D359A7", "#BA843E")

# Canvas layout (3200 × 1800 exact)
CANVAS_W, CANVAS_H = 3200, 1800
MARGIN, GAP = 40, 20
TOP_H = 860
BOT_H = CANVAS_H - 2 * MARGIN - TOP_H - GAP  # 840
HALF_W = (CANVAS_W - 2 * MARGIN - GAP) // 2  # 1550
FULL_W = CANVAS_W - 2 * MARGIN  # 3120

# Sub-chart style (sized for partial-canvas charts)
sub_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ANYPLOT_PALETTE,
    title_font_size=44,
    label_font_size=32,
    major_label_font_size=26,
    legend_font_size=26,
    value_font_size=20,
    stroke_width=2.5,
)

# Data: Iris dataset
iris = load_iris()
df = pd.DataFrame(iris.data, columns=["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"])
df["species"] = [iris.target_names[i] for i in iris.target]
means = df.groupby("species")[["Petal Length", "Sepal Length"]].mean()

# View 1 (top-left): Scatter — Petal Length vs Petal Width (clearest cluster separation)
scatter = pygal.XY(
    width=HALF_W,
    height=TOP_H,
    title="Petal Length vs Petal Width",
    x_title="Petal Length (cm)",
    y_title="Petal Width (cm)",
    style=sub_style,
    show_legend=True,
    dots_size=5,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
)
for sp in iris.target_names:
    sub = df[df["species"] == sp]
    scatter.add(sp, list(zip(sub["Petal Length"].round(2), sub["Petal Width"].round(2), strict=True)))
scatter_svg = scatter.render()
scatter.render_to_png(f"scatter-{THEME}.png")

# View 2 (top-right): Bar — mean Petal Length per species (confirms 1-D separation)
bar = pygal.Bar(
    width=HALF_W,
    height=TOP_H,
    title="Mean Petal Length by Species",
    y_title="Petal Length (cm)",
    style=sub_style,
    show_legend=True,
)
bar.x_labels = ["Mean Petal Length"]
for sp in iris.target_names:
    bar.add(sp, [round(means.loc[sp, "Petal Length"], 2)])
bar_svg = bar.render()
bar.render_to_png(f"bar-{THEME}.png")

# View 3 (bottom, full width): Box — Sepal Length distribution (species overlap visible)
title_main = "linked-views-selection · python · pygal · anyplot.ai"
box = pygal.Box(
    width=FULL_W,
    height=BOT_H,
    title=title_main,
    y_title="Sepal Length (cm)",
    style=sub_style,
    show_legend=True,
    box_mode="tukey",
)
for sp in iris.target_names:
    box.add(sp, df[df["species"] == sp]["Sepal Length"].tolist())
box_svg = box.render()
box.render_to_png(f"box-{THEME}.png")

# Composite PNG: exactly 3200 × 1800 px
page_bg_rgb = tuple(int(PAGE_BG.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), page_bg_rgb)

img_scatter = Image.open(f"scatter-{THEME}.png").resize((HALF_W, TOP_H), Image.LANCZOS)
img_bar = Image.open(f"bar-{THEME}.png").resize((HALF_W, TOP_H), Image.LANCZOS)
img_box = Image.open(f"box-{THEME}.png").resize((FULL_W, BOT_H), Image.LANCZOS)

canvas.paste(img_scatter, (MARGIN, MARGIN))
canvas.paste(img_bar, (MARGIN + HALF_W + GAP, MARGIN))
canvas.paste(img_box, (MARGIN, MARGIN + TOP_H + GAP))
canvas.save(f"plot-{THEME}.png")

# Interactive HTML with linked species selection
scatter_svg_str = scatter_svg.decode("utf-8")
bar_svg_str = bar_svg.decode("utf-8")
box_svg_str = box_svg.decode("utf-8")

html_open = (
    "<!DOCTYPE html>\n<html>\n<head>\n"
    '  <meta charset="utf-8">\n'
    "  <title>linked-views-selection · pygal · anyplot.ai</title>\n"
    "  <style>\n"
    "    * { margin: 0; padding: 0; box-sizing: border-box; }\n"
    "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;\n"
    "           background: " + PAGE_BG + "; color: " + INK + "; padding: 40px; }\n"
    "    h1 { font-size: 28px; font-weight: 600; margin-bottom: 6px; }\n"
    "    .subtitle { font-size: 14px; color: " + INK_MUTED + "; margin-bottom: 24px; }\n"
    "    .controls { display: flex; align-items: center; gap: 16px; margin-bottom: 28px;\n"
    "                background: " + ELEVATED_BG + "; padding: 16px 20px; border-radius: 8px; }\n"
    "    .controls label { font-size: 14px; color: " + INK_SOFT + "; font-weight: 600;\n"
    "                      margin-right: 4px; }\n"
    "    .sp-btn { border: 2px solid transparent; border-radius: 20px; padding: 6px 18px;\n"
    "              font-size: 14px; font-weight: 600; cursor: pointer; color: #fff;\n"
    "              transition: opacity 0.2s; }\n"
    "    .sp-btn.dim { opacity: 0.35; }\n"
    "    .sp-btn[data-idx='0'] { background: #009E73; }\n"
    "    .sp-btn[data-idx='1'] { background: #9418DB; }\n"
    "    .sp-btn[data-idx='2'] { background: #B71D27; }\n"
    "    .reset-btn { background: none; border: 1px solid " + INK_MUTED + ";\n"
    "                 color: " + INK + "; border-radius: 20px; padding: 6px 18px;\n"
    "                 font-size: 14px; cursor: pointer; margin-left: auto; }\n"
    "    .sel-info { font-size: 14px; color: " + INK_SOFT + "; }\n"
    "    .charts-top { display: grid; grid-template-columns: 1fr 1fr; gap: 20px;\n"
    "                  margin-bottom: 20px; }\n"
    "    .chart-wrap { background: " + PAGE_BG + "; border: 1px solid " + INK_MUTED + "20;\n"
    "                  border-radius: 6px; overflow: hidden; }\n"
    "    .chart-wrap svg { width: 100%; height: auto; display: block; }\n"
    "    .serie-dim .serie-0, .serie-dim .serie-1, .serie-dim .serie-2\n"
    "      { transition: opacity 0.25s; }\n"
    "  </style>\n</head>\n<body>\n"
    "  <h1>Multiple Linked Views with Selection Sync</h1>\n"
    '  <p class="subtitle">linked-views-selection · python · pygal · anyplot.ai</p>\n'
    '  <div class="controls">\n'
    "    <label>Filter by species:</label>\n"
    '    <button class="sp-btn" data-idx="0">setosa</button>\n'
    '    <button class="sp-btn" data-idx="1">versicolor</button>\n'
    '    <button class="sp-btn" data-idx="2">virginica</button>\n'
    '    <button class="reset-btn" onclick="resetAll()">Show all</button>\n'
    '    <span class="sel-info">Selected: <strong id="sel-label">All species</strong></span>\n'
    "  </div>\n"
    '  <div class="charts-top">\n'
    '    <div class="chart-wrap" id="scatter">\n'
)

html_mid1 = '\n    </div>\n    <div class="chart-wrap" id="bar">\n'

html_mid2 = '\n    </div>\n  </div>\n  <div class="chart-wrap" id="box">\n'

html_close = (
    "\n  </div>\n\n"
    "  <script>\n"
    "    const SPECIES = ['setosa', 'versicolor', 'virginica'];\n"
    "    let active = new Set([0, 1, 2]);\n\n"
    "    function applySelection() {\n"
    "      ['scatter', 'bar', 'box'].forEach(function(id) {\n"
    "        var wrap = document.getElementById(id);\n"
    "        if (!wrap) return;\n"
    "        for (var i = 0; i < 3; i++) {\n"
    "          var els = wrap.querySelectorAll('.serie-' + i);\n"
    "          var show = active.has(i);\n"
    "          els.forEach(function(el) {\n"
    "            el.style.opacity = show ? '1' : '0.08';\n"
    "            el.style.transition = 'opacity 0.25s';\n"
    "          });\n"
    "        }\n"
    "      });\n"
    "      var btns = document.querySelectorAll('.sp-btn');\n"
    "      btns.forEach(function(b) {\n"
    "        var idx = parseInt(b.getAttribute('data-idx'));\n"
    "        b.classList.toggle('dim', !active.has(idx));\n"
    "      });\n"
    "      var label = active.size === 3 ? 'All species'\n"
    "        : Array.from(active).map(function(i) { return SPECIES[i]; }).join(', ');\n"
    "      document.getElementById('sel-label').textContent = label;\n"
    "    }\n\n"
    "    function resetAll() {\n"
    "      active = new Set([0, 1, 2]);\n"
    "      applySelection();\n"
    "    }\n\n"
    "    document.querySelectorAll('.sp-btn').forEach(function(btn) {\n"
    "      btn.addEventListener('click', function() {\n"
    "        var idx = parseInt(this.getAttribute('data-idx'));\n"
    "        if (active.has(idx)) {\n"
    "          if (active.size > 1) active.delete(idx);\n"
    "        } else {\n"
    "          active.add(idx);\n"
    "        }\n"
    "        applySelection();\n"
    "      });\n"
    "    });\n\n"
    "    applySelection();\n"
    "  </script>\n"
    "</body>\n</html>"
)

html_content = html_open + scatter_svg_str + html_mid1 + bar_svg_str + html_mid2 + box_svg_str + html_close

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
