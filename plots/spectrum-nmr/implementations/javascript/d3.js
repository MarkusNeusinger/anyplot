// anyplot.ai
// spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-03
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

const margin = { top: 100, right: 80, bottom: 95, left: 90 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Ethanol ¹H NMR at 300 MHz — Lorentzian line shapes
// J-coupling ~7 Hz → Δppm = 7/300 ≈ 0.0233 ppm
const J = 7 / 300;
const gamma = 0.005; // Lorentzian HWHM in ppm

function lorentzian(x, x0, amp) {
  const d = x - x0;
  return amp * gamma * gamma / (d * d + gamma * gamma);
}

// [ppm_position, amplitude] for each multiplet line
const peakLines = [
  [0.00, 0.15],                                                // TMS singlet
  [1.2 - J, 0.50], [1.2, 1.00], [1.2 + J, 0.50],             // CH₃ triplet 1:2:1
  [2.60, 0.40],                                                // OH singlet
  [3.7 - 1.5 * J, 0.22], [3.7 - 0.5 * J, 0.66],              // CH₂ quartet 1:3:3:1
  [3.7 + 0.5 * J, 0.66], [3.7 + 1.5 * J, 0.22],
];

const nPoints = 4000;
const ppmMin = -0.5;
const ppmMax = 5.2;

const spectrum = [];
for (let i = 0; i < nPoints; i++) {
  const ppm = ppmMin + (ppmMax - ppmMin) * i / (nPoints - 1);
  // Deterministic micro-noise for realism; amplitude << peak heights
  let intensity = 0.002 * Math.sin(ppm * 127.3) * Math.sin(ppm * 43.7 + 0.5);
  for (const [pos, amp] of peakLines) {
    intensity += lorentzian(ppm, pos, amp);
  }
  spectrum.push({ ppm, intensity });
}

// SVG
const svg = d3.select("#container")
  .append("svg").attr("width", width).attr("height", height);

const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// Scales — x reversed per NMR convention (high ppm on left)
const x = d3.scaleLinear().domain([ppmMax, ppmMin]).range([0, iw]);
const maxInt = d3.max(spectrum, d => d.intensity);
const y = d3.scaleLinear().domain([-0.04, maxInt * 1.18]).range([ih, 0]);

// Horizontal gridlines
[0.25, 0.5, 0.75].forEach(val => {
  g.append("line")
    .attr("x1", 0).attr("x2", iw)
    .attr("y1", y(val)).attr("y2", y(val))
    .attr("stroke", t.grid).attr("stroke-width", 0.8);
});

// Baseline reference (dashed)
g.append("line")
  .attr("x1", 0).attr("x2", iw)
  .attr("y1", y(0)).attr("y2", y(0))
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1)
  .attr("stroke-dasharray", "5,4")
  .attr("opacity", 0.35);

// Spectrum line
const line = d3.line().x(d => x(d.ppm)).y(d => y(d.intensity));

g.append("path")
  .datum(spectrum)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 1.8)
  .attr("d", line);

// Axes
const xAxis = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(11).tickSize(6));

const yAxis = g.append("g")
  .call(d3.axisLeft(y).tickValues([0, 0.25, 0.5, 0.75, 1.0]).tickSize(6));

[xAxis, yAxis].forEach(ax => {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "15px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
});

// Axis labels
g.append("text")
  .attr("x", iw / 2).attr("y", ih + 68)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft).style("font-size", "18px")
  .text("Chemical Shift (ppm)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2).attr("y", -68)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft).style("font-size", "18px")
  .text("Intensity (a.u.)");

// Peak labels: name + chemical shift value
const peakLabels = [
  { ppm: 0.00, amp: 0.15, name: "TMS",  ppmStr: "0.00" },
  { ppm: 1.20, amp: 1.00, name: "CH₃", ppmStr: "1.20" },
  { ppm: 2.60, amp: 0.40, name: "OH",   ppmStr: "2.60" },
  { ppm: 3.70, amp: 0.66, name: "CH₂", ppmStr: "3.70" },
];

peakLabels.forEach(({ ppm, amp, name, ppmStr }) => {
  const lx = x(ppm);
  const peakY = y(amp);
  const nameY = peakY - 46;
  const shiftY = peakY - 28;

  // Short tick from peak top up to label
  g.append("line")
    .attr("x1", lx).attr("x2", lx)
    .attr("y1", peakY - 8).attr("y2", shiftY + 6)
    .attr("stroke", t.inkSoft).attr("stroke-width", 0.8).attr("opacity", 0.5);

  g.append("text")
    .attr("x", lx).attr("y", nameY)
    .attr("text-anchor", "middle")
    .attr("fill", t.ink).style("font-size", "14px").style("font-weight", "600")
    .text(name);

  g.append("text")
    .attr("x", lx).attr("y", shiftY)
    .attr("text-anchor", "middle")
    .attr("fill", t.inkSoft).style("font-size", "13px")
    .text(ppmStr + " ppm");
});

// Title
svg.append("text")
  .attr("x", width / 2).attr("y", 58)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px").style("font-weight", "600")
  .text("Ethanol ¹H NMR · spectrum-nmr · javascript · d3 · anyplot.ai");
