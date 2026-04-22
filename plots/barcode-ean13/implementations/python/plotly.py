""" pyplots.ai
barcode-ean13: EAN-13 Barcode
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-19
"""

import plotly.graph_objects as go


# EAN-13 encoding patterns
# L-codes (left side, odd parity)
L_CODES = {
    "0": "0001101",
    "1": "0011001",
    "2": "0010011",
    "3": "0111101",
    "4": "0100011",
    "5": "0110001",
    "6": "0101111",
    "7": "0111011",
    "8": "0110111",
    "9": "0001011",
}

# G-codes (left side, even parity)
G_CODES = {
    "0": "0100111",
    "1": "0110011",
    "2": "0011011",
    "3": "0100001",
    "4": "0011101",
    "5": "0111001",
    "6": "0000101",
    "7": "0010001",
    "8": "0001001",
    "9": "0010111",
}

# R-codes (right side)
R_CODES = {
    "0": "1110010",
    "1": "1100110",
    "2": "1101100",
    "3": "1000010",
    "4": "1011100",
    "5": "1001110",
    "6": "1010000",
    "7": "1000100",
    "8": "1001000",
    "9": "1110100",
}

# First digit encoding pattern (determines L/G pattern for left side)
FIRST_DIGIT_PATTERNS = {
    "0": "LLLLLL",
    "1": "LLGLGG",
    "2": "LLGGLG",
    "3": "LLGGGL",
    "4": "LGLLGG",
    "5": "LGGLLG",
    "6": "LGGGLL",
    "7": "LGLGLG",
    "8": "LGLGGL",
    "9": "LGGLGL",
}

# Data - example EAN-13 code (German product)
ean_code = "4006381333931"

# Calculate check digit if needed (this code already has it)
code = ean_code
if len(code) == 12:
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(code))
    code = code + str((10 - (total % 10)) % 10)

# Encode to binary pattern
first_digit = code[0]
left_digits = code[1:7]
right_digits = code[7:13]

# Start guard
binary_pattern = "101"

# Left side (6 digits with L/G pattern based on first digit)
lg_pattern = FIRST_DIGIT_PATTERNS[first_digit]
for i, digit in enumerate(left_digits):
    if lg_pattern[i] == "L":
        binary_pattern += L_CODES[digit]
    else:
        binary_pattern += G_CODES[digit]

# Center guard
binary_pattern += "01010"

# Right side (6 digits with R codes)
for digit in right_digits:
    binary_pattern += R_CODES[digit]

# End guard
binary_pattern += "101"

# Bar dimensions
module_width = 3
bar_height = 200
guard_height = 220
quiet_zone = 9 * module_width

# Create figure
fig = go.Figure()

# Draw bars
x_pos = quiet_zone
guard_positions = list(range(0, 3)) + list(range(45, 50)) + list(range(92, 95))

for i, bit in enumerate(binary_pattern):
    if bit == "1":
        # Determine bar height (guards are taller)
        height = guard_height if i in guard_positions else bar_height

        fig.add_shape(
            type="rect", x0=x_pos, y0=0, x1=x_pos + module_width, y1=height, fillcolor="black", line={"width": 0}
        )
    x_pos += module_width

# Total width for centering
total_width = quiet_zone * 2 + len(binary_pattern) * module_width

# Add human-readable digits
digit_y = -35
font_size = 24

# First digit (outside left guard)
fig.add_annotation(
    x=quiet_zone - module_width * 4,
    y=digit_y,
    text=code[0],
    showarrow=False,
    font={"size": font_size, "family": "monospace", "color": "black"},
)

# Left group (digits 2-7, under left bars)
left_start = quiet_zone + 3 * module_width
for i, digit in enumerate(code[1:7]):
    x = left_start + (i + 0.5) * 7 * module_width
    fig.add_annotation(
        x=x, y=digit_y, text=digit, showarrow=False, font={"size": font_size, "family": "monospace", "color": "black"}
    )

# Right group (digits 8-13, under right bars)
right_start = quiet_zone + 3 * module_width + 42 * module_width + 5 * module_width
for i, digit in enumerate(code[7:13]):
    x = right_start + (i + 0.5) * 7 * module_width
    fig.add_annotation(
        x=x, y=digit_y, text=digit, showarrow=False, font={"size": font_size, "family": "monospace", "color": "black"}
    )

# Layout
fig.update_layout(
    title={
        "text": "barcode-ean13 · plotly · pyplots.ai",
        "font": {"size": 28, "color": "black"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"visible": False, "range": [-20, total_width + 20], "scaleanchor": "y", "scaleratio": 1},
    yaxis={"visible": False, "range": [-80, guard_height + 40]},
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 50, "r": 50, "t": 80, "b": 50},
    width=1600,
    height=900,
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
