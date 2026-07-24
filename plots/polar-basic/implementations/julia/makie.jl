# anyplot.ai
# polar-basic: Basic Polar Chart
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-07-24

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const BRAND = IMPRINT_PALETTE[1]  # Imprint palette position 1 — always first series

# --- Data -----------------------------------------------------------------
# Hourly household energy consumption (kWh) — a bimodal morning/evening pattern
hour = 0:23
morning_peak = 1.2 .* exp.(-0.5 .* ((hour .- 7) ./ 1.5) .^ 2)
evening_peak = 2.0 .* exp.(-0.5 .* ((hour .- 19) ./ 2.0) .^ 2)
noise = 0.12 .* randn(length(hour))
consumption = 0.8 .+ morning_peak .+ evening_peak .+ noise

theta = collect(hour) ./ 24 .* 2pi
theta_closed = vcat(theta, 2pi)              # wrap the last segment back to hour 0
consumption_closed = vcat(consumption, consumption[1])

# --- Plot -------------------------------------------------------------------
fig = Figure(size = (1200, 1200), backgroundcolor = PAGE_BG)

ax = PolarAxis(
    fig[1, 1];
    theta_0 = -pi / 2,                         # midnight at the top
    direction = -1,                            # hours advance clockwise, like a clock face
    title = "polar-basic · julia · makie · anyplot.ai",
    titlesize = 20,
    titlecolor = INK,
    backgroundcolor = PAGE_BG,
    thetaticks = (
        0:(pi / 4):(7pi / 4),
        ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
    ),
    thetaticklabelsize = 14,
    thetaticklabelcolor = INK_SOFT,
    rticks = 0:1:5,
    rtickformat = values -> ["$(v) kWh" for v in values],
    rtickangle = pi / 8,                       # offset from the 00:00 spoke to avoid label clash
    rticklabelsize = 12,
    rticklabelcolor = INK_SOFT,
    spinecolor = INK_SOFT,
    rgridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
    thetagridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

band!(ax, theta_closed, zeros(length(theta_closed)), consumption_closed; color = (BRAND, 0.15))
lines!(ax, theta_closed, consumption_closed; color = BRAND, linewidth = 3)
scatter!(
    ax, theta, consumption;
    color = BRAND, markersize = 16, strokewidth = 1.5, strokecolor = PAGE_BG,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
