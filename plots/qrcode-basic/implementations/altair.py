""" pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: altair 6.0.0 | Python 3.14.3
Quality: 89/100 | Updated: 2026-04-07
"""

import altair as alt
import numpy as np
import pandas as pd
import qrcode


# Data - Generate a real, scannable QR code encoding "https://pyplots.ai"
content = "https://pyplots.ai"

qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
qr.add_data(content)
qr.make(fit=True)

# Convert QR code to numpy matrix and add quiet zone
qr_matrix = np.array(qr.get_matrix(), dtype=int)
quiet_zone = 4
padded = np.zeros((qr_matrix.shape[0] + 2 * quiet_zone, qr_matrix.shape[1] + 2 * quiet_zone), dtype=int)
padded[quiet_zone : quiet_zone + qr_matrix.shape[0], quiet_zone : quiet_zone + qr_matrix.shape[1]] = qr_matrix
total_size = padded.shape[0]

# Build DataFrame with region classification and color encoding
rows, cols = np.where(np.ones_like(padded, dtype=bool))
region_colors = {"Finder Pattern": "#1B3A5C", "Timing Pattern": "#2A7F62", "Data": "#306998", "Quiet Zone": "#FFFFFF"}
records = []
for r, c in zip(rows, cols, strict=True):
    qr_r, qr_c = r - quiet_zone, c - quiet_zone
    if qr_r < 0 or qr_r >= qr_matrix.shape[0] or qr_c < 0 or qr_c >= qr_matrix.shape[1]:
        region = "Quiet Zone"
    elif (
        (qr_r < 7 and qr_c < 7)
        or (qr_r < 7 and qr_c >= qr_matrix.shape[1] - 7)
        or (qr_r >= qr_matrix.shape[0] - 7 and qr_c < 7)
    ):
        region = "Finder Pattern"
    elif qr_r == 6 or qr_c == 6:
        region = "Timing Pattern"
    else:
        region = "Data"
    val = padded[r, c]
    display_region = region if val == 1 else "Background"
    records.append({"x": c, "y": total_size - 1 - r, "value": val, "region": region, "display": display_region})

data = pd.DataFrame(records)

# Color mapping: dark modules get region-specific colors, background is white
display_domain = ["Finder Pattern", "Timing Pattern", "Data", "Background"]
display_colors = ["#1B3A5C", "#2A7F62", "#306998", "#FFFFFF"]

# Plot - QR code with color-encoded structural regions
chart = (
    alt.Chart(data)
    .mark_rect(stroke=None, strokeWidth=0)
    .encode(
        x=alt.X("x:O", axis=None),
        y=alt.Y("y:O", axis=None),
        color=alt.Color(
            "display:N",
            scale=alt.Scale(domain=display_domain, range=display_colors),
            legend=alt.Legend(
                title="QR Code Regions",
                titleFontSize=16,
                labelFontSize=14,
                orient="bottom",
                direction="horizontal",
                values=["Finder Pattern", "Timing Pattern", "Data"],
            ),
        ),
        tooltip=[
            alt.Tooltip("region:N", title="Region"),
            alt.Tooltip("x:O", title="Col"),
            alt.Tooltip("y:O", title="Row"),
        ],
    )
    .properties(
        width=800,
        height=800,
        title=alt.Title(
            "qrcode-basic · altair · pyplots.ai",
            subtitle="Structural regions: Finder Patterns (navy) for orientation · Timing Patterns (green) for alignment · Data modules (blue)",
            fontSize=28,
            subtitleFontSize=16,
            subtitleColor="#555555",
            anchor="middle",
            dy=-10,
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False)
    .configure_legend(symbolStrokeWidth=0, padding=20)
)

# Save
chart.save("plot.png", scale_factor=4.5)
chart.save("plot.html")
