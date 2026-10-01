# root-locus-basic: Root Locus Plot for Control Systems

## Description

A root locus plot traces how the closed-loop poles of a transfer function migrate through the complex plane as a system parameter (typically gain K) varies from 0 to infinity. It is a fundamental tool in classical control theory for analyzing system stability and designing controllers. The plot reveals critical information about pole trajectories, stability boundaries, and gain margins.

## Applications

- Designing PID controllers by selecting gain values that place poles in desired locations
- Analyzing closed-loop stability margins as loop gain varies in feedback systems
- Determining breakaway and break-in points where locus branches merge or split on the real axis
- Teaching classical control theory concepts such as pole placement, damping, and natural frequency

## Data

- `real` (numeric) — real part of pole locations in the complex plane
- `imaginary` (numeric) — imaginary part of pole locations in the complex plane
- `gain` (numeric) — corresponding gain parameter K for each pole position
- `branch` (categorical) — branch identifier to distinguish separate locus paths
- Size: 500-2000 points per branch, typically 2-5 branches

## Notes

- Mark open-loop poles with x markers and open-loop zeros with o markers
- Show locus branches as continuous curves with arrows indicating the direction of increasing gain
- Draw real axis segments that are part of the root locus (segments to the left of an odd number of real-axis poles/zeros)
- Mark imaginary axis crossings prominently as they represent the stability boundary
- Use a dashed or light grid to indicate constant damping ratio and natural frequency lines
- The plot should be centered on the origin with equal axis scaling to preserve geometric relationships

## What a good version looks like

- A good version shows: open-loop poles as x markers and open-loop zeros, where the system has any, as o markers, as the Notes ask, each at its real and imaginary part and visible against the branches in both themes.
- A good version shows: every branch as a continuous curve through its pole positions in order of gain, complex branches mirrored across the real axis, with arrows pointing toward increasing gain and the real-axis segments of the locus drawn, as the Notes ask.
- A good version shows: the imaginary-axis crossings, where the locus has any, marked prominently, as the Notes ask, exactly where the branches cross from the left half-plane into the right.
- A good version shows: a plane centered on the origin with equal axis scaling and a dashed or light grid of constant damping ratio and natural frequency lines, as the Notes ask: rays from the origin and circles around it that look circular and stay behind the locus.
- A good version shows: the basic variant's standard root locus of one system: besides the pole and zero markers, direction arrows, imaginary-axis crossing marks and damping grid the Notes ask for, no asymptote or further reference lines, highlighted regions, callouts on other points or second locus.
- Expected, not a defect: branches that run off the plot toward infinity, branches lying along the real axis, branches that meet and split at a breakaway point, a short branch ending at a nearby zero, and a right half-plane left nearly empty by a locus that lives in the left half.
