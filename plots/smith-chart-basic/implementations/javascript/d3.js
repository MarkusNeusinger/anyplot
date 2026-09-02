// anyplot.ai
// smith-chart-basic: Smith Chart for RF/Impedance
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: pending | Created: 2026-09-02

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Complex-number helpers — the browser has no built-in complex type
const cSub = (a, b) => ({ re: a.re - b.re, im: a.im - b.im });
const cDiv = (a, b) => {
  const denom = b.re * b.re + b.im * b.im;
  return { re: (a.re * b.re + a.im * b.im) / denom, im: (a.im * b.re - a.re * b.im) / denom };
};

// Antenna feed-point impedance seen at the input of a lossless line as the
// sweep frequency changes the line's electrical length: |gamma| stays fixed
// at the load's magnitude while its phase rotates, tracing the classic
// constant-VSWR arc that a network analyzer records during S11 sweeps.
const z0 = 50; // Reference impedance (ohms)
const zLoad = { re: 75, im: 25 }; // Mismatched antenna feed, ohms
const gammaLoad = cDiv(cSub(zLoad, { re: z0, im: 0 }), { re: zLoad.re + z0, im: zLoad.im });
const gammaLoadMag = Math.hypot(gammaLoad.re, gammaLoad.im);
const gammaLoadPhase = Math.atan2(gammaLoad.im, gammaLoad.re);

const pointCount = 60;
const freqStartHz = 1e9;
const freqEndHz = 6e9;
const sweepDegrees = 250; // total electrical-length rotation across the band

const impedanceData = d3.range(pointCount).map((i) => {
  const frac = i / (pointCount - 1);
  const frequency = freqStartHz + frac * (freqEndHz - freqStartHz);
  const phase = gammaLoadPhase - frac * (sweepDegrees * Math.PI) / 180;
  const gamma = { re: gammaLoadMag * Math.cos(phase), im: gammaLoadMag * Math.sin(phase) };
  const z = cDiv({ re: z0 * (1 + gamma.re), im: z0 * gamma.im }, cSub({ re: 1, im: 0 }, gamma));
  return { frequency, z_real: z.re, z_imag: z.im };
});

// Normalize to Z/Z0 and derive the reflection coefficient for plotting
const locus = impedanceData.map((d) => {
  const zn = { re: d.z_real / z0, im: d.z_imag / z0 };
  return cDiv(cSub(zn, { re: 1, im: 0 }), { re: zn.re + 1, im: zn.im });
});

// Layout — the chart itself is circular, so it earns the square canvas
const margin = { top: 150, right: 100, bottom: 100, left: 100 };
const plotSize = Math.min(width - margin.left - margin.right, height - margin.top - margin.bottom);
const radius = plotSize / 2;
const cx = width / 2;
const cy = margin.top + plotSize / 2;
const toPixel = (re, im) => [cx + re * radius, cy - im * radius];
const boundaryPoint = (x) => {
  const denom = x * x + 1;
  return [(x * x - 1) / denom, (2 * x) / denom];
};

// SVG mount
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
svg.append("clipPath").attr("id", "smith-boundary")
  .append("circle").attr("cx", cx).attr("cy", cy).attr("r", radius);

// Grid — constant-resistance circles and constant-reactance arcs, clipped to
// the unit circle since only the arcs' interior segments are meaningful
const grid = svg.append("g").attr("clip-path", "url(#smith-boundary)");
const resistanceValues = [0.2, 0.5, 1, 2, 5];
const reactanceValues = [0.2, 0.5, 1, 2, 5];

grid.append("line")
  .attr("x1", cx - radius).attr("y1", cy).attr("x2", cx + radius).attr("y2", cy)
  .attr("stroke", t.grid).attr("stroke-width", 1.5);

resistanceValues.forEach((r) => {
  grid.append("circle")
    .attr("cx", cx + (r / (r + 1)) * radius).attr("cy", cy)
    .attr("r", (radius / (r + 1)))
    .attr("fill", "none").attr("stroke", t.grid).attr("stroke-width", 1.5);
});

reactanceValues.forEach((x) => {
  [1, -1].forEach((sign) => {
    const xs = sign * x;
    grid.append("circle")
      .attr("cx", cx + radius).attr("cy", cy - (radius / xs))
      .attr("r", Math.abs(radius / xs))
      .attr("fill", "none").attr("stroke", t.grid).attr("stroke-width", 1.5);
  });
});

// Boundary circle |gamma| = 1 — total reflection, drawn crisp on top of the grid
svg.append("circle")
  .attr("cx", cx).attr("cy", cy).attr("r", radius)
  .attr("fill", "none").attr("stroke", t.inkSoft).attr("stroke-width", 2.5);

// Matched-condition marker at the chart center (Z = Z0, gamma = 0)
svg.append("circle").attr("cx", cx).attr("cy", cy).attr("r", 4).attr("fill", t.muted);

// Resistance-circle labels along the real axis
resistanceValues.concat([0]).forEach((r) => {
  const [px, py] = toPixel((r - 1) / (r + 1), 0);
  svg.append("text")
    .attr("x", px).attr("y", py + 24)
    .attr("text-anchor", "middle")
    .attr("fill", t.inkSoft).style("font-size", "13px")
    .text(r);
});

// Reactance-arc labels just outside the boundary, at each arc's exit point
reactanceValues.forEach((x) => {
  [1, -1].forEach((sign) => {
    const xs = sign * x;
    const [gx, gy] = boundaryPoint(xs);
    const angle = Math.atan2(gy, gx);
    const lx = cx + Math.cos(angle) * radius * 1.06;
    const ly = cy - Math.sin(angle) * radius * 1.06;
    svg.append("text")
      .attr("x", lx).attr("y", ly)
      .attr("text-anchor", "middle").attr("dominant-baseline", "middle")
      .attr("fill", t.inkSoft).style("font-size", "13px")
      .text(`${xs > 0 ? "+" : "-"}j${x}`);
  });
});

// Impedance locus — the frequency-swept trajectory across the reflection plane
const lineGen = d3.line()
  .x((d) => toPixel(d.re, d.im)[0])
  .y((d) => toPixel(d.re, d.im)[1])
  .curve(d3.curveCatmullRom.alpha(0.5));

svg.append("path")
  .datum(locus)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 4)
  .attr("stroke-linejoin", "round")
  .attr("d", lineGen);

// Frequency markers at the sweep endpoints and two intermediate points
const markerIndices = [0, Math.round((pointCount - 1) / 3), Math.round((2 * (pointCount - 1)) / 3), pointCount - 1];
markerIndices.forEach((i) => {
  const [px, py] = toPixel(locus[i].re, locus[i].im);
  svg.append("circle")
    .attr("cx", px).attr("cy", py).attr("r", 7)
    .attr("fill", t.palette[0]).attr("stroke", t.pageBg).attr("stroke-width", 2);
  svg.append("text")
    .attr("x", px + 16).attr("y", py - 12)
    .attr("fill", t.ink).style("font-size", "15px").style("font-weight", "600")
    .text(`${(impedanceData[i].frequency / 1e9).toFixed(1)} GHz`);
});

// Title + subtitle
const title = "smith-chart-basic · javascript · d3 · anyplot.ai";
svg.append("text")
  .attr("x", width / 2).attr("y", 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "24px").style("font-weight", "600")
  .text(title);

svg.append("text")
  .attr("x", width / 2).attr("y", 92)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft).style("font-size", "16px")
  .text("Antenna feed impedance sweep · 1–6 GHz · Z₀ = 50 Ω");
