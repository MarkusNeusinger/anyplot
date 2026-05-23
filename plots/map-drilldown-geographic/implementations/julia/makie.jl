# anyplot.ai
# map-drilldown-geographic: Drillable Geographic Map
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 82/100 | Created: 2026-05-23

using CairoMakie
using Colors
using Random

Random.seed!(42)

const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#003D94"])

# World regions — annual sales ($B)
w_names = ["N. America", "Europe", "Asia-Pacific", "S. America", "Middle East", "Africa"]
w_lon   = Float64[-100.0,  15.0, 110.0, -60.0, 45.0, 20.0]
w_lat   = Float64[  45.0,  52.0,  25.0, -15.0, 25.0,  0.0]
w_vals  = Float64[   2.8,   2.1,   3.6,   1.4,  1.1,  0.7]

# US states — drill into North America
s_abbr  = ["CA", "TX", "NY", "FL", "WA", "IL", "MA", "CO"]
s_lon   = Float64[-119.0,  -99.0, -74.0, -81.0, -120.0, -89.0, -71.0, -105.0]
s_lat   = Float64[  37.0,   31.0,  43.0,  27.0,   47.0,  40.0,  42.0,   39.0]
s_vals  = Float64[  0.62,   0.48,  0.51,  0.38,   0.29,  0.25,  0.21,   0.18]

# California cities — drill into California (sorted ascending for bar chart)
c_names = ["Sacramento", "San Jose", "San Diego", "Los Angeles", "San Francisco"]
c_vals  = Float64[0.03, 0.07, 0.09, 0.19, 0.24]

# Normalize per level for color mapping
w_norm   = (w_vals .- minimum(w_vals)) ./ (maximum(w_vals) - minimum(w_vals))
s_norm   = (s_vals .- minimum(s_vals)) ./ (maximum(s_vals) - minimum(s_vals))
c_norm   = (c_vals .- minimum(c_vals)) ./ (maximum(c_vals) - minimum(c_vals))
c_colors = [ANYPLOT_SEQ[v] for v in c_norm]

fig = Figure(size=(1600, 900), fontsize=13, backgroundcolor=PAGE_BG)

Label(fig[0, 1:3],
    "Sales Drill-Down  ·  map-drilldown-geographic · julia · makie · anyplot.ai",
    fontsize=17, color=INK, font=:bold, halign=:center, padding=(0, 0, 4, 0),
)

# Panel 1 — World regions bubble map
ax1 = Axis(fig[1, 1];
    title="① World Regions",
    titlesize=14, titlecolor=INK,
    xlabel="Longitude", ylabel="Latitude",
    xlabelsize=11, ylabelsize=11,
    xlabelcolor=INK, ylabelcolor=INK,
    xticklabelsize=9, yticklabelsize=9,
    xticklabelcolor=INK_SOFT, yticklabelcolor=INK_SOFT,
    xtickcolor=INK_SOFT, ytickcolor=INK_SOFT,
    backgroundcolor=PAGE_BG,
    leftspinecolor=INK_SOFT, bottomspinecolor=INK_SOFT,
    topspinevisible=false, rightspinevisible=false,
    xgridvisible=false, ygridvisible=false,
)

scatter!(ax1, w_lon, w_lat;
    color=w_norm, colormap=ANYPLOT_SEQ, colorrange=(0.0, 1.0),
    markersize=28, strokewidth=1.2, strokecolor=INK_SOFT,
)
for i in eachindex(w_names)
    text!(ax1, w_lon[i], w_lat[i];
        text="$(w_names[i])\n\$$(w_vals[i])B",
        align=(:center, :bottom), offset=(0, 17),
        fontsize=8, color=INK_SOFT,
    )
end

# Panel 2 — US states bubble map
ax2 = Axis(fig[1, 2];
    title="② N. America → US States",
    titlesize=14, titlecolor=INK,
    xlabel="Longitude", ylabel="Latitude",
    xlabelsize=11, ylabelsize=11,
    xlabelcolor=INK, ylabelcolor=INK,
    xticklabelsize=9, yticklabelsize=9,
    xticklabelcolor=INK_SOFT, yticklabelcolor=INK_SOFT,
    xtickcolor=INK_SOFT, ytickcolor=INK_SOFT,
    backgroundcolor=PAGE_BG,
    leftspinecolor=INK_SOFT, bottomspinecolor=INK_SOFT,
    topspinevisible=false, rightspinevisible=false,
    xgridvisible=false, ygridvisible=false,
)

scatter!(ax2, s_lon, s_lat;
    color=s_norm, colormap=ANYPLOT_SEQ, colorrange=(0.0, 1.0),
    markersize=24, strokewidth=1.2, strokecolor=INK_SOFT,
)
for i in eachindex(s_abbr)
    text!(ax2, s_lon[i], s_lat[i];
        text=s_abbr[i],
        align=(:center, :bottom), offset=(0, 14),
        fontsize=9, color=INK_SOFT,
    )
end

# Panel 3 — California cities horizontal bar chart
ax3 = Axis(fig[1, 3];
    title="③ California → Cities",
    titlesize=14, titlecolor=INK,
    xlabel="Sales (\$B)", ylabel="",
    xlabelsize=11, ylabelsize=11,
    xlabelcolor=INK, ylabelcolor=INK,
    xticklabelsize=9, yticklabelsize=9,
    xticklabelcolor=INK_SOFT, yticklabelcolor=INK_SOFT,
    xtickcolor=INK_SOFT, ytickcolor=INK_SOFT,
    backgroundcolor=PAGE_BG,
    leftspinecolor=INK_SOFT, bottomspinecolor=INK_SOFT,
    topspinevisible=false, rightspinevisible=false,
    xgridvisible=false, ygridvisible=false,
    yticks=(1:5, c_names),
)

barplot!(ax3, 1:5, c_vals; direction=:x, color=c_colors)

# Shared colorbar — green = low, blue = high within each level
Colorbar(fig[2, 1:3];
    colormap=ANYPLOT_SEQ,
    limits=(0.0, 1.0),
    vertical=false,
    label="Relative Sales Volume (within each level)",
    labelsize=10, labelcolor=INK,
    ticklabelcolor=INK_SOFT, tickcolor=INK_SOFT,
    ticks=([0.0, 0.5, 1.0], ["Low", "Mid", "High"]),
    height=14, tellheight=true,
)

rowgap!(fig.layout, 1, 8)
rowgap!(fig.layout, 2, 6)
colgap!(fig.layout, 12)

save("plot-$(THEME).png", fig; px_per_unit=2)
