""" pyplots.ai
barcode-ean13: EAN-13 Barcode
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-19
"""

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure


# EAN-13 encoding patterns
# L-codes (left side, odd parity)
L_CODES = {
    "0": [0, 0, 0, 1, 1, 0, 1],
    "1": [0, 0, 1, 1, 0, 0, 1],
    "2": [0, 0, 1, 0, 0, 1, 1],
    "3": [0, 1, 1, 1, 1, 0, 1],
    "4": [0, 1, 0, 0, 0, 1, 1],
    "5": [0, 1, 1, 0, 0, 0, 1],
    "6": [0, 1, 0, 1, 1, 1, 1],
    "7": [0, 1, 1, 1, 0, 1, 1],
    "8": [0, 1, 1, 0, 1, 1, 1],
    "9": [0, 0, 0, 1, 0, 1, 1],
}

# G-codes (left side, even parity)
G_CODES = {
    "0": [0, 1, 0, 0, 1, 1, 1],
    "1": [0, 1, 1, 0, 0, 1, 1],
    "2": [0, 0, 1, 1, 0, 1, 1],
    "3": [0, 1, 0, 0, 0, 0, 1],
    "4": [0, 0, 1, 1, 1, 0, 1],
    "5": [0, 1, 1, 1, 0, 0, 1],
    "6": [0, 0, 0, 0, 1, 0, 1],
    "7": [0, 0, 1, 0, 0, 0, 1],
    "8": [0, 0, 0, 1, 0, 0, 1],
    "9": [0, 0, 1, 0, 1, 1, 1],
}

# R-codes (right side)
R_CODES = {
    "0": [1, 1, 1, 0, 0, 1, 0],
    "1": [1, 1, 0, 0, 1, 1, 0],
    "2": [1, 1, 0, 1, 1, 0, 0],
    "3": [1, 0, 0, 0, 0, 1, 0],
    "4": [1, 0, 1, 1, 1, 0, 0],
    "5": [1, 0, 0, 1, 1, 1, 0],
    "6": [1, 0, 1, 0, 0, 0, 0],
    "7": [1, 0, 0, 0, 1, 0, 0],
    "8": [1, 0, 0, 1, 0, 0, 0],
    "9": [1, 1, 1, 0, 1, 0, 0],
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

# Guard patterns
START_GUARD = [1, 0, 1]
CENTER_GUARD = [0, 1, 0, 1, 0]
END_GUARD = [1, 0, 1]

# EAN-13 code (German product example from spec)
code = "4006381333931"

# Verify and calculate check digit if needed
if len(code) == 12:
    # Calculate check digit
    total = 0
    for i, digit in enumerate(code):
        if i % 2 == 0:
            total += int(digit)
        else:
            total += int(digit) * 3
    check_digit = (10 - (total % 10)) % 10
    code = code + str(check_digit)

# Build the barcode pattern
barcode_pattern = []

# Add start guard
barcode_pattern.extend(START_GUARD)

# Get the encoding pattern for the first digit
first_digit = code[0]
pattern = FIRST_DIGIT_PATTERNS[first_digit]

# Encode left side (digits 2-7, indices 1-6)
for i, digit in enumerate(code[1:7]):
    if pattern[i] == "L":
        barcode_pattern.extend(L_CODES[digit])
    else:
        barcode_pattern.extend(G_CODES[digit])

# Add center guard
barcode_pattern.extend(CENTER_GUARD)

# Encode right side (digits 8-13, indices 7-12)
for digit in code[7:13]:
    barcode_pattern.extend(R_CODES[digit])

# Add end guard
barcode_pattern.extend(END_GUARD)

# Convert pattern to bar positions
module_width = 12  # Larger modules for better visibility at 4800px width
quiet_zone_modules = 11  # At least 9 modules, using 11 for safety
quiet_zone = quiet_zone_modules * module_width

# Build bar positions
bar_lefts = []
bar_widths_px = []
bar_colors = []

x_pos = quiet_zone

# Process the pattern and group consecutive 1s into bars
i = 0
while i < len(barcode_pattern):
    if barcode_pattern[i] == 1:
        # Start of a bar
        bar_start = x_pos
        bar_width = 0
        while i < len(barcode_pattern) and barcode_pattern[i] == 1:
            bar_width += module_width
            x_pos += module_width
            i += 1
        bar_lefts.append(bar_start)
        bar_widths_px.append(bar_width)
        bar_colors.append("#000000")
    else:
        x_pos += module_width
        i += 1

# Calculate total barcode width
total_width = x_pos + quiet_zone

# Bar heights (guard bars are taller)
bar_height = 1200
guard_height = 1400
text_y_pos = 80

# Determine which bars are guard bars (taller)
# Start guard: modules 0-2 (indices in barcode_pattern)
# Center guard: modules 45-49 (after 3 start + 42 left digits)
# End guard: modules 92-94 (after 3 start + 42 left + 5 center + 42 right)

# Calculate bar types and heights
bar_tops = []
bar_bottoms = []

# We need to track module positions to determine bar heights
module_positions = []
current_module = 0
for _i, val in enumerate(barcode_pattern):
    if val == 1:
        module_positions.append(current_module)
    current_module += 1

# Guard bar module ranges
start_guard_end = 2  # modules 0-2
center_guard_start = 3 + 6 * 7  # 3 + 42 = 45
center_guard_end = center_guard_start + 4  # 45-49
end_guard_start = center_guard_end + 1 + 6 * 7  # 50 + 42 = 92

# Recalculate with proper heights
bar_lefts = []
bar_widths_px = []
bar_tops = []
bar_bottoms = []

x_pos = quiet_zone
module_idx = 0
i = 0

while i < len(barcode_pattern):
    if barcode_pattern[i] == 1:
        bar_start = x_pos
        bar_width = 0
        start_module = module_idx

        while i < len(barcode_pattern) and barcode_pattern[i] == 1:
            bar_width += module_width
            x_pos += module_width
            module_idx += 1
            i += 1

        end_module = module_idx - 1

        # Check if this bar is part of a guard pattern
        is_guard = (
            start_module <= start_guard_end
            or (center_guard_start <= start_module <= center_guard_end)
            or start_module >= end_guard_start
        )

        bar_lefts.append(bar_start)
        bar_widths_px.append(bar_width)
        if is_guard:
            bar_tops.append(guard_height + 150)
            bar_bottoms.append(150)
        else:
            bar_tops.append(bar_height + 150)
            bar_bottoms.append(280)  # Leave space for text
    else:
        x_pos += module_width
        module_idx += 1
        i += 1

total_width = x_pos + quiet_zone

# Center the barcode horizontally in the figure
figure_width = 4800
figure_height = 2700
x_offset = (figure_width - total_width) / 2

# Adjust all bar positions to center the barcode
bar_lefts = [left + x_offset for left in bar_lefts]

# Create figure
p = figure(
    width=figure_width,
    height=figure_height,
    title="barcode-ean13 · bokeh · pyplots.ai",
    x_range=(0, figure_width),
    y_range=(0, guard_height + 450),
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

# Draw the bars
bar_rights = [left + width for left, width in zip(bar_lefts, bar_widths_px, strict=True)]

source = ColumnDataSource(
    data={
        "left": bar_lefts,
        "right": bar_rights,
        "top": bar_tops,
        "bottom": bar_bottoms,
        "color": ["#000000"] * len(bar_lefts),
    }
)

p.quad(left="left", right="right", top="top", bottom="bottom", color="color", source=source)

# Add human-readable digits below the barcode
# First digit is outside the left guard
first_digit_x = x_offset + quiet_zone - module_width * 5
first_digit_label = Label(
    x=first_digit_x,
    y=text_y_pos,
    text=code[0],
    text_font_size="48pt",
    text_align="center",
    text_baseline="bottom",
    text_color="#000000",
    text_font="monospace",
)
p.add_layout(first_digit_label)

# Left side digits (under first 6 data digits)
left_start = x_offset + quiet_zone + 3 * module_width  # After start guard
left_width = 6 * 7 * module_width  # 6 digits * 7 modules each
left_center = left_start + left_width / 2

left_digits_label = Label(
    x=left_center,
    y=text_y_pos,
    text=code[1:7],
    text_font_size="48pt",
    text_align="center",
    text_baseline="bottom",
    text_color="#000000",
    text_font="monospace",
)
p.add_layout(left_digits_label)

# Right side digits (under last 6 data digits)
right_start = left_start + left_width + 5 * module_width  # After center guard
right_width = 6 * 7 * module_width
right_center = right_start + right_width / 2

right_digits_label = Label(
    x=right_center,
    y=text_y_pos,
    text=code[7:13],
    text_font_size="48pt",
    text_align="center",
    text_baseline="bottom",
    text_color="#000000",
    text_font="monospace",
)
p.add_layout(right_digits_label)

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactive viewing
output_file("plot.html")
save(p)
