# anyplot.ai
# line-basic: Basic Line Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 78/100 | Created: 2026-08-24

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const BRAND = IMPRINT_PALETTE[1]

# --- Data ---------------------------------------------------------------
# Hourly temperature readings over a single day (24 hourly samples).
hours = 0:23
base_curve = 14 .+ 9 .* sin.((hours .- 6) .* (pi / 14))
temperatures = base_curve .+ randn(length(hours)) .* 0.6
temperatures[1:6] .-= 0.4 .* (6 .- (1:6))

# --- Plot -----------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

title_str = "line-basic · julia · makie · anyplot.ai"

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Hour of Day",
    ylabel             = "Temperature (°C)",
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
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
    xticks             = (0:4:23, string.(0:4:23) .* ":00"),
)

# Shade the midday plateau to give the chart a focal point before drawing the line.
vspan!(ax, 10.5, 15.5; color = RGBAf(BRAND.r, BRAND.g, BRAND.b, 0.08))

lines!(ax, hours, temperatures; color = BRAND, linewidth = 3.5)
scatter!(ax, hours, temperatures; color = BRAND, markersize = 10, strokewidth = 0)

# Highlight and label the daily peak.
peak_idx = argmax(temperatures)
peak_hour, peak_temp = hours[peak_idx], temperatures[peak_idx]
scatter!(ax, [peak_hour], [peak_temp]; color = BRAND, markersize = 16, strokewidth = 2, strokecolor = INK)
text!(
    ax, peak_hour, peak_temp;
    text     = "Peak: $(round(peak_temp, digits = 1))°C",
    align    = (:center, :bottom),
    offset   = (0, 12),
    fontsize = 13,
    color    = INK,
)

xlims!(ax, -0.5, 23.5)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
