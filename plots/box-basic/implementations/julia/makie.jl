# anyplot.ai
# box-basic: Basic Box Plot
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: pending | Created: 2026-05-28

using CairoMakie
using Colors
using DataFrames
using Random

# Theme tokens
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint palette
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# Columns: set these to your table's column names
const DEPARTMENT = "Department"            # role: category
const SALARY = "Annual Salary (K USD)"     # role: value

# Data: replace this block with your own table, for example df = CSV.read("salaries.csv", DataFrame)
Random.seed!(42)
dept_names = ["Engineering", "Marketing", "Finance", "Sales", "Operations"]
n_per_dept = [120, 80, 90, 100, 110]
dept_means = [95.0, 72.0, 88.0, 68.0, 62.0]
dept_stds  = [18.0, 14.0, 16.0, 15.0, 10.0]
df = DataFrame(
    DEPARTMENT => reduce(vcat, [fill(dept_names[i], n_per_dept[i]) for i in 1:5]),
    SALARY => reduce(vcat, [max.(randn(n_per_dept[i]) .* dept_stds[i] .+ dept_means[i], 30.0) for i in 1:5]),
)

# Plot: reads only df and the constants above
departments = unique(df[!, DEPARTMENT])
group = [findfirst(==(d), departments) for d in df[!, DEPARTMENT]]

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "box-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = DEPARTMENT,
    ylabel             = SALARY,
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
    xticks             = (1:length(departments), departments),
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    yminorgridvisible  = false,
    xminorgridvisible  = false,
)

boxplot!(ax, group, df[!, SALARY];
    color            = IMPRINT_PALETTE[group],
    strokecolor      = INK_SOFT,
    strokewidth      = 1.5,
    mediancolor      = INK,
    medianlinewidth  = 3,
    whiskercolor     = INK_SOFT,
    whiskerlinewidth = 2.0,
    width            = 0.65,
    markersize       = 9,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
