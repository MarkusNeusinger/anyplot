# anyplot.ai
# area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
# Library: makie 0.24.16 | Julia 1.13.3
# Quality: 83/100 | Updated: 2026-11-08

using CairoMakie
using Colors
using Random

Random.seed!(42)

const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const SKY_BG   = THEME == "light" ? colorant"#B8D8EF" : colorant"#0D1825"
# Dark-theme silhouette lifted to #5A6E8C: ~3.4:1 against the night sky
const MTN_FILL = THEME == "light" ? colorant"#262623" : colorant"#5A6E8C"
const BRAND    = colorant"#009E73"  # Imprint palette position 1

# Peaks: (position, elevation_m, name, left_flank, right_flank)
# Order is the real clockwise sweep seen from Gornergrat (SE → S → W → N → E);
# horizontal spacing is schematic, compressing the empty stretches of the 360° view
const PEAKS = [
    (  4.0, 4634.0, "Monte Rosa",      9.0, 10.0),
    ( 16.0, 4527.0, "Liskamm",         8.0,  8.0),
    ( 26.0, 4223.0, "Castor",          6.0,  5.0),
    ( 34.0, 4092.0, "Pollux",          5.0,  7.0),
    ( 46.0, 4164.0, "Breithorn",       8.0,  7.0),
    ( 72.0, 4478.0, "Matterhorn",      4.0,  5.5),
    ( 98.0, 4358.0, "Dent Blanche",   10.0,  7.0),
    (108.0, 4063.0, "Ober Gabelhorn",  6.0,  6.0),
    (120.0, 4221.0, "Zinalrothorn",    7.0,  6.0),
    (132.0, 4506.0, "Weisshorn",       9.0,  8.0),
    (150.0, 4545.0, "Dom",             7.0,  4.0),
    (155.0, 4491.0, "Täschhorn",       4.0,  6.0),
    (164.0, 4206.0, "Alphubel",        6.0,  6.0),
    (172.0, 4027.0, "Allalinhorn",     5.0,  5.0),
    (181.0, 4199.0, "Rimpfischhorn",   6.0,  5.0),
    (190.0, 4190.0, "Strahlhorn",      5.0,  8.0),
]
const ANCHOR = "Matterhorn"

# Unnamed sub-peaks and cols; the anchor horn is the steepest, narrowest summit,
# isolated by deep notches on both sides, with a Hörnli shoulder on its right flank
const SUBPEAKS = [
    ( 53.0, 3880.0, 4.0, 5.0),
    ( 60.0, 3350.0, 4.0, 5.0),
    ( 75.0, 3800.0, 1.0, 3.0),
    ( 84.0, 3560.0, 5.0, 5.0),
    ( 90.0, 3720.0, 5.0, 6.0),
    (141.0, 3700.0, 5.0, 5.0),
]

# Staggered label heights — three levels, set so no leader line crosses a neighbor's label
const LVL_A, LVL_B, LVL_C = 4790.0, 5010.0, 5230.0
const LABEL_YS = [
    LVL_B,  # Monte Rosa
    LVL_C,  # Liskamm
    LVL_A,  # Castor
    LVL_B,  # Pollux
    LVL_A,  # Breithorn
    LVL_C,  # Matterhorn
    LVL_B,  # Dent Blanche
    LVL_A,  # Ober Gabelhorn
    LVL_C,  # Zinalrothorn
    LVL_A,  # Weisshorn
    LVL_B,  # Dom
    LVL_C,  # Täschhorn
    LVL_A,  # Alphubel
    LVL_B,  # Allalinhorn
    LVL_C,  # Rimpfischhorn
    LVL_A,  # Strahlhorn
]

const BASELINE = 2780.0
const N        = 1600

angles = collect(LinRange(-6.0, 197.0, N))

# Ridgeline = max over asymmetric tent functions (sharp apex, linear flanks)
tents = vcat([(pa, pe, lw, rw) for (pa, pe, _, lw, rw) in PEAKS], SUBPEAKS)
ridgeline = [maximum(
                 a - pa <= -lw || a - pa >= rw ? BASELINE :
                 a < pa ? BASELINE + (pe - BASELINE) * (a - pa + lw) / lw :
                          pe - (pe - BASELINE) * (a - pa) / rw
                 for (pa, pe, lw, rw) in tents)
             for a in angles]

# Irregular rocky jaggedness, damped near summits to preserve sharp apexes
jitter = 30.0 .* (rand(N) .- 0.5)
for (pa, pe, pname, lw, rw) in PEAKS
    for i in eachindex(angles)
        d = abs(angles[i] - pa)
        d < 3.0 && (jitter[i] *= d / 3.0)
    end
end
ridgeline .+= jitter

# Restore exact summit elevations after jitter
for (pa, pe, pname, lw, rw) in PEAKS
    ridgeline[argmin(abs.(angles .- pa))] = pe
end
ridgeline = max.(ridgeline, BASELINE)

# Silhouette polygon: ridgeline + closed base
sil_pts = [Point2f(a, r) for (a, r) in zip(angles, ridgeline)]
push!(sil_pts, Point2f(Float32(angles[end]), 2400.0f0))
push!(sil_pts, Point2f(Float32(angles[1]),   2400.0f0))

# Composite Makie theme — consolidates all chrome into one reusable Theme object
const ANYPLOT_MAKIE_THEME = Theme(
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
    Axis = (
        backgroundcolor   = SKY_BG,
        titlecolor        = INK,
        xlabelcolor       = INK,
        ylabelcolor       = INK,
        xticklabelcolor   = INK_SOFT,
        yticklabelcolor   = INK_SOFT,
        xtickcolor        = INK_SOFT,
        ytickcolor        = INK_SOFT,
        leftspinecolor    = INK_SOFT,
        bottomspinecolor  = INK_SOFT,
        topspinevisible   = false,
        rightspinevisible = false,
        xgridvisible      = false,
        ygridvisible      = false,
    ),
)

with_theme(ANYPLOT_MAKIE_THEME) do
    title_str = "Wallis Peaks Panorama · area-mountain-panorama · julia · makie · anyplot.ai"
    title_sz  = round(Int, 20 * min(1.0, 67 / length(title_str)))

    fig = Figure(size = (1600, 900), backgroundcolor = PAGE_BG)

    ax = Axis(
        fig[2, 1];
        title          = title_str,
        titlesize      = title_sz,
        xlabel         = "Clockwise sweep from Gornergrat:  SE  →  S  →  W  →  N  →  E",
        ylabel         = "Elevation (m)",
        xlabelsize     = 14,
        ylabelsize     = 14,
        yticklabelsize = 14,
        xticksvisible      = false,
        xticklabelsvisible = false,
        yticks         = 2500:500:5000,
    )

    # Makie layout: subtitle Label sits above the axis panel in row 1
    Label(fig[1, 1], "Swiss Alps · Wallis · 360° view from Gornergrat (3100 m) · schematic horizontal spacing";
          fontsize = 13, color = INK_SOFT, tellwidth = false)
    rowgap!(fig.layout, 1, 2)

    xlims!(ax, -6.0, 197.0)
    ylims!(ax, 2450.0, 5450.0)

    # Mountain silhouette fill
    poly!(ax, sil_pts; color = MTN_FILL, strokewidth = 0)

    # Peak markers and staggered labels with leader lines; the anchor summit gets
    # a larger marker, a brand-green leader and a bold, larger label
    for (i, (pa, pe, name, lw, rw)) in enumerate(PEAKS)
        is_anchor = name == ANCHOR
        lh = LABEL_YS[i]
        lines!(ax, [pa, pa], [pe + 40.0, lh - 40.0];
               color = is_anchor ? BRAND : INK_SOFT, linewidth = is_anchor ? 2.0 : 1.0)
        scatter!(ax, [pa], [pe]; color = BRAND, markersize = is_anchor ? 18 : 9,
                 strokewidth = is_anchor ? 2.0 : 0.0, strokecolor = PAGE_BG)
        text!(ax, pa, lh; text = "$(name)\n$(Int(pe)) m", color = INK,
              fontsize = is_anchor ? 18 : 15, font = is_anchor ? :bold : :regular,
              align = (:center, :bottom))
    end

    save("plot-$(THEME).png", fig; px_per_unit = 2)
end
