// anyplot.ai
// waveform-audio: Audio Waveform Plot
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-03

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 80, right: 50, bottom: 90, left: 100 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: synthetic vocal phrase — three syllables, fully deterministic, 1.7 s at 8 kHz ---
const SR = 8000;
const DUR = 1.7;
const N = Math.ceil(SR * DUR);  // 13600 samples

// Three voiced syllables: start/end seconds, fundamental F0 (Hz), attack/release durations (s)
const SYLS = [
  { start: 0.10, end: 0.55, f0: 130, atk: 0.04, rel: 0.12 },
  { start: 0.65, end: 1.10, f0: 155, atk: 0.04, rel: 0.12 },
  { start: 1.20, end: 1.60, f0: 145, atk: 0.04, rel: 0.10 },
];

function envAt(time, syl) {
  const tl = time - syl.start;
  const dur = syl.end - syl.start;
  if (tl < 0 || tl >= dur) return 0;
  if (tl < syl.atk) return tl / syl.atk;
  if (dur - tl < syl.rel) return (dur - tl) / syl.rel;
  return 1;
}

function signalAt(time) {
  let s = 0;
  for (const syl of SYLS) {
    const env = envAt(time, syl);
    if (env === 0) continue;
    const tau = 2 * Math.PI * time;
    const f = syl.f0;
    s += env * (
      0.45 * Math.sin(f * tau) +
      0.28 * Math.sin(2 * f * tau) +
      0.16 * Math.sin(3 * f * tau) +
      0.11 * Math.sin(4 * f * tau)
    );
  }
  return s;
}

// Build raw signal, then downsample to display-width bins (min/max envelope per pixel column)
const rawAmp = new Float32Array(N);
for (let i = 0; i < N; i++) rawAmp[i] = signalAt(i / SR);

const nBins = Math.round(iw);
const bSz = N / nBins;
const waveData = Array.from({ length: nBins }, (_, b) => {
  const s = Math.floor(b * bSz);
  const e = Math.min(Math.ceil((b + 1) * bSz), N);
  let lo = Infinity, hi = -Infinity;
  for (let j = s; j < e; j++) {
    if (rawAmp[j] < lo) lo = rawAmp[j];
    if (rawAmp[j] > hi) hi = rawAmp[j];
  }
  return { tPos: s / SR, lo, hi };
});

// --- SVG mount ---
const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales ---
const xScale = d3.scaleLinear().domain([0, DUR]).range([0, iw]);
const yScale = d3.scaleLinear().domain([-1.05, 1.05]).range([ih, 0]);

// --- Horizontal gridlines (y-axis only, subtle) ---
g.selectAll(".hg").data([-1, -0.5, 0, 0.5, 1]).join("line")
  .attr("class", "hg")
  .attr("x1", 0).attr("x2", iw)
  .attr("y1", d => yScale(d)).attr("y2", d => yScale(d))
  .attr("stroke", t.grid)
  .attr("stroke-width", 0.5);

// --- Waveform filled area (min/max envelope per display column) ---
g.append("path")
  .datum(waveData)
  .attr("d", d3.area()
    .x(d => xScale(d.tPos))
    .y0(d => yScale(d.lo))
    .y1(d => yScale(d.hi)))
  .attr("fill", t.palette[0])
  .attr("fill-opacity", 0.72)
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 0.4)
  .attr("stroke-opacity", 0.9);

// --- Zero reference line (slightly more visible than gridlines) ---
g.append("line")
  .attr("x1", 0).attr("x2", iw)
  .attr("y1", yScale(0)).attr("y2", yScale(0))
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1);

// --- Axes ---
const xAxis = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(xScale).ticks(9).tickFormat(d => d.toFixed(1)));

const yAxis = g.append("g")
  .call(d3.axisLeft(yScale).tickValues([-1, -0.5, 0, 0.5, 1]));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.selectAll("line").attr("stroke", t.inkSoft).attr("stroke-width", 0.5);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels ---
svg.append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 18)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "20px")
  .text("Time (s)");

svg.append("text")
  .attr("transform", `translate(22, ${margin.top + ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "20px")
  .text("Amplitude");

// --- Title ---
svg.append("text")
  .attr("x", width / 2).attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "28px")
  .style("font-weight", "600")
  .text("waveform-audio · javascript · d3 · anyplot.ai");
