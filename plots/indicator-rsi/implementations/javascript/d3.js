// anyplot.ai
// indicator-rsi: RSI Technical Indicator Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 60, bottom: 70, left: 80 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: 120-day RSI(14) series derived from a synthetic price walk ------
// Deterministic LCG (browser has no seeded Math.random)
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const numDays = 120;
const prices = [180];
for (let i = 1; i < numDays + 1; i++) {
  const drift = Math.sin(i / 9) * 0.9;
  const noise = (rand() - 0.5) * 3.2;
  prices.push(prices[i - 1] + drift + noise);
}

const lookback = 14;
function computeRsi(series, period) {
  const rsi = new Array(series.length).fill(null);
  let gainSum = 0;
  let lossSum = 0;
  for (let i = 1; i <= period; i++) {
    const change = series[i] - series[i - 1];
    if (change > 0) gainSum += change;
    else lossSum -= change;
  }
  let avgGain = gainSum / period;
  let avgLoss = lossSum / period;
  rsi[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  for (let i = period + 1; i < series.length; i++) {
    const change = series[i] - series[i - 1];
    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? -change : 0;
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    rsi[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }
  return rsi;
}

const startDate = new Date(2025, 5, 2);
const rsiSeries = computeRsi(prices, lookback);
const data = rsiSeries
  .map((value, i) => ({ date: new Date(startDate.getTime() + i * 86400000), value }))
  .filter((d) => d.value !== null);

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const x = d3
  .scaleTime()
  .domain(d3.extent(data, (d) => d.date))
  .range([0, iw]);
const y = d3.scaleLinear().domain([0, 100]).range([ih, 0]);

// --- Zone shading (overbought 70-100, oversold 0-30) --------------------------
g.append("rect")
  .attr("x", 0)
  .attr("y", y(100))
  .attr("width", iw)
  .attr("height", y(70) - y(100))
  .attr("fill", t.palette[4])
  .attr("opacity", 0.1);

g.append("rect")
  .attr("x", 0)
  .attr("y", y(30))
  .attr("width", iw)
  .attr("height", y(0) - y(30))
  .attr("fill", t.palette[2])
  .attr("opacity", 0.1);

// --- Threshold + centerline lines ---------------------------------------------
const thresholds = [
  { level: 70, label: "Overbought (70)", color: t.palette[4] },
  { level: 50, label: "Centerline (50)", color: t.grid },
  { level: 30, label: "Oversold (30)", color: t.palette[2] },
];

for (const th of thresholds) {
  g.append("line")
    .attr("x1", 0)
    .attr("x2", iw)
    .attr("y1", y(th.level))
    .attr("y2", y(th.level))
    .attr("stroke", th.color)
    .attr("stroke-width", th.level === 50 ? 1.5 : 2)
    .attr("stroke-dasharray", th.level === 50 ? "2,4" : "6,4")
    .attr("opacity", th.level === 50 ? 0.6 : 0.85);

  g.append("text")
    .attr("x", iw - 4)
    .attr("y", y(th.level) - 8)
    .attr("text-anchor", "end")
    .attr("fill", th.color)
    .style("font-size", "13px")
    .style("font-weight", "600")
    .text(th.label);
}

// --- Axes -----------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(7).tickFormat(d3.timeFormat("%b %d")));
const yAxis = g.append("g").call(d3.axisLeft(y).tickValues([0, 30, 50, 70, 100]));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
}
xAxis.selectAll(".tick line").remove();
yAxis.selectAll(".tick line").remove();

// --- RSI line ---------------------------------------------------------------
const line = d3
  .line()
  .x((d) => x(d.date))
  .y((d) => y(d.value))
  .curve(d3.curveMonotoneX);

g.append("path").datum(data).attr("fill", "none").attr("stroke", t.palette[0]).attr("stroke-width", 3).attr("d", line);

// --- Axis labels --------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Trading Date");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("RSI");

// --- Title + subtitle -----------------------------------------------------
const title = "indicator-rsi · javascript · d3 · anyplot.ai";
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text(title);

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 68)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text(`14-period RSI on a synthetic 120-day daily close series`);
