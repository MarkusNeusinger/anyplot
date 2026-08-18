// anyplot.ai
// box-grouped: Grouped Box Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-08-18

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 150, right: 60, bottom: 110, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Reaction-time study: task type x age group, 70 trials per cell.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);
function randNormal(mean, sd) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * sd;
}

const taskTypes = ["Visual", "Auditory", "Tactile", "Combined"];
const ageGroups = ["Young (18-30)", "Middle (31-50)", "Older (51-70)"];
const baseMean = { Visual: 320, Auditory: 280, Tactile: 350, Combined: 420 };
const ageOffset = { "Young (18-30)": 0, "Middle (31-50)": 40, "Older (51-70)": 90 };
const trialsPerCell = 70;

const cells = [];
for (const task of taskTypes) {
  for (const age of ageGroups) {
    const mean = baseMean[task] + ageOffset[age];
    const values = Array.from({ length: trialsPerCell }, () =>
      Math.max(120, randNormal(mean, 45)),
    ).sort((a, b) => a - b);

    const q1 = d3.quantile(values, 0.25);
    const median = d3.quantile(values, 0.5);
    const q3 = d3.quantile(values, 0.75);
    const iqr = q3 - q1;
    const lowerFence = q1 - 1.5 * iqr;
    const upperFence = q3 + 1.5 * iqr;
    const inliers = values.filter((v) => v >= lowerFence && v <= upperFence);
    const outliers = values.filter((v) => v < lowerFence || v > upperFence);

    cells.push({
      task,
      age,
      q1,
      median,
      q3,
      whiskerLow: d3.min(inliers),
      whiskerHigh: d3.max(inliers),
      outliers,
    });
  }
}

const allValues = cells.flatMap((c) => [c.whiskerLow, c.whiskerHigh, ...c.outliers]);
const valueExtent = d3.extent(allValues);
const valuePad = (valueExtent[1] - valueExtent[0]) * 0.08;

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales ---------------------------------------------------------------------
const x0 = d3.scaleBand().domain(taskTypes).range([0, iw]).paddingInner(0.35).paddingOuter(0.15);
const x1 = d3.scaleBand().domain(ageGroups).range([0, x0.bandwidth()]).padding(0.25);
const y = d3
  .scaleLinear()
  .domain([valueExtent[0] - valuePad, valueExtent[1] + valuePad])
  .nice()
  .range([ih, 0]);
const color = d3.scaleOrdinal().domain(ageGroups).range(t.palette.slice(0, ageGroups.length));

// --- Gridlines --------------------------------------------------------------
g.append("g")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .selectAll("line")
  .attr("stroke", t.grid);
g.select(".domain").remove();

// --- Axes ---------------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x0));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6).tickFormat((d) => `${d} ms`));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels --------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 66)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Task Type");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -78)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Reaction Time (ms)");

// --- Grouped boxes --------------------------------------------------------------
const boxWidth = x1.bandwidth();
const capWidth = boxWidth * 0.5;

const group = g
  .selectAll(".cell")
  .data(cells)
  .join("g")
  .attr("class", "cell")
  .attr("transform", (d) => `translate(${x0(d.task) + x1(d.age)},0)`);

// Whiskers
group
  .append("line")
  .attr("x1", boxWidth / 2)
  .attr("x2", boxWidth / 2)
  .attr("y1", (d) => y(d.whiskerLow))
  .attr("y2", (d) => y(d.q1))
  .attr("stroke", (d) => color(d.age))
  .attr("stroke-width", 2);
group
  .append("line")
  .attr("x1", boxWidth / 2)
  .attr("x2", boxWidth / 2)
  .attr("y1", (d) => y(d.q3))
  .attr("y2", (d) => y(d.whiskerHigh))
  .attr("stroke", (d) => color(d.age))
  .attr("stroke-width", 2);

// Whisker caps
for (const key of ["whiskerLow", "whiskerHigh"]) {
  group
    .append("line")
    .attr("x1", (boxWidth - capWidth) / 2)
    .attr("x2", (boxWidth + capWidth) / 2)
    .attr("y1", (d) => y(d[key]))
    .attr("y2", (d) => y(d[key]))
    .attr("stroke", (d) => color(d.age))
    .attr("stroke-width", 2);
}

// Box (Q1-Q3)
group
  .append("rect")
  .attr("x", 0)
  .attr("y", (d) => y(d.q3))
  .attr("width", boxWidth)
  .attr("height", (d) => y(d.q1) - y(d.q3))
  .attr("fill", (d) => color(d.age))
  .attr("fill-opacity", 0.55)
  .attr("stroke", (d) => color(d.age))
  .attr("stroke-width", 2);

// Median line
group
  .append("line")
  .attr("x1", 0)
  .attr("x2", boxWidth)
  .attr("y1", (d) => y(d.median))
  .attr("y2", (d) => y(d.median))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 3);

// Outliers — cluster near-duplicate values within the same box get a small
// deterministic horizontal spread so individual points stay separable.
const yDomainSpan = y.domain()[1] - y.domain()[0];
const clusterThreshold = yDomainSpan * 0.01;
function spreadOutliers(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const dx = new Array(sorted.length).fill(0);
  let clusterStart = 0;
  for (let i = 1; i <= sorted.length; i++) {
    const closeToPrev = i < sorted.length && sorted[i] - sorted[i - 1] < clusterThreshold;
    if (!closeToPrev) {
      const clusterSize = i - clusterStart;
      if (clusterSize > 1) {
        for (let j = clusterStart; j < i; j++) {
          dx[j] = (j - clusterStart - (clusterSize - 1) / 2) * 6;
        }
      }
      clusterStart = i;
    }
  }
  return sorted.map((value, i) => ({ value, dx: dx[i] }));
}

group
  .selectAll(".outlier")
  .data((d) => spreadOutliers(d.outliers).map(({ value, dx }) => ({ value, dx, age: d.age })))
  .join("circle")
  .attr("class", "outlier")
  .attr("cx", (d) => boxWidth / 2 + d.dx)
  .attr("cy", (d) => y(d.value))
  .attr("r", 4.5)
  .attr("fill", (d) => color(d.age))
  .attr("fill-opacity", 0.85)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1);

// --- Age-gap callout: highlight the task type with the largest Young→Older shift ---
const youngAge = ageGroups[0];
const olderAge = ageGroups[ageGroups.length - 1];
const gapByTask = taskTypes.map((task) => {
  const young = cells.find((c) => c.task === task && c.age === youngAge);
  const older = cells.find((c) => c.task === task && c.age === olderAge);
  return { task, young, older, gap: older.median - young.median };
});
const widestGap = gapByTask.reduce((a, b) => (b.gap > a.gap ? b : a));
const gapYoungX = x0(widestGap.task) + x1(youngAge) + boxWidth / 2;
const gapOlderX = x0(widestGap.task) + x1(olderAge) + boxWidth / 2;
const gapY = Math.min(y(widestGap.young.q3), y(widestGap.older.q3)) - 16;

const callout = g.append("g").attr("class", "age-gap-callout");
callout
  .append("line")
  .attr("x1", gapYoungX)
  .attr("x2", gapOlderX)
  .attr("y1", gapY)
  .attr("y2", gapY)
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1)
  .attr("stroke-dasharray", "3,2");
for (const cx of [gapYoungX, gapOlderX]) {
  callout
    .append("line")
    .attr("x1", cx)
    .attr("x2", cx)
    .attr("y1", gapY)
    .attr("y2", gapY + 6)
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1);
}
callout
  .append("text")
  .attr("x", (gapYoungX + gapOlderX) / 2)
  .attr("y", gapY - 7)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "12px")
  .style("font-style", "italic")
  .text(`+${Math.round(widestGap.gap)} ms largest age gap`);

// --- Legend ---------------------------------------------------------------------
const legend = svg.append("g").attr("transform", `translate(0, 96)`);
let xOffset = 0;
for (const age of ageGroups) {
  const item = legend.append("g").attr("transform", `translate(${xOffset},0)`);
  item.append("rect").attr("width", 18).attr("height", 18).attr("y", -13).attr("rx", 3).attr("fill", color(age));
  const label = item
    .append("text")
    .attr("x", 26)
    .attr("y", 0)
    .attr("dominant-baseline", "middle")
    .attr("fill", t.ink)
    .style("font-size", "14px")
    .text(age);
  xOffset += 26 + label.node().getBBox().width + 34;
}
const legendWidth = xOffset - 34;
legend.attr("transform", `translate(${(width - legendWidth) / 2}, 96)`);

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("box-grouped · javascript · d3 · anyplot.ai");
