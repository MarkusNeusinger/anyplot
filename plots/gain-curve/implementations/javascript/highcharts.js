// anyplot.ai
// gain-curve: Cumulative Gains Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const N_TRANSACTIONS = 2000;
const FRAUD_RATE = 0.05;

function mulberry32(seed) {
  return function () {
    seed = (seed + 0x6d2b79f5) | 0;
    let z = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z;
    return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(42);

function randNormal() {
  let u1 = rand();
  while (u1 === 0) u1 = rand();
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// A fraud-detection risk score: fraudulent transactions skew higher, but
// overlap with legitimate ones, mimicking a realistic (imperfect) model.
const transactions = [];
for (let i = 0; i < N_TRANSACTIONS; i++) {
  const isFraud = rand() < FRAUD_RATE ? 1 : 0;
  const riskScore = isFraud ? 0.62 + 0.22 * randNormal() : 0.22 + 0.18 * randNormal();
  transactions.push({ isFraud, riskScore });
}
transactions.sort((a, b) => b.riskScore - a.riskScore);

const totalFraud = transactions.reduce((sum, tx) => sum + tx.isFraud, 0);

const modelGains = [[0, 0]];
let capturedFraud = 0;
transactions.forEach((tx, i) => {
  capturedFraud += tx.isFraud;
  const targetedPct = ((i + 1) / N_TRANSACTIONS) * 100;
  const capturedPct = (capturedFraud / totalFraud) * 100;
  modelGains.push([targetedPct, capturedPct]);
});

const baselineGains = [
  [0, 0],
  [100, 100],
];

// Highlight the point where the model first captures 95% of fraud cases —
// the "diminishing returns" transition called out via a plotLine dropline.
const PLATEAU_CAPTURE_PCT = 95;
const [plateauTargetedPct, plateauCapturedPct] =
  modelGains.find(([, capturedPct]) => capturedPct >= PLATEAU_CAPTURE_PCT) ??
  modelGains[modelGains.length - 1];

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "gain-curve · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Fraud investigations ranked by model risk score vs. random selection",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: {
      text: "Transactions Investigated (%)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    min: 0,
    max: 100,
    tickInterval: 20,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { format: "{value}%", style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      {
        value: plateauTargetedPct,
        color: t.inkSoft,
        width: 1,
        dashStyle: "ShortDot",
        zIndex: 4,
        label: {
          text: `${PLATEAU_CAPTURE_PCT}% captured at ${plateauTargetedPct.toFixed(0)}% targeted`,
          style: { color: t.inkSoft, fontSize: "12px" },
          rotation: 0,
          align: "left",
          x: 8,
          verticalAlign: "bottom",
          y: -10,
        },
      },
    ],
  },
  yAxis: {
    title: {
      text: "Fraud Cases Captured (%)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    min: 0,
    max: 100,
    tickInterval: 20,
    gridLineColor: t.grid,
    labels: { format: "{value}%", style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      { value: plateauCapturedPct, color: t.inkSoft, width: 1, dashStyle: "ShortDot", zIndex: 4 },
    ],
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    formatter: function () {
      const lift = this.x > 0 ? (this.y / this.x).toFixed(2) : "—";
      return `<b>${this.series.name}</b><br/>Targeted: ${this.x.toFixed(1)}%<br/>Captured: ${this.y.toFixed(1)}%<br/>Lift vs. random: ${lift}×`;
    },
  },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
  },
  series: [
    {
      name: "Fraud Risk Model",
      type: "area",
      data: modelGains,
      color: t.palette[0],
      fillOpacity: 0.15,
      threshold: 0,
      lineWidth: 3,
      zIndex: 2,
    },
    {
      name: "Random Selection",
      type: "line",
      data: baselineGains,
      color: t.ink,
      lineWidth: 2,
      dashStyle: "Dash",
      zIndex: 3,
    },
  ],
});
