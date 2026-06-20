// anyplot.ai
// curve-oc: Operating Characteristic (OC) Curve
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-20

const t = window.ANYPLOT_TOKENS;

// Binomial CDF: P(X ≤ c | n, p) via log-space for numerical stability
function probAccept(n, c, p) {
  if (p <= 0) return 1.0;
  if (p >= 1) return 0.0;
  const logP = Math.log(p);
  const logQ = Math.log(1 - p);
  let prob = 0;
  for (let k = 0; k <= c; k++) {
    let logBinom = 0;
    for (let i = 0; i < k; i++) {
      logBinom += Math.log(n - i) - Math.log(i + 1);
    }
    prob += Math.exp(logBinom + k * logP + (n - k) * logQ);
  }
  return Math.min(1, Math.max(0, prob));
}

// Quality thresholds
const AQL   = 0.02;  // Acceptable Quality Level (2%)
const LTPD  = 0.08;  // Lot Tolerance Percent Defective (8%)
const X_MAX = 0.15;  // x-axis upper bound

// Three sampling plans — vary n and c to show discrimination power
const plans = [
  { n: 50,  c: 2, label: "n=50, c=2"  },
  { n: 100, c: 3, label: "n=100, c=3" },
  { n: 200, c: 5, label: "n=200, c=5" },
];

// Build 151 (p, Pa) pairs per sampling plan
function buildOCCurve(n, c) {
  const pts = [];
  for (let i = 0; i <= 150; i++) {
    const p = (i / 150) * X_MAX;
    pts.push({ x: p, y: probAccept(n, c, p) });
  }
  return pts;
}

// OC curve datasets — Imprint palette positions 0, 1, 2
const datasets = plans.map((plan, i) => ({
  label: plan.label,
  data: buildOCCurve(plan.n, plan.c),
  showLine: true,
  fill: false,
  borderColor: t.palette[i],
  backgroundColor: "transparent",
  borderWidth: 3,
  pointRadius: 0,
  tension: 0,
}));

// AQL vertical reference line — amber (warning/acceptable threshold)
datasets.push({
  label: `AQL (${(AQL * 100).toFixed(0)}%)`,
  data: [{ x: AQL, y: 0 }, { x: AQL, y: 1 }],
  showLine: true,
  fill: false,
  borderColor: t.amber,
  backgroundColor: "transparent",
  borderWidth: 2,
  borderDash: [10, 5],
  pointRadius: 0,
  tension: 0,
});

// LTPD vertical reference line — matte red (rejection threshold)
datasets.push({
  label: `LTPD (${(LTPD * 100).toFixed(0)}%)`,
  data: [{ x: LTPD, y: 0 }, { x: LTPD, y: 1 }],
  showLine: true,
  fill: false,
  borderColor: t.palette[4],
  backgroundColor: "transparent",
  borderWidth: 2,
  borderDash: [10, 5],
  pointRadius: 0,
  tension: 0,
});

// Mount
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Inline plugin: annotate α (producer's risk) and β (consumer's risk) from plan[0]
const riskLabels = {
  id: "riskLabels",
  afterDraw(chart) {
    const ctx = chart.ctx;
    const xsc = chart.scales.x;
    const ysc = chart.scales.y;
    const ref = plans[0];

    ctx.save();
    ctx.textBaseline = "middle";
    ctx.font = "bold 16px sans-serif";

    // α = producer's risk (probability of rejecting a good lot) at AQL
    const paAql = probAccept(ref.n, ref.c, AQL);
    ctx.fillStyle = t.amber;
    ctx.fillText(
      `α = ${(1 - paAql).toFixed(2)}`,
      xsc.getPixelForValue(AQL) + 10,
      ysc.getPixelForValue(paAql) - 14
    );

    // β = consumer's risk (probability of accepting a bad lot) at LTPD
    const paLtpd = probAccept(ref.n, ref.c, LTPD);
    ctx.fillStyle = t.palette[4];
    ctx.fillText(
      `β = ${paLtpd.toFixed(2)}`,
      xsc.getPixelForValue(LTPD) + 10,
      ysc.getPixelForValue(paLtpd) + 14
    );

    ctx.restore();
  },
};

// Chart
new Chart(canvas, {
  type: "scatter",
  plugins: [riskLabels],
  data: { datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "curve-oc · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { top: 12, bottom: 8 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          boxWidth: 30,
          padding: 20,
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: X_MAX,
        title: {
          display: true,
          text: "Fraction Defective (p)",
          color: t.ink,
          font: { size: 18 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (v) => (v * 100).toFixed(0) + "%",
          maxTicksLimit: 9,
        },
        grid: { color: t.grid },
      },
      y: {
        type: "linear",
        min: 0,
        max: 1,
        title: {
          display: true,
          text: "Probability of Acceptance",
          color: t.ink,
          font: { size: 18 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (v) => (v * 100).toFixed(0) + "%",
          maxTicksLimit: 6,
        },
        grid: { color: t.grid },
      },
    },
  },
});
