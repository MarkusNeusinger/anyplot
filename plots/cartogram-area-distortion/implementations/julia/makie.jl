# anyplot.ai
# cartogram-area-distortion: Cartogram with Area Distortion by Data Value
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 78/100 | Created: 2026-06-08

using CairoMakie
using Colors

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Imprint palette — positions 1–4 for four US census regions
const REGION_COLORS = [
    colorant"#009E73",  # Northeast — brand green
    colorant"#C475FD",  # South     — lavender
    colorant"#4467A3",  # Midwest   — blue
    colorant"#BD8233",  # West      — ochre
]

# US states: (abbreviation, longitude, latitude, population_millions, region_index)
# Alaska and Hawaii repositioned to lower-left corner for display
const STATE_DATA = [
    ("AL", -86.7,  32.7, 5.03,  2),
    ("AK", -127.0, 26.5, 0.73,  4),
    ("AZ", -111.7, 34.3, 7.15,  4),
    ("AR", -92.4,  34.9, 3.01,  2),
    ("CA", -119.7, 37.2, 39.54, 4),
    ("CO", -105.5, 39.0, 5.77,  4),
    ("CT", -72.7,  41.6, 3.60,  1),
    ("DE", -75.5,  39.0, 0.99,  2),
    ("FL", -81.5,  28.1, 21.54, 2),
    ("GA", -83.4,  32.7, 10.71, 2),
    ("HI", -120.5, 24.0, 1.44,  4),
    ("ID", -114.5, 44.4, 1.83,  4),
    ("IL", -89.2,  40.1, 12.81, 3),
    ("IN", -86.3,  40.3, 6.79,  3),
    ("IA", -93.1,  42.1, 3.19,  3),
    ("KS", -98.4,  38.5, 2.94,  3),
    ("KY", -84.3,  37.5, 4.51,  2),
    ("LA", -91.8,  31.2, 4.65,  2),
    ("ME", -69.2,  45.4, 1.36,  1),
    ("MD", -76.6,  39.0, 6.18,  2),
    ("MA", -71.5,  42.2, 7.03,  1),
    ("MI", -85.6,  44.3, 10.08, 3),
    ("MN", -94.3,  46.4, 5.71,  3),
    ("MS", -89.7,  32.7, 2.96,  2),
    ("MO", -92.3,  38.5, 6.15,  3),
    ("MT", -110.5, 46.9, 1.08,  4),
    ("NE", -99.9,  41.5, 1.96,  3),
    ("NV", -116.9, 39.5, 3.10,  4),
    ("NH", -71.6,  43.7, 1.38,  1),
    ("NJ", -74.4,  40.0, 9.29,  1),
    ("NM", -106.1, 34.4, 2.12,  4),
    ("NY", -75.4,  42.9, 20.20, 1),
    ("NC", -79.4,  35.6, 10.44, 2),
    ("ND", -100.5, 47.5, 0.78,  3),
    ("OH", -82.8,  40.4, 11.80, 3),
    ("OK", -97.5,  35.5, 3.96,  2),
    ("OR", -120.5, 43.9, 4.24,  4),
    ("PA", -77.2,  40.9, 13.00, 1),
    ("RI", -71.4,  41.7, 1.10,  1),
    ("SC", -80.9,  33.8, 5.12,  2),
    ("SD", -100.2, 44.4, 0.89,  3),
    ("TN", -86.7,  35.9, 6.91,  2),
    ("TX", -99.3,  31.5, 29.15, 2),
    ("UT", -111.1, 39.5, 3.27,  4),
    ("VT", -72.7,  44.0, 0.64,  1),
    ("VA", -78.5,  37.5, 8.63,  2),
    ("WA", -120.7, 47.4, 7.71,  4),
    ("WV", -80.7,  38.9, 1.79,  2),
    ("WI", -89.8,  44.5, 5.89,  3),
    ("WY", -107.6, 43.0, 0.58,  4),
]

abbrevs     = [s[1] for s in STATE_DATA]
lons        = Float64[s[2] for s in STATE_DATA]
lats        = Float64[s[3] for s in STATE_DATA]
pops        = Float64[s[4] for s in STATE_DATA]
region_idxs = Int[s[5] for s in STATE_DATA]
colors      = [REGION_COLORS[r] for r in region_idxs]

# Dorling layout jitter — offset crowded NE states to reduce circle/label overlap
const NE_JITTER = Dict(
    "CT" => (-0.5, -0.4),
    "RI" => ( 0.7,  0.0),
    "VT" => (-0.5,  0.5),
    "NH" => ( 0.6,  0.4),
    "DE" => ( 0.5, -0.4),
)
disp_lons = copy(lons)
disp_lats = copy(lats)
for (i, abbr) in enumerate(abbrevs)
    if haskey(NE_JITTER, abbr)
        disp_lons[i] += NE_JITTER[abbr][1]
        disp_lats[i] += NE_JITTER[abbr][2]
    end
end

# Marker sizes: area ∝ population; minimum enforced so tiny states remain visible
size_scale   = 44.0 / sqrt(maximum(pops))
marker_sizes = [max(sqrt(p) * size_scale, 8.0) for p in pops]

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

# Main Dorling cartogram axis
ax = Axis(
    fig[1, 1];
    title              = "cartogram-area-distortion · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Longitude",
    ylabel             = "Latitude",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

scatter!(ax, disp_lons, disp_lats;
    color       = colors,
    markersize  = marker_sizes,
    strokecolor = PAGE_BG,
    strokewidth = 1.5,
)

for i in eachindex(abbrevs)
    text!(ax, disp_lons[i], disp_lats[i];
        text     = abbrevs[i],
        align    = (:center, :center),
        fontsize = 10,
        color    = INK,
    )
end

xlims!(ax, -131.0, -64.0)
ylims!(ax, 22.5, 50.5)

# Right panel — reference map and census region legend
right_grid = fig[1, 2] = GridLayout()

# Reference map: equal-size dots at geographic centers for comparison with cartogram
ref_ax = Axis(
    right_grid[1, 1];
    title              = "Reference Map",
    titlesize          = 11,
    titlecolor         = INK,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = true,
    rightspinevisible  = true,
    leftspinevisible   = true,
    bottomspinevisible = true,
    topspinecolor      = INK_MUTED,
    rightspinecolor    = INK_MUTED,
    leftspinecolor     = INK_MUTED,
    bottomspinecolor   = INK_MUTED,
    xticksvisible      = false,
    yticksvisible      = false,
    xticklabelsvisible = false,
    yticklabelsvisible = false,
    xgridvisible       = false,
    ygridvisible       = false,
)
scatter!(ref_ax, lons, lats;
    color       = colors,
    markersize  = 5.0,
    strokecolor = PAGE_BG,
    strokewidth = 0.8,
)
xlims!(ref_ax, -131.0, -64.0)
ylims!(ref_ax, 22.5, 50.5)

# Census region legend
Legend(
    right_grid[2, 1],
    [MarkerElement(color = REGION_COLORS[i], marker = :circle, markersize = 18) for i in 1:4],
    ["Northeast", "South", "Midwest", "West"];
    title           = "Census Region",
    titlesize       = 13,
    titlecolor      = INK,
    labelsize       = 12,
    labelcolor      = INK_SOFT,
    framevisible    = true,
    framecolor      = INK_SOFT,
    backgroundcolor = ELEVATED_BG,
    padding         = (12, 12, 12, 12),
    rowgap          = 8,
)

# Caption
Label(
    fig[2, 1:2];
    text    = "Dorling cartogram — circle area ∝ state population (2020 US Census). Reference map shows equal-size geographic layout. AK/HI repositioned.",
    fontsize = 10,
    color   = INK_MUTED,
    halign  = :left,
)

# Layout proportions
colsize!(fig.layout, 1, Relative(0.78))
rowsize!(fig.layout, 1, Relative(0.92))
rowsize!(right_grid, 1, Fixed(140))

save("plot-$(THEME).png", fig; px_per_unit = 2)
