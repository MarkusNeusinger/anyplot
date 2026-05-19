"""anyplot.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-19
"""

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# Ensure we import the pygal package, not this file (filename collision)
_this_dir = Path(__file__).parent
if str(_this_dir) in sys.path:
    sys.path.remove(str(_this_dir))

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
PIL_BG = (250, 248, 241) if THEME == "light" else (26, 26, 23)

# Okabe-Ito palette — position 1 (#009E73) is always first series
OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data: file-system storage allocation (GB) — 4 top-level folders, 3 sub-folders each
hierarchy = [
    {"id": "root", "parent": "", "label": "Storage (240 GB)", "value": 0},
    # Top-level categories
    {"id": "media", "parent": "root", "label": "Media", "value": 0},
    {"id": "documents", "parent": "root", "label": "Documents", "value": 0},
    {"id": "apps", "parent": "root", "label": "Applications", "value": 0},
    {"id": "system", "parent": "root", "label": "System", "value": 0},
    # Media sub-folders
    {"id": "videos", "parent": "media", "label": "Videos", "value": 52},
    {"id": "photos", "parent": "media", "label": "Photos", "value": 24},
    {"id": "music", "parent": "media", "label": "Music", "value": 12},
    # Documents sub-folders
    {"id": "work", "parent": "documents", "label": "Work Docs", "value": 22},
    {"id": "personal", "parent": "documents", "label": "Personal", "value": 16},
    {"id": "archived", "parent": "documents", "label": "Archived", "value": 14},
    # Applications sub-folders
    {"id": "productivity", "parent": "apps", "label": "Productivity", "value": 28},
    {"id": "games", "parent": "apps", "label": "Games", "value": 22},
    {"id": "devtools", "parent": "apps", "label": "Dev Tools", "value": 18},
    # System sub-folders
    {"id": "os", "parent": "system", "label": "OS", "value": 16},
    {"id": "cache", "parent": "system", "label": "Cache", "value": 10},
    {"id": "logs", "parent": "system", "label": "Logs", "value": 6},
]

# Calculate parent sums bottom-up
for node in reversed(hierarchy):
    if node["value"] == 0:
        node["value"] = sum(n["value"] for n in hierarchy if n["parent"] == node["id"])

# Sub-folder colors: tints of each Okabe-Ito category (data colors are theme-invariant)
sub_colors = {
    "videos": "#009E73",
    "photos": "#4DBB9D",
    "music": "#99D7C7",
    "work": "#D55E00",
    "personal": "#E28B4D",
    "archived": "#EEB899",
    "productivity": "#0072B2",
    "games": "#4D9EC9",
    "devtools": "#99C9E0",
    "os": "#CC79A7",
    "cache": "#DAA0C0",
    "logs": "#E8C7D8",
}

categories = [n for n in hierarchy if n["parent"] == "root"]

# Pygal style for HTML charts (interactive, 1600×900)
html_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Pygal style for PNG charts (large canvas, ~2300×2400 each half)
png_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=64,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=28,
    value_label_font_size=28,
    stroke_width=4,
)

# --- HTML: interactive toggle view ---

html_treemap = pygal.Treemap(
    width=1600,
    height=900,
    style=html_style,
    title="Treemap — Disk Storage by Folder",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"{x} GB",
)
for cat in categories:
    items = [n for n in hierarchy if n["parent"] == cat["id"]]
    html_treemap.add(
        f"{cat['label']} ({cat['value']} GB)",
        [{"value": t["value"], "label": t["label"], "color": sub_colors[t["id"]]} for t in items],
    )

html_sunburst = pygal.Pie(
    width=1600,
    height=900,
    style=html_style,
    title="Sunburst — Disk Storage Hierarchy",
    inner_radius=0.35,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    print_values=True,
    value_formatter=lambda x: f"{x} GB",
)
for cat in categories:
    items = [n for n in hierarchy if n["parent"] == cat["id"]]
    for item in items:
        html_sunburst.add(
            f"{cat['label']}: {item['label']}", [{"value": item["value"], "color": sub_colors[item["id"]]}]
        )

treemap_svg = html_treemap.render(is_unicode=True)
sunburst_svg = html_sunburst.render(is_unicode=True)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Disk Storage · hierarchy-toggle-view · python · pygal · anyplot.ai</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; background: {PAGE_BG}; color: {INK}; padding: 24px; }}
    .container {{ max-width: 1600px; margin: 0 auto; }}
    h1 {{ text-align: center; color: {OKABE_ITO[0]}; font-size: 26px; margin-bottom: 8px; }}
    .subtitle {{ text-align: center; color: {INK_MUTED}; font-size: 15px; margin-bottom: 22px; }}
    .toggle {{ text-align: center; margin-bottom: 18px; }}
    .btn {{
      padding: 10px 30px; font-size: 15px; margin: 0 6px; cursor: pointer;
      border: 2px solid {OKABE_ITO[0]}; background: {PAGE_BG}; color: {OKABE_ITO[0]};
      border-radius: 6px; font-weight: bold; transition: background 0.2s, color 0.2s;
    }}
    .btn.active {{ background: {OKABE_ITO[0]}; color: {PAGE_BG}; }}
    .chart {{ display: none; width: 100%; }}
    .chart.active {{ display: block; }}
    .chart svg {{ max-width: 100%; height: auto; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Disk Storage · hierarchy-toggle-view · python · pygal · anyplot.ai</h1>
    <p class="subtitle">240 GB total — toggle between rectangular (Treemap) and radial (Sunburst) views</p>
    <div class="toggle">
      <button class="btn active" id="btn-treemap" onclick="switchView('treemap')">&#9632; Treemap</button>
      <button class="btn" id="btn-sunburst" onclick="switchView('sunburst')">&#9685; Sunburst</button>
    </div>
    <div id="treemap" class="chart active">{treemap_svg}</div>
    <div id="sunburst" class="chart">{sunburst_svg}</div>
  </div>
  <script>
    var VIEWS = ['treemap', 'sunburst'];
    function switchView(id) {{
      var current = document.querySelector('.chart.active');
      var next = document.getElementById(id);
      if (current === next) return;
      // Fade out current
      current.style.transition = 'opacity 0.3s';
      current.style.opacity = '0';
      setTimeout(function() {{
        current.style.display = 'none';
        current.classList.remove('active');
        current.style.opacity = '';
        current.style.transition = '';
        // Fade in next
        next.style.opacity = '0';
        next.style.display = 'block';
        next.classList.add('active');
        requestAnimationFrame(function() {{
          requestAnimationFrame(function() {{
            next.style.transition = 'opacity 0.3s';
            next.style.opacity = '1';
            setTimeout(function() {{
              next.style.opacity = '';
              next.style.transition = '';
            }}, 310);
          }});
        }});
      }}, 310);
      // Update buttons immediately
      VIEWS.forEach(function(v) {{
        document.getElementById('btn-' + v).classList.remove('active');
      }});
      document.getElementById('btn-' + id).classList.add('active');
    }}
  </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# --- PNG: side-by-side static view (4800×2700 canvas) ---

png_treemap = pygal.Treemap(
    width=2300,
    height=2400,
    style=png_style,
    title="Treemap View",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"{x} GB",
    margin_left=20,
    margin_right=20,
)
for cat in categories:
    items = [n for n in hierarchy if n["parent"] == cat["id"]]
    png_treemap.add(
        cat["label"], [{"value": t["value"], "label": t["label"], "color": sub_colors[t["id"]]} for t in items]
    )

png_sunburst = pygal.Pie(
    width=2300,
    height=2400,
    style=png_style,
    title="Sunburst View",
    inner_radius=0.35,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    print_values=True,
    value_formatter=lambda x: f"{x} GB",
    margin_left=20,
    margin_right=20,
)
for cat in categories:
    items = [n for n in hierarchy if n["parent"] == cat["id"]]
    for item in items:
        png_sunburst.add(item["label"], [{"value": item["value"], "color": sub_colors[item["id"]]}])

png_treemap.render_to_png("treemap_tmp.png")
png_sunburst.render_to_png("sunburst_tmp.png")

# Assemble 4800×2700 canvas
combined = Image.new("RGB", (4800, 2700), PIL_BG)
draw = ImageDraw.Draw(combined)

try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
except OSError:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()

title_str = "Disk Storage · hierarchy-toggle-view · python · pygal · anyplot.ai"
tw = draw.textbbox((0, 0), title_str, font=font_title)
draw.text(((4800 - (tw[2] - tw[0])) // 2, 40), title_str, fill=OKABE_ITO[0], font=font_title)

sub_str = "240 GB total — Treemap excels at size comparison; Sunburst reveals hierarchy depth"
sw = draw.textbbox((0, 0), sub_str, font=font_sub)
draw.text(((4800 - (sw[2] - sw[0])) // 2, 140), sub_str, fill=INK_MUTED, font=font_sub)

treemap_img = Image.open("treemap_tmp.png").resize((2200, 2400), Image.Resampling.LANCZOS)
combined.paste(treemap_img, (100, 250))

sunburst_img = Image.open("sunburst_tmp.png").resize((2200, 2400), Image.Resampling.LANCZOS)
combined.paste(sunburst_img, (2500, 250))

combined.save(f"plot-{THEME}.png", "PNG")

os.remove("treemap_tmp.png")
os.remove("sunburst_tmp.png")
