""" pyplots.ai
barcode-code128: Code 128 Barcode
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-19
"""

import plotly.graph_objects as go


# Code 128 encoding patterns (0 = space, 1 = bar)
# Each character is 11 modules (6 bars, quiet zone not included)
CODE128_PATTERNS = {
    # Start codes
    "START_A": "11010000100",
    "START_B": "11010010000",
    "START_C": "11010011100",
    "STOP": "1100011101011",  # Stop pattern (13 modules)
    # Values 0-106
    0: "11011001100",
    1: "11001101100",
    2: "11001100110",
    3: "10010011000",
    4: "10010001100",
    5: "10001001100",
    6: "10011001000",
    7: "10011000100",
    8: "10001100100",
    9: "11001001000",
    10: "11001000100",
    11: "11000100100",
    12: "10110011100",
    13: "10011011100",
    14: "10011001110",
    15: "10111001100",
    16: "10011101100",
    17: "10011100110",
    18: "11001110010",
    19: "11001011100",
    20: "11001001110",
    21: "11011100100",
    22: "11001110100",
    23: "11101101110",
    24: "11101001100",
    25: "11100101100",
    26: "11100100110",
    27: "11101100100",
    28: "11100110100",
    29: "11100110010",
    30: "11011011000",
    31: "11011000110",
    32: "11000110110",
    33: "10100011000",
    34: "10001011000",
    35: "10001000110",
    36: "10110001000",
    37: "10001101000",
    38: "10001100010",
    39: "11010001000",
    40: "11000101000",
    41: "11000100010",
    42: "10110111000",
    43: "10110001110",
    44: "10001101110",
    45: "10111011000",
    46: "10111000110",
    47: "10001110110",
    48: "11101110110",
    49: "11010001110",
    50: "11000101110",
    51: "11011101000",
    52: "11011100010",
    53: "11011101110",
    54: "11101011000",
    55: "11101000110",
    56: "11100010110",
    57: "11101101000",
    58: "11101100010",
    59: "11100011010",
    60: "11101111010",
    61: "11001000010",
    62: "11110001010",
    63: "10100110000",
    64: "10100001100",
    65: "10010110000",
    66: "10010000110",
    67: "10000101100",
    68: "10000100110",
    69: "10110010000",
    70: "10110000100",
    71: "10011010000",
    72: "10011000010",
    73: "10000110100",
    74: "10000110010",
    75: "11000010010",
    76: "11001010000",
    77: "11110111010",
    78: "11000010100",
    79: "10001111010",
    80: "10100111100",
    81: "10010111100",
    82: "10010011110",
    83: "10111100100",
    84: "10011110100",
    85: "10011110010",
    86: "11110100100",
    87: "11110010100",
    88: "11110010010",
    89: "11011011110",
    90: "11011110110",
    91: "11110110110",
    92: "10101111000",
    93: "10100011110",
    94: "10001011110",
    95: "10111101000",
    96: "10111100010",
    97: "11110101000",
    98: "11110100010",
    99: "10111011110",
    100: "10111101110",
    101: "11101011110",
    102: "11110101110",
    103: "11010000100",
    104: "11010010000",
    105: "11010011100",
    106: "1100011101011",
}

# Code 128B character to value mapping (ASCII 32-127)
CODE128B_MAP = {chr(i): i - 32 for i in range(32, 128)}

# Data - encode a sample string
content = "PYPLOTS-2024"

# Encode using Code 128B
values = [104]  # Start B
for char in content:
    if char in CODE128B_MAP:
        values.append(CODE128B_MAP[char])
    else:
        values.append(0)  # Space for unsupported chars

# Calculate check digit (modulo 103)
checksum = values[0]
for i, val in enumerate(values[1:], 1):
    checksum += i * val
checksum = checksum % 103
values.append(checksum)

# Build pattern
barcode_pattern = CODE128_PATTERNS["START_B"]
for val in values[1:-1]:
    barcode_pattern += CODE128_PATTERNS[val]
barcode_pattern += CODE128_PATTERNS[values[-1]]  # Check digit
barcode_pattern += CODE128_PATTERNS["STOP"]

# Calculate bar positions
bar_width = 3
x_positions = []
widths = []
current_x = 50  # Start with quiet zone

for i, bit in enumerate(barcode_pattern):
    if bit == "1":
        # Find consecutive 1s
        if i == 0 or barcode_pattern[i - 1] == "0":
            start_x = current_x
            width = bar_width
            j = i + 1
            while j < len(barcode_pattern) and barcode_pattern[j] == "1":
                width += bar_width
                j += 1
            x_positions.append(start_x + width / 2)
            widths.append(width)
    current_x += bar_width

# Calculate total width
total_width = 50 + len(barcode_pattern) * bar_width + 50  # quiet zones

# Plot
fig = go.Figure()

# Add bars
for x, w in zip(x_positions, widths, strict=True):
    fig.add_shape(type="rect", x0=x - w / 2, x1=x + w / 2, y0=100, y1=500, fillcolor="black", line={"width": 0})

# Add human-readable text below barcode
fig.add_annotation(
    x=total_width / 2,
    y=50,
    text=content,
    showarrow=False,
    font={"size": 36, "family": "Courier New, monospace", "color": "black"},
    xanchor="center",
    yanchor="middle",
)

# Layout
fig.update_layout(
    title={"text": "barcode-code128 · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={"visible": False, "range": [0, total_width], "fixedrange": True},
    yaxis={"visible": False, "range": [0, 600], "fixedrange": True, "scaleanchor": "x", "scaleratio": 1},
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 50, "r": 50, "t": 100, "b": 50},
    showlegend=False,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
