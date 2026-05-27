# anyplot.ai
# map-animated-temporal: Animated Map over Time
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-05-27

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Grid color as explicit RGBAf (avoids N0f8 promotion ambiguity)
const GRID_COLOR = THEME == "light" ?
    RGBAf(26f0/255f0, 26f0/255f0, 23f0/255f0, 0.10f0) :
    RGBAf(240f0/255f0, 239f0/255f0, 232f0/255f0, 0.10f0)

# Sequential colormap: anyplot brand green → blue (single-polarity continuous)
const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# Earthquake aftershock sequence (synthetic, central Japan)
const N_STEPS  = 12
const MAIN_LAT = 34.5f0
const MAIN_LON = 135.8f0
const N_ROWS   = 3
const N_COLS   = 4

event_lats = Float32[MAIN_LAT]
event_lons = Float32[MAIN_LON]
event_mags = Float32[7.2f0]
event_days = Int[1]

for day in 1:N_STEPS
    n_shocks = max(3, round(Int, 55 / day))
    spread   = 0.25f0 + 0.07f0 * sqrt(Float32(day))
    for _ in 1:n_shocks
        push!(event_lats, MAIN_LAT + Float32(randn()) * spread)
        push!(event_lons, MAIN_LON + Float32(randn()) * spread * 1.3f0)
        push!(event_mags, 2.5f0 + Float32(rand()) * 3.2f0)
        push!(event_days, day)
    end
end

const LAT_LO = MAIN_LAT - 2.0f0
const LAT_HI = MAIN_LAT + 2.0f0
const LON_LO = MAIN_LON - 2.5f0
const LON_HI = MAIN_LON + 2.5f0

# Figure: landscape 1600×900 → 3200×1800 at px_per_unit=2
fig = Figure(
    size            = (1600, 900),
    fontsize        = 11,
    backgroundcolor = PAGE_BG,
)

Label(fig[0, 1:N_COLS],
    "map-animated-temporal · julia · makie · anyplot.ai",
    fontsize   = 20,
    color      = INK,
    font       = :bold,
    padding    = (0, 0, 8, 2),
    tellwidth  = false,
    tellheight = true,
)

# Small multiples: 12 daily cumulative snapshots in 3×4 grid
for i in 1:N_STEPS
    row = div(i - 1, N_COLS) + 1
    col = mod(i - 1, N_COLS) + 1

    ax = Axis(
        fig[row, col];
        title              = "Day $i",
        titlesize          = 11,
        titlecolor         = INK,
        backgroundcolor    = PAGE_BG,
        topspinevisible    = false,
        rightspinevisible  = false,
        leftspinecolor     = INK_SOFT,
        bottomspinecolor   = INK_SOFT,
        xticklabelsize     = 8,
        yticklabelsize     = 8,
        xticklabelcolor    = INK_SOFT,
        yticklabelcolor    = INK_SOFT,
        xtickcolor         = INK_SOFT,
        ytickcolor         = INK_SOFT,
        xgridcolor         = GRID_COLOR,
        ygridcolor         = GRID_COLOR,
        xticklabelsvisible = (row == N_ROWS),
        yticklabelsvisible = (col == 1),
        xlabel             = "Longitude",
        ylabel             = "Latitude",
        xlabelcolor        = INK_SOFT,
        ylabelcolor        = INK_SOFT,
        xlabelsize         = 8,
        ylabelsize         = 8,
        xlabelvisible      = (row == N_ROWS),
        ylabelvisible      = (col == 1),
    )
    limits!(ax, LON_LO, LON_HI, LAT_LO, LAT_HI)

    # Cumulative events up to day i
    mask      = event_days .<= i
    lons_cum  = event_lons[mask]
    lats_cum  = event_lats[mask]
    mags_cum  = event_mags[mask]
    days_cum  = Float32.(event_days[mask])
    time_frac = (days_cum .- 1f0) ./ Float32(N_STEPS - 1)
    sizes_pt  = clamp.((mags_cum .- 2.5f0) .* 2.5f0 .+ 3f0, 2f0, 11f0)

    # Color encodes age: green = early (day 1), blue = late (day 12)
    scatter!(ax, lons_cum, lats_cum;
        color       = time_frac,
        colormap    = ANYPLOT_SEQ,
        markersize  = sizes_pt,
        strokewidth = 0,
        alpha       = 0.7,
    )

    # Mainshock star marker (M7.2 epicentre)
    scatter!(ax, [MAIN_LON], [MAIN_LAT];
        color       = colorant"#AE3030",
        markersize  = 12,
        marker      = :star5,
        strokewidth = 0.8f0,
        strokecolor = INK,
    )
end

# Shared colorbar
Colorbar(fig[N_ROWS + 1, 1:N_COLS];
    colormap       = ANYPLOT_SEQ,
    limits         = (1f0, Float32(N_STEPS)),
    label          = "Day of sequence  (green = early  |  blue = late)",
    labelcolor     = INK,
    tickcolor      = INK_SOFT,
    ticklabelcolor = INK_SOFT,
    ticklabelsize  = 10,
    labelsize      = 10,
    vertical       = false,
    height         = 14,
)

rowsize!(fig.layout, 0, Fixed(50))
rowsize!(fig.layout, N_ROWS + 1, Fixed(60))
colgap!(fig.layout, 6)
rowgap!(fig.layout, 6)

save("plot-$(THEME).png", fig; px_per_unit = 2)
