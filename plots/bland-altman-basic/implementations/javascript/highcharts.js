// anyplot.ai
// bland-altman-basic: Bland-Altman Agreement Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-11

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
let seed = 42;
function lcg() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}
function randNormal() {
  const u1 = lcg() || 1e-9;
  const u2 = lcg();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Paired systolic blood pressure readings from two sphygmomanometers
const pairCount = 90;
const points = [];
for (let i = 0; i < pairCount; i++) {
  const trueSystolic = 100 + lcg() * 80;
  const deviceA = trueSystolic + randNormal() * 4;
  const deviceB = trueSystolic + 2.5 + randNormal() * 5;
  const mean = (deviceA + deviceB) / 2;
  const diff = deviceA - deviceB;
  points.push([mean, diff]);
}

const diffs = points.map((p) => p[1]);
const bias = diffs.reduce((a, b) => a + b, 0) / diffs.length;
const variance =
  diffs.reduce((a, b) => a + (b - bias) ** 2, 0) / (diffs.length - 1);
const sd = Math.sqrt(variance);
const upperLoA = bias + 1.96 * sd;
const lowerLoA = bias - 1.96 * sd;

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    marginRight: 150,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "bland-altman-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: {
      text: "Mean of Two Devices (mmHg)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Difference: Device A − Device B (mmHg)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      {
        value: bias,
        color: t.ink,
        width: 2,
        dashStyle: "Solid",
        zIndex: 5,
        label: {
          text: `Bias: ${bias.toFixed(1)}`,
          align: "right",
          textAlign: "left",
          x: 14,
          y: 4,
          style: { color: t.ink, fontSize: "14px", fontWeight: "600" },
        },
      },
      {
        value: upperLoA,
        color: t.inkSoft,
        width: 1.5,
        dashStyle: "Dash",
        zIndex: 5,
        label: {
          text: `+1.96 SD: ${upperLoA.toFixed(1)}`,
          align: "right",
          textAlign: "left",
          x: 14,
          y: 4,
          style: { color: t.inkSoft, fontSize: "14px" },
        },
      },
      {
        value: lowerLoA,
        color: t.inkSoft,
        width: 1.5,
        dashStyle: "Dash",
        zIndex: 5,
        label: {
          text: `−1.96 SD: ${lowerLoA.toFixed(1)}`,
          align: "right",
          textAlign: "left",
          x: 14,
          y: 4,
          style: { color: t.inkSoft, fontSize: "14px" },
        },
      },
    ],
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: {
        radius: 5,
        fillOpacity: 0.55,
        lineWidth: 1,
        lineColor: t.pageBg,
      },
    },
  },
  series: [
    {
      name: "Paired Measurements",
      data: points,
      color: t.palette[0],
    },
  ],
});
