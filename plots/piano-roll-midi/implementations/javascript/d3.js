// anyplot.ai
// piano-roll-midi: MIDI Piano Roll Visualization
// Library: d3 7.9.0 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-03

const t = window.ANYPLOT_TOKENS;
const theme = window.ANYPLOT_THEME;
const { width, height } = window.ANYPLOT_SIZE;

const margin = { top: 80, right: 158, bottom: 75, left: 90 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- MIDI notes: 4-measure C major melody with crescendo/decrescendo arc ---
const notes = [
  // Measure 1 — ascending scale, pp to mf
  { pitch: 60, start: 0,      duration: 0.5,  velocity: 62 },
  { pitch: 62, start: 0.5,    duration: 0.5,  velocity: 68 },
  { pitch: 64, start: 1.0,    duration: 0.5,  velocity: 74 },
  { pitch: 65, start: 1.5,    duration: 0.5,  velocity: 78 },
  { pitch: 67, start: 2.0,    duration: 0.5,  velocity: 84 },
  { pitch: 69, start: 2.5,    duration: 0.5,  velocity: 88 },
  { pitch: 71, start: 3.0,    duration: 0.5,  velocity: 94 },
  { pitch: 72, start: 3.5,    duration: 0.5,  velocity: 100 },
  // Measure 2 — descending, f to mp
  { pitch: 71, start: 4.0,    duration: 0.5,  velocity: 95 },
  { pitch: 69, start: 4.5,    duration: 0.5,  velocity: 88 },
  { pitch: 67, start: 5.0,    duration: 1.0,  velocity: 96 },
  { pitch: 65, start: 6.0,    duration: 0.5,  velocity: 80 },
  { pitch: 64, start: 6.5,    duration: 0.5,  velocity: 74 },
  { pitch: 62, start: 7.0,    duration: 1.0,  velocity: 82 },
  // Measure 3 — syncopated rhythm, building to climax
  { pitch: 60, start: 8.0,    duration: 0.25, velocity: 90 },
  { pitch: 64, start: 8.25,   duration: 0.25, velocity: 88 },
  { pitch: 67, start: 8.5,    duration: 0.5,  velocity: 100 },
  { pitch: 64, start: 9.0,    duration: 0.25, velocity: 85 },
  { pitch: 60, start: 9.25,   duration: 0.25, velocity: 80 },
  { pitch: 62, start: 9.5,    duration: 0.5,  velocity: 88 },
  { pitch: 65, start: 10.0,   duration: 0.5,  velocity: 100 },
  { pitch: 69, start: 10.5,   duration: 0.25, velocity: 108 },
  { pitch: 67, start: 10.75,  duration: 0.25, velocity: 104 },
  { pitch: 65, start: 11.0,   duration: 0.5,  velocity: 98 },
  { pitch: 64, start: 11.5,   duration: 0.25, velocity: 92 },
  { pitch: 62, start: 11.75,  duration: 0.25, velocity: 86 },
  // Measure 4 — final resolution: C major chord + fade out
  { pitch: 60, start: 12.0,   duration: 1.0,  velocity: 112 },
  { pitch: 64, start: 12.0,   duration: 1.0,  velocity: 104 },
  { pitch: 67, start: 12.0,   duration: 1.0,  velocity: 96 },
  { pitch: 69, start: 13.0,   duration: 0.5,  velocity: 88 },
  { pitch: 67, start: 13.5,   duration: 0.5,  velocity: 82 },
  { pitch: 64, start: 14.0,   duration: 0.5,  velocity: 76 },
  { pitch: 62, start: 14.5,   duration: 0.5,  velocity: 70 },
  { pitch: 60, start: 15.0,   duration: 1.0,  velocity: 64 },
];

const totalBeats = 16;

// Note name helpers
const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const isBlackKey = (midi) => [1, 3, 6, 8, 10].includes(midi % 12);
const midiToName = (midi) => `${NOTE_NAMES[midi % 12]}${Math.floor(midi / 12) - 1}`;

// Auto-fit pitch range with 1-semitone padding
const minPitch = d3.min(notes, (d) => d.pitch) - 1;  // 59 = B3
const maxPitch = d3.max(notes, (d) => d.pitch) + 1;  // 73 = C#5
const domainSpan = maxPitch - minPitch + 1;           // 15 semitones
const rowH = ih / domainSpan;

// Velocity range
const velMin = d3.min(notes, (d) => d.velocity);
const velMax = d3.max(notes, (d) => d.velocity);

// Scales
const x = d3.scaleLinear().domain([0, totalBeats]).range([0, iw]);
const y = d3.scaleLinear()
  .domain([minPitch - 0.5, maxPitch + 0.5])
  .range([ih, 0]);

// Velocity color: blue (t.div[2], low) → neutral (t.div[1]) → red (t.div[0], high)
const velColor = d3.scaleSequential()
  .domain([velMin, velMax])
  .interpolator(d3.interpolateRgbBasis([t.div[2], t.div[1], t.div[0]]));

// Black key row background (slightly darker than page bg)
const blackKeyBg = theme === "light" ? "rgba(26,26,23,0.11)" : "rgba(240,239,232,0.09)";

const pitchRange = d3.range(minPitch, maxPitch + 1);

// --- SVG setup ---
const svg = d3.select("#container").append("svg")
  .attr("width", width)
  .attr("height", height);

const defs = svg.append("defs");
defs.append("clipPath").attr("id", "notes-clip")
  .append("rect").attr("width", iw).attr("height", ih);

// Velocity gradient for colorbar: bottom=low=blue, top=high=red
const grad = defs.append("linearGradient")
  .attr("id", "vel-grad")
  .attr("x1", "0%").attr("x2", "0%")
  .attr("y1", "100%").attr("y2", "0%");
grad.append("stop").attr("offset", "0%").attr("stop-color", t.div[2]);
grad.append("stop").attr("offset", "50%").attr("stop-color", t.div[1]);
grad.append("stop").attr("offset", "100%").attr("stop-color", t.div[0]);

const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Background: alternating rows for black / white keys ---
g.selectAll(".key-row")
  .data(pitchRange)
  .join("rect")
  .attr("class", "key-row")
  .attr("x", 0)
  .attr("y", (p) => y(p + 0.5))
  .attr("width", iw)
  .attr("height", rowH)
  .attr("fill", (p) => (isBlackKey(p) ? blackKeyBg : "transparent"));

// --- Horizontal row dividers ---
g.selectAll(".row-line")
  .data(pitchRange)
  .join("line")
  .attr("class", "row-line")
  .attr("x1", 0).attr("x2", iw)
  .attr("y1", (p) => y(p - 0.5))
  .attr("y2", (p) => y(p - 0.5))
  .attr("stroke", t.grid)
  .attr("stroke-width", 0.3);

// --- Vertical gridlines: beat and measure boundaries (skip borders at 0 and totalBeats) ---
d3.range(1, totalBeats).forEach((beat) => {
  const isMeasure = beat % 4 === 0;
  g.append("line")
    .attr("x1", x(beat)).attr("x2", x(beat))
    .attr("y1", 0).attr("y2", ih)
    .attr("stroke", isMeasure ? t.inkSoft : t.grid)
    .attr("stroke-width", isMeasure ? 1 : 0.4);
});

// --- Note rectangles ---
const noteGap = 2;
const notesG = g.append("g").attr("clip-path", "url(#notes-clip)");
notesG.selectAll(".note")
  .data(notes)
  .join("rect")
  .attr("class", "note")
  .attr("x", (d) => x(d.start) + noteGap)
  .attr("y", (d) => y(d.pitch + 0.5) + noteGap)
  .attr("width", (d) => Math.max(x(d.start + d.duration) - x(d.start) - noteGap * 2, 6))
  .attr("height", Math.max(rowH - noteGap * 2, 2))
  .attr("fill", (d) => velColor(d.velocity))
  .attr("rx", 3)
  .attr("ry", 3);

// --- Y axis: note names ---
const yAxisG = g.append("g")
  .call(d3.axisLeft(y)
    .tickValues(pitchRange)
    .tickFormat(midiToName)
    .tickSize(4)
  );
yAxisG.selectAll("text")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .style("font-family", "monospace");
yAxisG.selectAll("line").attr("stroke", t.grid);
yAxisG.select(".domain").attr("stroke", t.inkSoft);

// Emphasize C notes (octave markers)
yAxisG.selectAll("text")
  .filter((d) => d % 12 === 0)
  .attr("fill", t.ink)
  .style("font-weight", "700")
  .style("font-size", "15px");

// Y axis label
svg.append("text")
  .attr("transform", `translate(${28},${margin.top + ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Pitch");

// --- X axis: beats and measure labels ---
const xAxisG = g.append("g").attr("transform", `translate(0,${ih})`);

xAxisG.append("line")
  .attr("x1", 0).attr("x2", iw)
  .attr("y1", 0).attr("y2", 0)
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1);

// Measure labels (centered within each measure)
xAxisG.selectAll(".measure-label")
  .data(d3.range(4))
  .join("text")
  .attr("class", "measure-label")
  .attr("x", (m) => x(m * 4 + 2))
  .attr("y", 32)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .style("font-weight", "600")
  .text((m) => `Measure ${m + 1}`);

// Beat tick marks and sub-beat labels
d3.range(0, totalBeats + 1).forEach((beat) => {
  xAxisG.append("line")
    .attr("x1", x(beat)).attr("x2", x(beat))
    .attr("y1", 0)
    .attr("y2", beat % 4 === 0 ? 10 : 5)
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", beat % 4 === 0 ? 1.5 : 0.8);
});

// Beat numbers within measures (2, 3, 4)
d3.range(0, totalBeats).forEach((beat) => {
  const beatInMeasure = beat % 4;
  if (beatInMeasure !== 0) {
    xAxisG.append("text")
      .attr("x", x(beat))
      .attr("y", 19)
      .attr("text-anchor", "middle")
      .attr("fill", t.inkSoft)
      .style("font-size", "12px")
      .style("opacity", "0.75")
      .text(beatInMeasure + 1);
  }
});

// X axis label
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 62)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Time (Beats)");

// --- Velocity colorbar ---
const cbW = 18;
const cbH = Math.round(ih * 0.65);
const cbX = margin.left + iw + 32;
const cbY = margin.top + Math.round((ih - cbH) / 2);

svg.append("rect")
  .attr("x", cbX).attr("y", cbY)
  .attr("width", cbW).attr("height", cbH)
  .attr("fill", "url(#vel-grad)")
  .attr("rx", 3);

svg.append("rect")
  .attr("x", cbX).attr("y", cbY)
  .attr("width", cbW).attr("height", cbH)
  .attr("fill", "none")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 0.5)
  .attr("rx", 3);

// Colorbar axis
const velScale = d3.scaleLinear()
  .domain([velMin, velMax])
  .range([cbY + cbH, cbY]);

const cbAxisG = svg.append("g")
  .attr("transform", `translate(${cbX + cbW}, 0)`)
  .call(d3.axisRight(velScale).ticks(5).tickSize(4));
cbAxisG.selectAll("text")
  .attr("fill", t.inkSoft)
  .style("font-size", "12px");
cbAxisG.selectAll("line").attr("stroke", t.inkSoft);
cbAxisG.select(".domain").attr("stroke", "none");

svg.append("text")
  .attr("x", cbX + cbW / 2)
  .attr("y", cbY - 14)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .text("Velocity");

// Dynamic range markers (pp, mf, ff) to the left of the colorbar
[{ f: 0.1, label: "pp" }, { f: 0.5, label: "mf" }, { f: 0.9, label: "ff" }].forEach(({ f, label }) => {
  const vel = velMin + f * (velMax - velMin);
  svg.append("text")
    .attr("x", cbX - 6)
    .attr("y", velScale(vel) + 4)
    .attr("text-anchor", "end")
    .attr("fill", t.inkSoft)
    .style("font-size", "13px")
    .style("font-style", "italic")
    .text(label);
});

// --- Title ---
svg.append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("piano-roll-midi · javascript · d3 · anyplot.ai");
