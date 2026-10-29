# The renderer's precompile workload (step 5 of agentic/specs/261024-agent-all-libraries.md, J1.1). The toolchain's
# Julia stage develops this package into the image's copy of the project and precompiles it; the renderer's Julia row
# loads it with `-L /opt/anyplot/toolchain/warmup.jl` before `plot.jl` (agents/renderer/commands.py, JULIA_WARMUP).
#
# PrecompileTools stores the native code the workload below compiles, for methods of CairoMakie, Makie, CSV,
# DataFrames, TimeZones and Base alike, in this package's image, and a render uses it only while this package is
# loaded, hence the `-L`. The package loads CSV, DataFrames and TimeZones itself: each pulls in InlineStrings, whose
# methods invalidate much of Makie's own precompiled code (a Makie render that loads any of them took 5 to 6 s longer,
# measured on 2026-10-29), so the workload is compiled in the world an adapted render runs in, where those packages
# are always loaded. The package defines no method of its own, so it invalidates nothing.
#
# The workload runs once, at precompile time, and leaves no file behind. It makes the calls the catalogue's Makie files
# make most, on the argument types they pass, and the data loader's read and conversions.
module AnyplotWarmup

using CairoMakie
using Colors
using FileIO
using ImageIO
using PNGFiles
using Printf
using Random
using Statistics
import CSV, DataFrames, Dates, TimeZones
using PrecompileTools: @compile_workload, @setup_workload

@setup_workload begin
    grid2d = [sin(i / 3) * cos(j / 4) for i in 1:12, j in 1:10]
    file = tempname() * ".png"
    csvfile = tempname() * ".csv"
    # Every column kind the loader reads: datetimes with an offset, `Z`, a space and none, a fraction past the
    # millisecond, a big integer, booleans, dates, and missing cells.
    write(csvfile, """
    when,region,value,count,big,flag,day,gap
    2026-03-29T01:30:00.250+01:00,North,1.5,3,-9223372036854775807,True,2026-01-02,1.0
    2026-03-29 02:30:00,South,2.25,4,,False,2026-01-03,
    2026-03-29T03:30:00Z,,3.0,5,7,,2026-01-04,3.0
    2026-03-29T04:30:00.123456-05:30,East,4.5,6,8,True,2026-01-05,4.0
    """)
    @compile_workload begin
        ink = colorant"#1A1A17"
        soft = colorant"#4A4A44"
        bg = colorant"#FAF8F1"
        brand = colorant"#009E73"
        palette = [colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233"]
        grid = RGBAf(ink.r, ink.g, ink.b, 0.15)
        seq = cgrad([colorant"#009E73", colorant"#4467A3"])
        x = collect(1.0:12.0)
        y = sin.(x) .+ 2.0
        ints = collect(1:12)

        Random.seed!(42)
        r = randn(12)
        u = rand(12)
        mean(r); std(r); median(u); quantile(u, [0.25, 0.75]); cor(r, u); cor(grid2d)
        sum(grid2d, dims = 1); maximum(grid2d, dims = 2); round(1.2345; digits = 2)
        Printf.format(Printf.Format("%.2f"), 1.2345)

        # The data loader's statement as J2a's code profile writes it (agents/anyplot/code/profiles/julia/loader.py,
        # PR #12459), verbatim but for the file's path. The keyword arguments, their order and the `types` Dict mirror
        # it: if the loader changes them, a render recompiles only the outer call, not the read.
        df = let
            integer(cell::Missing) = missing
            integer(cell::AbstractString) = parse(Int64, cell)
            utc(cell::Missing) = missing
            function utc(cell::AbstractString)
                m = match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(:\d{2})?(?:[.,](\d{1,9}))?(Z|[+-]\d{2}(?::?\d{2})?)?$", cell)
                m === nothing && throw(ArgumentError("not an ISO 8601 date and time: $(repr(cell))"))
                stamp = string(m[1], "T", m[2], something(m[3], ":00"), ".", rpad(something(m[4], ""), 3, '0')[1:3])
                m[5] === nothing && return Dates.DateTime(stamp)
                return Dates.DateTime(TimeZones.ZonedDateTime(stamp * m[5], Dates.dateformat"yyyy-mm-ddTHH:MM:SS.ssszzzz"), TimeZones.UTC)
            end
            table = CSV.read(
                csvfile,
                DataFrames.DataFrame;
                types = Dict(
                    "when" => String,
                    "region" => String,
                    "value" => Float64,
                    "count" => Int64,
                    "big" => String,
                    "flag" => Bool,
                    "day" => Dates.Date,
                    "gap" => Float64,
                ),
                missingstring = "",
                truestrings = ["True"],
                falsestrings = ["False"],
                strict = true,
                normalizenames = false,
                pool = false,
                stringtype = String,
                ntasks = 1,
            )
            table[!, "when"] = utc.(table[!, "when"])
            table[!, "big"] = integer.(table[!, "big"])
            table
        end

        fig = Figure(size = (1600, 900), fontsize = 14, backgroundcolor = bg)
        Label(fig[0, 1:2], "subtitle", fontsize = 13, color = soft, halign = :left, tellwidth = false)
        ax = Axis(
            fig[1, 1];
            title = "warmup", titlesize = 20, titlecolor = ink, xlabel = "x", ylabel = "y",
            xlabelsize = 14, ylabelsize = 14, xlabelcolor = ink, ylabelcolor = ink,
            xticklabelsize = 12, yticklabelsize = 12, xticklabelcolor = soft, yticklabelcolor = soft,
            xtickcolor = soft, ytickcolor = soft, backgroundcolor = bg,
            topspinevisible = false, rightspinevisible = false, leftspinecolor = soft, bottomspinecolor = soft,
            xgridcolor = grid, ygridcolor = grid,
        )
        scatter!(ax, x, y; color = (brand, 0.7), markersize = 12, strokewidth = 1, strokecolor = bg, label = "points")
        scatter!(ax, ints, sin.(ints); color = palette[2], marker = :diamond, markersize = 10)
        lines!(ax, x, y; color = soft, linewidth = 2.0, linestyle = :dash, label = "line")
        lines!(ax, LinRange(1, 12, 50), sin; color = brand, linewidth = 3)
        band!(ax, x, y .- 0.3, y .+ 0.3; color = (brand, 0.2))
        hlines!(ax, [2.0]; color = grid, linewidth = 1)
        vlines!(ax, [3.0, 6.0]; color = soft, linestyle = :dot)
        text!(ax, Point2f(2, 3); text = "note", align = (:center, :bottom), fontsize = 12, color = ink, font = :bold)
        text!(ax, [Point2f(1, 1), Point2f(2, 2)]; text = ["a", "b"], color = soft, fontsize = 11)
        text!(ax, x[1:2], y[1:2]; text = ["a", "b"], color = soft, fontsize = 11)
        poly!(ax, Point2f[(0, 0), (1, 0), (1, 1)]; color = (palette[3], 0.5), strokecolor = ink, strokewidth = 1)
        linesegments!(ax, [Point2f(1, 1), Point2f(2, 2)]; color = ink)
        axislegend(ax; position = :rt, framevisible = false, labelcolor = soft)
        xlims!(ax, 0, 13)
        ylims!(ax, 0, 4)

        # Plots fed from the table's columns: Float64 and Int64, a Float64 column with a missing cell, and the DateTime
        # and Date columns on time axes.
        axd = Axis(fig[4, 1]; xlabel = "Time (UTC)")
        when = df[!, "when"]
        value = df[!, "value"]
        lines!(axd, when, value; color = brand, linewidth = 3)
        scatter!(axd, when, value; color = brand, markersize = 10, strokewidth = 0)
        peak = argmax(value)
        text!(axd, when[peak], value[peak]; text = "Peak: $(round(value[peak], digits = 1))", align = (:center, :bottom),
            offset = (0, 12), fontsize = 13, color = ink, space = :data)
        axe = Axis(fig[4, 2])
        lines!(axe, df[!, "day"], df[!, "count"]; color = soft)
        axf = Axis(fig[4, 3])
        scatter!(axf, df[!, "value"], df[!, "count"]; color = (brand, 0.7), markersize = 12)
        lines!(axf, df[!, "count"], df[!, "gap"]; color = ink)
        barplot!(axf, df[!, "count"], df[!, "value"]; color = palette[1])

        ax2 = Axis(fig[1, 2]; xgridvisible = false, ygridcolor = grid, backgroundcolor = bg)
        barplot!(ax2, repeat(1:4, inner = 2), [3.0, 2.0, 4.0, 1.0, 2.5, 3.5, 1.5, 2.0];
            dodge = repeat(1:2, outer = 4), color = palette[repeat(1:2, outer = 4)], gap = 0.2)
        barplot!(ax2, ints[1:4], [1.0, 2.0, 3.0, 4.0]; color = brand, strokecolor = ink, strokewidth = 1)
        ax2.xticks = (1:4, ["A", "B", "C", "D"])
        Legend(fig[1, 3], [PolyElement(color = c) for c in palette[1:2]], ["one", "two"], "Group";
            framevisible = false, labelcolor = soft, titlecolor = ink)

        ax3 = Axis(fig[2, 1]; aspect = DataAspect())
        hm = heatmap!(ax3, 1:12, 1:10, grid2d; colormap = seq)
        heatmap!(ax3, grid2d; colormap = :viridis, colorrange = (-1, 1))
        Colorbar(fig[2, 2], hm; label = "value", width = 15)

        ax4 = Axis(fig[2, 3])
        hist!(ax4, randn(MersenneTwister(1), 100); bins = 20, color = (brand, 0.6))
        density!(ax4, randn(MersenneTwister(2), 100); color = (palette[2], 0.3))
        ax5 = Axis(fig[3, 1])
        boxplot!(ax5, repeat(1:3, inner = 20), randn(MersenneTwister(3), 60); color = brand)
        violin!(ax5, repeat(1:3, inner = 20), randn(MersenneTwister(4), 60); color = (palette[3], 0.5))
        errorbars!(ax5, [1.0, 2.0, 3.0], [0.0, 0.5, 1.0], [0.2, 0.3, 0.1]; color = ink, whiskerwidth = 8)

        ax6 = Axis(fig[3, 2])
        stairs!(ax6, x, y; color = ink)
        scatterlines!(ax6, x, y .+ 1; color = brand, markersize = 8)
        contour!(ax6, 1:12, 1:10, grid2d; levels = 5, color = ink)
        contourf!(ax6, 1:12, 1:10, grid2d; levels = 5, colormap = seq)
        hspan!(ax6, 0.5, 1.0; color = (soft, 0.1))
        vspan!(ax6, 2.0, 3.0; color = (soft, 0.1))
        ax7 = Axis(fig[3, 3]; aspect = DataAspect())
        pie!(ax7, [1.0, 2.0, 3.0]; color = palette[1:3], strokecolor = bg, strokewidth = 2)
        Legend(fig[0, 3], [LineElement(color = ink), MarkerElement(color = brand, marker = :circle)], ["l", "m"];
            orientation = :horizontal)

        hidespines!(ax2, :t, :r)
        hidedecorations!(ax2; grid = false)
        colsize!(fig.layout, 1, Relative(0.5))
        rowsize!(fig.layout, 1, Relative(0.4))
        colgap!(fig.layout, 20)
        rowgap!(fig.layout, 10)
        limits!(ax, 0, 13, 0, 4)

        save(file, fig; px_per_unit = 2)
    end
    rm(file; force = true)
    rm(csvfile; force = true)
end

end
