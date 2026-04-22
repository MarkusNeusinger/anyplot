""" pyplots.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: pygal 3.1.0 | Python 3.13.11
Quality: 55/100 | Created: 2026-01-20
"""

import io

import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Data - 200 trading days of stock data with price, volume, and RSI
np.random.seed(42)
n_days = 200
dates = [f"Day {i + 1}" for i in range(n_days)]

# Price series (random walk starting at 100)
returns = np.random.randn(n_days) * 0.02
price = 100 * np.cumprod(1 + returns)

# Volume series (correlated with price changes)
volume = np.abs(np.random.randn(n_days)) * 1000000 + 500000
volume = volume * (1 + np.abs(returns) * 10)

# RSI indicator (bounded 0-100)
rsi = 50 + np.cumsum(np.random.randn(n_days) * 2)
rsi = np.clip(rsi, 0, 100)

# Style for Price chart (top) - Blue
price_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#333333",
    foreground_strong="#222222",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=42,
    label_font_size=26,
    major_label_font_size=24,
    legend_font_size=26,
    value_font_size=20,
    font_family="sans-serif",
    guide_stroke_color="#cccccc",
    stroke_width=4,
)

# Style for Volume chart (middle) - Gold
volume_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#333333",
    foreground_strong="#222222",
    foreground_subtle="#666666",
    colors=("#E6A800",),
    title_font_size=42,
    label_font_size=26,
    major_label_font_size=24,
    legend_font_size=26,
    value_font_size=20,
    font_family="sans-serif",
    guide_stroke_color="#cccccc",
    stroke_width=3,
)

# Style for RSI chart (bottom) - Red
rsi_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#333333",
    foreground_strong="#222222",
    foreground_subtle="#666666",
    colors=("#C0392B",),
    title_font_size=42,
    label_font_size=26,
    major_label_font_size=24,
    legend_font_size=26,
    value_font_size=20,
    font_family="sans-serif",
    guide_stroke_color="#cccccc",
    stroke_width=4,
)

# Chart 1: Price Line Chart (top panel) - Independent Y-axis for price values
price_chart = pygal.Line(
    width=4800,
    height=800,
    style=price_style,
    title="Panel 1: Stock Price",
    y_title="Price ($)",
    show_x_labels=False,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=True,
    dots_size=0,
    fill=False,
    truncate_label=-1,
    margin_bottom=5,
    margin_top=40,
    margin_left=120,
    margin_right=50,
)
price_chart.add("Price", price.tolist())
price_chart.x_labels = dates

# Chart 2: Volume Bar/Area Chart (middle panel) - Independent Y-axis for volume
volume_chart = pygal.Line(
    width=4800,
    height=700,
    style=volume_style,
    title="Panel 2: Trading Volume",
    y_title="Volume (M)",
    show_x_labels=False,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=True,
    dots_size=0,
    fill=True,
    truncate_label=-1,
    margin_top=20,
    margin_bottom=5,
    margin_left=120,
    margin_right=50,
)
volume_chart.add("Volume", (volume / 1000000).tolist())
volume_chart.x_labels = dates

# Chart 3: RSI Indicator (bottom panel) - Independent Y-axis bounded 0-100
rsi_chart = pygal.Line(
    width=4800,
    height=900,
    style=rsi_style,
    title="Panel 3: RSI Indicator",
    x_title="Trading Day",
    y_title="RSI (0-100)",
    show_x_labels=True,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=True,
    dots_size=0,
    fill=False,
    x_labels_major_count=10,
    show_minor_x_labels=False,
    truncate_label=-1,
    x_label_rotation=45,
    range=(0, 100),
    margin_top=20,
    margin_left=120,
    margin_right=50,
)
rsi_chart.add("RSI", rsi.tolist())
rsi_chart.x_labels = dates

# Create combined HTML dashboard with synchronized crosshair via JavaScript
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>dashboard-synchronized-crosshair · pygal · pyplots.ai</title>
    <style>
        body {{
            font-family: sans-serif;
            background: white;
            margin: 0;
            padding: 20px;
        }}
        .dashboard-title {{
            text-align: center;
            font-size: 32px;
            color: #333;
            margin-bottom: 15px;
            font-weight: bold;
        }}
        .chart-container {{
            width: 100%;
            max-width: 4800px;
            margin: 0 auto;
            position: relative;
        }}
        .chart {{
            width: 100%;
            display: block;
            border-bottom: 2px solid #e0e0e0;
        }}
        .chart:last-child {{
            border-bottom: none;
        }}
        .crosshair {{
            position: absolute;
            width: 3px;
            background: rgba(48, 105, 152, 0.8);
            pointer-events: none;
            display: none;
            z-index: 1000;
        }}
        #crosshair1 {{ height: 300px; top: 80px; }}
        #crosshair2 {{ height: 260px; top: 400px; }}
        #crosshair3 {{ height: 340px; top: 680px; }}
        .tooltip {{
            position: fixed;
            background: rgba(48, 105, 152, 0.95);
            color: white;
            padding: 12px 16px;
            border-radius: 6px;
            font-size: 14px;
            pointer-events: none;
            display: none;
            z-index: 1001;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="dashboard-title">dashboard-synchronized-crosshair · pygal · pyplots.ai</div>
    <div class="chart-container" id="dashboard">
        <div class="crosshair" id="crosshair1"></div>
        <div class="crosshair" id="crosshair2"></div>
        <div class="crosshair" id="crosshair3"></div>
        <div class="chart" id="chart1">{price_chart.render(is_unicode=True)}</div>
        <div class="chart" id="chart2">{volume_chart.render(is_unicode=True)}</div>
        <div class="chart" id="chart3">{rsi_chart.render(is_unicode=True)}</div>
    </div>
    <div class="tooltip" id="tooltip"></div>
    <script>
        const priceData = {price.tolist()};
        const volumeData = {(volume / 1000000).tolist()};
        const rsiData = {rsi.tolist()};
        const n = {n_days};

        const dashboard = document.getElementById('dashboard');
        const crosshairs = [
            document.getElementById('crosshair1'),
            document.getElementById('crosshair2'),
            document.getElementById('crosshair3')
        ];
        const tooltip = document.getElementById('tooltip');

        dashboard.addEventListener('mousemove', function(e) {{
            const rect = dashboard.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const chartWidth = rect.width;

            const leftMargin = chartWidth * 0.025;
            const rightMargin = chartWidth * 0.01;
            const plotWidth = chartWidth - leftMargin - rightMargin;

            if (x >= leftMargin && x <= chartWidth - rightMargin) {{
                const relX = x - leftMargin;
                const idx = Math.min(Math.floor((relX / plotWidth) * n), n - 1);

                crosshairs.forEach(ch => {{
                    ch.style.left = x + 'px';
                    ch.style.display = 'block';
                }});

                tooltip.innerHTML = `
                    <strong>Day ${{idx + 1}}</strong><br>
                    <span style="color: #89CFF0;">Price:</span> $${{priceData[idx].toFixed(2)}}<br>
                    <span style="color: #FFD43B;">Volume:</span> ${{volumeData[idx].toFixed(2)}}M<br>
                    <span style="color: #FF6B6B;">RSI:</span> ${{rsiData[idx].toFixed(1)}}
                `;
                tooltip.style.left = (e.clientX + 15) + 'px';
                tooltip.style.top = (e.clientY + 15) + 'px';
                tooltip.style.display = 'block';
            }}
        }});

        dashboard.addEventListener('mouseleave', function() {{
            crosshairs.forEach(ch => ch.style.display = 'none');
            tooltip.style.display = 'none';
        }});
    </script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Render each chart to PNG and combine vertically for static preview
price_png = price_chart.render_to_png()
price_img = Image.open(io.BytesIO(price_png))

volume_png = volume_chart.render_to_png()
volume_img = Image.open(io.BytesIO(volume_png))

rsi_png = rsi_chart.render_to_png()
rsi_img = Image.open(io.BytesIO(rsi_png))

# Create title banner
title_height = 120
title_img = Image.new("RGB", (4800, title_height), "white")
draw = ImageDraw.Draw(title_img)
title_text = "dashboard-synchronized-crosshair · pygal · pyplots.ai"
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
except OSError:
    title_font = ImageFont.load_default()
bbox = draw.textbbox((0, 0), title_text, font=title_font)
text_width = bbox[2] - bbox[0]
text_x = (4800 - text_width) // 2
draw.text((text_x, 30), title_text, fill="#333333", font=title_font)

# Panel spacing for visual separation
panel_gap = 30

# Calculate total height
total_height = title_height + price_img.height + panel_gap + volume_img.height + panel_gap + rsi_img.height

# Create combined dashboard image with white background
combined = Image.new("RGB", (4800, total_height), "white")
y_offset = 0

combined.paste(title_img, (0, y_offset))
y_offset += title_height

combined.paste(price_img, (0, y_offset))
price_chart_top = y_offset
price_chart_bottom = y_offset + price_img.height
y_offset += price_img.height + panel_gap

combined.paste(volume_img, (0, y_offset))
volume_chart_top = y_offset
volume_chart_bottom = y_offset + volume_img.height
y_offset += volume_img.height + panel_gap

combined.paste(rsi_img, (0, y_offset))
rsi_chart_top = y_offset
rsi_chart_bottom = y_offset + rsi_img.height

# Draw on combined image
crosshair_draw = ImageDraw.Draw(combined)

# Add bold panel separator lines
separator_color = "#999999"
crosshair_draw.line([(0, price_chart_bottom + 1), (4800, price_chart_bottom + 1)], fill=separator_color, width=4)
crosshair_draw.line([(0, volume_chart_bottom + 1), (4800, volume_chart_bottom + 1)], fill=separator_color, width=4)

# Draw synchronized crosshair line at Day 100 spanning all three chart panels
crosshair_x = 2400  # Center of chart area (Day ~100)
data_idx = 100
price_at_crosshair = price[data_idx]
volume_at_crosshair = volume[data_idx] / 1000000
rsi_at_crosshair = rsi[data_idx]

# Draw vertical crosshair line through all panels
crosshair_color = "#306998"
crosshair_draw.line(
    [(crosshair_x, price_chart_top + 60), (crosshair_x, price_chart_bottom - 20)], fill=crosshair_color, width=4
)
crosshair_draw.line(
    [(crosshair_x, volume_chart_top + 40), (crosshair_x, volume_chart_bottom - 20)], fill=crosshair_color, width=4
)
crosshair_draw.line(
    [(crosshair_x, rsi_chart_top + 40), (crosshair_x, rsi_chart_bottom - 100)], fill=crosshair_color, width=4
)

# Draw markers at data points on each chart
marker_radius = 12
marker_positions = [
    (crosshair_x, price_chart_top + price_img.height // 2),
    (crosshair_x, volume_chart_top + volume_img.height // 2),
    (crosshair_x, rsi_chart_top + rsi_img.height // 2 - 30),
]
marker_colors = ["#306998", "#E6A800", "#C0392B"]

for (mx, my), color in zip(marker_positions, marker_colors, strict=True):
    crosshair_draw.ellipse(
        [mx - marker_radius, my - marker_radius, mx + marker_radius, my + marker_radius],
        fill=color,
        outline="white",
        width=3,
    )

# Add crosshair annotation with synchronized tooltip info
try:
    annotation_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
except OSError:
    annotation_font = ImageFont.load_default()

annotation_text = f"Synchronized Crosshair at Day {data_idx + 1}"
crosshair_draw.text(
    (crosshair_x + 25, price_chart_top + 70), annotation_text, fill=crosshair_color, font=annotation_font
)

# Add value annotations next to each marker
try:
    value_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
except OSError:
    value_font = ImageFont.load_default()

crosshair_draw.text(
    (crosshair_x + 25, marker_positions[0][1] - 14), f"${price_at_crosshair:.2f}", fill="#306998", font=value_font
)
crosshair_draw.text(
    (crosshair_x + 25, marker_positions[1][1] - 14), f"{volume_at_crosshair:.2f}M", fill="#E6A800", font=value_font
)
crosshair_draw.text(
    (crosshair_x + 25, marker_positions[2][1] - 14), f"RSI: {rsi_at_crosshair:.1f}", fill="#C0392B", font=value_font
)

combined.save("plot.png", dpi=(300, 300))
