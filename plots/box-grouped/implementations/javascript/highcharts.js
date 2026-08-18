// anyplot.ai
// box-grouped: Grouped Box Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-08-18

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
function makeLcg(seed) {
  let state = seed >>> 0;
  return function lcg() {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

function randNormal(mean, std) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

const departments = ["Engineering", "Sales", "Support", "Operations"];
const levels = ["Junior", "Mid-level", "Senior"];

// Baseline productivity score per department, plus a per-level offset and
// spread — seniority raises the median and tightens the spread.
const deptBase = { Engineering: 58, Sales: 66, Support: 60, Operations: 63 };
const levelOffset = { Junior: 0, "Mid-level": 12, Senior: 21 };
const levelStd = { Junior: 10, "Mid-level": 8.5, Senior: 6.5 };
const sampleSize = 45;

const rawSamples = departments.map((dept) =>
  levels.map((level) => {
    const mean = deptBase[dept] + levelOffset[level];
    const std = levelStd[level];
    const values = [];
    for (let j = 0; j < sampleSize; j++) {
      values.push(Math.round(randNormal(mean, std) * 10) / 10);
    }
    return values;
  })
);

// A few realistic outliers: a struggling senior, a standout junior.
rawSamples[0][2].push(94.2);
rawSamples[1][0].push(91.5);
rawSamples[2][1].push(35.8);
rawSamples[3][2].push(45.1);

function quantile(sorted, q) {
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  return sorted[base + 1] !== undefined
    ? sorted[base] + rest * (sorted[base + 1] - sorted[base])
    : sorted[base];
}

const boxStats = rawSamples.map((deptSamples) =>
  deptSamples.map((values) => {
    const sorted = values.slice().sort((a, b) => a - b);
    const q1 = quantile(sorted, 0.25);
    const median = quantile(sorted, 0.5);
    const q3 = quantile(sorted, 0.75);
    const iqr = q3 - q1;
    const lowFence = q1 - 1.5 * iqr;
    const highFence = q3 + 1.5 * iqr;
    const inFence = sorted.filter((v) => v >= lowFence && v <= highFence);
    const outliers = sorted.filter((v) => v < lowFence || v > highFence);
    return {
      q1,
      median,
      q3,
      whiskerLow: Math.min(...inFence),
      whiskerHigh: Math.max(...inFence),
      outliers,
    };
  })
);

const allValues = rawSamples.flat(2);
const valueRange = Math.max(...allValues) - Math.min(...allValues);
const yPad = valueRange * 0.06;
const yMin = Math.min(...allValues) - yPad;
const yMax = Math.max(...allValues) + yPad;

// --- Chart -------------------------------------------------------------------
let customGroup = null;

Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    events: {
      render() {
        if (customGroup) customGroup.destroy();
        customGroup = this.renderer.g("grouped-boxes").add();

        const xAxis = this.xAxis[0];
        const yAxis = this.yAxis[0];
        const nSub = levels.length;
        const slot = Math.abs(xAxis.toPixels(1, false) - xAxis.toPixels(0, false));
        const groupWidth = slot * 0.72;
        const boxWidth = (groupWidth / nSub) * 0.78;
        const capWidth = boxWidth * 0.55;

        boxStats.forEach((deptStats, i) => {
          const xc0 = xAxis.toPixels(i, false);

          deptStats.forEach((s, k) => {
            const color = t.palette[k % t.palette.length];
            const offset = (k - (nSub - 1) / 2) * (groupWidth / nSub);
            const xc = xc0 + offset;
            const left = xc - boxWidth / 2;

            const yQ1 = yAxis.toPixels(s.q1, false);
            const yQ3 = yAxis.toPixels(s.q3, false);
            const yMed = yAxis.toPixels(s.median, false);
            const yWhiskerLow = yAxis.toPixels(s.whiskerLow, false);
            const yWhiskerHigh = yAxis.toPixels(s.whiskerHigh, false);

            // Whiskers + caps
            this.renderer
              .path(["M", xc, yQ3, "L", xc, yWhiskerHigh])
              .attr({ "stroke-width": 2, stroke: color, zIndex: 3 })
              .add(customGroup);
            this.renderer
              .path(["M", xc, yQ1, "L", xc, yWhiskerLow])
              .attr({ "stroke-width": 2, stroke: color, zIndex: 3 })
              .add(customGroup);
            this.renderer
              .path(["M", xc - capWidth / 2, yWhiskerHigh, "L", xc + capWidth / 2, yWhiskerHigh])
              .attr({ "stroke-width": 2, stroke: color, zIndex: 3 })
              .add(customGroup);
            this.renderer
              .path(["M", xc - capWidth / 2, yWhiskerLow, "L", xc + capWidth / 2, yWhiskerLow])
              .attr({ "stroke-width": 2, stroke: color, zIndex: 3 })
              .add(customGroup);

            // Box body (Q1–Q3)
            const r = Math.min(4, boxWidth * 0.12);
            this.renderer
              .rect(left, yQ3, boxWidth, yQ1 - yQ3, r)
              .attr({
                fill: Highcharts.color(color).setOpacity(0.45).get(),
                stroke: color,
                "stroke-width": 2,
                zIndex: 4,
              })
              .add(customGroup);

            // Median line
            this.renderer
              .path(["M", left, yMed, "L", left + boxWidth, yMed])
              .attr({ "stroke-width": 2.5, stroke: t.ink, zIndex: 5 })
              .add(customGroup);

            // Outliers
            s.outliers.forEach((v) => {
              this.renderer
                .circle(xc, yAxis.toPixels(v, false), 6.5)
                .attr({ fill: t.pageBg, stroke: color, "stroke-width": 2, zIndex: 6 })
                .add(customGroup);
            });
          });
        });
      },
    },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "box-grouped · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: departments,
    title: { text: "Department", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    min: yMin,
    max: yMax,
    startOnTick: false,
    endOnTick: false,
    title: { text: "Productivity Score", style: { color: t.inkSoft, fontSize: "16px" } },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    title: { text: "Experience Level", style: { color: t.inkSoft, fontSize: "14px" } },
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false },
    column: {
      opacity: 0,
      borderWidth: 0,
      enableMouseTracking: false,
      states: { hover: { enabled: false } },
    },
  },
  series: levels.map((level, k) => ({
    type: "column",
    name: level,
    color: t.palette[k % t.palette.length],
    data: boxStats.map((deptStats) => deptStats[k].median),
    showInLegend: true,
  })),
});
