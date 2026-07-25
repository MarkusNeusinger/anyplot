# anyplot.ai
# step-basic: Basic Step Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-07-25

using CairoMakie
using Colors

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data --------------------------------------------------------------------
# Open checkout lanes at a retail store — staffing changes at discrete times
# throughout the day, holding constant until the next adjustment ('post' step).
hours = [6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
open_lanes = [2, 4, 7, 9, 8, 10, 12, 8, 4, 0]

# Expand to 'post'-step coordinates so the area under the stairs can be
# shaded with band!() — a Makie-distinctive way to give the step curve
# visual weight instead of a bare line.
step_x = Float64[]
step_y = Float64[]
for i in 1:length(hours)-1
    push!(step_x, hours[i]); push!(step_y, open_lanes[i])
    push!(step_x, hours[i+1]); push!(step_y, open_lanes[i])
end
push!(step_x, hours[end]); push!(step_y, open_lanes[end])

peak_idx = argmax(open_lanes)

# --- Plot ----------------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "Checkout Lanes Open · step-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Time of Day",
    ylabel             = "Open Checkout Lanes",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xticks             = (hours, [lpad(h, 2, '0') * ":00" for h in hours]),
)
xlims!(ax, 5.5, 24.5)
ylims!(ax, -0.5, 13.5)

band!(ax, step_x, zeros(length(step_x)), step_y;
    color = (IMPRINT_PALETTE[1], 0.15))
stairs!(ax, hours, open_lanes; color = IMPRINT_PALETTE[1], linewidth = 3, step = :post)
scatter!(ax, hours, open_lanes;
    color = IMPRINT_PALETTE[1], markersize = 16,
    strokewidth = 1.5, strokecolor = PAGE_BG)
scatter!(ax, [hours[peak_idx]], [open_lanes[peak_idx]];
    color = IMPRINT_PALETTE[1], markersize = 24,
    strokewidth = 2, strokecolor = PAGE_BG)

# --- Save ----------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
