# anyplot.ai
# polar-line: Polar Line Plot
# Library: Makie.jl 0.21.9 | Julia 1.11
# Quality: pending | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data -----------------------------------------------------------------
# Average monthly rainfall (mm) across three climate zones — a seasonal cycle
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
months = 0:11

tropical = 180 .+ 60 .* sin.(2pi .* (months .- 3) ./ 12) .+ 8 .* randn(12)
temperate = 90 .+ 40 .* sin.(2pi .* (months .- 9) ./ 12) .+ 6 .* randn(12)
arid = 25 .+ 15 .* sin.(2pi .* months ./ 12) .+ 3 .* randn(12)

tropical = max.(tropical, 5.0)
temperate = max.(temperate, 5.0)
arid = max.(arid, 2.0)

theta = collect(months) ./ 12 .* 2pi
theta_closed = vcat(theta, 2pi)  # wrap December back to January to close each loop

tropical_closed = vcat(tropical, tropical[1])
temperate_closed = vcat(temperate, temperate[1])
arid_closed = vcat(arid, arid[1])

# --- Plot -------------------------------------------------------------------
fig = Figure(size = (1200, 1200), backgroundcolor = PAGE_BG)

ax = PolarAxis(
    fig[1, 1];
    theta_0 = pi / 2,                  # January at the top
    direction = 1,                     # months advance counter-clockwise
    title = "polar-line · julia · makie · anyplot.ai",
    titlesize = 20,
    titlecolor = INK,
    backgroundcolor = PAGE_BG,
    thetaticks = (0:(pi / 6):(11pi / 6), month_labels),
    thetaticklabelsize = 14,
    thetaticklabelcolor = INK_SOFT,
    rticks = 0:50:250,
    rtickformat = values -> ["$(round(Int, v)) mm" for v in values],
    rtickangle = pi / 12,               # offset from the January spoke to avoid label clash
    rticklabelsize = 12,
    rticklabelcolor = INK_SOFT,
    spinecolor = INK_SOFT,
    rgridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
    thetagridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

lines!(ax, theta_closed, tropical_closed; color = IMPRINT_PALETTE[1], linewidth = 3.5)
lines!(ax, theta_closed, temperate_closed; color = IMPRINT_PALETTE[2], linewidth = 3.5)
lines!(ax, theta_closed, arid_closed; color = IMPRINT_PALETTE[3], linewidth = 3.5)

Legend(
    fig[1, 2],
    [LineElement(color = IMPRINT_PALETTE[1], linewidth = 3.5),
     LineElement(color = IMPRINT_PALETTE[2], linewidth = 3.5),
     LineElement(color = IMPRINT_PALETTE[3], linewidth = 3.5)],
    ["Tropical", "Temperate", "Arid"];
    labelsize = 16,
    labelcolor = INK,
    backgroundcolor = ELEVATED_BG,
    framevisible = false,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
