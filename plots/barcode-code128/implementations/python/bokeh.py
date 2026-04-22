""" pyplots.ai
barcode-code128: Code 128 Barcode
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-19
"""

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure


# Code 128 encoding tables
# Each character is encoded as a sequence of bar widths (6 values summing to 11 modules)
CODE128_B = {
    " ": [2, 1, 2, 2, 2, 2],
    "!": [2, 2, 2, 1, 2, 2],
    '"': [2, 2, 2, 2, 2, 1],
    "#": [1, 2, 1, 2, 2, 3],
    "$": [1, 2, 1, 3, 2, 2],
    "%": [1, 3, 1, 2, 2, 2],
    "&": [1, 2, 2, 2, 1, 3],
    "'": [1, 2, 2, 3, 1, 2],
    "(": [1, 3, 2, 2, 1, 2],
    ")": [2, 2, 1, 2, 1, 3],
    "*": [2, 2, 1, 3, 1, 2],
    "+": [2, 3, 1, 2, 1, 2],
    ",": [1, 1, 2, 2, 3, 2],
    "-": [1, 2, 2, 1, 3, 2],
    ".": [1, 2, 2, 2, 3, 1],
    "/": [1, 1, 3, 2, 2, 2],
    "0": [1, 2, 3, 1, 2, 2],
    "1": [1, 2, 3, 2, 2, 1],
    "2": [2, 2, 3, 2, 1, 1],
    "3": [2, 2, 1, 1, 3, 2],
    "4": [2, 2, 1, 2, 3, 1],
    "5": [2, 1, 3, 2, 1, 2],
    "6": [2, 2, 3, 1, 1, 2],
    "7": [3, 1, 2, 1, 3, 1],
    "8": [3, 1, 1, 2, 2, 2],
    "9": [3, 2, 1, 1, 2, 2],
    ":": [3, 2, 1, 2, 2, 1],
    ";": [3, 1, 2, 2, 1, 2],
    "<": [3, 2, 2, 1, 1, 2],
    "=": [3, 2, 2, 2, 1, 1],
    ">": [2, 1, 2, 1, 2, 3],
    "?": [2, 1, 2, 3, 2, 1],
    "@": [2, 3, 2, 1, 2, 1],
    "A": [1, 1, 1, 3, 2, 3],
    "B": [1, 3, 1, 1, 2, 3],
    "C": [1, 3, 1, 3, 2, 1],
    "D": [1, 1, 2, 3, 1, 3],
    "E": [1, 3, 2, 1, 1, 3],
    "F": [1, 3, 2, 3, 1, 1],
    "G": [2, 1, 1, 3, 1, 3],
    "H": [2, 3, 1, 1, 1, 3],
    "I": [2, 3, 1, 3, 1, 1],
    "J": [1, 1, 2, 1, 3, 3],
    "K": [1, 1, 2, 3, 3, 1],
    "L": [1, 3, 2, 1, 3, 1],
    "M": [1, 1, 3, 1, 2, 3],
    "N": [1, 1, 3, 3, 2, 1],
    "O": [1, 3, 3, 1, 2, 1],
    "P": [3, 1, 3, 1, 2, 1],
    "Q": [2, 1, 1, 3, 3, 1],
    "R": [2, 3, 1, 1, 3, 1],
    "S": [2, 1, 3, 1, 1, 3],
    "T": [2, 1, 3, 3, 1, 1],
    "U": [2, 1, 3, 1, 3, 1],
    "V": [3, 1, 1, 1, 2, 3],
    "W": [3, 1, 1, 3, 2, 1],
    "X": [3, 3, 1, 1, 2, 1],
    "Y": [3, 1, 2, 1, 1, 3],
    "Z": [3, 1, 2, 3, 1, 1],
    "[": [3, 3, 2, 1, 1, 1],
    "\\": [3, 1, 4, 1, 1, 1],
    "]": [2, 2, 1, 4, 1, 1],
    "^": [4, 3, 1, 1, 1, 1],
    "_": [1, 1, 1, 2, 2, 4],
    "`": [1, 1, 1, 4, 2, 2],
    "a": [1, 2, 1, 1, 2, 4],
    "b": [1, 2, 1, 4, 2, 1],
    "c": [1, 4, 1, 1, 2, 2],
    "d": [1, 4, 1, 2, 2, 1],
    "e": [1, 1, 2, 2, 1, 4],
    "f": [1, 1, 2, 4, 1, 2],
    "g": [1, 2, 2, 1, 1, 4],
    "h": [1, 2, 2, 4, 1, 1],
    "i": [1, 4, 2, 1, 1, 2],
    "j": [1, 4, 2, 2, 1, 1],
    "k": [2, 4, 1, 2, 1, 1],
    "l": [2, 2, 1, 1, 1, 4],
    "m": [4, 1, 3, 1, 1, 1],
    "n": [2, 4, 1, 1, 1, 2],
    "o": [1, 3, 4, 1, 1, 1],
    "p": [1, 1, 1, 2, 4, 2],
    "q": [1, 2, 1, 1, 4, 2],
    "r": [1, 2, 1, 2, 4, 1],
    "s": [1, 1, 4, 2, 1, 2],
    "t": [1, 2, 4, 1, 1, 2],
    "u": [1, 2, 4, 2, 1, 1],
    "v": [4, 1, 1, 2, 1, 2],
    "w": [4, 2, 1, 1, 1, 2],
    "x": [4, 2, 1, 2, 1, 1],
    "y": [2, 1, 2, 1, 4, 1],
    "z": [2, 1, 4, 1, 2, 1],
    "{": [4, 1, 2, 1, 2, 1],
    "|": [1, 1, 1, 1, 4, 3],
    "}": [1, 1, 1, 3, 4, 1],
    "~": [1, 3, 1, 1, 4, 1],
}

# Code 128 value lookup for checksum calculation
CODE128_VALUES = {
    " ": 0,
    "!": 1,
    '"': 2,
    "#": 3,
    "$": 4,
    "%": 5,
    "&": 6,
    "'": 7,
    "(": 8,
    ")": 9,
    "*": 10,
    "+": 11,
    ",": 12,
    "-": 13,
    ".": 14,
    "/": 15,
    "0": 16,
    "1": 17,
    "2": 18,
    "3": 19,
    "4": 20,
    "5": 21,
    "6": 22,
    "7": 23,
    "8": 24,
    "9": 25,
    ":": 26,
    ";": 27,
    "<": 28,
    "=": 29,
    ">": 30,
    "?": 31,
    "@": 32,
    "A": 33,
    "B": 34,
    "C": 35,
    "D": 36,
    "E": 37,
    "F": 38,
    "G": 39,
    "H": 40,
    "I": 41,
    "J": 42,
    "K": 43,
    "L": 44,
    "M": 45,
    "N": 46,
    "O": 47,
    "P": 48,
    "Q": 49,
    "R": 50,
    "S": 51,
    "T": 52,
    "U": 53,
    "V": 54,
    "W": 55,
    "X": 56,
    "Y": 57,
    "Z": 58,
    "[": 59,
    "\\": 60,
    "]": 61,
    "^": 62,
    "_": 63,
    "`": 64,
    "a": 65,
    "b": 66,
    "c": 67,
    "d": 68,
    "e": 69,
    "f": 70,
    "g": 71,
    "h": 72,
    "i": 73,
    "j": 74,
    "k": 75,
    "l": 76,
    "m": 77,
    "n": 78,
    "o": 79,
    "p": 80,
    "q": 81,
    "r": 82,
    "s": 83,
    "t": 84,
    "u": 85,
    "v": 86,
    "w": 87,
    "x": 88,
    "y": 89,
    "z": 90,
    "{": 91,
    "|": 92,
    "}": 93,
    "~": 94,
}

# Special patterns
START_B = [2, 1, 1, 2, 1, 4]  # Start Code B (value 104)
STOP = [2, 3, 3, 1, 1, 1, 2]  # Stop pattern (7 elements, includes termination bar)

# Checksum patterns (values 0-105)
CHECKSUM_PATTERNS = [
    [2, 1, 2, 2, 2, 2],
    [2, 2, 2, 1, 2, 2],
    [2, 2, 2, 2, 2, 1],
    [1, 2, 1, 2, 2, 3],
    [1, 2, 1, 3, 2, 2],
    [1, 3, 1, 2, 2, 2],
    [1, 2, 2, 2, 1, 3],
    [1, 2, 2, 3, 1, 2],
    [1, 3, 2, 2, 1, 2],
    [2, 2, 1, 2, 1, 3],
    [2, 2, 1, 3, 1, 2],
    [2, 3, 1, 2, 1, 2],
    [1, 1, 2, 2, 3, 2],
    [1, 2, 2, 1, 3, 2],
    [1, 2, 2, 2, 3, 1],
    [1, 1, 3, 2, 2, 2],
    [1, 2, 3, 1, 2, 2],
    [1, 2, 3, 2, 2, 1],
    [2, 2, 3, 2, 1, 1],
    [2, 2, 1, 1, 3, 2],
    [2, 2, 1, 2, 3, 1],
    [2, 1, 3, 2, 1, 2],
    [2, 2, 3, 1, 1, 2],
    [3, 1, 2, 1, 3, 1],
    [3, 1, 1, 2, 2, 2],
    [3, 2, 1, 1, 2, 2],
    [3, 2, 1, 2, 2, 1],
    [3, 1, 2, 2, 1, 2],
    [3, 2, 2, 1, 1, 2],
    [3, 2, 2, 2, 1, 1],
    [2, 1, 2, 1, 2, 3],
    [2, 1, 2, 3, 2, 1],
    [2, 3, 2, 1, 2, 1],
    [1, 1, 1, 3, 2, 3],
    [1, 3, 1, 1, 2, 3],
    [1, 3, 1, 3, 2, 1],
    [1, 1, 2, 3, 1, 3],
    [1, 3, 2, 1, 1, 3],
    [1, 3, 2, 3, 1, 1],
    [2, 1, 1, 3, 1, 3],
    [2, 3, 1, 1, 1, 3],
    [2, 3, 1, 3, 1, 1],
    [1, 1, 2, 1, 3, 3],
    [1, 1, 2, 3, 3, 1],
    [1, 3, 2, 1, 3, 1],
    [1, 1, 3, 1, 2, 3],
    [1, 1, 3, 3, 2, 1],
    [1, 3, 3, 1, 2, 1],
    [3, 1, 3, 1, 2, 1],
    [2, 1, 1, 3, 3, 1],
    [2, 3, 1, 1, 3, 1],
    [2, 1, 3, 1, 1, 3],
    [2, 1, 3, 3, 1, 1],
    [2, 1, 3, 1, 3, 1],
    [3, 1, 1, 1, 2, 3],
    [3, 1, 1, 3, 2, 1],
    [3, 3, 1, 1, 2, 1],
    [3, 1, 2, 1, 1, 3],
    [3, 1, 2, 3, 1, 1],
    [3, 3, 2, 1, 1, 1],
    [3, 1, 4, 1, 1, 1],
    [2, 2, 1, 4, 1, 1],
    [4, 3, 1, 1, 1, 1],
    [1, 1, 1, 2, 2, 4],
    [1, 1, 1, 4, 2, 2],
    [1, 2, 1, 1, 2, 4],
    [1, 2, 1, 4, 2, 1],
    [1, 4, 1, 1, 2, 2],
    [1, 4, 1, 2, 2, 1],
    [1, 1, 2, 2, 1, 4],
    [1, 1, 2, 4, 1, 2],
    [1, 2, 2, 1, 1, 4],
    [1, 2, 2, 4, 1, 1],
    [1, 4, 2, 1, 1, 2],
    [1, 4, 2, 2, 1, 1],
    [2, 4, 1, 2, 1, 1],
    [2, 2, 1, 1, 1, 4],
    [4, 1, 3, 1, 1, 1],
    [2, 4, 1, 1, 1, 2],
    [1, 3, 4, 1, 1, 1],
    [1, 1, 1, 2, 4, 2],
    [1, 2, 1, 1, 4, 2],
    [1, 2, 1, 2, 4, 1],
    [1, 1, 4, 2, 1, 2],
    [1, 2, 4, 1, 1, 2],
    [1, 2, 4, 2, 1, 1],
    [4, 1, 1, 2, 1, 2],
    [4, 2, 1, 1, 1, 2],
    [4, 2, 1, 2, 1, 1],
    [2, 1, 2, 1, 4, 1],
    [2, 1, 4, 1, 2, 1],
    [4, 1, 2, 1, 2, 1],
    [1, 1, 1, 1, 4, 3],
    [1, 1, 1, 3, 4, 1],
    [1, 3, 1, 1, 4, 1],
    [1, 1, 4, 1, 1, 3],
    [1, 1, 4, 3, 1, 1],
    [4, 1, 1, 1, 1, 3],
    [4, 1, 1, 3, 1, 1],
    [1, 1, 3, 1, 4, 1],
    [1, 1, 4, 1, 3, 1],
    [3, 1, 1, 1, 4, 1],
    [4, 1, 1, 1, 3, 1],
    [2, 1, 1, 4, 1, 2],
    [2, 1, 1, 2, 1, 4],
    [2, 1, 1, 2, 3, 2],
]


# Barcode content
content = "SHIP-2024-ABC123"

# Encode the content using Code 128 subset B
bar_widths = []

# Add start pattern (Code B)
bar_widths.extend(START_B)

# Calculate checksum
checksum = 104  # Start B value

# Encode each character
for i, char in enumerate(content):
    if char in CODE128_B:
        bar_widths.extend(CODE128_B[char])
        checksum += CODE128_VALUES[char] * (i + 1)

# Calculate final checksum
checksum = checksum % 103
bar_widths.extend(CHECKSUM_PATTERNS[checksum])

# Add stop pattern
bar_widths.extend(STOP)

# Convert bar widths to pixel positions for rendering
module_width = 4  # Base width for each module
quiet_zone = 40  # Quiet zone width in modules

# Build bar positions
bar_lefts = []
bar_widths_px = []
bar_colors = []
is_bar = True  # Start with a bar (black)

x_pos = quiet_zone * module_width  # Start after quiet zone

for width in bar_widths:
    pixel_width = width * module_width
    if is_bar:
        bar_lefts.append(x_pos)
        bar_widths_px.append(pixel_width)
        bar_colors.append("#000000")
    x_pos += pixel_width
    is_bar = not is_bar

# Calculate total barcode width
total_width = x_pos + quiet_zone * module_width

# Bar height
bar_height = 400

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="barcode-code128 \u00b7 bokeh \u00b7 pyplots.ai",
    x_range=(0, total_width),
    y_range=(0, bar_height + 200),
    toolbar_location=None,
)

# Style the figure
p.title.text_font_size = "32pt"
p.title.align = "center"
p.title.text_color = "#333333"

# Remove axes and grid
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# White background
p.background_fill_color = "#FFFFFF"
p.border_fill_color = "#FFFFFF"

# Draw the bars using quad
bar_rights = [left + width for left, width in zip(bar_lefts, bar_widths_px, strict=True)]
bar_tops = [bar_height + 50] * len(bar_lefts)
bar_bottoms = [50] * len(bar_lefts)

source = ColumnDataSource(
    data={"left": bar_lefts, "right": bar_rights, "top": bar_tops, "bottom": bar_bottoms, "color": bar_colors}
)

p.quad(left="left", right="right", top="top", bottom="bottom", color="color", source=source)

# Add human-readable text below the barcode
text_x = total_width / 2
text_y = 20

human_text = Label(
    x=text_x,
    y=text_y,
    text=content,
    text_font_size="28pt",
    text_align="center",
    text_baseline="bottom",
    text_color="#000000",
    text_font="monospace",
)

p.add_layout(human_text)

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactive viewing
output_file("plot.html")
save(p)
