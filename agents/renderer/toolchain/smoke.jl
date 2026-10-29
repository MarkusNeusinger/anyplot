# The toolchain image's own check (agents/renderer/toolchain.Dockerfile): Julia starts under the
# exec filter with --compiled-modules=strict, so every package of Project.toml loads from the
# depot's precompiled images or this script fails; a program start is refused; TimeZones turns a
# fixed offset into UTC offline; and CairoMakie writes a PNG with a non-ASCII title.
import TOML

# The row loads the precompile workload with `-L warmup.jl` before the program, as it does before a plot.
@assert isdefined(Main, :AnyplotWarmup) "the precompile workload was not loaded before the program"
@assert endswith(PROGRAM_FILE, "smoke.jl")

for name in sort!(collect(keys(TOML.parsefile(Base.active_project())["deps"])))
    Core.eval(Main, :(using $(Symbol(name))))
end
using CairoMakie, Dates, Random, TimeZones

# The filter kills the child before it runs anything: a failed start, never a started program.
@assert !success(`true`)
@assert ENV["LANG"] == "C.UTF-8"

# Offsets go to UTC, with the milliseconds kept (step 5, owner decision of 2026-10-29); the zone
# data is TZJData's artifact in the depot, so no download and no build at run time.
zoned = ZonedDateTime("2026-03-29T01:30:00.250+01:00", dateformat"yyyy-mm-ddTHH:MM:SS.ssszzzz")
@assert DateTime(zoned, UTC) == DateTime(2026, 3, 29, 0, 30, 0, 250)

png = joinpath(tempdir(), "smoke.png")
fig = Figure(size = (400, 300))
ax = Axis(fig[1, 1], title = "Gewicht über Verbrauch – été")
scatter!(ax, randn(MersenneTwister(1), 20), randn(MersenneTwister(2), 20))
save(png, fig)
@assert filesize(png) > 1000
println(
    "toolchain smoke: Julia ", VERSION, ", Makie ", pkgversion(Makie), ", CairoMakie ", pkgversion(CairoMakie),
    ", TimeZones ", pkgversion(TimeZones),
)
