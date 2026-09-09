# anyplot.ai
# venn-basic: Venn Diagram
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-09-09

using CairoMakie
using Colors

# --- Theme tokens -------------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3",
]

# --- Data: developer skill survey (n = 270 engineers) --------------------------
set_labels = ["Python", "SQL", "JavaScript"]
size_python, size_sql, size_js = 145, 120, 95
overlap_py_sql, overlap_py_js, overlap_sql_js = 45, 35, 25
overlap_all = 15

only_python     = size_python - overlap_py_sql - overlap_py_js + overlap_all
only_sql        = size_sql - overlap_py_sql - overlap_sql_js + overlap_all
only_js         = size_js - overlap_py_js - overlap_sql_js + overlap_all
only_py_sql     = overlap_py_sql - overlap_all
only_py_js      = overlap_py_js - overlap_all
only_sql_js     = overlap_sql_js - overlap_all
total = only_python + only_sql + only_js + only_py_sql + only_py_js + only_sql_js + overlap_all

pct(n) = round(Int, 100 * n / total)
region_label(n) = "$(n)\n($(pct(n))%)"

# --- Circle geometry: symmetric three-circle layout ----------------------------
radius = 1.6
center_python     = Point2f(-0.65, 0.55)
center_sql        = Point2f(0.65, 0.55)
center_javascript = Point2f(0.0, -0.55)

# --- Plot -----------------------------------------------------------------------
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title           = "venn-basic · julia · makie · anyplot.ai",
    titlesize       = 20,
    titlecolor      = INK,
    backgroundcolor = PAGE_BG,
    aspect          = DataAspect(),
)
hidedecorations!(ax)
hidespines!(ax)
xlims!(ax, -2.6, 2.6)
ylims!(ax, -2.6, 2.6)

fill_alpha = 0.55
poly!(ax, Circle(center_python, radius);
      color = (IMPRINT_PALETTE[1], fill_alpha), strokecolor = INK_SOFT, strokewidth = 2)
poly!(ax, Circle(center_sql, radius);
      color = (IMPRINT_PALETTE[2], fill_alpha), strokecolor = INK_SOFT, strokewidth = 2)
poly!(ax, Circle(center_javascript, radius);
      color = (IMPRINT_PALETTE[3], fill_alpha), strokecolor = INK_SOFT, strokewidth = 2)

# Set name labels, placed outside each circle
text!(ax, -1.55, 2.05; text = set_labels[1], color = INK, fontsize = 22,
      font = :bold, align = (:center, :center))
text!(ax, 1.55, 2.05; text = set_labels[2], color = INK, fontsize = 22,
      font = :bold, align = (:center, :center))
text!(ax, 0.0, -2.2; text = set_labels[3], color = INK, fontsize = 22,
      font = :bold, align = (:center, :center))

# Region count labels
text!(ax, -1.35, 1.05; text = region_label(only_python), color = INK, fontsize = 15,
      align = (:center, :center))
text!(ax, 1.35, 1.05; text = region_label(only_sql), color = INK, fontsize = 15,
      align = (:center, :center))
text!(ax, 0.0, -1.55; text = region_label(only_js), color = INK, fontsize = 15,
      align = (:center, :center))
text!(ax, 0.0, 0.95; text = region_label(only_py_sql), color = INK, fontsize = 15,
      align = (:center, :center))
text!(ax, -0.65, -0.35; text = region_label(only_py_js), color = INK, fontsize = 15,
      align = (:center, :center))
text!(ax, 0.65, -0.35; text = region_label(only_sql_js), color = INK, fontsize = 15,
      align = (:center, :center))
text!(ax, 0.0, 0.15; text = region_label(overlap_all), color = INK, fontsize = 15,
      align = (:center, :center))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
