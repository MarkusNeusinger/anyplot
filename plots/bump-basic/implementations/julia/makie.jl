# anyplot.ai
# bump-basic: Basic Bump Chart
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: pending | Created: 2026-05-29

using CairoMakie
using Colors
using DataFrames
using Random

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const GRID_INK    = THEME == "light" ?
    RGBAf(26 / 255, 26 / 255, 23 / 255, 0.12) :
    RGBAf(240 / 255, 239 / 255, 232 / 255, 0.12)

const IMPRINT_PALETTE = [
    colorant"#009E73",
    colorant"#C475FD",
    colorant"#4467A3",
    colorant"#BD8233",
    colorant"#AE3030",
    colorant"#2ABCCD",
]

Random.seed!(42)

# Columns: set these to your table's column names
const COMPANY = "Company"   # role: group
const QUARTER = "Quarter"   # role: category
const RANK = "Rank"         # role: value

# Data: tech startup investor-ranking competition, Q1 2023 to Q2 2024
quarter_labels = ["Q1'23", "Q2'23", "Q3'23", "Q4'23", "Q1'24", "Q2'24"]
rankings = [
    2  1  1  1  1  2;   # NovaTech
    4  3  2  2  2  1;   # PulseAI
    1  2  3  3  3  3;   # CircleCloud
    3  4  4  4  4  4;   # ApexRobotics
    6  5  5  5  5  5;   # QuantumIO
    5  6  6  6  6  6;   # ShieldSec
]
company_names = ["NovaTech", "PulseAI", "CircleCloud", "ApexRobotics", "QuantumIO", "ShieldSec"]
df = DataFrame(
    COMPANY => repeat(company_names; inner = length(quarter_labels)),
    QUARTER => repeat(quarter_labels, length(company_names)),
    RANK => vec(permutedims(rankings)),
)

# Plot
companies = unique(df[!, COMPANY])
quarters = unique(df[!, QUARTER])
n_companies = length(companies)

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "bump-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = QUARTER,
    ylabel             = RANK,
    xlabelsize         = 16,
    ylabelsize         = 16,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 14,
    yticklabelsize     = 14,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xticks             = (eachindex(quarters), quarters),
    yticks             = 1:maximum(df[!, RANK]),
    yreversed          = true,
    xgridvisible       = false,
    ygridvisible       = true,
    ygridcolor         = GRID_INK,
    xminorgridvisible  = false,
    yminorgridvisible  = false,
    limits             = (0.7, length(quarters) + 0.3, nothing, nothing),
)

for (i, company) in enumerate(companies)
    rows = df[df[!, COMPANY] .== company, :]
    x = [findfirst(==(q), quarters) for q in rows[!, QUARTER]]
    lines!(ax, x, rows[!, RANK]; color = IMPRINT_PALETTE[i], linewidth = 3.5)
    scatter!(ax, x, rows[!, RANK];
        color       = IMPRINT_PALETTE[i],
        markersize  = 16,
        strokecolor = PAGE_BG,
        strokewidth = 2,
    )
end

legend_elements = [LineElement(color = IMPRINT_PALETTE[i], linewidth = 3.5) for i in 1:n_companies]
Legend(
    fig[1, 2],
    legend_elements,
    companies,
    COMPANY;
    titlecolor      = INK,
    backgroundcolor = ELEVATED_BG,
    framecolor      = INK_SOFT,
    labelcolor      = INK,
    labelsize       = 14,
)

# Proportion the legend column to ~18% of figure width using colsize!
colsize!(fig.layout, 2, Relative(0.18))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
