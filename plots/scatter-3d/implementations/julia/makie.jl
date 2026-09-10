# anyplot.ai
# scatter-3d: 3D Scatter Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 81/100 | Created: 2026-09-10

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens ------------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const GRID        = RGBAf(INK.r, INK.g, INK.b, 0.15)

const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data ----------------------------------------------------------------------
# Sensor readings from a machine feature space (vibration, temperature,
# pressure), forming three distinct clusters by operating mode.
n_per_mode = 60
modes = ["Idle", "Normal", "Stress"]
centers = [(1.0, 40.0, 1.0), (3.5, 65.0, 2.6), (6.5, 92.0, 4.4)]
spreads = [(0.35, 3.0, 0.25), (0.5, 4.0, 0.35), (0.7, 5.0, 0.5)]

vibration = Float64[]
temperature = Float64[]
pressure = Float64[]
mode_idx = Int[]

for (i, (cx, cy, cz)) in enumerate(centers)
    sx, sy, sz = spreads[i]
    append!(vibration, cx .+ sx .* randn(n_per_mode))
    append!(temperature, cy .+ sy .* randn(n_per_mode))
    append!(pressure, cz .+ sz .* randn(n_per_mode))
    append!(mode_idx, fill(i, n_per_mode))
end

# --- Plot ------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis3(
    fig[1, 1];
    title             = "scatter-3d · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Vibration (mm/s)",
    ylabel            = "Temperature (°C)",
    zlabel            = "Pressure (bar)",
    xlabelsize        = 14,
    ylabelsize        = 14,
    zlabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    zlabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    zticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    zticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    ztickcolor        = INK_SOFT,
    xspinecolor_1     = INK_SOFT, xspinecolor_2 = INK_SOFT, xspinecolor_3 = INK_SOFT,
    yspinecolor_1     = INK_SOFT, yspinecolor_2 = INK_SOFT, yspinecolor_3 = INK_SOFT,
    zspinecolor_1     = INK_SOFT, zspinecolor_2 = INK_SOFT, zspinecolor_3 = INK_SOFT,
    xgridcolor        = GRID,
    ygridcolor        = GRID,
    zgridcolor        = GRID,
    xypanelcolor      = ELEVATED_BG,
    xzpanelcolor      = ELEVATED_BG,
    yzpanelcolor      = ELEVATED_BG,
    backgroundcolor   = PAGE_BG,
    azimuth           = 1.1 * pi,
    elevation         = 0.18 * pi,
    aspect            = (1, 1, 1),
)

for (i, name) in enumerate(modes)
    sel = mode_idx .== i
    scatter!(
        ax, vibration[sel], temperature[sel], pressure[sel];
        color = IMPRINT_PALETTE[i], markersize = 14,
        strokewidth = 0.5, strokecolor = PAGE_BG, label = name,
    )
end

axislegend(
    ax; position = :lt, framevisible = false, labelcolor = INK,
    labelsize = 12, backgroundcolor = :transparent,
)

# --- Save --------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
