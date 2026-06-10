// anyplot.ai
// recurrence-basic: Recurrence Plot for Nonlinear Time Series
// Library: d3 7.9.0 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-10

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

const margin = { top: 70, right: 70, bottom: 90, left: 90 };
const iw = width - margin.left - margin.right;  // 1040
const ih = height - margin.top - margin.bottom;  // 1040

// --- Data: logistic map (deterministic, r=3.85 → chaotic regime) ----------
const R = 3.85, TAU = 3, N_STEPS = 350, N_BURN = 50;
const xs = new Array(N_STEPS);
xs[0] = 0.5;
for (let k = 1; k < N_STEPS; k++) xs[k] = R * xs[k - 1] * (1 - xs[k - 1]);

const series = xs.slice(N_BURN);      // 300 post-transient values
const M = series.length - TAU;        // 297 embedded points

// Time-delay embedding: e[i] = [x(i), x(i + TAU)]
const emb = new Array(M);
for (let i = 0; i < M; i++) emb[i] = [series[i], series[i + TAU]];

// Euclidean distance matrix — collect upper triangle for threshold
const dist = Array.from({ length: M }, () => new Float32Array(M));
const upperD = [];
for (let i = 0; i < M; i++) {
  for (let j = i + 1; j < M; j++) {
    const d = Math.hypot(emb[i][0] - emb[j][0], emb[i][1] - emb[j][1]);
    dist[i][j] = dist[j][i] = d;
    upperD.push(d);
  }
}
upperD.sort((a, b) => a - b);
const eps = upperD[Math.floor(upperD.length * 0.15)];  // ~15% recurrence rate

// --- Recurrence matrix → offscreen canvas → SVG image ---------------------
// Imprint palette[0] = #009E73 for recurrent points; pageBg for background
const offCanvas = document.createElement("canvas");
offCanvas.width = M;
offCanvas.height = M;
const ctx = offCanvas.getContext("2d");

// Parse hex #RRGGBB → [r, g, b]
const hr = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
const [bR, bG, bB] = hr(t.pageBg);
const [fR, fG, fB] = hr(t.palette[0]);  // Imprint palette position 1 — always first series

const imgData = ctx.createImageData(M, M);
const px = imgData.data;

// Matrix convention: row i = time index i (increases top → bottom)
for (let i = 0; i < M; i++) {
  for (let j = 0; j < M; j++) {
    const idx = 4 * (i * M + j);
    if (dist[i][j] <= eps) {
      px[idx] = fR; px[idx + 1] = fG; px[idx + 2] = fB; px[idx + 3] = 255;
    } else {
      px[idx] = bR; px[idx + 1] = bG; px[idx + 2] = bB; px[idx + 3] = 255;
    }
  }
}
ctx.putImageData(imgData, 0, 0);

// --- SVG mount --------------------------------------------------------------
const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);

svg.append("rect").attr("width", width).attr("height", height).attr("fill", t.pageBg);

const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Recurrence image — pixelated rendering keeps cell edges crisp
g.append("image")
  .attr("x", 0).attr("y", 0)
  .attr("width", iw).attr("height", ih)
  .attr("preserveAspectRatio", "none")
  .style("image-rendering", "pixelated")
  .attr("href", offCanvas.toDataURL());

// Plot border (matrix visualizations use all four sides)
g.append("rect")
  .attr("x", 0).attr("y", 0)
  .attr("width", iw).attr("height", ih)
  .attr("fill", "none")
  .attr("stroke", t.inkSoft).attr("stroke-width", 0.5);

// --- Axes ------------------------------------------------------------------
// Matrix convention: time 0 at top-left corner
const xScale = d3.scaleLinear().domain([0, M - 1]).range([0, iw]);
const yScale = d3.scaleLinear().domain([0, M - 1]).range([0, ih]);

const xAxisG = g.append("g").attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(xScale).ticks(6).tickSize(4));
const yAxisG = g.append("g")
  .call(d3.axisLeft(yScale).ticks(6).tickSize(4));

for (const ax of [xAxisG, yAxisG]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", "none");  // border rect handles the edge
}

// --- Axis labels -----------------------------------------------------------
g.append("text")
  .attr("x", iw / 2).attr("y", ih + 65)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft).style("font-size", "16px")
  .text("Time Index (i)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -(ih / 2)).attr("y", -68)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft).style("font-size", "16px")
  .text("Time Index (j)");

// --- Title -----------------------------------------------------------------
svg.append("text")
  .attr("x", width / 2).attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px").style("font-weight", "600")
  .text("recurrence-basic · javascript · d3 · anyplot.ai");
