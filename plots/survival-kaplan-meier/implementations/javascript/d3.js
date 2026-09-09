// anyplot.ai
// survival-kaplan-meier: Kaplan-Meier Survival Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-09

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 70, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Simple LCG — the browser has no seeded Math.random.
let seed = 42;
function rand() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const FOLLOW_UP_MONTHS = 36;

function simulatePatients(n, hazardRate, dropoutProb) {
  const patients = [];
  for (let i = 0; i < n; i++) {
    const eventTime = -Math.log(rand()) / hazardRate;
    const dropoutTime = rand() < dropoutProb ? rand() * FOLLOW_UP_MONTHS : Infinity;
    const censorTime = Math.min(dropoutTime, FOLLOW_UP_MONTHS);
    const time = Math.min(eventTime, censorTime);
    patients.push({ time, event: eventTime <= censorTime ? 1 : 0 });
  }
  return patients;
}

function kaplanMeier(patients) {
  const eventTimes = Array.from(new Set(patients.filter((d) => d.event === 1).map((d) => d.time))).sort(
    (a, b) => a - b,
  );

  let survival = 1;
  let varianceSum = 0;
  const steps = [{ time: 0, survival: 1, lower: 1, upper: 1 }];

  for (const time of eventTimes) {
    const atRisk = patients.filter((d) => d.time >= time).length;
    const deaths = patients.filter((d) => d.time === time && d.event === 1).length;
    survival *= 1 - deaths / atRisk;
    if (atRisk > deaths) varianceSum += deaths / (atRisk * (atRisk - deaths));
    const se = survival * Math.sqrt(varianceSum);
    steps.push({
      time,
      survival,
      lower: Math.max(0, survival - 1.96 * se),
      upper: Math.min(1, survival + 1.96 * se),
    });
  }
  steps.push({ ...steps[steps.length - 1], time: FOLLOW_UP_MONTHS });

  const censored = patients
    .filter((d) => d.event === 0 && d.time > 0)
    .map((d) => {
      let level = steps[0];
      for (const s of steps) if (s.time <= d.time) level = s;
      return { time: d.time, survival: level.survival };
    });

  return { steps, censored };
}

const groups = [
  { name: "Standard Therapy", n: 95, hazardRate: 0.05, dropoutProb: 0.18 },
  { name: "Novel Therapy", n: 95, hazardRate: 0.027, dropoutProb: 0.18 },
];
const curves = groups.map((group) => ({ ...group, ...kaplanMeier(simulatePatients(group.n, group.hazardRate, group.dropoutProb)) }));

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales ---------------------------------------------------------------
const x = d3.scaleLinear().domain([0, FOLLOW_UP_MONTHS]).range([0, iw]);
const y = d3.scaleLinear().domain([0, 1]).range([ih, 0]);

// --- Gridlines (y-axis only) -----------------------------------------------
g.append("g")
  .selectAll("line")
  .data(y.ticks(5))
  .join("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", (d) => y(d))
  .attr("y2", (d) => y(d))
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- 95% confidence bands ----------------------------------------------------
const band = d3
  .area()
  .x((d) => x(d.time))
  .y0((d) => y(d.lower))
  .y1((d) => y(d.upper))
  .curve(d3.curveStepAfter);

curves.forEach((c, i) => {
  g.append("path").datum(c.steps).attr("d", band).attr("fill", t.palette[i]).attr("fill-opacity", 0.15);
});

// --- Survival step curves -----------------------------------------------------
const stepLine = d3
  .line()
  .x((d) => x(d.time))
  .y((d) => y(d.survival))
  .curve(d3.curveStepAfter);

curves.forEach((c, i) => {
  g.append("path")
    .datum(c.steps)
    .attr("d", stepLine)
    .attr("fill", "none")
    .attr("stroke", t.palette[i])
    .attr("stroke-width", 3.5);
});

// --- Censoring tick marks -------------------------------------------------
const tickHalf = 7;
curves.forEach((c, i) => {
  g.append("g")
    .selectAll("line")
    .data(c.censored)
    .join("line")
    .attr("x1", (d) => x(d.time))
    .attr("x2", (d) => x(d.time))
    .attr("y1", (d) => y(d.survival) - tickHalf)
    .attr("y2", (d) => y(d.survival) + tickHalf)
    .attr("stroke", t.palette[i])
    .attr("stroke-width", 2);
});

// --- Axes -------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(9).tickSize(0).tickPadding(14));
const yAxis = g
  .append("g")
  .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format(".0%")).tickSize(0).tickPadding(14));

for (const axisG of [xAxis, yAxis]) {
  axisG.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  axisG.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels --------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "20px")
  .text("Time Since Enrollment (months)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -72)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "20px")
  .text("Survival Probability");

// --- Legend -----------------------------------------------------------------
const legend = g.append("g").attr("transform", `translate(${iw - 300}, 6)`);
curves.forEach((c, i) => {
  const row = legend.append("g").attr("transform", `translate(0, ${i * 34})`);
  row
    .append("line")
    .attr("x1", 0)
    .attr("x2", 28)
    .attr("y1", 0)
    .attr("y2", 0)
    .attr("stroke", t.palette[i])
    .attr("stroke-width", 4);
  row
    .append("text")
    .attr("x", 38)
    .attr("y", 5)
    .attr("fill", t.ink)
    .style("font-size", "16px")
    .text(`${c.name} (n=${c.n})`);
});

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "24px")
  .style("font-weight", "600")
  .text("survival-kaplan-meier · javascript · d3 · anyplot.ai");
