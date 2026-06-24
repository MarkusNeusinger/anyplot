// anyplot.ai
// heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-24
//# anyplot-orientation: square

const tok = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Pitch classes: B at top, C at bottom (conventional chromagram layout)
const pitchClasses = ["B", "A#", "A", "G#", "G", "F#", "F", "E", "D#", "D", "C#", "C"];

const N_FRAMES = 80;
const DURATION = 8; // seconds

// Fixed-seed LCG — browser provides no seeded RNG
let _seed = 42;
function rand() {
  _seed = (Math.imul(1664525, _seed) + 1013904223) | 0;
  return (_seed >>> 0) / 4294967296;
}

// Base energies per pitch class for each chord in the I–V–vi–IV progression
const CHORDS = {
  "C major": { C: 0.92, "C#": 0.07, D: 0.10, "D#": 0.06, E: 0.88, F: 0.12, "F#": 0.07, G: 0.90, "G#": 0.07, A: 0.15, "A#": 0.08, B: 0.12 },
  "G major": { C: 0.15, "C#": 0.07, D: 0.88, "D#": 0.06, E: 0.12, F: 0.08, "F#": 0.10, G: 0.92, "G#": 0.08, A: 0.12, "A#": 0.07, B: 0.90 },
  "A minor": { C: 0.88, "C#": 0.07, D: 0.12, "D#": 0.06, E: 0.90, F: 0.10, "F#": 0.08, G: 0.15, "G#": 0.08, A: 0.92, "A#": 0.07, B: 0.10 },
  "F major": { C: 0.88, "C#": 0.07, D: 0.10, "D#": 0.08, E: 0.12, F: 0.92, "F#": 0.08, G: 0.12, "G#": 0.07, A: 0.88, "A#": 0.15, B: 0.08 },
};

// I–V–vi–IV chord sections (2 s each)
const CHORD_SECTIONS = [
  { label: "C maj", start: 0, end: 2 },
  { label: "G maj", start: 2, end: 4 },
  { label: "A min", start: 4, end: 6 },
  { label: "F maj", start: 6, end: 8 },
];

const CHORD_SEQ = ["C major", "C major", "G major", "G major", "A minor", "A minor", "F major", "F major"];
const N_SECTIONS = CHORD_SEQ.length;

// Generate 80 × 12 = 960 chroma data points
const data = [];
for (let ti = 0; ti < N_FRAMES; ti++) {
  const si = Math.floor((ti / N_FRAMES) * N_SECTIONS);
  const chord = CHORDS[CHORD_SEQ[si]];
  const t_sec = (ti / N_FRAMES) * DURATION;
  for (const pc of pitchClasses) {
    const base = chord[pc] !== undefined ? chord[pc] : 0.07;
    const energy = Math.min(1, Math.max(0, base + (rand() - 0.5) * 0.12));
    data.push({ time: t_sec, pitch: pc, energy });
  }
}

const margin = { top: 115, right: 150, bottom: 70, left: 70 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const timeValues = Array.from(new Set(data.map(d => d.time))).sort((a, b) => a - b);

const xScale = d3.scaleBand().domain(timeValues).range([0, iw]).padding(0);
const yScale = d3.scaleBand().domain(pitchClasses).range([0, ih]).padding(0);
const cmap = d3.scaleSequential(d3.interpolateRgbBasis(tok.seq)).domain([0, 1]);

// Heatmap cells — nested binding via d3.groups(data, pitch class)
const byPitch = d3.groups(data, d => d.pitch);
g.selectAll("g.row")
  .data(byPitch)
  .join("g")
  .attr("class", "row")
  .each(function([pc, frames]) {
    d3.select(this).selectAll("rect")
      .data(frames)
      .join("rect")
      .attr("x", d => xScale(d.time))
      .attr("y", yScale(pc))
      .attr("width", xScale.bandwidth() + 0.5)
      .attr("height", yScale.bandwidth() + 0.5)
      .attr("fill", d => cmap(d.energy));
  });

// X axis — one tick per second
const xTickVals = timeValues.filter((_, i) => i % 10 === 0);
const xAxis = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(xScale).tickValues(xTickVals).tickFormat(d => `${Math.round(d)}s`));
xAxis.selectAll("text").attr("fill", tok.inkSoft).style("font-size", "14px");
xAxis.selectAll("line").attr("stroke", tok.inkSoft);
xAxis.select(".domain").remove(); // open-face axis; cells define the boundary

// Y axis — all 12 pitch classes
const yAxis = g.append("g").call(d3.axisLeft(yScale));
yAxis.selectAll("text").attr("fill", tok.inkSoft).style("font-size", "14px");
yAxis.selectAll("line").attr("stroke", tok.inkSoft);
yAxis.select(".domain").remove();

// Chord section boundary lines at t = 2, 4, 6 s
g.selectAll("line.chord-boundary")
  .data([2, 4, 6])
  .join("line")
  .attr("class", "chord-boundary")
  .attr("x1", d => xScale(d))
  .attr("x2", d => xScale(d))
  .attr("y1", -8)
  .attr("y2", ih)
  .attr("stroke", tok.ink)
  .attr("stroke-width", 1.5)
  .attr("stroke-dasharray", "5,3")
  .attr("opacity", 0.6);

// Chord section labels — centered above each 2 s segment
g.selectAll("text.chord-label")
  .data(CHORD_SECTIONS)
  .join("text")
  .attr("class", "chord-label")
  .attr("x", d => iw * (d.start + d.end) / 2 / DURATION)
  .attr("y", -14)
  .attr("text-anchor", "middle")
  .attr("fill", tok.ink)
  .style("font-size", "13px")
  .style("font-weight", "500")
  .text(d => d.label);

// Axis labels
g.append("text")
  .attr("x", iw / 2).attr("y", ih + 55)
  .attr("text-anchor", "middle")
  .attr("fill", tok.ink).style("font-size", "16px")
  .text("Time (s)");

svg.append("text")
  .attr("transform", `translate(22, ${margin.top + ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", tok.ink).style("font-size", "16px")
  .text("Pitch Class");

// Colorbar — smooth gradient as 200 stacked SVG rects
const CB_WIDTH = 22;
const CB_X = iw + 40;
const CB_STEPS = 200;
const cbCellH = ih / CB_STEPS;

g.selectAll("rect.cb")
  .data(d3.range(CB_STEPS))
  .join("rect")
  .attr("class", "cb")
  .attr("x", CB_X)
  .attr("y", (_, i) => i * cbCellH)
  .attr("width", CB_WIDTH)
  .attr("height", cbCellH + 0.5)
  .attr("fill", (_, i) => cmap(1 - i / (CB_STEPS - 1))); // top = 1.0, bottom = 0.0

// Colorbar axis (energy 1.0 → 0.0)
const cbAxisScale = d3.scaleLinear().domain([1, 0]).range([0, ih]);
const cbAxis = g.append("g")
  .attr("transform", `translate(${CB_X + CB_WIDTH}, 0)`)
  .call(d3.axisRight(cbAxisScale).ticks(5).tickFormat(d3.format(".1f")));
cbAxis.selectAll("text").attr("fill", tok.inkSoft).style("font-size", "13px");
cbAxis.selectAll("line").attr("stroke", tok.inkSoft);
cbAxis.select(".domain").attr("stroke", tok.inkSoft);

// Colorbar label
g.append("text")
  .attr("x", CB_X + CB_WIDTH / 2).attr("y", -14)
  .attr("text-anchor", "middle")
  .attr("fill", tok.ink).style("font-size", "13px")
  .text("Energy");

// Title
svg.append("text")
  .attr("x", width / 2).attr("y", 58)
  .attr("text-anchor", "middle")
  .attr("fill", tok.ink).style("font-size", "22px").style("font-weight", "600")
  .text("heatmap-chromagram · javascript · d3 · anyplot.ai");
