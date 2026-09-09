# anyplot.ai
# venn-basic: Venn Diagram
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 94/100 | Created: 2026-09-09

using CairoMakie
using Colors

# --- Theme tokens -------------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG      = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG  = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK          = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT     = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3",
]

# --- Data: developer skill survey (n = 270 engineers) --------------------------
set_labels = ["Python", "SQL", "JavaScript"]
size_python, size_sql, size_js = 145, 120, 95
overlap_py_sql, overlap_py_js, overlap_sql_js = 45, 35, 25
overlap_all = 15

only_python = size_python - overlap_py_sql - overlap_py_js + overlap_all
only_sql    = size_sql - overlap_py_sql - overlap_sql_js + overlap_all
only_js     = size_js - overlap_py_js - overlap_sql_js + overlap_all
only_py_sql = overlap_py_sql - overlap_all
only_py_js  = overlap_py_js - overlap_all
only_sql_js = overlap_sql_js - overlap_all
total = only_python + only_sql + only_js + only_py_sql + only_py_js + only_sql_js + overlap_all

# --- Circle geometry: radii scaled by sqrt(set size) for an area-proportional
#     impression; centers pulled in toward the largest circle by the same
#     ratio so the three circles keep overlapping cleanly. ---------------------
base_radius = 1.6
radius_python = base_radius * sqrt(size_python / size_python)
radius_sql    = base_radius * sqrt(size_sql / size_python)
radius_js     = base_radius * sqrt(size_js / size_python)

center_python = Point2f(-0.65, 0.55)
center_sql    = Point2f(0.65, 0.55) * (radius_sql / base_radius)
center_js     = Point2f(0.0, -0.55) * (radius_js / base_radius)

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
xlims!(ax, -2.5, 2.5)
ylims!(ax, -2.3, 2.5)

fill_alpha = 0.55
poly!(ax, Circle(center_python, radius_python);
      color = (IMPRINT_PALETTE[1], fill_alpha), strokecolor = INK_SOFT, strokewidth = 2)
poly!(ax, Circle(center_sql, radius_sql);
      color = (IMPRINT_PALETTE[2], fill_alpha), strokecolor = INK_SOFT, strokewidth = 2)
poly!(ax, Circle(center_js, radius_js);
      color = (IMPRINT_PALETTE[3], fill_alpha), strokecolor = INK_SOFT, strokewidth = 2)

# Set name labels, placed outside each circle
text!(ax, -1.55, 2.05; text = set_labels[1], color = INK, fontsize = 22,
      font = :bold, align = (:center, :center))
text!(ax, 1.41, 1.86; text = set_labels[2], color = INK, fontsize = 22,
      font = :bold, align = (:center, :center))
text!(ax, 0.0, -1.78; text = set_labels[3], color = INK, fontsize = 22,
      font = :bold, align = (:center, :center))

# Region count labels (count + percentage, inline — no helper functions)
text!(ax, -1.35, 1.05; text = "$(only_python)\n($(round(Int, 100 * only_python / total))%)",
      color = INK, fontsize = 17, align = (:center, :center))
text!(ax, 1.23, 0.96; text = "$(only_sql)\n($(round(Int, 100 * only_sql / total))%)",
      color = INK, fontsize = 17, align = (:center, :center))
text!(ax, 0.0, -1.25; text = "$(only_js)\n($(round(Int, 100 * only_js / total))%)",
      color = INK, fontsize = 17, align = (:center, :center))
text!(ax, -0.04, 0.88; text = "$(only_py_sql)\n($(round(Int, 100 * only_py_sql / total))%)",
      color = INK, fontsize = 17, align = (:center, :center))
text!(ax, -0.59, -0.08; text = "$(only_py_js)\n($(round(Int, 100 * only_py_js / total))%)",
      color = INK, fontsize = 17, align = (:center, :center))
text!(ax, 0.56, -0.12; text = "$(only_sql_js)\n($(round(Int, 100 * only_sql_js / total))%)",
      color = INK, fontsize = 17, align = (:center, :center))

# Focal point: the triple overlap is the rarest — and most interesting —
# combination, so it gets a soft halo backdrop plus a bolder, larger label.
poly!(ax, Circle(Point2f(0.0, 0.20), 0.32);
      color = (ELEVATED_BG, 0.9), strokecolor = INK_SOFT, strokewidth = 1)
text!(ax, 0.0, 0.20; text = "$(overlap_all)\n($(round(Int, 100 * overlap_all / total))%)",
      color = INK, fontsize = 19, font = :bold, align = (:center, :center))

# Makie-distinctive touch: a grid-layout callout row (not axis text) that
# turns the triple-overlap number into a short data story.
Label(
    fig[2, 1],
    "$(overlap_all) engineers ($(round(Int, 100 * overlap_all / total))%) are full-stack — fluent in Python, SQL, and JavaScript alike, the rarest combination in the survey.";
    fontsize = 15,
    color = INK_SOFT,
    tellwidth = false,
)
rowgap!(fig.layout, 10)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
