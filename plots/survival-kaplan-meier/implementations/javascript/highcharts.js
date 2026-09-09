// anyplot.ai
// survival-kaplan-meier: Kaplan-Meier Survival Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-09-09

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Reproducible RNG (fixed-seed LCG — the browser has no seeded Math.random) --
const makeLcg = (seed) => {
  let state = seed >>> 0;
  return () => {
    state = (1103515245 * state + 12345) & 0x7fffffff;
    return state / 0x7fffffff;
  };
};
const rand = makeLcg(42);
const exponential = (rate) => -Math.log(1 - rand()) / rate;

// --- Data: time-to-failure (months in service) for two bearing designs -----
const STUDY_END = 60;
const DROPOUT_RATE = 0.01;
const GROUPS = [
  { name: "Standard Bearing", failureRate: 0.035, n: 70 },
  { name: "Reinforced Bearing", failureRate: 0.018, n: 70 },
];

const records = GROUPS.map((group) => {
  const units = [];
  for (let i = 0; i < group.n; i++) {
    const failureTime = exponential(group.failureRate);
    const dropoutTime = exponential(DROPOUT_RATE);
    const time = Math.min(failureTime, dropoutTime, STUDY_END);
    const event = failureTime <= dropoutTime && failureTime <= STUDY_END ? 1 : 0;
    units.push({ time, event });
  }
  return units.sort((a, b) => a.time - b.time);
});

// --- Kaplan-Meier estimator with Greenwood confidence intervals ------------
const kaplanMeier = (units) => {
  const eventTimes = [...new Set(units.filter((u) => u.event === 1).map((u) => u.time))].sort(
    (a, b) => a - b
  );
  let survival = 1;
  let greenwoodSum = 0;
  const steps = [{ time: 0, survival: 1, lower: 1, upper: 1 }];
  eventTimes.forEach((time) => {
    const atRisk = units.filter((u) => u.time >= time).length;
    const deaths = units.filter((u) => u.time === time && u.event === 1).length;
    survival *= 1 - deaths / atRisk;
    if (atRisk > deaths) greenwoodSum += deaths / (atRisk * (atRisk - deaths));
    const se = survival * Math.sqrt(greenwoodSum);
    steps.push({
      time,
      survival,
      lower: Math.max(0, survival - 1.96 * se),
      upper: Math.min(1, survival + 1.96 * se),
    });
  });
  const censoredTimes = units.filter((u) => u.event === 0).map((u) => u.time);
  return { steps, censoredTimes };
};

const curves = records.map(kaplanMeier);

// Step-held survival value at an arbitrary time (for placing censoring ticks).
const survivalAt = (steps, time) => {
  let value = 1;
  for (const step of steps) {
    if (step.time > time) break;
    value = step.survival;
  }
  return value;
};

// First time the curve reaches 50% survival, or null if never reached.
const medianSurvival = (steps) => {
  const hit = steps.find((s) => s.survival <= 0.5);
  return hit ? hit.time : null;
};

// --- Log-rank test (Mantel-Cox) comparing the two groups --------------------
const erf = (x) => {
  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x);
  const a1 = 0.254829592;
  const a2 = -0.284496736;
  const a3 = 1.421413741;
  const a4 = -1.453152027;
  const a5 = 1.061405429;
  const p = 0.3275911;
  const tt = 1 / (1 + p * x);
  const y = 1 - ((((a5 * tt + a4) * tt + a3) * tt + a2) * tt + a1) * tt * Math.exp(-x * x);
  return sign * y;
};

const logRankTest = (unitsA, unitsB) => {
  const eventTimes = [...new Set([...unitsA, ...unitsB].filter((u) => u.event === 1).map((u) => u.time))].sort(
    (a, b) => a - b
  );
  let observedA = 0;
  let expectedA = 0;
  let variance = 0;
  eventTimes.forEach((time) => {
    const atRiskA = unitsA.filter((u) => u.time >= time).length;
    const atRiskB = unitsB.filter((u) => u.time >= time).length;
    const deathsA = unitsA.filter((u) => u.time === time && u.event === 1).length;
    const deathsB = unitsB.filter((u) => u.time === time && u.event === 1).length;
    const atRisk = atRiskA + atRiskB;
    const deaths = deathsA + deathsB;
    if (atRisk < 2) return;
    observedA += deathsA;
    expectedA += (deaths * atRiskA) / atRisk;
    variance += (deaths * (atRiskA / atRisk) * (atRiskB / atRisk) * (atRisk - deaths)) / (atRisk - 1);
  });
  const chiSquare = variance > 0 ? (observedA - expectedA) ** 2 / variance : 0;
  const pValue = 1 - erf(Math.sqrt(chiSquare / 2));
  return { chiSquare, pValue };
};

const { chiSquare, pValue } = logRankTest(records[0], records[1]);

// --- Series data: step curve, plus tick markers at censored times ----------
const buildLineData = (steps, censoredTimes) => {
  const points = steps.map((s) => ({ x: s.time, y: s.survival, marker: { enabled: false } }));
  censoredTimes.forEach((time) => {
    points.push({ x: time, y: survivalAt(steps, time), marker: { enabled: true } });
  });
  points.push({ x: STUDY_END, y: steps[steps.length - 1].survival, marker: { enabled: false } });
  return points.sort((a, b) => a.x - b.x);
};

// Custom vertical-tick marker symbol for censored observations (core
// SVGRenderer API — no add-on module needed).
Highcharts.SVGRenderer.prototype.symbols.tick = (x, y, w, h) => ["M", x + w / 2, y, "L", x + w / 2, y + h];

// Confidence-band outline in pixel space, following the same step-after
// shape as the survival line. `arearange` (the natural fit) lives in the
// highcharts-more module, which anyplot doesn't vendor — the core
// SVGRenderer draws the equivalent polygon directly instead.
const bandOutline = (steps, xAxis, yAxis, key) => {
  const extended = steps.concat([{ ...steps[steps.length - 1], time: STUDY_END }]);
  const pixels = [];
  extended.forEach((step, i) => {
    const x = xAxis.toPixels(step.time);
    if (i > 0) pixels.push([x, pixels[pixels.length - 1][1]]);
    pixels.push([x, yAxis.toPixels(step[key])]);
  });
  return pixels;
};

Highcharts.chart(
  "container",
  {
    chart: {
      type: "line",
      backgroundColor: "transparent",
      animation: false,
      style: { fontFamily: "inherit" },
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
      text: "survival-kaplan-meier · javascript · highcharts · anyplot.ai",
      style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
    },
    subtitle: {
      text: `Log-rank test: χ² = ${chiSquare.toFixed(2)}, p ${pValue < 0.001 ? "< 0.001" : `= ${pValue.toFixed(3)}`} (df=1)`,
      style: { color: t.inkSoft, fontSize: "14px" },
    },
    xAxis: {
      title: { text: "Months in Service", style: { color: t.inkSoft, fontSize: "16px" } },
      min: 0,
      max: STUDY_END,
      tickInterval: 12,
      lineColor: t.inkSoft,
      tickColor: t.inkSoft,
      gridLineColor: t.grid,
      labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    },
    yAxis: {
      title: { text: "Survival Probability", style: { color: t.inkSoft, fontSize: "16px" } },
      min: 0,
      max: 1,
      tickInterval: 0.2,
      gridLineColor: t.grid,
      labels: {
        style: { color: t.inkSoft, fontSize: "14px" },
        formatter() {
          return `${Math.round(this.value * 100)}%`;
        },
      },
      plotLines: [
        {
          value: 0.5,
          color: t.inkSoft,
          dashStyle: "Dash",
          width: 1.5,
          zIndex: 4,
          label: { text: "Median", align: "left", style: { color: t.inkSoft, fontSize: "12px" } },
        },
      ],
    },
    legend: {
      itemStyle: { color: t.inkSoft, fontSize: "14px" },
      itemHoverStyle: { color: t.ink },
    },
    plotOptions: {
      series: {
        animation: false,
        lineWidth: 3,
        step: "left",
        marker: { enabled: false, symbol: "tick", radius: 7, lineWidth: 1.5, fillColor: "transparent" },
      },
    },
    series: GROUPS.map((group, i) => ({
      name: group.name,
      data: buildLineData(curves[i].steps, curves[i].censoredTimes),
      color: t.palette[i],
      zIndex: 3,
    })),
  },
  (chart) => {
    // Shaded 95% CI bands, drawn behind the survival lines.
    curves.forEach((curve, i) => {
      const bandColor = Highcharts.color(t.palette[i]).setOpacity(0.15).get();
      const upper = bandOutline(curve.steps, chart.xAxis[0], chart.yAxis[0], "upper");
      const lower = bandOutline(curve.steps, chart.xAxis[0], chart.yAxis[0], "lower").reverse();
      const path = ["M", upper[0][0], upper[0][1]];
      upper.slice(1).forEach(([x, y]) => path.push("L", x, y));
      lower.forEach(([x, y]) => path.push("L", x, y));
      path.push("Z");
      chart.renderer.path(path).attr({ fill: bandColor, zIndex: 0 }).add(chart.seriesGroup);
    });

    // Per-group median survival markers.
    GROUPS.forEach((group, i) => {
      const median = medianSurvival(curves[i].steps);
      if (median !== null) {
        chart.xAxis[0].addPlotLine({ value: median, color: t.palette[i], dashStyle: "Dot", width: 1, zIndex: 2 });
      }
    });
  }
);
