"""anyplot.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-23
"""

import io
import os
import sys


# Prevent this file (pygal.py) from shadowing the installed pygal package
_self_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p != _self_dir]

import numpy as np
import pygal
from PIL import Image
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

ANYPLOT_PALETTE = ("#009E73", "#9418DB", "#B71D27", "#16B8F3", "#99B314", "#D359A7", "#BA843E")

# Data: 200 trading days with price, volume, and RSI
np.random.seed(42)
n_days = 200
dates = [f"Day {i + 1}" for i in range(n_days)]
returns = np.random.randn(n_days) * 0.02
price = 100 * np.cumprod(1 + returns)
volume = (np.abs(np.random.randn(n_days)) * 1e6 + 5e5) * (1 + np.abs(returns) * 10)
rsi = np.clip(50 + np.cumsum(np.random.randn(n_days) * 2), 0, 100)

# Panel dimensions — widths=3200, heights sum to 1800
W, H_PRICE, H_VOLUME, H_RSI = 3200, 680, 540, 580

# Price chart — full anyplot title, pos-1 green (#009E73)
price_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ANYPLOT_PALETTE,
    title_font_size=48,
    label_font_size=36,
    major_label_font_size=30,
    legend_font_size=30,
    value_font_size=26,
    stroke_width=3,
)
price_chart = pygal.Line(
    width=W,
    height=H_PRICE,
    style=price_style,
    title="dashboard-synchronized-crosshair · python · pygal · anyplot.ai",
    y_title="Price ($)",
    show_x_labels=False,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    dots_size=0,
    fill=False,
    truncate_label=-1,
    margin_top=60,
    margin_bottom=10,
    margin_left=150,
    margin_right=60,
)
price_chart.add("Price", price.tolist())
price_chart.x_labels = dates

# Volume chart — pos-2 purple (#9418DB)
volume_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=("#9418DB", "#009E73", "#B71D27", "#16B8F3", "#99B314", "#D359A7", "#BA843E"),
    title_font_size=40,
    label_font_size=36,
    major_label_font_size=30,
    legend_font_size=30,
    value_font_size=26,
    stroke_width=3,
)
volume_chart = pygal.Line(
    width=W,
    height=H_VOLUME,
    style=volume_style,
    title="Trading Volume",
    y_title="Volume (M)",
    show_x_labels=False,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    dots_size=0,
    fill=True,
    truncate_label=-1,
    margin_top=30,
    margin_bottom=10,
    margin_left=150,
    margin_right=60,
)
volume_chart.add("Volume", (volume / 1e6).tolist())
volume_chart.x_labels = dates

# RSI chart — pos-3 red (#B71D27), x-axis visible on bottom panel
rsi_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=("#B71D27", "#009E73", "#9418DB", "#16B8F3", "#99B314", "#D359A7", "#BA843E"),
    title_font_size=40,
    label_font_size=36,
    major_label_font_size=30,
    legend_font_size=30,
    value_font_size=26,
    stroke_width=3,
)
rsi_chart = pygal.Line(
    width=W,
    height=H_RSI,
    style=rsi_style,
    title="RSI Indicator",
    x_title="Trading Day",
    y_title="RSI (0–100)",
    show_x_labels=True,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    dots_size=0,
    fill=False,
    truncate_label=-1,
    x_labels_major_count=10,
    show_minor_x_labels=False,
    x_label_rotation=20,
    range=(0, 100),
    margin_top=30,
    margin_bottom=40,
    margin_left=150,
    margin_right=60,
)
rsi_chart.add("RSI", rsi.tolist())
rsi_chart.x_labels = dates

# Render SVGs for the interactive HTML
price_svg = price_chart.render(is_unicode=True)
volume_svg = volume_chart.render(is_unicode=True)
rsi_svg = rsi_chart.render(is_unicode=True)

price_js = price.tolist()
volume_js = (volume / 1e6).tolist()
rsi_js = rsi.tolist()

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>dashboard-synchronized-crosshair · python · pygal · anyplot.ai</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: {PAGE_BG}; font-family: sans-serif; }}
.dash {{ position: relative; width: 100%; }}
.panel {{ width: 100%; display: block; line-height: 0; }}
.sep {{ height: 1px; background: {INK_MUTED}; opacity: 0.35; }}
.ch {{ position: absolute; width: 2px; background: {INK}; opacity: 0.4;
       pointer-events: none; display: none; top: 0; }}
.tip {{ position: fixed; background: {ELEVATED_BG}; color: {INK};
        border: 1px solid {INK_MUTED}; padding: 10px 14px; border-radius: 6px;
        font-size: 13px; line-height: 1.9; pointer-events: none;
        display: none; z-index: 100; white-space: nowrap;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
</style>
</head>
<body>
<div class="dash" id="dash">
  <div class="panel">{price_svg}</div>
  <div class="sep"></div>
  <div class="panel">{volume_svg}</div>
  <div class="sep"></div>
  <div class="panel">{rsi_svg}</div>
  <div class="ch" id="ch"></div>
</div>
<div class="tip" id="tip"></div>
<script>
(function() {{
  var n = {n_days};
  var prices = {price_js};
  var vols = {volume_js};
  var rsis = {rsi_js};
  var dash = document.getElementById('dash');
  var ch = document.getElementById('ch');
  var tip = document.getElementById('tip');
  var LF = 150 / {W}, RF = 60 / {W};

  dash.addEventListener('mousemove', function(e) {{
    var r = dash.getBoundingClientRect();
    var x = e.clientX - r.left;
    var w = r.width;
    var pl = w * LF, pr = w * (1 - RF);
    if (x < pl || x > pr) {{
      ch.style.display = 'none';
      tip.style.display = 'none';
      return;
    }}
    var idx = Math.min(Math.floor((x - pl) / (pr - pl) * n), n - 1);
    ch.style.left = x + 'px';
    ch.style.height = r.height + 'px';
    ch.style.display = 'block';
    tip.innerHTML =
      '<strong>Day ' + (idx + 1) + ' / {n_days}</strong><br>' +
      '<span style="color:#009E73">■</span> Price: <strong>$' + prices[idx].toFixed(2) + '</strong><br>' +
      '<span style="color:#9418DB">■</span> Volume: <strong>' + vols[idx].toFixed(2) + 'M</strong><br>' +
      '<span style="color:#B71D27">■</span> RSI: <strong>' + rsis[idx].toFixed(1) + '</strong>';
    tip.style.left = (e.clientX + 16) + 'px';
    tip.style.top = (e.clientY + 16) + 'px';
    tip.style.display = 'block';
  }});
  dash.addEventListener('mouseleave', function() {{
    ch.style.display = 'none';
    tip.style.display = 'none';
  }});
}})();
</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html)

# PNG: composite three panels into exactly 3200×1800
bg_rgb = tuple(int(PAGE_BG[i : i + 2], 16) for i in (1, 3, 5))
price_img = Image.open(io.BytesIO(price_chart.render_to_png())).resize((W, H_PRICE), Image.LANCZOS)
volume_img = Image.open(io.BytesIO(volume_chart.render_to_png())).resize((W, H_VOLUME), Image.LANCZOS)
rsi_img = Image.open(io.BytesIO(rsi_chart.render_to_png())).resize((W, H_RSI), Image.LANCZOS)

canvas = Image.new("RGB", (W, H_PRICE + H_VOLUME + H_RSI), bg_rgb)
canvas.paste(price_img, (0, 0))
canvas.paste(volume_img, (0, H_PRICE))
canvas.paste(rsi_img, (0, H_PRICE + H_VOLUME))

canvas.save(f"plot-{THEME}.png", dpi=(300, 300))
