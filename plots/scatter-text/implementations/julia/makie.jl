# anyplot.ai
# scatter-text: Scatter Plot with Text Labels Instead of Points
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint palette — 8 hues, theme-independent, hybrid-v3 sort
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data -----------------------------------------------------------------
# Fictional companies positioned by revenue growth vs. profit margin —
# competitive-landscape mapping where the company name matters more than density.
sectors = ["Technology", "Healthcare", "Finance", "Energy"]

companies = Dict(
    "Technology" => ["NovaTech", "ByteForge", "QuantumEdge", "SiliconLoop", "CloudSpire", "DataForge", "PixelWorks"],
    "Healthcare" => ["VitalCure", "BioNova", "MediSphere", "PulseCare", "GenomeWorks", "CarePoint", "TheraLink"],
    "Finance" => ["CapitalArc", "TrustBridge", "LedgerPeak", "FiscalCore", "AssetWave", "VaultStream", "PrimeYield"],
    "Energy" => ["SolarPeak", "WindForge", "HydroCore", "GeoVolt", "EcoGrid", "TerraPower", "BrightFuel"],
)

# (growth_mean, growth_std, margin_mean, margin_std) per sector
cluster_params = Dict(
    "Technology" => (28.0, 6.0, 18.0, 5.0),
    "Healthcare" => (14.0, 4.0, 24.0, 5.0),
    "Finance" => (6.0, 5.0, 22.0, 5.5),
    "Energy" => (10.0, 7.0, 10.0, 6.0),
)

labels = String[]
growth = Float64[]
margin = Float64[]
point_colors = RGB{Float64}[]

for (i, sector) in enumerate(sectors)
    growth_mean, growth_std, margin_mean, margin_std = cluster_params[sector]
    for name in companies[sector]
        push!(labels, name)
        push!(growth, growth_mean + growth_std * randn())
        push!(margin, margin_mean + margin_std * randn())
        push!(point_colors, IMPRINT_PALETTE[i])
    end
end

# --- Plot -------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "scatter-text · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Revenue Growth (%)",
    ylabel             = "Profit Margin (%)",
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
)

text!(
    ax, Point2f.(growth, margin);
    text = labels,
    color = point_colors,
    fontsize = 18,
    font = :bold,
    align = (:center, :center),
)

xlims!(ax, -6, 42)
ylims!(ax, -2, 36)

legend_elements = [PolyElement(color = IMPRINT_PALETTE[i], strokecolor = :transparent) for i in 1:length(sectors)]
Legend(
    fig[1, 2], legend_elements, sectors, "Sector";
    framevisible = false,
    labelcolor = INK_SOFT,
    titlecolor = INK,
    backgroundcolor = PAGE_BG,
)
colsize!(fig.layout, 1, Relative(0.85))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
