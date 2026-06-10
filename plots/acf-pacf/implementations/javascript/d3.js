// anyplot.ai
// acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-10
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Deterministic LCG (no seeded RNG in browser)
let _seed = 42;
function lcg() {
  _seed = (Math.imul(_seed, 1664525) + 1013904223) >>> 0;
  return _seed / 4294967296;
}
function randn() {
  return Math.sqrt(-2 * Math.log(Math.max(lcg(), 1e-12))) * Math.cos(2 * Math.PI * lcg());
}

// AR(2) series: x_t = 0.7·x_{t-1} − 0.3·x_{t-2} + ε_t
// Stationary; PACF cuts off after lag 2 — canonical AR-order diagnostic
const N = 200;
const series = [randn(), 0.7 * randn() + randn()];
for (let i = 2; i < N; i++) {
  series.push(0.7 * series[i - 1] - 0.3 * series[i - 2] + randn());
}

// ACF: r(k) = Cov(x_t, x_{t-k}) / Var(x)
function computeACF(x, maxLag) {
  const n = x.length;
  const mean = x.reduce((s, v) => s + v, 0) / n;
  const variance = x.reduce((s, v) => s + (v - mean) ** 2, 0) / n;
  return Array.from({ length: maxLag + 1 }, (_, k) => {
    if (k === 0) return 1.0;
    let cov = 0;
    for (let i = k; i < n; i++) cov += (x[i] - mean) * (x[i - k] - mean);
    return cov / (n * variance);
  });
}

// PACF via Durbin-Levinson: phi_{k,k} is partial autocorrelation at lag k
function computePACF(acf, maxLag) {
  const phi = Array.from({ length: maxLag + 1 }, () => new Array(maxLag + 1).fill(0));
  const pacf = new Array(maxLag + 1).fill(0);
  pacf[0] = 1.0;
  for (let k = 1; k <= maxLag; k++) {
    let num = acf[k], den = 1.0;
    for (let j = 1; j < k; j++) {
      num -= phi[k - 1][j] * acf[k - j];
      den -= phi[k - 1][j] * acf[j];
    }
    phi[k][k] = Math.abs(den) > 1e-10 ? num / den : 0;
    for (let j = 1; j < k; j++) {
      phi[k][j] = phi[k - 1][j] - phi[k][k] * phi[k - 1][k - j];
    }
    pacf[k] = phi[k][k];
  }
  return pacf;
}

const maxLag = 30;
const acfVals = computeACF(series, maxLag);
const pacfVals = computePACF(acfVals, maxLag);
const confBand = 1.96 / Math.sqrt(N);

// Layout
const margin = { top: 70, right: 60, bottom: 70, left: 80 };
const iw = width - margin.left - margin.right;
const panelGap = 40;
const panelH = (height - margin.top - margin.bottom - panelGap) / 2;

const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);

const root = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Draw an ACF or PACF panel
function drawPanel(g, data, yLabel, color, yTop, showXLabels) {
  const vals = data.map((d) => d.val);
  const vMin = Math.min(d3.min(vals), -confBand) - 0.08;
  const vMax = Math.max(d3.max(vals), confBand, yLabel === "ACF" ? 1.0 : 0) + 0.08;

  const xScale = d3.scaleLinear().domain([-0.5, maxLag + 0.5]).range([0, iw]);
  const yScale = d3.scaleLinear().domain([vMin, vMax]).nice().range([panelH, 0]);

  const pg = g.append("g").attr("transform", `translate(0,${yTop})`);

  // Horizontal gridlines
  for (const tick of yScale.ticks(5)) {
    pg.append("line")
      .attr("x1", 0)
      .attr("x2", iw)
      .attr("y1", yScale(tick))
      .attr("y2", yScale(tick))
      .attr("stroke", t.grid)
      .attr("stroke-width", 1);
  }

  // Zero baseline
  pg.append("line")
    .attr("x1", 0)
    .attr("x2", iw)
    .attr("y1", yScale(0))
    .attr("y2", yScale(0))
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1.5)
    .attr("opacity", 0.5);

  // Confidence band fill (amber, very subtle)
  pg.append("rect")
    .attr("x", 0)
    .attr("width", iw)
    .attr("y", yScale(confBand))
    .attr("height", yScale(-confBand) - yScale(confBand))
    .attr("fill", "#DDCC77")
    .attr("opacity", 0.08);

  // Confidence band dashed boundary lines
  for (const cb of [confBand, -confBand]) {
    pg.append("line")
      .attr("x1", 0)
      .attr("x2", iw)
      .attr("y1", yScale(cb))
      .attr("y2", yScale(cb))
      .attr("stroke", "#DDCC77")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "8,5");
  }

  // Stem lines
  pg.selectAll(".stem")
    .data(data)
    .join("line")
    .attr("class", "stem")
    .attr("x1", (d) => xScale(d.lag))
    .attr("x2", (d) => xScale(d.lag))
    .attr("y1", yScale(0))
    .attr("y2", (d) => yScale(d.val))
    .attr("stroke", color)
    .attr("stroke-width", 2.5);

  // Tip markers
  pg.selectAll(".dot")
    .data(data)
    .join("circle")
    .attr("class", "dot")
    .attr("cx", (d) => xScale(d.lag))
    .attr("cy", (d) => yScale(d.val))
    .attr("r", 4.5)
    .attr("fill", color)
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 1);

  // Y axis
  const yAx = pg.append("g").call(d3.axisLeft(yScale).ticks(5).tickSize(5));
  yAx.selectAll("text").attr("fill", t.inkSoft).style("font-size", "13px");
  yAx.selectAll(".tick line").attr("stroke", t.inkSoft);
  yAx.select(".domain").attr("stroke", t.inkSoft);

  // X axis
  const xAx = pg
    .append("g")
    .attr("transform", `translate(0,${panelH})`)
    .call(d3.axisBottom(xScale).ticks(10).tickSize(5));
  if (showXLabels) {
    xAx.selectAll("text").attr("fill", t.inkSoft).style("font-size", "13px");
  } else {
    xAx.selectAll("text").remove();
  }
  xAx.selectAll(".tick line").attr("stroke", t.inkSoft);
  xAx.select(".domain").attr("stroke", t.inkSoft);

  // Y-axis label (rotated)
  pg.append("text")
    .attr("transform", `translate(${-60},${panelH / 2}) rotate(-90)`)
    .attr("text-anchor", "middle")
    .attr("fill", t.ink)
    .style("font-size", "15px")
    .style("font-weight", "600")
    .text(yLabel);
}

// ACF panel: lags 0 … maxLag (lag 0 = 1.0)
drawPanel(
  root,
  acfVals.map((v, k) => ({ lag: k, val: v })),
  "ACF",
  t.palette[0],
  0,
  false
);

// PACF panel: lags 1 … maxLag (skip lag 0)
drawPanel(
  root,
  pacfVals.slice(1).map((v, i) => ({ lag: i + 1, val: v })),
  "PACF",
  t.palette[2],
  panelH + panelGap,
  true
);

// X-axis label
svg
  .append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 22)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Lag");

// Title
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("Monthly Retail Sales · acf-pacf · javascript · d3 · anyplot.ai");
